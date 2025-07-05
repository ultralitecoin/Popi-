# Fractal Path Finder using Dijkstra's Algorithm

import heapq
from typing import List, Dict, Tuple, Optional, Set

from fractal_blockchain.core.addressing import AddressedFractalCoordinate
# For neighbor identification, we use the function from geometry_validator.
# The current version of get_neighbors in geometry_validator returns all siblings (solid and void).
from fractal_blockchain.core.geometry_validator import get_neighbors

# Prompt 5: Create fractal path finder.
# - Fractal-aware routing: Dijkstra’s algorithm adapted for Sierpinski geometry.
# - Finds optimal transaction path between any two valid (non-void) fractal coordinates.
# - Optimize for minimal hop count and geometric distance (hop count is primary for now).
# - Routing tables caching (out of scope for initial implementation).
# - Pathfinding supports dynamic topology (node join/leave - out of scope for math foundation).

Path = List[AddressedFractalCoordinate]
Cost = float # Using float for cost, could be int if only hop count.

# Define a cost function for moving between adjacent coordinates.
# For now, let's assume a uniform cost of 1 (hop count).
# Geometric distance could be added later.
def get_edge_cost(coord1: AddressedFractalCoordinate, coord2: AddressedFractalCoordinate) -> Cost:
    """
    Calculates the cost of traversing an edge between two adjacent coordinates.
    Currently, uses a uniform cost of 1 (hop count).
    """
    # In a more advanced system, this could depend on:
    # - Geometric distance between centroids of coord1 and coord2.
    # - Type of coordinates (e.g., moving into/out of a void might have different cost).
    # - Network congestion or other dynamic factors (out of scope for Phase 1).
    return 1.0


def find_path_dijkstra(start_coord: AddressedFractalCoordinate,
                       end_coord: AddressedFractalCoordinate,
                       max_depth_for_pathfinding: Optional[int] = None) -> Optional[Path]:
    """
    Finds the shortest path between start_coord and end_coord using Dijkstra's algorithm.
    The "graph" is dynamically explored using a neighbor function (get_geometric_neighbors).
    Only considers non-void coordinates for path segments unless explicitly allowed by neighbor function.

    Args:
        start_coord: The starting AddressedFractalCoordinate.
        end_coord: The target AddressedFractalCoordinate.
        max_depth_for_pathfinding: Optional maximum depth to explore for neighbors.
                                   If None, uses depth of start/end coordinates.

    Returns:
        A list of AddressedFractalCoordinates representing the path, or None if no path is found.
    """

    if start_coord.is_void_path() or end_coord.is_void_path():
        # Pathfinding is typically between "solid" locations.
        # If voids can be part of paths, get_geometric_neighbors must handle them.
        # Current get_geometric_neighbors placeholder returns [] for voids.
        return None

    if start_coord == end_coord:
        return [start_coord]

    # Priority queue: stores (cost, coordinate_object)
    # We store the object itself to avoid issues with tuple comparison if AddressedFractalCoordinate was mutable
    # or had complex comparison. Since it's a NamedTuple, it's hashable and comparable.
    pq: List[Tuple[Cost, AddressedFractalCoordinate]] = [(0.0, start_coord)]

    # came_from: stores the predecessor of each coordinate in the shortest path
    came_from: Dict[AddressedFractalCoordinate, Optional[AddressedFractalCoordinate]] = {start_coord: None}

    # cost_so_far: stores the cost to reach each coordinate from the start
    cost_so_far: Dict[AddressedFractalCoordinate, Cost] = {start_coord: 0.0}

    # Set of visited coordinates to avoid reprocessing (optional, Dijkstra handles cycles with costs)
    # visited: Set[AddressedFractalCoordinate] = set()

    while pq:
        current_cost, current_coord = heapq.heappop(pq)

        # if current_coord in visited: # Optional optimization
        #     continue
        # visited.add(current_coord)

        if current_coord == end_coord:
            # Path found, reconstruct it
            path: Path = []
            temp_coord: Optional[AddressedFractalCoordinate] = end_coord
            while temp_coord is not None:
                path.append(temp_coord)
                temp_coord = came_from.get(temp_coord)
            return path[::-1] # Reverse to get start -> end order

        # Consider depth limits for neighbor exploration
        # If max_depth_for_pathfinding is set, neighbors should not exceed this.
        # Current get_geometric_neighbors doesn't take max_depth. This is a simplification.
        # A more robust get_neighbors would need to handle depth constraints.

        neighbors = get_neighbors(current_coord) # Call the imported get_neighbors

        for neighbor_coord in neighbors:
            if neighbor_coord.is_void_path(): # Typically, don't route through voids unless specified
                continue

            # Apply depth constraint if applicable
            if max_depth_for_pathfinding is not None and neighbor_coord.depth > max_depth_for_pathfinding:
                continue

            new_cost = cost_so_far[current_coord] + get_edge_cost(current_coord, neighbor_coord)

            if neighbor_coord not in cost_so_far or new_cost < cost_so_far[neighbor_coord]:
                cost_so_far[neighbor_coord] = new_cost
                came_from[neighbor_coord] = current_coord
                heapq.heappush(pq, (new_cost, neighbor_coord))

    return None # No path found


