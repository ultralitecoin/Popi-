# Fractal Geometry Validator

from typing import List, Optional, Tuple

from fractal_blockchain.core.mathematics.fractal_math import (
    FractalCoordinate,
    CartesianPoint,
    TriangleVertices,
    GENESIS_TRIAD_VERTICES,
    subdivide_triangle,
    get_triangle_for_fractal_coord as get_solid_triangle_for_coord, # Alias for clarity
    # We might need to redefine or adapt some math functions if they are to work with voids
)
from fractal_blockchain.core.addressing import AddressedFractalCoordinate

# Prompt 3: Build fractal geometry validator
# - Functions to verify valid fractal positions (extending `is_valid_fractal_coordinate` if needed, handling voids).
# - Neighbors calculation for any coordinate (considering adjacent triangles at same depth).
# - Validation of geometric relationships (parent, siblings, children - already in `fractal_math.py` but can be grouped/exposed here, and consider voids).
# - Detect orphaned/invalid positions (e.g., path refers to a void beyond current max depth for solid triangles).
# - Fractal boundary detection and edge case handling.
# - Algorithms for geometric integrity (no overlaps, no holes - primarily ensured by subdivision logic).

# --- Extended Validation for AddressedFractalCoordinate ---

def is_valid_addressed_coordinate(coord: AddressedFractalCoordinate, initial_triad_vertices: TriangleVertices = GENESIS_TRIAD_VERTICES) -> bool:
    """
    Validates an AddressedFractalCoordinate.
    - Path elements must be 0, 1, 2 (child) or 3 (void). (Handled by AddressedFractalCoordinate constructor)
    - Path length must equal depth. (Handled by AddressedFractalCoordinate constructor)
    - Geometrically, a path involving '3' (void) means it doesn't correspond to a "solid" triangle
      at that exact path's end.
    - This function checks if the path is structurally valid up to the point it might enter a void.
    """
    if coord.depth < 0: return False
    # Constructor of AddressedFractalCoordinate already checks path element values and length vs depth.

    current_triangle_vertices = initial_triad_vertices
    for i in range(coord.depth):
        path_element = coord.path[i]

        children_triangles, void_triangle_vertices = subdivide_triangle(current_triangle_vertices)

        if path_element == 0: # Child 0
            current_triangle_vertices = children_triangles[0]
        elif path_element == 1: # Child 1
            current_triangle_vertices = children_triangles[1]
        elif path_element == 2: # Child 2
            current_triangle_vertices = children_triangles[2]
        elif path_element == 3: # Void
            # If path element is void, the subsequent path elements define a path *within* that void.
            # The "current_triangle_vertices" for the next step becomes the void triangle.
            current_triangle_vertices = void_triangle_vertices
        else:
            # This case should be prevented by AddressedFractalCoordinate constructor.
            return False

    return True # If we successfully traversed the path according to subdivisions.

def get_vertices_for_addressed_coord(coord: AddressedFractalCoordinate, initial_triad_vertices: TriangleVertices = GENESIS_TRIAD_VERTICES) -> Optional[TriangleVertices]:
    """
    Retrieves the Cartesian vertices of the triangle/space corresponding to an AddressedFractalCoordinate.
    If the path ends in a void, it returns the vertices of that void space.
    """
    if not is_valid_addressed_coordinate(coord, initial_triad_vertices): # Structural check first
        # The AddressedFractalCoordinate constructor already does some validation.
        # is_valid_addressed_coordinate re-traverses, which is redundant if constructor is trusted.
        # Let's rely on constructor for path elements and length, and just traverse.
        pass

    current_triangle_v = initial_triad_vertices

    if coord.depth == 0:
        return initial_triad_vertices

    for i in range(coord.depth):
        if i >= len(coord.path): return None # Should be caught by constructor

        path_element = coord.path[i]
        children_triangles, void_triangle_v = subdivide_triangle(current_triangle_v)

        if 0 <= path_element <= 2: # Solid child
            if path_element >= len(children_triangles): return None # Should not happen
            current_triangle_v = children_triangles[path_element]
        elif path_element == 3: # Void
            current_triangle_v = void_triangle_v
        else: # Invalid path element, should be caught by AddressedFractalCoordinate constructor
            return None

    return current_triangle_v


