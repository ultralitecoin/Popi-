import unittest
import time

from fractal_blockchain.consensus.validator import BlockValidator, BlockValidationResult, MAX_FUTURE_TIME_SECONDS, HASH_REGEX
from fractal_blockchain.blockchain.block import FractalBlock, FractalBlockHeader, PlaceholderTransaction, create_genesis_block
from fractal_blockchain.core.addressing import AddressedFractalCoordinate
from fractal_blockchain.structures.merkle import build_merkle_tree_from_hashes, hash_data
import json

# Mock time for testing timestamp validation
MOCKED_CURRENT_TIME = time.time()

def mock_time_provider():
    return MOCKED_CURRENT_TIME

class TestBlockValidator(unittest.TestCase):

    def setUp(self):
        self.validator = BlockValidator(current_time_provider=mock_time_provider)
        self.genesis_block = create_genesis_block()

        # Prepare a standard valid child block relative to genesis
        self.tx1 = PlaceholderTransaction(id="tx_child_1", data={"val": 100})
        self.tx_list = [self.tx1]
        # Use same separators as in validator for consistent hashing
        tx_hashes = [hash_data(json.dumps(tx.to_json_serializable(), sort_keys=True, separators=(',',':'))) for tx in self.tx_list]
        self.merkle_root = build_merkle_tree_from_hashes(tx_hashes).value if tx_hashes else None

        self.child_coord = AddressedFractalCoordinate(1, (0,)) # Child of Genesis (0,())
        self.valid_child_header = FractalBlockHeader(
            parent_hash=self.genesis_block.block_hash,
            timestamp=MOCKED_CURRENT_TIME + 10, # Slightly after genesis/mocked current time
            depth=1,
            coordinate=self.child_coord,
            merkle_root_transactions=self.merkle_root,
            nonce=123
        )
        self.valid_child_block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)

    def test_validate_block_structure_timestamp_too_future(self):
        self.valid_child_header.timestamp = MOCKED_CURRENT_TIME + MAX_FUTURE_TIME_SECONDS + 100
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        self.assertIn("too far in the future", result.error_messages[0])

    def test_validate_block_structure_timestamp_in_past_ok_without_context(self):
        # Without parent_block_timestamp or max_drift_past_seconds, past timestamp is okay by this func
        self.valid_child_header.timestamp = MOCKED_CURRENT_TIME - 1000
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertTrue(result.is_valid) # No error if no past constraint given

    def test_validate_block_structure_timestamp_too_past_with_max_drift(self):
        self.valid_child_header.timestamp = MOCKED_CURRENT_TIME - 1000
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block, max_drift_past_seconds=500)
        self.assertFalse(result.is_valid)
        self.assertIn("too far in the past", result.error_messages[0])

    def test_validate_block_structure_timestamp_not_greater_than_parent(self):
        # This check is primarily in validate_block_in_chain_context,
        # but structure_and_header can take parent_block_timestamp
        self.valid_child_header.timestamp = self.genesis_block.header.timestamp # Same as parent
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block, parent_block_timestamp=self.genesis_block.header.timestamp)
        self.assertFalse(result.is_valid)
        self.assertIn("not greater than parent's timestamp", result.error_messages[0])

    def test_validate_block_structure_invalid_coordinate_geometry(self):
        # Mock is_valid_addressed_coordinate to return False for a specific coord
        # The module is fractal_blockchain.consensus.validator, function is is_valid_addressed_coordinate
        validator_module = __import__('fractal_blockchain.consensus.validator', fromlist=['is_valid_addressed_coordinate'])
        original_is_valid_coord = validator_module.is_valid_addressed_coordinate

        def mock_is_valid_coord_false(coord):
            if coord == self.child_coord: return False
            return True # True for others

        validator_module.is_valid_addressed_coordinate = mock_is_valid_coord_false

        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        self.assertIn("not geometrically valid", result.error_messages[0])

        validator_module.is_valid_addressed_coordinate = original_is_valid_coord


    def test_validate_block_structure_invalid_parent_hash_format(self):
        self.valid_child_header.parent_hash = "not_a_hash"
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        self.assertIn("invalid format", result.error_messages[0])

    def test_validate_block_structure_mismatched_merkle_root(self):
        self.valid_child_header.merkle_root_transactions = "completely_wrong_root"
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        self.assertIn("does not match calculated root", result.error_messages[0])

    def test_validate_block_structure_merkle_root_none_with_transactions(self):
        self.valid_child_header.merkle_root_transactions = None # Should have a root
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        # The error will be "does not match calculated root" because calculated will not be None
        self.assertIn("does not match calculated root", result.error_messages[0])

    def test_validate_block_structure_merkle_root_not_none_empty_transactions(self):
        self.valid_child_header.merkle_root_transactions = "some_root"
        block = FractalBlock(header=self.valid_child_header, transactions=[]) # No TXs
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        self.assertIn("Block has no transactions, but merkle_root_transactions is not None", result.error_messages[0])

    def test_validate_block_structure_valid_empty_transactions(self):
        self.valid_child_header.merkle_root_transactions = None
        block = FractalBlock(header=self.valid_child_header, transactions=[])
        result = self.validator.validate_block_structure_and_header(block)
        self.assertTrue(result.is_valid, result.error_messages)


    def test_validate_block_in_chain_context_valid(self):
        result = self.validator.validate_block_in_chain_context(self.valid_child_block, self.genesis_block)
        self.assertTrue(result.is_valid, result.error_messages)

    def test_validate_block_in_chain_context_wrong_parent_hash(self):
        self.valid_child_header.parent_hash = "000" + "1"*61 # Wrong hash
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_in_chain_context(block, self.genesis_block)
        self.assertFalse(result.is_valid)
        self.assertIn("does not match actual parent's hash", result.error_messages[0])

    def test_validate_block_in_chain_context_wrong_depth(self):
        self.valid_child_header.depth = self.genesis_block.header.depth + 2 # Skipped a depth
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_in_chain_context(block, self.genesis_block)
        self.assertFalse(result.is_valid)
        self.assertIn(f"Block depth {self.valid_child_header.depth} is not parent depth {self.genesis_block.header.depth} + 1", result.error_messages[0])

    def test_validate_block_in_chain_context_invalid_child_coordinate_relation(self):
        # Test scenario: Parent P has coordinate (depth=1, path=(0,))
        # Child C has coordinate (depth=2, path=(1,0))
        # Child C's path prefix (1,) does not match Parent P's path (0,).

        # Construct Parent P for this test
        parent_coord_p = AddressedFractalCoordinate(1,(0,))
        parent_header_p = FractalBlockHeader(
            parent_hash=self.genesis_block.block_hash, # P is child of Genesis for this setup
            timestamp=MOCKED_CURRENT_TIME + 5, # Sometime after Genesis
            depth=1,
            coordinate=parent_coord_p,
            merkle_root_transactions=None, # No tx for simplicity
            nonce=10
        )
        parent_block_p = FractalBlock(header=parent_header_p, transactions=[])

        # Construct Child C with invalid coordinate relation to P
        # Child C's merkle root can be the one from self.merkle_root (using self.tx_list)
        child_coord_c_invalid = AddressedFractalCoordinate(2, (1,0)) # Path prefix (1,)

        child_header_c = FractalBlockHeader(
            parent_hash=parent_block_p.block_hash, # Correctly points to P's hash
            timestamp=MOCKED_CURRENT_TIME + 15, # After P
            depth=2, # Correct depth: P.depth + 1
            coordinate=child_coord_c_invalid,   # Invalid relation: path prefix mismatch
            merkle_root_transactions=self.merkle_root,
            nonce=1234
        )
        child_block_c = FractalBlock(header=child_header_c, transactions=self.tx_list)

        result = self.validator.validate_block_in_chain_context(child_block_c, parent_block_p)
        self.assertFalse(result.is_valid, f"Validation should fail. Errors: {result.error_messages}")
        self.assertTrue(result.error_messages, "Error messages should not be empty.")
        # Ensure the specific error message about coordinate relation is present.
        # It might not be the *first* error if other preceding checks fail, but it should be there.
        expected_error_msg = f"Block coordinate {child_header_c.coordinate} is not a valid geometric child of parent {parent_header_p.coordinate}"
        self.assertTrue(any(expected_error_msg in msg for msg in result.error_messages),
                        f"Expected error '{expected_error_msg}' not found in {result.error_messages}")


    def test_validate_block_structure_child_ref_format(self):
        self.valid_child_header.child_block_references = {"invalid_key": "hash"} # type: ignore
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid child index", result.error_messages[0])

        self.valid_child_header.child_block_references = {0: 123} # type: ignore
        block2 = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result2 = self.validator.validate_block_structure_and_header(block2)
        self.assertFalse(result2.is_valid)
        self.assertIn("Child reference for index 0 is not a string", result2.error_messages[0])

    def test_validate_block_structure_nonce_type(self):
        self.valid_child_header.nonce = "not_an_int" # type: ignore
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        self.assertIn("Nonce is not an integer", result.error_messages[0])

    def test_validate_block_structure_geometric_proof_type(self):
        self.valid_child_header.geometric_proof = "not_bytes" # type: ignore
        block = FractalBlock(header=self.valid_child_header, transactions=self.tx_list)
        result = self.validator.validate_block_structure_and_header(block)
        self.assertFalse(result.is_valid)
        self.assertIn("Geometric proof is not bytes", result.error_messages[0])


if __name__ == '__main__':
    unittest.main()
