# Fractal Merkle Tree Structure

import hashlib
from typing import List, Tuple, Optional, Dict, Any, Union

from fractal_blockchain.core.addressing import AddressedFractalCoordinate
# We'll need a way to get children or relevant data points for a given fractal coordinate/level
from fractal_blockchain.core.mathematics.fractal_math import get_children as get_solid_children_coords

# Prompt 6: Design fractal merkle tree structure.
# - Each fractal level maintains its own merkle root (conceptually).
# - Void positions serve as merkle coordinators (aggregators).
# - Hierarchical merkle forests, allowing cross-level verification.
# - Hash aggregation functions for efficient root computation.
# - Merkle proof generation tailored to fractal structure.

# Helper function for hashing
def hash_data(data: Union[str, bytes]) -> str:
    """Computes SHA256 hash of the given data."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def hash_pair(hash1: str, hash2: str) -> str:
    """Hashes a concatenated pair of hex digests."""
    # Ensure consistent order for hashing pairs if not intrinsically ordered
    # For Merkle trees, order usually matters (left child, right child)
    # If order doesn't matter or is handled by input, simple concatenation is fine.
    # Here, we'll assume order is managed by the caller (e.g. sorted hashes if items are unordered)
    return hash_data(hash1 + hash2)


class FractalMerkleNode:
    """Represents a node in a standard Merkle tree (can be part of the fractal structure)."""
    def __init__(self, value: str,
                 left_child: Optional['FractalMerkleNode'] = None,
                 right_child: Optional['FractalMerkleNode'] = None):
        self.value = value # Hash value of the node
        self.left = left_child
        self.right = right_child

    def __repr__(self) -> str:
        return f"MerkleNode({self.value[:8]}..)"

def build_merkle_tree_from_hashes(data_hashes: List[str]) -> Optional[FractalMerkleNode]:
    """
    Builds a standard Merkle tree from a list of data hashes (leaves).
    Returns the root node of the Merkle tree.
    """
    if not data_hashes:
        return None

    nodes: List[FractalMerkleNode] = [FractalMerkleNode(h) for h in data_hashes]

    while len(nodes) > 1:
        if len(nodes) % 2 != 0:
            # Duplicate the last node if the number of nodes is odd
            nodes.append(nodes[-1])

        new_level_nodes: List[FractalMerkleNode] = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i+1]
            parent_hash = hash_pair(left.value, right.value)
            parent_node = FractalMerkleNode(parent_hash, left_child=left, right_child=right)
            new_level_nodes.append(parent_node)
        nodes = new_level_nodes

    return nodes[0] if nodes else None


# --- Fractal-Specific Merkle Logic ---
# This part is more conceptual for Phase 1 math foundation.
# How data at fractal coordinates (or entire sub-fractals) is aggregated.

# "Each fractal level maintains its own merkle root."
# This could mean that for a given depth D, all 3^D solid triangles (or data associated with them)
# form a Merkle tree, and its root is "the Merkle root for depth D".

# "Void positions serve as merkle coordinators (aggregators)."
# This is interesting. A void, defined by AddressedFractalCoordinate(..., path=(...,3,...)),
# could itself hold a Merkle root that aggregates information from its "child regions"
# (which would be the 3 solid triangles and 1 central void formed by subdividing the space
# that this void occupies).

class FractalLevelMerkleTree:
    """
    Manages Merkle roots related to fractal geometry.
    This is a high-level concept for now.
    """
    def __init__(self):
        # Stores Merkle roots, perhaps indexed by AddressedFractalCoordinate (e.g., a void acting as coordinator)
        # or by depth level.
        self.merkle_roots: Dict[Any, str] = {}
        # self.data_at_coords: Dict[AddressedFractalCoordinate, Any] = {} # Raw data

    def get_data_hash_for_coord(self, coord: AddressedFractalCoordinate, data_payload: Any) -> str:
        """
        Computes the hash for data associated with a specific fractal coordinate.
        The data_payload could be transactions, state, etc.
        The coordinate itself might be part of the hashed data to bind it.
        """
        # Example: hash(coord_string_representation + data_payload_string)
        coord_str = f"d{coord.depth}p{''.join(map(str, coord.path))}"
        payload_str = str(data_payload) # Simplistic serialization
        return hash_data(coord_str + payload_str)

    def calculate_merkle_root_for_children(self, parent_coord: AddressedFractalCoordinate, children_data: Dict[AddressedFractalCoordinate, Any]) -> Optional[str]:
        """
        Calculates a Merkle root for data associated with children of a parent_coord.
        'children_data' provides the data for each child coordinate.

        This is a simplified model. In reality, which children are included (solid, void?)
        and how they are ordered for Merkle tree construction needs careful definition.
        """
        if not children_data:
            return None

        # For simplicity, let's assume children are ordered by their path's last digit (0,1,2 for solid)
        # Or, if it's a void being subdivided, its "children" could be the 3 solid + 1 void sub-regions.

        child_hashes: List[str] = []
        # Sort children by path to ensure consistent hash order for the Merkle tree
        sorted_children_coords = sorted(children_data.keys(), key=lambda c: c.path)

        for child_coord in sorted_children_coords:
            data = children_data[child_coord]
            child_hashes.append(self.get_data_hash_for_coord(child_coord, data))

        if not child_hashes:
            return None

        merkle_tree_root_node = build_merkle_tree_from_hashes(child_hashes)
        return merkle_tree_root_node.value if merkle_tree_root_node else None


    # "Hierarchical merkle forests, allowing cross-level verification."
    # This implies that the Merkle root of a parent fractal region (e.g., a void coordinator)
    # might be calculated from the Merkle roots of its constituent sub-regions (children).
    # Example: MerkleRoot(Void_X) = Hash( MerkleRoot(Child0_of_X), MerkleRoot(Child1_of_X), ... )

    def update_merkle_root_for_void_coordinator(self, void_coord: AddressedFractalCoordinate,
                                                constituent_merkle_roots: List[str]) -> Optional[str]:
        """
        A void coordinator's Merkle root is formed from the Merkle roots of the regions it coordinates.
        `constituent_merkle_roots` are the roots of its 3 child triangles and 1 child void (if that's the model).
        """
        if not void_coord.is_void_path() and 3 not in void_coord.path : # Simplified check if it's a void, needs better type
             # This function is intended for void coordinators.
             # However, AddressedFractalCoordinate.is_void_path() checks if *any* part is void.
             # We might need a more specific "is_terminal_void_coord()" check.
             # For now, let's assume void_coord is indeed a void space.
             pass

        if not constituent_merkle_roots:
            return None

        # The order of constituent_merkle_roots must be well-defined.
        # E.g., [root_child0, root_child1, root_child2, root_child_void_center]
        merkle_tree_root_node = build_merkle_tree_from_hashes(constituent_merkle_roots)
        if merkle_tree_root_node:
            self.merkle_roots[void_coord] = merkle_tree_root_node.value
            return merkle_tree_root_node.value
        return None

    # "Merkle proof generation tailored to fractal structure."
    # This would involve providing the necessary sibling hashes along a path from a leaf
    # up to a known Merkle root (which could be a level root or a void coordinator's root).
    # Standard Merkle proof algorithms can be adapted.

    def generate_merkle_proof(self, leaf_hash: str, tree_root_node: FractalMerkleNode) -> Optional[List[Tuple[str, str]]]:
        """
        Generates a Merkle proof for a leaf_hash given the tree's root_node.
        Proof consists of sibling hashes needed to reconstruct the root.
        Each tuple in the list is (sibling_hash, direction_left_right).
        """
        proof: List[Tuple[str, str]] = []

        node = tree_root_node
        # This requires finding the leaf_hash in the tree first, or assuming its path is known.
        # A full implementation needs to traverse to find the leaf or its parent.
        # This is a simplified conceptual outline.

        # Simplified: if we had the path of nodes from leaf to root:
        # For each node on path from leaf's parent up to root's child:
        #   if current_node is left child of its parent: add parent.right.value to proof
        #   if current_node is right child of its parent: add parent.left.value to proof

        # Proper proof generation is non-trivial from just root and leaf hash without tree structure access.
        # It's usually done during tree construction or with full tree access.
        # For now, this is a placeholder for the concept.
        # if tree_root_node and tree_root_node.value == leaf_hash and not tree_root_node.left and not tree_root_node.right:
        #      return [] # Leaf is the root - this is valid, but for placeholder simplicity, always None for now.

        # Placeholder: actual implementation is more involved.
        # print(f"Placeholder: Merkle proof generation for {leaf_hash} in tree {tree_root_node}") # Reduce noise
        # return None # Placeholder always returns None until fully implemented. #-- Replacing this

        proof_path: List[Tuple[str, str]] = []

        # Helper function to find the path from root to leaf and collect sibling hashes
        def find_path_and_collect_siblings(current_node: Optional[FractalMerkleNode], target_hash: str) -> bool:
            if not current_node:
                return False

            if current_node.value == target_hash and not current_node.left and not current_node.right:
                # We are at the leaf node. Path collection happens on the way up.
                return True

            if current_node.left:
                if find_path_and_collect_siblings(current_node.left, target_hash):
                    if current_node.right: # Should exist if left exists in a proper Merkle tree branch
                        proof_path.append((current_node.right.value, "right")) # current_node.left was on path, so right is sibling
                    # Else: if no right child, implies an unbalanced tree or last node duplication,
                    # which build_merkle_tree_from_hashes handles by pairing with itself.
                    # This case should be consistent with how tree was built.
                    # If build_merkle_tree_from_hashes duplicates N-1 to pair with N, then N-1's sibling is N-1.
                    # The current build_merkle_tree_from_hashes ensures pairs.
                    return True

            if current_node.right:
                if find_path_and_collect_siblings(current_node.right, target_hash):
                    if current_node.left: # Should exist
                        proof_path.append((current_node.left.value, "left")) # current_node.right was on path, so left is sibling
                    return True

            return False

        if not tree_root_node:
            return None # Or empty list if preferred for "no proof possible"

        if tree_root_node.value == leaf_hash and not tree_root_node.left and not tree_root_node.right:
            return [] # Leaf is the root, proof is empty

        found = find_path_and_collect_siblings(tree_root_node, leaf_hash)

        if not found:
            return None # Leaf hash not found in the tree

        return proof_path # Siblings are collected in order from leaf's sibling upwards.

    def verify_merkle_proof(self, leaf_hash: str, proof: List[Tuple[str, str]], expected_root_hash: str) -> bool:
        """
        Verifies a Merkle proof for a leaf_hash against an expected_root_hash.
        `proof` is a list of (sibling_hash, "left" or "right") tuples indicating if the current hash
        was the left or right input with the sibling to compute the next level hash.
        """
        current_hash = leaf_hash
        for sibling_hash, direction in proof:
            if direction == "left": # current_hash is on the right
                current_hash = hash_pair(sibling_hash, current_hash)
            elif direction == "right": # current_hash is on the left
                current_hash = hash_pair(current_hash, sibling_hash)
            else:
                raise ValueError("Direction in proof must be 'left' or 'right'.")
        return current_hash == expected_root_hash


if __name__ == '__main__':
    print("Fractal Merkle Tree Structure Demo")

    # --- Standard Merkle Tree Demo ---
    data_items = ["item1", "item2", "item3", "item4", "item5"]
    data_item_hashes = [hash_data(d) for d in data_items]
    print(f"\nData item hashes: {[(h[:6] + '..') for h in data_item_hashes]}")

    merkle_root_node = build_merkle_tree_from_hashes(data_item_hashes)
    if merkle_root_node:
        print(f"Merkle Root: {merkle_root_node.value}")

        # Simple proof verification demo (manual proof)
        # For item1 (leaf_hash = data_item_hashes[0])
        # Assume tree structure for data_items = [h0, h1, h2, h3, h4, h4_dup]
        # Level 0: [h0, h1, h2, h3, h4, h4] (nodes)
        # Level 1: [h01, h23, h44] (parents) where h01=hash(h0,h1) etc.
        # Level 2: [h0123, h4444] (h44 is duplicated as h44_dup for h4444)
        #          where h0123=hash(h01,h23), h4444=hash(h44,h44_dup)
        # Level 3: [h01234444] (root) hash(h0123, h4444)

        leaf_to_prove = data_item_hashes[0] # h0
        h1 = data_item_hashes[1]
        h01 = hash_pair(leaf_to_prove, h1)

        h2 = data_item_hashes[2]
        h3 = data_item_hashes[3]
        h23 = hash_pair(h2, h3)

        h0123 = hash_pair(h01, h23)

        h4 = data_item_hashes[4]
        h4_dup = h4 # Odd number handling duplicates last item
        h44 = hash_pair(h4, h_dup)
        h44_dup = h44 # For the next level if h44 itself is odd one out (not in this specific case of 3 nodes at L1)
                      # If L1 was [h01, h23, h44], then h44 is duplicated, h4444 = hash(h44, h44)

        # Correcting the manual trace for 5 items:
        # L0: [h0, h1, h2, h3, h4]
        # Nodes: [N0, N1, N2, N3, N4]
        # L0_padded: [N0, N1, N2, N3, N4, N4] (N4 is duplicated)
        # L1_parents: [P01(N0,N1), P23(N2,N3), P44(N4,N4)]
        # L1_padded: [P01, P23, P44, P44] (P44 is duplicated)
        # L2_parents: [P0123(P01,P23), P4444(P44,P44)]
        # L3_parent (ROOT): [R(P0123, P4444)]

        # Proof for h0 (data_item_hashes[0]):
        # 1. Sibling h1, h0 is on 'left' -> hash(h0,h1) = P01
        # 2. Sibling P23, P01 is on 'left' -> hash(P01,P23) = P0123
        # 3. Sibling P4444, P0123 is on 'left' -> hash(P0123,P4444) = ROOT

        manual_proof_for_h0 = [
            (data_item_hashes[1], "right"), # h1 is to the right of h0
            (hash_pair(data_item_hashes[2], data_item_hashes[3]), "right"), # P23 is to the right of P01
            (hash_pair(hash_pair(data_item_hashes[4],data_item_hashes[4]), hash_pair(data_item_hashes[4],data_item_hashes[4])), "right") # P4444 is to the right of P0123
        ]
        # The last hash in manual_proof_for_h0 is complex: P44 = hash(h4,h4). P4444 = hash(P44, P44_dup_from_L1)
        # If L1 nodes are [P01, P23, P44], then P44 is duplicated for L2 pairing. So P44_dup_from_L1 = P44.
        # Thus P4444 = hash(P44, P44).
        p44_val = hash_pair(data_item_hashes[4], data_item_hashes[4])
        p4444_val = hash_pair(p44_val, p44_val)

        manual_proof_for_h0_corrected = [
            (data_item_hashes[1], "right"),
            (hash_pair(data_item_hashes[2], data_item_hashes[3]), "right"),
            (p4444_val, "right")
        ]

        merkle_manager = FractalLevelMerkleTree() # For verify_merkle_proof method
        is_valid = merkle_manager.verify_merkle_proof(leaf_to_prove, manual_proof_for_h0_corrected, merkle_root_node.value)
        print(f"Verification of manual proof for h0: {is_valid}")
        assert is_valid

    # --- Fractal Specific Demo (Conceptual) ---
    print("\n--- Fractal Merkle Concepts (Demo) ---")
    fractal_merkle_manager = FractalLevelMerkleTree()

    # Data for children of a hypothetical parent_coord
    parent = AddressedFractalCoordinate(0, tuple()) # Genesis
    child0 = AddressedFractalCoordinate(1, (0,))
    child1 = AddressedFractalCoordinate(1, (1,))
    child2 = AddressedFractalCoordinate(1, (2,))

    children_data_map = {
        child0: "data_for_child0",
        child1: "data_for_child1",
        child2: "data_for_child2"
    }

    children_merkle_root = fractal_merkle_manager.calculate_merkle_root_for_children(parent, children_data_map)
    if children_merkle_root:
        print(f"Merkle root for children of {parent}: {children_merkle_root}")

    # Demo for void coordinator
    # Assume void_coord_d1p3 is AddressedFractalCoordinate(1,(3,))
    # Its constituent regions could be its own "children" if it were subdivided.
    # Let's say we have pre-calculated Merkle roots for these 4 sub-regions:
    # mr_solid0, mr_solid1, mr_solid2, mr_central_void
    # These would be roots of Merkle trees over data in those sub-regions.

    void_coord = AddressedFractalCoordinate(1, (3,)) # The main void at depth 1
    # Roots of the 3 solid children + 1 central void that would form if this void_coord region was subdivided.
    # These are hypothetical roots for this example.
    mock_sub_region_roots = [
        hash_data("root_of_sub_solid0_in_void"),
        hash_data("root_of_sub_solid1_in_void"),
        hash_data("root_of_sub_solid2_in_void"),
        hash_data("root_of_sub_void_in_void")
    ]

    void_coordinator_root = fractal_merkle_manager.update_merkle_root_for_void_coordinator(void_coord, mock_sub_region_roots)
    if void_coordinator_root:
        print(f"Merkle root for void coordinator {void_coord}: {void_coordinator_root}")
        stored_root = fractal_merkle_manager.merkle_roots.get(void_coord)
        print(f"Stored root for {void_coord}: {stored_root}")
        assert stored_root == void_coordinator_root

    print("\nPrompt 6 Merkle tree structure initial concepts are in place.")
    print("Full proof generation and fractal integration are more involved.")
