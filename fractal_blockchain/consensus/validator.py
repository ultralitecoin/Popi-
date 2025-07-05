# Block Validator for the Fractal Blockchain

import time
import re # For hash format validation
from typing import Optional, List, Tuple

from fractal_blockchain.blockchain.block import FractalBlock, FractalBlockHeader, PlaceholderTransaction
from fractal_blockchain.core.geometry_validator import is_valid_addressed_coordinate
from fractal_blockchain.structures.merkle import build_merkle_tree_from_hashes, hash_data
import json # For serializing transactions for Merkle root calculation


# --- Validation Rules (Conceptual List from Prompt Plan) ---
# 1. Header Integrity:
#    - Required fields present (dataclass handles).
#    - Timestamp reasonable.
# 2. Geometric Consistency:
#    - Coordinate valid for depth (AddressedFractalCoordinate constructor).
#    - Depth vs parent depth (needs parent context).
#    - Coordinate geometrically valid (is_valid_addressed_coordinate).
# 3. Cryptographic Checks:
#    - Merkle root of transactions.
# 4. Parent Linkage:
#    - parent_hash format.

# --- Constants for Validation ---
MAX_FUTURE_TIME_SECONDS = 2 * 60 * 60  # Max 2 hours in the future
HASH_REGEX = re.compile(r"^[a-f0-9]{64}$") # Standard SHA256 hex hash