# --- Neighbors Calculation ---
# Neighbors are typically other triangles/voids at the same depth that share an edge or vertex.
# This is a complex geometric problem.
# For Sierpinski, solid triangles only touch at vertices.
# A solid triangle has 3 children. Its "void" child is the central hole.
# The definition of "neighbor" needs to be precise.
# Are we talking about neighbors of the *solid* parts, or any defined region?

# Placeholder:
def get_neighbors(coord: AddressedFractalCoordinate) -> List[AddressedFractalCoordinate]:
    """
    Calculates neighbors of a given fractal coordinate.
    This is a complex function and highly dependent on the precise definition of "neighbor"
    (e.g., sharing an edge, sharing a vertex, for solid parts, or also including voids).

    For now, this is a placeholder. A full implementation would require:
    1. Determining the parent of `coord`.
    2. Identifying siblings of `coord` (these are direct neighbors if they are not voids).
    3. Identifying "cousins" that might touch at edges/vertices, which involves looking at
       parent's siblings' children.
    4. Handling boundary conditions of the overall fractal structure.
    """
    """
    Calculates neighbors of a given fractal coordinate.
    A neighbor is defined as another coordinate of the same depth that shares at least one vertex.
    This version aims for a more geometrically accurate neighbor list than just siblings.
    """

    # TODO: This is a complex geometric problem. The implementation below is a step towards it.
    # It will identify siblings and potentially "cousins" that touch at vertices.
    # True vertex sharing identification requires comparing Cartesian vertex coordinates.

    neighbors: Set[AddressedFractalCoordinate] = set()
    if coord.depth == 0: # Genesis has no same-depth neighbors in this context
        return []

    # 1. Siblings (share the same parent and are at the same depth)
    # These are guaranteed to share vertices with `coord` if `coord` is solid and they are solid.
    # If `coord` is a void, its solid siblings form its boundary.
    # If `coord` is solid, its void sibling is its central hole.
    parent_path = coord.path[:-1]
    current_child_idx = coord.path[-1]

    for i in range(4): # Try all 4 potential children of the parent (0,1,2 for solid, 3 for void)
        if i == current_child_idx:
            continue
        try:
            sibling_coord = AddressedFractalCoordinate(depth=coord.depth, path=parent_path + (i,))
            neighbors.add(sibling_coord)
        except ValueError:
            pass # Invalid path

    # 2. "Cousins" - children of parent's siblings that touch at vertices.
    # This is the most complex part.
    # Example: Triangle T_00 (path (0,0)) touches T_12 (path (1,2)) at a shared vertex
    # if T_0 (parent of T_00) and T_1 (parent of T_12) are siblings and they touch appropriately.
    #
    # For a Sierpinski gasket, a solid triangle at (d, path_self) has 3 vertices.
    # Each vertex is shared with two other solid triangles at the same depth.
    # - Two of these are its siblings (if they exist and are solid).
    # - The other 0 to 3 neighbors (up to 6 total for internal nodes) are "cousins".
    #
    # A full implementation would:
    # a. Get Cartesian vertices of `coord`.
    # b. For each vertex of `coord`:
    #    i. Identify which other *potential* fractal coordinates at the same depth could share this vertex.
    #       This involves going up to parent, finding parent's siblings, then their children.
    #    ii. Check if those potential coordinates are valid and add them.
    #
    # This is too complex for the current enhancement iteration without significantly more geometric utilities.
    # The current placeholder `get_geometric_adjacencies` from which this function is derived
    # only returned solid siblings. The above loop (step 1) already finds all siblings (solid and void).
    #
    # For now, we'll stick to siblings as the primary identified neighbors.
    # A more advanced version would be needed for true pathfinding across the fractal surface.

    # If coord is solid, its void sibling is its central hole.
    # If coord is void, its solid siblings are its boundary.
    # The current logic adds all siblings (0,1,2,3 except self) to the neighbors set.

    # For the purpose of pathfinding between solid regions, we might filter out void neighbors
    # unless pathfinding explicitly allows routing through specified void relays.
    # However, the `get_neighbors` function itself should probably return all geometrically relevant neighbors.
    # The pathfinder can then filter them.

    # The current implementation returns all siblings (solid or void).
    return list(neighbors)


