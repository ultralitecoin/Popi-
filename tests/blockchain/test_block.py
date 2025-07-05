import unittest
import time
import hashlib
import json

from fractal_blockchain.blockchain.block import (
    FractalBlockHeader, FractalBlock, PlaceholderTransaction, create_genesis_block
)
from fractal_blockchain.core.addressing import AddressedFractalCoordinate
from fractal_blockchain.structures.merkle import build_merkle_tree_from_hashes, hash_data


class TestBlockStructure(unittest.TestCase):

    def test_placeholder_transaction(self):
        tx = PlaceholderTransaction(id="tx001", data={"value": 100})
        self.assertEqual(tx.id, "tx001")
        self.assertEqual(tx.to_json_serializable(), {"id": "tx001", "data": {"value": 100}})

    def test_fractal_block_header_creation_and_hash(self):
        coord = AddressedFractalCoordinate(1, (0,))
        ts = time.time()
        header1 = FractalBlockHeader(
            parent_hash="0"*64,
            timestamp=ts,
            depth=1,
            coordinate=coord,
            merkle_root_transactions="merkle_placeholder",
            child_block_references={0: "child0_hash", 1: "child1_hash"},
            geometric_proof=b"geom_proof",
            nonce=123
        )

        # Test basic attributes
        self.assertEqual(header1.depth, 1)
        self.assertEqual(header1.coordinate, coord)
        self.assertEqual(header1.nonce, 123)

        # Test hash calculation (consistency)
        hash1 = header1.calculate_hash()
        self.assertIsNotNone(hash1)
        self.assertEqual(len(hash1), 64) # SHA256 hex

        header1_copy = FractalBlockHeader(
            parent_hash="0"*64, timestamp=ts, depth=1, coordinate=coord,
            merkle_root_transactions="merkle_placeholder",
            child_block_references={0: "child0_hash", 1: "child1_hash"},
            geometric_proof=b"geom_proof", nonce=123
        )
        self.assertEqual(header1_copy.calculate_hash(), hash1, "Hashes of identical headers should match")

        # Test that changing a field changes the hash
        header1_modified_nonce = FractalBlockHeader(
            parent_hash="0"*64, timestamp=ts, depth=1, coordinate=coord,
            merkle_root_transactions="merkle_placeholder",
            child_block_references={0: "child0_hash", 1: "child1_hash"},
            geometric_proof=b"geom_proof", nonce=124 # Changed nonce
        )
        self.assertNotEqual(header1_modified_nonce.calculate_hash(), hash1, "Changing nonce should change hash")

        header1_modified_children = FractalBlockHeader(
            parent_hash="0"*64, timestamp=ts, depth=1, coordinate=coord,
            merkle_root_transactions="merkle_placeholder",
            child_block_references={0: "child0_hash_MODIFIED"}, # Changed child ref
            geometric_proof=b"geom_proof", nonce=123
        )
        self.assertNotEqual(header1_modified_children.calculate_hash(), hash1, "Changing child refs should change hash")

        # Test with None for optional fields
        header_optional_none = FractalBlockHeader(
            parent_hash="0"*64, timestamp=ts, depth=1, coordinate=coord, nonce=0
        )
        hash_optional_none = header_optional_none.calculate_hash()
        self.assertIsNotNone(hash_optional_none)
        # Ensure it doesn't crash and that different None configurations hash differently if serialization matters
        header_optional_mrt = FractalBlockHeader(
            parent_hash="0"*64, timestamp=ts, depth=1, coordinate=coord, merkle_root_transactions="abc", nonce=0
        )
        self.assertNotEqual(header_optional_mrt.calculate_hash(), hash_optional_none)


    def test_fractal_block_creation_and_hash_access(self):
        coord = AddressedFractalCoordinate(1, (0,))
        ts = time.time()
        header = FractalBlockHeader(
            parent_hash="parent_example_hash",
            timestamp=ts,
            depth=1,
            coordinate=coord,
            merkle_root_transactions="tx_root_hash_example",
            nonce=101
        )

        tx_list = [
            PlaceholderTransaction(id="txA", data={"info": "A"}),
            PlaceholderTransaction(id="txB", data={"info": "B"})
        ]

        block = FractalBlock(header=header, transactions=tx_list)

        self.assertEqual(block.header, header)
        self.assertEqual(block.transactions, tx_list)
        self.assertEqual(block.block_hash, header.calculate_hash(), "Block's hash should be its header's hash")

    def test_create_genesis_block(self):
        genesis = create_genesis_block()

        self.assertIsInstance(genesis, FractalBlock)
        self.assertEqual(genesis.header.parent_hash, "0"*64)
        self.assertEqual(genesis.header.depth, 0)
        self.assertEqual(genesis.header.coordinate, AddressedFractalCoordinate(0, tuple()))
        self.assertEqual(genesis.transactions, [])
        self.assertIsNone(genesis.header.merkle_root_transactions)
        # self.assertEqual(genesis.header.nonce, 0) # Default genesis nonce
        self.assertIsNotNone(genesis.block_hash)

        # Test with a custom genesis coordinate (though unusual for main genesis)
        custom_coord = AddressedFractalCoordinate(0, tuple()) # Still standard for this test
        genesis_custom = create_genesis_block(genesis_coord=custom_coord)
        self.assertEqual(genesis_custom.header.coordinate, custom_coord)

    def test_block_and_header_to_dict(self):
        coord = AddressedFractalCoordinate(1, (0,))
        ts = time.time()
        header = FractalBlockHeader(
            parent_hash="parent123", timestamp=ts, depth=1, coordinate=coord,
            merkle_root_transactions="mrt123", geometric_proof=b"\x01\x02", nonce=77
        )
        header_dict = header.to_dict()

        self.assertEqual(header_dict['parent_hash'], "parent123")
        self.assertEqual(header_dict['coordinate'], {"depth": 1, "path": [0]}) # Check list for path
        self.assertEqual(header_dict['geometric_proof'], "0102") # Hex representation
        self.assertEqual(header_dict['nonce'], 77)

        txs = [PlaceholderTransaction(id="tx1", data={})]
        block = FractalBlock(header=header, transactions=txs)
        block_dict = block.to_dict()

        self.assertEqual(block_dict['header'], header_dict)
        self.assertEqual(len(block_dict['transactions']), 1)
        self.assertEqual(block_dict['transactions'][0]['id'], "tx1")


    def test_hash_consistency_with_sorted_child_refs(self):
        coord = AddressedFractalCoordinate(1, (0,))
        ts = time.time()

        header_children_sorted = FractalBlockHeader(
            parent_hash="p_hash", timestamp=ts, depth=1, coordinate=coord,
            child_block_references={0: "child0", 1: "child1", 2: "child2"} # Sorted by key
        )
        hash_sorted = header_children_sorted.calculate_hash()

        header_children_unsorted_keys = FractalBlockHeader(
            parent_hash="p_hash", timestamp=ts, depth=1, coordinate=coord,
            child_block_references={2: "child2", 0: "child0", 1: "child1"} # Unsorted by key
        )
        # The calculate_hash method sorts child_block_references by key before serializing
        hash_unsorted = header_children_unsorted_keys.calculate_hash()

        self.assertEqual(hash_sorted, hash_unsorted,
                         "Hash should be consistent regardless of initial dict order for child_block_references")


if __name__ == '__main__':
    unittest.main()