class BlockValidationResult:
    def __init__(self, is_valid: bool, error_messages: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.error_messages = error_messages if error_messages is not None else []

    def __bool__(self):
        return self.is_valid

    def add_error(self, message: str):
        self.is_valid = False
        self.error_messages.append(message)

class BlockValidator:
    """
    Validates individual FractalBlocks based on a set of rules.
    Some rules might require context (e.g., parent block, current chain state)
    which can be passed to specific validation methods.
    """

    def __init__(self, current_time_provider: Optional[callable] = None):
        """
        Args:
            current_time_provider: A function that returns the current time (float timestamp).
                                   Defaults to time.time(). Useful for testing.
        """
        self.get_current_time = current_time_provider if current_time_provider else time.time

    def validate_block_structure_and_header(self, block: FractalBlock,
                                            max_drift_past_seconds: Optional[int] = None,
                                            parent_block_timestamp: Optional[float] = None
                                           ) -> BlockValidationResult:
        """
        Validates basic header integrity and structure.
        Args:
            block: The FractalBlock to validate.
            max_drift_past_seconds: Max time drift allowed into the past relative to parent or median time (if known).
                                    If None, no check against parent/median.
            parent_block_timestamp: Timestamp of the parent block, for relative time validation.
        """
        result = BlockValidationResult(True)
        header = block.header

        # 1. Timestamp Reasonableness
        current_time = self.get_current_time()
        if header.timestamp > current_time + MAX_FUTURE_TIME_SECONDS:
            result.add_error(f"Block timestamp {header.timestamp} is too far in the future (current: {current_time}).")

        if parent_block_timestamp is not None:
            if header.timestamp <= parent_block_timestamp:
                result.add_error(f"Block timestamp {header.timestamp} is not greater than parent's timestamp {parent_block_timestamp}.")
        elif max_drift_past_seconds is not None: # Only if no parent_block_timestamp to compare directly
            # This would typically use median time of recent blocks in a real chain.
            # For a single block, can compare to current_time - drift.
            if header.timestamp < current_time - max_drift_past_seconds:
                 result.add_error(f"Block timestamp {header.timestamp} is too far in the past (current: {current_time}, drift: {max_drift_past_seconds}).")


        # 2. Geometric Consistency
        # AddressedFractalCoordinate constructor already validates path length vs depth.
        if not is_valid_addressed_coordinate(header.coordinate):
            result.add_error(f"Block coordinate {header.coordinate} is not geometrically valid.")

        # Depth vs parent depth: Requires parent block.
        # This check is better suited for validate_block_in_chain_context.

        # 3. Parent Hash Format
        if not HASH_REGEX.fullmatch(header.parent_hash):
            result.add_error(f"Parent hash '{header.parent_hash}' has invalid format.")

        # 4. Merkle Root of Transactions
        # This is calculated and compared, not just format checked.
        if block.transactions:
            calculated_merkle_root = self._calculate_tx_merkle_root(block.transactions)
            if header.merkle_root_transactions != calculated_merkle_root:
                result.add_error(f"Header merkle_root_transactions '{header.merkle_root_transactions}' "
                                 f"does not match calculated root '{calculated_merkle_root}'.")
        elif header.merkle_root_transactions is not None:
            # If there are no transactions, Merkle root should be None (or a pre-defined empty hash)
            result.add_error("Block has no transactions, but merkle_root_transactions is not None.")

        # 5. Child Block References (Format Check)
        for child_idx, child_ref in header.child_block_references.items():
            if not isinstance(child_idx, int) or not (0 <= child_idx <= 3):
                result.add_error(f"Invalid child index '{child_idx}' in child_block_references.")
            if not isinstance(child_ref, str): # Assuming refs are hashes or string identifiers
                result.add_error(f"Child reference for index {child_idx} is not a string: '{child_ref}'.")
            # Further validation if refs are hashes: check HASH_REGEX.

        # 6. Nonce and Geometric Proof (Basic type checks for now)
        if not isinstance(header.nonce, int):
            result.add_error(f"Nonce is not an integer: {header.nonce}.")
        if header.geometric_proof is not None and not isinstance(header.geometric_proof, bytes):
            result.add_error(f"Geometric proof is not bytes: {type(header.geometric_proof)}.")

        return result

    def _calculate_tx_merkle_root(self, transactions: List[PlaceholderTransaction]) -> Optional[str]:
        if not transactions:
            return None

        # Ensure consistent serialization for hashing transactions
        # Standard practice is to use transaction IDs (which are hashes of transaction content)
        # as leaves for the Merkle tree.
        if not transactions: # Should be caught by the caller, but good check
             return None

        tx_ids = [tx.id for tx in transactions] # Assuming tx objects are new Transaction type
        if not tx_ids: # Should not happen if transactions list is not empty
            return None

        merkle_root_node = build_merkle_tree_from_hashes(tx_ids)
        return merkle_root_node.value if merkle_root_node else None


    def validate_block_in_chain_context(self, block: FractalBlock, parent_block: FractalBlock) -> BlockValidationResult:
        """
        Validates a block against its parent in a chain context.
        Assumes block structure and header have already been partially validated by
        `validate_block_structure_and_header`.
        """
        result = self.validate_block_structure_and_header(block, parent_block_timestamp=parent_block.header.timestamp)
        if not result: # If basic validation already failed
            return result

        header = block.header
        parent_header = parent_block.header

        # 1. Parent Hash Match
        if header.parent_hash != parent_block.block_hash:
            result.add_error(f"Block's parent_hash '{header.parent_hash}' does not match actual parent's hash '{parent_block.block_hash}'.")

        # 2. Depth Progression
        if header.depth != parent_header.depth + 1:
            # This rule might be flexible if fractal structure allows non-sequential depth linking,
            # but for a simple chain, depth should increment.
            # Or, if linking to a void parent, depth might be same or +1 depending on rules.
            # For now, assume simple +1 progression from any parent type.
            result.add_error(f"Block depth {header.depth} is not parent depth {parent_header.depth} + 1.")

        # 3. Coordinate Relationship with Parent (Conceptual - Very Complex)
        # - Is `block.header.coordinate` a valid child of `parent_block.header.coordinate`?
        #   This involves checking if parent_block.header.coordinate.path is prefix of block.header.coordinate.path
        #   and the last digit of block.header.coordinate.path is a valid child index (0,1,2,3).
        #   AddressedFractalCoordinate structure already implies this if paths are correctly formed.
        #   We can add an explicit check.
        if not (block.header.coordinate.path[:-1] == parent_header.coordinate.path and \
                block.header.coordinate.depth == parent_header.coordinate.depth + 1 and \
                0 <= block.header.coordinate.path[-1] <= 3 ): # Path element 0,1,2,3
            # This check might be redundant if AddressedFractalCoordinate construction is strict
            # and parent-child relationships are built correctly.
            # However, it's a good sanity check for chain integrity.
            result.add_error(f"Block coordinate {header.coordinate} is not a valid geometric child of parent {parent_header.coordinate}.")


        # TODO: Add more context-dependent rules:
        # - Proof-of-Work / Proof-of-Stake validation (requires difficulty, etc.)
        # - Transaction execution and state change validation (requires state DB)
        # - Signature validation for transactions.
        # - Gas limits / block size limits.

        return result


if __name__ == '__main__':
    print("Block Validator Demo")
    validator = BlockValidator()

    # Create a Genesis block (assumed valid by definition for this demo)
    genesis_block = create_genesis_block()
    print(f"Genesis block hash: {genesis_block.block_hash}")

    # Create a valid child block
    tx1 = PlaceholderTransaction(id="tx_val_1", data={"val": 10})
    tx_hashes_val = [hash_data(json.dumps(tx1.to_json_serializable(), sort_keys=True))]
    m_root_val = build_merkle_tree_from_hashes(tx_hashes_val).value

    valid_child_coord = AddressedFractalCoordinate(1, (0,)) # Child of Genesis at (0,())
    valid_child_header = FractalBlockHeader(
        parent_hash=genesis_block.block_hash,
        timestamp=genesis_block.header.timestamp + 10,
        depth=1,
        coordinate=valid_child_coord,
        merkle_root_transactions=m_root_val,
        nonce=1
    )
    valid_child_block = FractalBlock(header=valid_child_header, transactions=[tx1])

    print(f"\nValidating well-formed child block (structurally):")
    val_res_struct = validator.validate_block_structure_and_header(valid_child_block)
    print(f"  Result: {val_res_struct.is_valid}, Errors: {val_res_struct.error_messages}")
    assert val_res_struct.is_valid

    print(f"\nValidating well-formed child block (in context of Genesis):")
    val_res_context = validator.validate_block_in_chain_context(valid_child_block, genesis_block)
    print(f"  Result: {val_res_context.is_valid}, Errors: {val_res_context.error_messages}")
    assert val_res_context.is_valid

    # Create a block with an invalid timestamp (too far in future)
    invalid_ts_header = FractalBlockHeader(
        parent_hash=genesis_block.block_hash,
        timestamp=time.time() + MAX_FUTURE_TIME_SECONDS * 2, # Way too future
        depth=1, coordinate=valid_child_coord, merkle_root_transactions=m_root_val
    )
    invalid_ts_block = FractalBlock(header=invalid_ts_header, transactions=[tx1])
    print(f"\nValidating block with future timestamp:")
    val_res_ts = validator.validate_block_structure_and_header(invalid_ts_block)
    print(f"  Result: {val_res_ts.is_valid}, Errors: {val_res_ts.error_messages}")
    assert not val_res_ts.is_valid
    assert "too far in the future" in val_res_ts.error_messages[0]

    # Create a block with incorrect Merkle root
    incorrect_merkle_header = FractalBlockHeader(
        parent_hash=genesis_block.block_hash, timestamp=time.time()+20, depth=1,
        coordinate=valid_child_coord, merkle_root_transactions="wrong_root"
    )
    incorrect_merkle_block = FractalBlock(header=incorrect_merkle_header, transactions=[tx1])
    print(f"\nValidating block with incorrect Merkle root:")
    val_res_merkle = validator.validate_block_structure_and_header(incorrect_merkle_block)
    print(f"  Result: {val_res_merkle.is_valid}, Errors: {val_res_merkle.error_messages}")
    assert not val_res_merkle.is_valid
    assert "does not match calculated root" in val_res_merkle.error_messages[0]

    # Create a block with invalid parent hash in context
    invalid_parent_link_header = FractalBlockHeader(
        parent_hash="clearly_not_genesis_hash" + "0"*(64-len("clearly_not_genesis_hash")),
        timestamp=time.time()+30, depth=1, coordinate=valid_child_coord, merkle_root_transactions=m_root_val
    )
    invalid_parent_link_block = FractalBlock(header=invalid_parent_link_header, transactions=[tx1])
    print(f"\nValidating block with incorrect parent hash (in context):")
    val_res_parent_link = validator.validate_block_in_chain_context(invalid_parent_link_block, genesis_block)
    print(f"  Result: {val_res_parent_link.is_valid}, Errors: {val_res_parent_link.error_messages}")
    assert not val_res_parent_link.is_valid
    assert "does not match actual parent's hash" in val_res_parent_link.error_messages[0]

    print("\nPrompt 10 BlockValidator initial structure and some rules implemented.")