# --- Orphaned/Invalid Positions ---
def is_orphaned(coord: AddressedFractalCoordinate) -> bool:
    """
    Detects if a coordinate is orphaned.
    An orphan could be a coordinate whose parent path segment is a void, if such paths are disallowed
    for certain types of entities, or a path that's structurally valid but geometrically impossible.
    `is_valid_addressed_coordinate` already checks basic geometric derivability.

    A more specific definition of "orphaned" might be needed.
    E.g., a solid child (path element 0,1,2) cannot stem from a parent path ending in void (3).
    """
    if coord.depth == 0: return False # Genesis is not orphaned

    # Check if any solid segment directly follows a void segment in the path.
    # Example: d2p30 (depth 2, path (3,0)) -> child 0 of a void.
    # This might be valid depending on rules (e.g. a void can be subdivided).
    # If voids are terminal for "solid" paths, then (3,0) would be an orphan if it claims to be solid.

    # For now, rely on is_valid_addressed_coordinate for basic validity.
    # This function might be more about semantic orphaned status based on higher-level rules.
    return not is_valid_addressed_coordinate(coord) # Basic check

# --- Fractal Boundary Detection ---
# This would involve finding coordinates that lie on the "edge" of the fractal structure,
# meaning they have fewer neighbors than an internal coordinate.
# For the theoretical Sierpinski triangle, it's infinite. For a finite depth,
# the triangles at the max depth on the convex hull are boundary triangles.