if __name__ == '__main__':
    print("Fractal Path Finder Demo")

    # Define some coordinates for testing.
    # We need a get_geometric_neighbors that works for these tests.
    # The current placeholder only returns direct siblings of the same type.
    # This makes pathfinding beyond siblings impossible without a better get_neighbors.

    # Let's mock a get_geometric_neighbors for a simple scenario, e.g., a linear path or small grid.
    # For this demo, we'll assume a very simple topology that our placeholder get_neighbors can handle.

    # Scenario 1: Path between siblings
    start_s1 = AddressedFractalCoordinate(depth=1, path=(0,)) # d1p0
    end_s1   = AddressedFractalCoordinate(depth=1, path=(1,)) # d1p1
    # get_geometric_neighbors(d1p0) should yield d1p1 and d1p2.
    # So, path d1p0 -> d1p1 should be found.

    path1 = find_path_dijkstra(start_s1, end_s1)
    print(f"\nPath from {start_s1} to {end_s1}:")
    if path1:
        print(" -> ".join([f"{c.depth}p{''.join(map(str,c.path))}" for c in path1]))
        # Expected: [d1p0, d1p1] (cost 1)
        assert path1 == [start_s1, end_s1]
    else:
        print("No path found.")
        assert False, "Path between siblings should be found"

    # Scenario 2: Start = End
    path2 = find_path_dijkstra(start_s1, start_s1)
    print(f"\nPath from {start_s1} to {start_s1}:")
    if path2:
        print(" -> ".join([f"{c.depth}p{''.join(map(str,c.path))}" for c in path2]))
        assert path2 == [start_s1]
    else:
        print("No path found.")
        assert False, "Path from start to start should be found"

    # Scenario 3: No path (e.g., target is a void, or disconnected)
    end_s3_void = AddressedFractalCoordinate(depth=1, path=(3,)) # d1p3 (a void)
    path3 = find_path_dijkstra(start_s1, end_s3_void)
    print(f"\nPath from {start_s1} to void {end_s3_void}:")
    if path3:
        print(" -> ".join([f"{c.depth}p{''.join(map(str,c.path))}" for c in path3]))
        assert False, "Path to a void should not be found by default"
    else:
        print("No path found (as expected for void target).")
        assert path3 is None

    # Scenario 4: Path across multiple "sibling hops" - requires a more complex get_neighbors
    # Example: d2p00 -> d2p01 -> d2p02
    # With current get_neighbors:
    # get_neighbors(d2p00) = [d2p01, d2p02]
    # get_neighbors(d2p01) = [d2p00, d2p02]
    start_s4 = AddressedFractalCoordinate(depth=2, path=(0,0))
    end_s4   = AddressedFractalCoordinate(depth=2, path=(0,2))
    path4 = find_path_dijkstra(start_s4, end_s4)
    print(f"\nPath from {start_s4} to {end_s4}:")
    if path4:
        print(" -> ".join([f"d{c.depth}p{''.join(map(str,c.path))}" for c in path4]))
        # Expected: [d2p00, d2p02] if direct sibling, or [d2p00, d2p01, d2p02] if through middle sibling
        # Current get_neighbors for d2p00 returns d2p01 and d2p02.
        # So, d2p00 -> d2p02 is a direct edge. Cost 1.
        assert path4 == [start_s4, end_s4]
    else:
        print("No path found.")
        assert False, "Path between siblings of same parent should be found"

    # Scenario 5: No path if get_geometric_neighbors is too limited
    # E.g., path from d2p00 to d2p10. These are not siblings.
    # Parent of d2p00 is d1p0. Parent of d2p10 is d1p1.
    # d1p0 and d1p1 are siblings.
    # A true path would be: d2p00 -> (up to parent d1p0) -> (sibling d1p1) -> (down to child d2p10)
    # This requires a get_neighbors that can suggest parent/child traversal or connections
    # between children of sibling triangles. The current placeholder cannot do this.
    start_s5 = AddressedFractalCoordinate(depth=2, path=(0,0))
    end_s5   = AddressedFractalCoordinate(depth=2, path=(1,0))
    path5 = find_path_dijkstra(start_s5, end_s5)
    print(f"\nPath from {start_s5} to {end_s5} (cousins):")
    if path5:
        print(" -> ".join([f"d{c.depth}p{''.join(map(str,c.path))}" for c in path5]))
        # This should NOT find a path with the current simple get_neighbors
        assert False, "Path between cousins should not be found with placeholder get_neighbors"
    else:
        print("No path found (as expected with placeholder get_neighbors).")
        assert path5 is None


    print("\nPathfinder demo complete. Relies heavily on a proper get_geometric_neighbors function.")
    print("Prompt 5 initial Dijkstra implementation is structurally in place.")
    print("Functionality is limited by the current placeholder get_neighbors.")
