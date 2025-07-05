# Fractal Network Topology Mapper

from typing import List, Optional, Set, Any
from fractal_blockchain.core.addressing import AddressedFractalCoordinate
# For geometric relationships, we might use functions from geometry_validator or fractal_math
from fractal_blockchain.core.mathematics.fractal_math import get_parent, get_children as get_solid_children_math
from fractal_blockchain.core.geometry_validator import get_neighbors as get_geometric_adjacencies


# Prompt 8: Create fractal network topology mapper.
# - Peer/node connections follow Sierpinski fractal pattern (adjacency).
# - Void nodes serve as natural relays and traffic balancers (implies voids can be network nodes).
# - Dynamic peer discovery using fractal coordinates.
# - Connection optimization maintaining geometric topology.
# - Load balancing and congestion avoidance algorithms.

# For Phase 1, this will be conceptual, focusing on identifying potential neighbors
# or connections based on fractal coordinates, including how voids might participate.

class FractalTopologyMapper:
    """
    Provides helper functions to understand network topology based on fractal coordinates.
    This is a conceptual class for Phase 1.
    """

    def __init__(self, max_network_depth: Optional[int] = None):
        """
        Args:
            max_network_depth: Optional maximum depth considered for network participation.
        """
        self.max_network_depth = max_network_depth
        # In a real system, this might hold a list of active nodes and their fractal coordinates.
        self._active_nodes: Dict[AddressedFractalCoordinate, Any] = {} # Value could be node info

    def add_network_node(self, coord: AddressedFractalCoordinate, node_info: Any = True):
        """Registers an active node at a given fractal coordinate."""
        if self.max_network_depth is not None and coord.depth > self.max_network_depth:
            # Optionally enforce max depth for network nodes
            # print(f"Node at {coord} exceeds max_network_depth {self.max_network_depth}")
            return
        self._active_nodes[coord] = node_info

    def remove_network_node(self, coord: AddressedFractalCoordinate):
        """Unregisters a node."""
        if coord in self._active_nodes:
            del self._active_nodes[coord]

    def get_active_nodes_at_depth(self, depth: int) -> List[AddressedFractalCoordinate]:
        """Returns a list of active nodes at a specific depth."""
        return [coord for coord in self._active_nodes if coord.depth == depth]

    def get_potential_peers(self, coord: AddressedFractalCoordinate,
                              include_parent: bool = True,
                              include_children: bool = True,
                              include_siblings: bool = True,
                              include_geometric_adjacencies: bool = True,
                              radius: int = 1 # For future "nearby" N-hop non-direct peers
                             ) -> Set[AddressedFractalCoordinate]:
        """
        Identifies potential peers for a node at `coord` based on fractal relationships.
        This is a high-level suggestion list; actual peering involves liveness and reachability.
        """
        potential_peers: Set[AddressedFractalCoordinate] = set()

        # 1. Parent
        if include_parent:
            # Using fractal_math.get_parent which expects FractalCoordinate (implicitly solid path)
            # If coord can be a void, its parent logic needs care.
            # Assuming AddressedFractalCoordinate is compatible if path is solid.
            if coord.depth > 0 : # Genesis has no parent
                parent_path = coord.path[:-1]
                try:
                    parent_coord = AddressedFractalCoordinate(coord.depth -1, parent_path)
                    potential_peers.add(parent_coord)
                except ValueError: pass # Invalid path for parent

        # 2. Children
        if include_children:
            # Children can be solid (path elements 0,1,2) or void (path element 3)
            # This applies whether the current 'coord' is solid or void.
            # If 'coord' is solid, (coord.path,3) is its central void.
            # If 'coord' is void, (coord.path,3) is the central void of its subdivision.
            for i in range(4): # Try path extensions 0, 1, 2, 3 for children
                child_path = coord.path + (i,)
                try:
                    child_coord = AddressedFractalCoordinate(coord.depth + 1, child_path)
                    if self.max_network_depth is None or child_coord.depth <= self.max_network_depth:
                        potential_peers.add(child_coord)
                except ValueError:
                    pass # Should not happen if coord.path is valid and i is 0-3

        # 3. Siblings (other children of the same parent)
        if include_siblings and coord.depth > 0:
            parent_path = coord.path[:-1]
            current_child_idx = coord.path[-1]

            # Iterate through all possible child indices (0,1,2 for solid, 3 for void)
            for i in range(4):
                if i != current_child_idx:
                    sibling_path = parent_path + (i,)
                    try:
                        sibling_coord = AddressedFractalCoordinate(coord.depth, sibling_path)
                        potential_peers.add(sibling_coord)
                    except ValueError: pass

        # 4. Geometric Adjacencies (from geometry_validator placeholder)
        # This is where true "Sierpinski pattern" connections would come from.
        # The current get_geometric_adjacencies is a placeholder (returns solid siblings).
        if include_geometric_adjacencies:
            adj_coords = get_geometric_adjacencies(coord) # This is the placeholder
            for ac in adj_coords:
                potential_peers.add(ac) # ac is already AddressedFractalCoordinate

        # Filter out self, if present
        potential_peers.discard(coord)

        # Further filtering: only include peers that are known active nodes (optional)
        # active_potential_peers = {p for p in potential_peers if p in self._active_nodes}
        # return active_potential_peers

        return potential_peers

    def is_void_relay_candidate(self, coord: AddressedFractalCoordinate) -> bool:
        """
        Determines if a void coordinate is a candidate for being a relay node.
        Based on its position, depth, or rules about void functionality.
        """
        # Example rule: Voids at certain depths, or voids that bridge significant sub-fractals.
        # For now, any valid void coordinate could be a candidate.
        return coord.is_void_path() # Basic check: is it a path containing a void element?
                                    # Or, more strictly: does its path *terminate* in a void element?
                                    # AddressedFractalCoordinate.is_void_path() is true if '3' is anywhere.