# Placeholder:
def is_on_boundary(coord: AddressedFractalCoordinate, max_depth: int) -> bool:
    """
    Checks if a coordinate is on the boundary of the fractal up to a given max_depth.
    This is complex. A simple heuristic: if it's at max_depth and its parent was on
    the boundary of max_depth-1, or if it's one of the "outer" children.
    """
    if not coord.is_solid_path(): # Voids are not typically on the "solid" boundary
        return False
    if coord.depth < max_depth:
        return False # Only consider coordinates at max_depth for this simple boundary definition
    if coord.depth == 0 and max_depth == 0:
        return True # Genesis itself is the boundary at depth 0

    # This requires a much more sophisticated geometric analysis.
    # For example, the children of the original Genesis vertices (0,0), (1,0), (2,0) at depth 1
    # have segments that form part of the boundary.
    # Child 0 (top), Child 1 (left base), Child 2 (right base).
    # Path (0,0,0...) is always on boundary. Path (1,1,1...) is always on boundary. Path (2,2,2...) is always on boundary.
    # Path (0,2,2...) might be on boundary. Path (0,1,1...) might be on boundary.

    # Simplistic check: if all path elements are the same (e.g., (0,0,0) or (1,1,1) or (2,2,2))
    # these correspond to the vertices of the main fractal shape.
    if coord.depth > 0 and all(p == coord.path[0] for p in coord.path):
        if coord.path[0] in [0,1,2]: # Must be one of the three main branches
             # This identifies the "corner" paths leading to the vertices of the overall fractal.
             return True

    # This is a very rough approximation and not geometrically complete.
    # return False # Placeholder -- Replacing this

    # Targeted debug for the failing case: is_on_boundary(AFC(1,(0,)), 0)
    if coord.depth == 1 and coord.path == (0,) and max_depth == 0:
        return "DEBUG_FAILING_CASE_REACHED" # Unique string return

    # New implementation using geometric checks

    # Import necessary math functions
    from fractal_blockchain.core.mathematics.fractal_math import (
        points_are_close, is_point_on_line_segment, GENESIS_TRIAD_VERTICES
    )
    # get_vertices_for_addressed_coord is already imported in this file.

    tolerance = 1e-9 # Standard tolerance for geometric comparisons

    # 1. Handle base cases
    if not coord.is_solid_path():
        return False
    if coord.depth != max_depth:
        return False
    if coord.depth == 0: # and max_depth is also 0 here
        return True

    # 2. Get Cartesian vertices of coord
    coord_vertices = get_vertices_for_addressed_coord(coord)
    if not coord_vertices: # Should not happen if coord is valid and solid
        return False
    v = list(coord_vertices) # Ensure it's a list v[0], v[1], v[2]

    # 3. Get Cartesian vertices of GENESIS_TRIAD_VERTICES
    GV = list(GENESIS_TRIAD_VERTICES)

    # 4. Vertex Coincidence Check
    # Check if any vertex of 'coord' is one of the Genesis vertices.
    # This means 'coord' is one of the three main corner triangles of the fractal.
    for coord_v in v:
        for genesis_v in GV:
            if points_are_close(coord_v, genesis_v, tolerance):
                return True # Coord shares a vertex with Genesis Triad - it's a corner.

    # 5. Edge Collinearity/Overlap Check
    # Define edges of coord and Genesis
    coord_edges = [ (v[0],v[1]), (v[1],v[2]), (v[2],v[0]) ]
    genesis_edges = [ (GV[0],GV[1]), (GV[1],GV[2]), (GV[2],GV[0]) ]

    for ce_p1, ce_p2 in coord_edges: # For each edge of the small coordinate triangle
        for ge_p1, ge_p2 in genesis_edges: # For each edge of the main Genesis triangle
            # Check if both endpoints of the coord_edge lie on the current genesis_edge segment
            if is_point_on_line_segment(ce_p1, ge_p1, ge_p2, tolerance) and \
               is_point_on_line_segment(ce_p2, ge_p1, ge_p2, tolerance):
                # This means the small edge ce_p1-ce_p2 is part of a main boundary edge.
                # We also need to ensure they are not just single points unless it's a vertex match (covered above)
                # If ce_p1 and ce_p2 are distinct (not points_are_close), then it's a line segment.
                if not points_are_close(ce_p1, ce_p2, tolerance): # It's a non-degenerate edge
                    return True # Found an edge of 'coord' that lies on a Genesis boundary edge.

    # 6. If none of the above, it's not on the boundary by these geometric checks.
    return False


