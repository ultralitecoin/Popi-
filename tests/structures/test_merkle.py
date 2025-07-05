import unittest
from fractal_blockchain.structures.merkle import (
    hash_data, hash_pair,
    FractalMerkleNode, build_merkle_tree_from_hashes,
    FractalLevelMerkleTree
)
from fractal_blockchain.core.addressing import AddressedFractalCoordinate

class TestMerkleTree(unittest.TestCase):

    def test_hash_data(self):
        h1 = hash_data("hello")
        h2 = hash_data("hello")
        h3 = hash_data("world")
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertEqual(len(h1), 64) # SHA256 hex digest

        h_bytes = hash_data(b"hello bytes")
        self.assertEqual(len(h_bytes), 64)

    def test_hash_pair(self):
        h1 = hash_data("a")
        h2 = hash_data("b")
        pair_hash1 = hash_pair(h1, h2)
        pair_hash2 = hash_pair(h1, h2) # Same input, same output
        pair_hash_rev = hash_pair(h2, h1) # Different input order

        self.assertEqual(pair_hash1, pair_hash2)
        self.assertNotEqual(pair_hash1, pair_hash_rev) # Order matters
        self.assertEqual(len(pair_hash1), 64)

    def test_build_merkle_tree_from_hashes(self):
        # No hashes
        self.assertIsNone(build_merkle_tree_from_hashes([]))

        # Single hash
        h0 = hash_data("item0")
        root_single = build_merkle_tree_from_hashes([h0])
        self.assertIsNotNone(root_single)
        self.assertEqual(root_single.value, h0)
        self.assertIsNone(root_single.left)
        self.assertIsNone(root_single.right)

        # Two hashes
        h1 = hash_data("item1")
        root_two = build_merkle_tree_from_hashes([h0, h1])
        self.assertIsNotNone(root_two)
        self.assertEqual(root_two.value, hash_pair(h0, h1))
        self.assertIsNotNone(root_two.left)
        self.assertIsNotNone(root_two.right)
        self.assertEqual(root_two.left.value, h0)
        self.assertEqual(root_two.right.value, h1)

        # Three hashes (h2 duplicated)
        h2 = hash_data("item2")
        # Expected structure:
        #       Root
        #      /    \
        #   hash(h0,h1)  hash(h2,h2_dup)
        #   /   \        /    \
        #  h0   h1      h2    h2_dup
        root_three = build_merkle_tree_from_hashes([h0, h1, h2])
        self.assertIsNotNone(root_three)
        h01 = hash_pair(h0,h1)
        h22 = hash_pair(h2,h2) # h2 duplicated
        expected_root_val_three = hash_pair(h01, h22)
        self.assertEqual(root_three.value, expected_root_val_three)
        self.assertEqual(root_three.left.value, h01)
        self.assertEqual(root_three.right.value, h22)
        self.assertEqual(root_three.left.left.value, h0)
        self.assertEqual(root_three.left.right.value, h1)
        self.assertEqual(root_three.right.left.value, h2)
        self.assertEqual(root_three.right.right.value, h2) # Duplicated h2

        # Four hashes
        h3 = hash_data("item3")
        # Expected structure:
        #         Root
        #        /    \
        #   hash(h0,h1)  hash(h2,h3)
        #   /   \        /    \
        #  h0   h1      h2     h3
        root_four = build_merkle_tree_from_hashes([h0, h1, h2, h3])
        self.assertIsNotNone(root_four)
        h23 = hash_pair(h2,h3)
        expected_root_val_four = hash_pair(h01, h23)
        self.assertEqual(root_four.value, expected_root_val_four)


    def test_fractal_level_merkle_tree_get_data_hash_for_coord(self):
        manager = FractalLevelMerkleTree()
        coord = AddressedFractalCoordinate(1, (0,))
        data = "test_data"

        h = manager.get_data_hash_for_coord(coord, data)
        expected_hash_input = f"d{coord.depth}p{''.join(map(str, coord.path))}{data}"
        self.assertEqual(h, hash_data(expected_hash_input))

    def test_fractal_level_merkle_tree_calculate_merkle_root_for_children(self):
        manager = FractalLevelMerkleTree()
        parent = AddressedFractalCoordinate(0, tuple())
        c0 = AddressedFractalCoordinate(1, (0,))
        c1 = AddressedFractalCoordinate(1, (1,))
        data_c0 = "data0"
        data_c1 = "data1"

        children_data = {c0: data_c0, c1: data_c1}

        hash_c0 = manager.get_data_hash_for_coord(c0, data_c0)
        hash_c1 = manager.get_data_hash_for_coord(c1, data_c1)

        # Children are sorted by path for Merkle tree construction in the method.
        # (0,) comes before (1,)
        expected_root = hash_pair(hash_c0, hash_c1)

        actual_root = manager.calculate_merkle_root_for_children(parent, children_data)
        self.assertEqual(actual_root, expected_root)

        # Test with odd number of children
        c2 = AddressedFractalCoordinate(1, (2,))
        data_c2 = "data2"
        children_data_odd = {c0: data_c0, c1: data_c1, c2: data_c2}
        hash_c2 = manager.get_data_hash_for_coord(c2, data_c2)
        # Sorted hashes: [hash_c0, hash_c1, hash_c2]
        # Merkle tree: hash( hash(hash_c0,hash_c1), hash(hash_c2,hash_c2_dup) )
        h_c0c1 = hash_pair(hash_c0, hash_c1)
        h_c2c2 = hash_pair(hash_c2, hash_c2)
        expected_root_odd = hash_pair(h_c0c1, h_c2c2)
        actual_root_odd = manager.calculate_merkle_root_for_children(parent, children_data_odd)
        self.assertEqual(actual_root_odd, expected_root_odd)

        self.assertIsNone(manager.calculate_merkle_root_for_children(parent, {}))


    def test_fractal_level_merkle_tree_update_merkle_root_for_void_coordinator(self):
        manager = FractalLevelMerkleTree()
        void_coord = AddressedFractalCoordinate(1, (3,)) # A void

        sub_roots = [hash_data("r1"), hash_data("r2"), hash_data("r3")]
        # Expected Merkle root of these three sub_roots
        h_r1r2 = hash_pair(sub_roots[0], sub_roots[1])
        h_r3r3 = hash_pair(sub_roots[2], sub_roots[2]) # r3 duplicated
        expected_void_root = hash_pair(h_r1r2, h_r3r3)

        actual_void_root = manager.update_merkle_root_for_void_coordinator(void_coord, sub_roots)
        self.assertEqual(actual_void_root, expected_void_root)
        self.assertEqual(manager.merkle_roots.get(void_coord), expected_void_root)

        self.assertIsNone(manager.update_merkle_root_for_void_coordinator(void_coord, []))

    def test_verify_merkle_proof(self):
        manager = FractalLevelMerkleTree()
        # Data: h0, h1, h2, h3
        h = [hash_data(f"item{i}") for i in range(4)]

        # Tree:
        #      R
        #    /   \
        #  P01   P23
        # / \   / \
        # h0 h1 h2 h3
        p01 = hash_pair(h[0], h[1])
        p23 = hash_pair(h[2], h[3])
        root_val = hash_pair(p01, p23)

        # Proof for h[0] (item0)
        # Sibling h[1] is to the right. Sibling p23 is to the right.
        proof_h0 = [
            (h[1], "right"),  # Hash with h[1] (h[0] is left child of p01) -> p01
            (p23, "right")    # Hash p01 with p23 (p01 is left child of root_val) -> root_val
        ]
        self.assertTrue(manager.verify_merkle_proof(h[0], proof_h0, root_val))

        # Proof for h[2] (item2)
        # Sibling h[3] is to the right. Sibling p01 is to the left.
        proof_h2 = [
            (h[3], "right"), # Hash with h[3] (h[2] is left child of p23) -> p23
            (p01, "left")    # Hash p01 with p23 (p23 is right child of root_val) -> root_val
        ]
        self.assertTrue(manager.verify_merkle_proof(h[2], proof_h2, root_val))

        # Invalid proof
        invalid_proof_h0 = [
            (h[1], "right"),
            (hash_data("wrong_sibling"), "right")
        ]
        self.assertFalse(manager.verify_merkle_proof(h[0], invalid_proof_h0, root_val))

        # Proof for a leaf that is also the root
        single_leaf_hash = hash_data("single_item")
        self.assertTrue(manager.verify_merkle_proof(single_leaf_hash, [], single_leaf_hash))

        # Invalid direction
        with self.assertRaises(ValueError):
            manager.verify_merkle_proof(h[0], [(h[1], "up")], root_val)


    def test_generate_merkle_proof(self): # Renamed from test_generate_merkle_proof_placeholder
        manager = FractalLevelMerkleTree()

        # Test case 1: Leaf is the root
        h0 = hash_data("item0")
        root_is_leaf = FractalMerkleNode(h0)
        proof0 = manager.generate_merkle_proof(h0, root_is_leaf)
        self.assertIsNotNone(proof0)
        self.assertEqual(proof0, [])
        self.assertTrue(manager.verify_merkle_proof(h0, proof0, root_is_leaf.value))

        # Test case 2: Tree with 2 leaves
        #    R(h0,h1)
        #   /   \
        #  h0   h1
        h1 = hash_data("item1")
        root_two_leaves_node = build_merkle_tree_from_hashes([h0, h1])

        proof_h0_in_two = manager.generate_merkle_proof(h0, root_two_leaves_node)
        self.assertIsNotNone(proof_h0_in_two)
        self.assertEqual(proof_h0_in_two, [(h1, "right")])
        self.assertTrue(manager.verify_merkle_proof(h0, proof_h0_in_two, root_two_leaves_node.value))

        proof_h1_in_two = manager.generate_merkle_proof(h1, root_two_leaves_node)
        self.assertIsNotNone(proof_h1_in_two)
        self.assertEqual(proof_h1_in_two, [(h0, "left")])
        self.assertTrue(manager.verify_merkle_proof(h1, proof_h1_in_two, root_two_leaves_node.value))

        # Test case 3: Tree with 4 leaves
        #         R
        #       /   \
        #    P01     P23
        #   / \     / \
        #  h0 h1   h2 h3
        h2 = hash_data("item2")
        h3 = hash_data("item3")
        hashes_four = [h0, h1, h2, h3]
        root_four_leaves_node = build_merkle_tree_from_hashes(hashes_four)
        p01 = hash_pair(h0,h1)
        p23 = hash_pair(h2,h3)

        # Proof for h0
        proof_h0_in_four = manager.generate_merkle_proof(h0, root_four_leaves_node)
        expected_proof_h0_in_four = [(h1, "right"), (p23, "right")]
        self.assertEqual(proof_h0_in_four, expected_proof_h0_in_four)
        self.assertTrue(manager.verify_merkle_proof(h0, proof_h0_in_four, root_four_leaves_node.value))

        # Proof for h2
        proof_h2_in_four = manager.generate_merkle_proof(h2, root_four_leaves_node)
        expected_proof_h2_in_four = [(h3, "right"), (p01, "left")]
        self.assertEqual(proof_h2_in_four, expected_proof_h2_in_four)
        self.assertTrue(manager.verify_merkle_proof(h2, proof_h2_in_four, root_four_leaves_node.value))

        # Test case 4: Tree with 3 leaves (h2 duplicated)
        #       R
        #      / \
        #   P01   P22(h2,h2)
        #  / \   / \
        # h0 h1 h2 h2(dup)
        hashes_three = [h0, h1, h2]
        root_three_leaves_node = build_merkle_tree_from_hashes(hashes_three)
        p22 = hash_pair(h2,h2)

        # Proof for h1
        proof_h1_in_three = manager.generate_merkle_proof(h1, root_three_leaves_node)
        expected_proof_h1_in_three = [(h0, "left"), (p22, "right")]
        self.assertEqual(proof_h1_in_three, expected_proof_h1_in_three)
        self.assertTrue(manager.verify_merkle_proof(h1, proof_h1_in_three, root_three_leaves_node.value))

        # Proof for h2 (original h2, not the duplicated one)
        proof_h2_in_three = manager.generate_merkle_proof(h2, root_three_leaves_node)
        # h2 is left child of P22, P22's sibling is P01 (left of P22)
        # Sibling of h2 is the duplicated h2.
        expected_proof_h2_in_three = [(h2, "right"), (p01, "left")]
        self.assertEqual(proof_h2_in_three, expected_proof_h2_in_three)
        self.assertTrue(manager.verify_merkle_proof(h2, proof_h2_in_three, root_three_leaves_node.value))


        # Test case 5: Leaf not in tree
        hash_not_in_tree = hash_data("not_in_tree")
        proof_not_found = manager.generate_merkle_proof(hash_not_in_tree, root_four_leaves_node)
        self.assertIsNone(proof_not_found)

        # Test case 6: Empty tree (root is None)
        proof_empty_tree = manager.generate_merkle_proof(h0, None)
        self.assertIsNone(proof_empty_tree)


if __name__ == '__main__':
    unittest.main()