# --- Dynamic Peer Discovery using Fractal Coordinates (Conceptual Notes) ---
# - A new node joining the network at a specific fractal coordinate `C`.
# - It could query known bootstrap nodes for peers near `C`.
# - "Near" could mean:
#   - Same parent.
#   - Siblings.
#   - Parent/Children.
#   - Geometrically adjacent (touching) regions.
#   - Nodes within a certain "fractal distance" (path difference, or hops in the fractal graph).
# - Nodes could periodically announce their fractal coordinate and liveness.

# --- Connection Optimization / Load Balancing (Conceptual Notes) ---
# - Prefer connections to peers that maintain geometric locality.
# - If a region (e.g., a sub-fractal coordinated by a void) is heavily loaded,
#   new connections or traffic might be preferentially routed to less loaded adjacent regions.
# - Void nodes, as relays, could monitor load in their "managed" sub-fractals and influence routing.


if __name__ == '__main__':
    print("Fractal Network Topology Mapper Demo")
    mapper = FractalTopologyMapper(max_network_depth=3)

    # Register some active nodes
    n_d0 = AddressedFractalCoordinate(0, tuple())
    n_d1p0 = AddressedFractalCoordinate(1, (0,))
    n_d1p1 = AddressedFractalCoordinate(1, (1,))
    n_d1p3 = AddressedFractalCoordinate(1, (3,)) # A void node
    n_d2p00 = AddressedFractalCoordinate(2, (0,0))
    n_d2p03 = AddressedFractalCoordinate(2, (0,3)) # Void child of n_d1p0

    mapper.add_network_node(n_d0)
    mapper.add_network_node(n_d1p0)
    mapper.add_network_node(n_d1p1)
    mapper.add_network_node(n_d1p3) # Void node active
    mapper.add_network_node(n_d2p00)
    mapper.add_network_node(n_d2p03) # Void node active

    print(f"Active nodes at depth 1: {mapper.get_active_nodes_at_depth(1)}")

    print(f"\nPotential peers for {n_d1p0}:")
    peers_n_d1p0 = mapper.get_potential_peers(n_d1p0)
    for p in sorted(list(peers_n_d1p0), key=lambda c: (c.depth, c.path)): print(f"  - {p}")
    # Expected for n_d1p0 (path (0,)):
    # Parent: d0p () -> n_d0
    # Children (solid): d2p00, d2p01, d2p02 (n_d2p00 is active)
    # Child (void): d2p03 (n_d2p03 is active)
    # Siblings: d1p1, d1p2, d1p3 (n_d1p1, n_d1p3 active)
    # Geometric Adjacencies (placeholder returns solid siblings d1p1, d1p2):
    #   So d1p1 is already from siblings. d1p2 might be new if not active.

    # Verify some expected peers for n_d1p0 (d1p0)
    self_coord = n_d1p0
    expected_peers_for_d1p0 = {
        AddressedFractalCoordinate(0, tuple()),      # Parent
        AddressedFractalCoordinate(2, (0,0)),      # Child 0
        AddressedFractalCoordinate(2, (0,1)),      # Child 1
        AddressedFractalCoordinate(2, (0,2)),      # Child 2
        AddressedFractalCoordinate(2, (0,3)),      # Void Child of d1p0
        AddressedFractalCoordinate(1, (1,)),        # Sibling (solid)
        AddressedFractalCoordinate(1, (2,)),        # Sibling (solid)
        AddressedFractalCoordinate(1, (3,)),        # Sibling (void)
    }
    # Note: get_geometric_adjacencies placeholder returns solid siblings, so (1,1) and (1,2) might be redundant.
    # The set will handle redundancy.

    missing_peers = expected_peers_for_d1p0 - peers_n_d1p0
    extra_peers = peers_n_d1p0 - expected_peers_for_d1p0
    if not missing_peers and not extra_peers:
        print(f"Peer list for {n_d1p0} matches expectations.")
    else:
        if missing_peers: print(f"Missing peers for {n_d1p0}: {missing_peers}")
        if extra_peers: print(f"Extra peers for {n_d1p0}: {extra_peers}")
        assert False, "Peer list mismatch"


    print(f"\nPotential peers for void node {n_d1p3} (path (3,)):") # A void node
    peers_n_d1p3 = mapper.get_potential_peers(n_d1p3)
    for p in sorted(list(peers_n_d1p3), key=lambda c: (c.depth, c.path)): print(f"  - {p}")
    # Expected for n_d1p3 (d1p3):
    # Parent: d0p ()
    # Children (if void can have children in this topology sense): d2p30, d2p31, d2p32, d2p33 (void child)
    # Siblings: d1p0, d1p1, d1p2
    # Geometric Adjacencies (placeholder returns [] for voids)

    # Check if a void is a relay candidate
    print(f"\nIs {n_d1p0} a void relay candidate? {mapper.is_void_relay_candidate(n_d1p0)}") # False
    assert not mapper.is_void_relay_candidate(n_d1p0)
    print(f"Is {n_d1p3} a void relay candidate? {mapper.is_void_relay_candidate(n_d1p3)}") # True
    assert mapper.is_void_relay_candidate(n_d1p3)
    print(f"Is {n_d2p03} (path (0,3)) a void relay candidate? {mapper.is_void_relay_candidate(n_d2p03)}") # True
    assert mapper.is_void_relay_candidate(n_d2p03)


    print("\nPrompt 8 Network Topology Mapper initial concepts are in place.")
    print("Focus is on identifying potential connections based on fractal structure.")