if __name__ == '__main__':
    # Test is_valid_addressed_coordinate
    valid_solid = AddressedFractalCoordinate(depth=2, path=(0,1))
    valid_void_path = AddressedFractalCoordinate(depth=2, path=(0,3)) # Path leads into a void
    valid_path_through_void = AddressedFractalCoordinate(depth=3, path=(0,3,1)) # Path continues inside a void

    print(f"Coord {valid_solid}: valid? {is_valid_addressed_coordinate(valid_solid)}")
    assert is_valid_addressed_coordinate(valid_solid)

    print(f"Coord {valid_void_path}: valid? {is_valid_addressed_coordinate(valid_void_path)}")
    assert is_valid_addressed_coordinate(valid_void_path)

    print(f"Coord {valid_path_through_void}: valid? {is_valid_addressed_coordinate(valid_path_through_void)}")
    assert is_valid_addressed_coordinate(valid_path_through_void)

    try:
        invalid_path_el = AddressedFractalCoordinate(depth=1, path=(4,)) # Constructor should catch
    except ValueError as e:
        print(f"Caught expected error for invalid path element: {e}")

    # Test get_vertices_for_addressed_coord
    v_genesis = get_vertices_for_addressed_coord(AddressedFractalCoordinate(0, tuple()))
    print(f"Genesis vertices: {v_genesis is not None}")
    assert v_genesis == GENESIS_TRIAD_VERTICES

    v_d1_c0 = get_vertices_for_addressed_coord(AddressedFractalCoordinate(1, (0,)))
    children_g, _ = subdivide_triangle(GENESIS_TRIAD_VERTICES)
    print(f"D1C0 vertices: {v_d1_c0 == children_g[0]}")
    assert v_d1_c0 == children_g[0]

    v_d1_v3 = get_vertices_for_addressed_coord(AddressedFractalCoordinate(1, (3,))) # Vertices of the main void
    _, void_g = subdivide_triangle(GENESIS_TRIAD_VERTICES)
    print(f"D1V3 (main void) vertices: {v_d1_v3 == void_g}")
    assert v_d1_v3 == void_g

    v_d2_c0_v3 = get_vertices_for_addressed_coord(AddressedFractalCoordinate(2, (0,3))) # Void of child 0 of Genesis
    _, void_of_child0 = subdivide_triangle(children_g[0])
    print(f"D2P03 (void of child 0) vertices: {v_d2_c0_v3 == void_of_child0}")
    assert v_d2_c0_v3 == void_of_child0

    # Test get_neighbors (placeholder behavior - only solid siblings)
    coord_d1_c0 = AddressedFractalCoordinate(1, (0,))
    neighbors_d1_c0 = get_neighbors(coord_d1_c0)
    print(f"Neighbors of {coord_d1_c0}: {neighbors_d1_c0}")
    expected_neighbors_d1_c0 = [
        AddressedFractalCoordinate(1, (1,)),
        AddressedFractalCoordinate(1, (2,))
    ]
    assert all(n in neighbors_d1_c0 for n in expected_neighbors_d1_c0)
    assert len(neighbors_d1_c0) == len(expected_neighbors_d1_c0)

    coord_d1_v3 = AddressedFractalCoordinate(1, (3,)) # A void coordinate
    neighbors_d1_v3 = get_neighbors(coord_d1_v3)
    print(f"Neighbors of void {coord_d1_v3}: {neighbors_d1_v3}") # Expected empty by current placeholder
    assert neighbors_d1_v3 == []

    # Test is_orphaned (placeholder behavior)
    print(f"Is {valid_solid} orphaned? {is_orphaned(valid_solid)}") # Expected False
    assert not is_orphaned(valid_solid)

    # Test is_on_boundary (placeholder behavior)
    b_coord_d2_p00 = AddressedFractalCoordinate(2, (0,0)) # path (0,0) at depth 2
    print(f"Is {b_coord_d2_p00} on boundary of depth 2? {is_on_boundary(b_coord_d2_p00, 2)}") # Expected True by simple rule
    assert is_on_boundary(b_coord_d2_p00, 2)

    b_coord_d2_p01 = AddressedFractalCoordinate(2, (0,1)) # path (0,1) at depth 2
    print(f"Is {b_coord_d2_p01} on boundary of depth 2? {is_on_boundary(b_coord_d2_p01, 2)}") # Expected False by simple rule
    assert not is_on_boundary(b_coord_d2_p01, 2)

    b_coord_d1_p0 = AddressedFractalCoordinate(1, (0,))
    print(f"Is {b_coord_d1_p0} on boundary of depth 2? {is_on_boundary(b_coord_d1_p0, 2)}") # False (not at max_depth)
    assert not is_on_boundary(b_coord_d1_p0, 2)
    print(f"Is {b_coord_d1_p0} on boundary of depth 1? {is_on_boundary(b_coord_d1_p0, 1)}") # True
    assert is_on_boundary(b_coord_d1_p0, 1)

    print("\nPrompt 3 initial geometry validator placeholders and functions in place.")
