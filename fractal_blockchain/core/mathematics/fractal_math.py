# Core Fractal Mathematics Module
# This file will contain the mathematical foundations for the Fractal Blockchain.

import math
from typing import NamedTuple, List, Tuple, Optional

class CartesianPoint(NamedTuple):
    """Represents a point in 2D Cartesian space."""
    x: float
    y: float

class FractalCoordinate(NamedTuple):
    """
    Represents a fractal coordinate.
    Path is a sequence of digits (0, 1, 2 for child triangle, 3 for void)
    representing the journey from the Genesis Triad.
    Example: (depth=0, path=()) for a genesis triad point,
             (depth=1, path=(0,)) for the first child of a genesis point,
             (depth=2, path=(0,1)) for the second child of the first child.
    """
    depth: int
    path: Tuple[int, ...] # Base-4 identifier sequence

# Define the Genesis Triad (equilateral triangle for simplicity)
# Centered at (0,0) for now, can be adjusted. Side length can also be a parameter.
SIDE_LENGTH = 1000.0
SQRT_3 = math.sqrt(3)

# Vertices of the Genesis Triad (an equilateral triangle pointing upwards)
# If we want it centered at (0,0) with base on y = -h/3 and peak at y = 2h/3
# Height of equilateral triangle: h = (sqrt(3)/2) * side
HEIGHT = (SQRT_3 / 2) * SIDE_LENGTH

GENESIS_TRIAD_VERTICES: Tuple[CartesianPoint, CartesianPoint, CartesianPoint] = (
    CartesianPoint(x=0, y=(2/3) * HEIGHT),             # Top vertex
    CartesianPoint(x=-SIDE_LENGTH / 2, y=(-1/3) * HEIGHT), # Bottom-left vertex
    CartesianPoint(x=SIDE_LENGTH / 2, y=(-1/3) * HEIGHT)  # Bottom-right vertex
)

# For Sierpinski, each triangle is defined by 3 vertices.
# A "triangle" can be represented as a tuple of 3 CartesianPoints.
TriangleVertices = Tuple[CartesianPoint, CartesianPoint, CartesianPoint]

def get_midpoint(p1: CartesianPoint, p2: CartesianPoint) -> CartesianPoint:
    """Calculates the midpoint between two Cartesian points."""
    return CartesianPoint((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)

def subdivide_triangle(vertices: TriangleVertices) -> Tuple[List[TriangleVertices], TriangleVertices]:
    """
    Subdivides a given triangle into 3 child triangles (vertices) and 1 central void triangle.
    The child triangles maintain the same orientation as the parent.
    Assumes vertices = (top, left_base, right_base) for an upward pointing triangle.
    For a downward pointing void, the order might be different or interpreted differently.

    Returns:
        A tuple containing:
        - A list of 3 TriangleVertices for the child triangles.
        - TriangleVertices for the central void triangle.
    """
    p_top, p_left_base, p_right_base = vertices

    # Midpoints of the sides
    m_top_left = get_midpoint(p_top, p_left_base)
    m_top_right = get_midpoint(p_top, p_right_base)
    m_left_right_base = get_midpoint(p_left_base, p_right_base)

    # Child triangles (these are the "solid" parts in Sierpinski)
    # These maintain the orientation of the parent triangle.
    child_triangle_0 = (p_top, m_top_left, m_top_right) # Top child
    child_triangle_1 = (m_top_left, p_left_base, m_left_right_base) # Bottom-left child
    child_triangle_2 = (m_top_right, m_left_right_base, p_right_base) # Bottom-right child

    children = [child_triangle_0, child_triangle_1, child_triangle_2]

    # Central void triangle (this triangle points downwards if the parent points upwards)
    void_triangle = (m_top_left, m_left_right_base, m_top_right) # Order defines orientation

    return children, void_triangle

# --- Coordinate Transformation and Generation ---
# These are more complex and will require a clear definition of how fractal paths map to geometry.
# For now, let's assume a fractal coordinate directly refers to one of the N triangles at a given depth.

def get_triangle_for_fractal_coord(coord: FractalCoordinate, initial_triad: TriangleVertices = GENESIS_TRIAD_VERTICES) -> Optional[TriangleVertices]:
    """
    Retrieves the Cartesian vertices of the triangle corresponding to a FractalCoordinate.
    This function recursively subdivides the Genesis Triad based on the path in FractalCoordinate.
    """
    if coord.depth < 0:
        return None # Invalid depth

    current_triangle = initial_triad

    if coord.depth == 0: # Path should be empty for depth 0 if it refers to the whole triad
        # Or, if depth 0 means one of the initial vertices, this needs clarification.
        # For now, let's assume depth 0 refers to the initial triad itself.
        # If path is not empty, it's an invalid coordinate for depth 0.
        return current_triangle if not coord.path else None

    for i in range(coord.depth):
        if i >= len(coord.path): # Path is shorter than depth
            return None

        child_index = coord.path[i]
        if not (0 <= child_index <= 2): # Path component must be 0, 1, or 2 (cannot point to void)
            return None

        children_triangles, _ = subdivide_triangle(current_triangle)
        if child_index >= len(children_triangles): # Should not happen if child_index is 0,1,2
            return None
        current_triangle = children_triangles[child_index]

    return current_triangle

# Placeholder functions for Prompt 1 requirements.
# Actual implementation of cartesian_to_fractal and fractal_to_cartesian
# requires a robust definition of how a specific point maps to a fractal path.
# This often involves determining which sub-triangle a point lies within.

def cartesian_to_fractal(point: CartesianPoint, max_depth: int, initial_triad: TriangleVertices = GENESIS_TRIAD_VERTICES) -> Optional[FractalCoordinate]:
    """
    Converts a CartesianPoint to a FractalCoordinate by determining its path from the Genesis Triad.
    This is a complex function that needs a point-in-triangle test and recursive descent.
    For now, this is a simplified placeholder.
    It would find the smallest containing triangle up to max_depth.
    """
    # This is a highly complex function.
    # 1. Check if point is within initial_triad. If not, return None.
    # 2. For d from 0 to max_depth:
    #    a. Subdivide current_triangle into 3 children + 1 void.
    #    b. For each child triangle:
    #       i. If point is in child_triangle_i:
    #          - Append i to path.
    #          - current_triangle = child_triangle_i
    #          - break from inner loop (found containing child for this depth)
    #    c. If point was not in any child (e.g., it's in the void or on a boundary dealt with specifically):
    #       - This logic needs to be clearly defined. Does it map to a void path?
    #       - For Sierpinski, points are typically on the vertices/lines of the solid triangles.
    # For now, returning a placeholder.
    # print(f"Placeholder: cartesian_to_fractal for {point} up to depth {max_depth}")
    # Example: if point is near the top of the genesis triad
    # if point.y > 0 and abs(point.x) < SIDE_LENGTH / 4:
    #    return FractalCoordinate(depth=1, path=(0,)) # Assuming it's in the top child of genesis
    # return None # Placeholder  -- Replacing this

    # Need AddressedFractalCoordinate for path elements potentially including '3' for voids
    from fractal_blockchain.core.addressing import AddressedFractalCoordinate

    # Helper for point_in_triangle
    def get_triangle_area(p1: CartesianPoint, p2: CartesianPoint, p3: CartesianPoint) -> float:
        """Calculates area of a triangle using determinant method (half of cross product magnitude)."""
        return 0.5 * abs(p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y))

    def point_in_triangle(pt: CartesianPoint, v1: CartesianPoint, v2: CartesianPoint, v3: CartesianPoint, tolerance=1e-9) -> bool:
        """
        Checks if a point pt is inside the triangle defined by v1, v2, v3.
        Uses barycentric coordinate approach: sum of areas of sub-triangles PAB, PBC, PCA equals area of ABC.
        Includes points on the edge.
        """
        area_total = get_triangle_area(v1, v2, v3)
        if area_total < tolerance: # Degenerate triangle (collinear points)
            # For simplicity, if total area is near zero, point is not "in" it unless it's one of the vertices
            # or on the line segment if that's desired. This case needs careful handling if points on lines are critical.
            # A robust check for collinearity and point on segment would be needed.
            # For now, assume non-degenerate triangles for main logic.
            return False

        area1 = get_triangle_area(pt, v1, v2)
        area2 = get_triangle_area(pt, v2, v3)
        area3 = get_triangle_area(pt, v3, v1)

        return abs((area1 + area2 + area3) - area_total) < tolerance

    current_triangle_vertices = initial_triad
    path_elements = []

    # Check if point is within the initial triad first
    if not point_in_triangle(point, current_triangle_vertices[0], current_triangle_vertices[1], current_triangle_vertices[2]):
        return None # Point is outside the fractal boundaries

    for d in range(max_depth):
        children_triangles, void_triangle = subdivide_triangle(current_triangle_vertices)

        found_in_sub_region = False
        # Check solid children first
        for i, child_v_set in enumerate(children_triangles):
            if point_in_triangle(point, child_v_set[0], child_v_set[1], child_v_set[2]):
                path_elements.append(i)
                current_triangle_vertices = child_v_set
                found_in_sub_region = True
                break

        if found_in_sub_region:
            continue

        # If not in any solid child, check the void
        if point_in_triangle(point, void_triangle[0], void_triangle[1], void_triangle[2]):
            path_elements.append(3) # 3 represents the void path element
            current_triangle_vertices = void_triangle
            found_in_sub_region = True

        if not found_in_sub_region:
            # Point is on a boundary line between sub-regions, or floating point precision issue.
            # For now, if not strictly within one, we stop and return the path so far.
            # A more robust solution might assign to the "closest" or based on specific rules for boundaries.
            # Or, if it's exactly on a vertex shared by multiple, a tie-breaking rule is needed.
            # This implies the point might be on a line that is NOT part of any further subdivision at this resolution.
            break

    # Path length should be equal to the depth reached.
    # If we broke early from loop, depth is len(path_elements). Otherwise, it's max_depth.
    # The problem statement implies path length indicates depth.
    current_depth = len(path_elements)
    return AddressedFractalCoordinate(depth=current_depth, path=tuple(path_elements))


def fractal_to_cartesian(coord: FractalCoordinate, initial_triad: TriangleVertices = GENESIS_TRIAD_VERTICES) -> Optional[CartesianPoint]:
    """
    Converts a FractalCoordinate to a representative CartesianPoint.
    This could be the centroid of the fractal triangle, or one of its vertices.
    Let's use the centroid of the triangle identified by the fractal coordinate.
    """
    triangle_vertices = get_triangle_for_fractal_coord(coord, initial_triad)
    if not triangle_vertices:
        return None

    # Calculate centroid
    p1, p2, p3 = triangle_vertices
    centroid_x = (p1.x + p2.x + p3.x) / 3
    centroid_y = (p1.y + p2.y + p3.y) / 3
    return CartesianPoint(x=centroid_x, y=centroid_y)

def get_fractal_positions_recursive(current_triangle_vertices: TriangleVertices, current_depth: int, target_depth: int, current_path: Tuple[int, ...]) -> List[FractalCoordinate]:
    """Helper function to recursively generate fractal positions."""
    positions = []
    if current_depth == target_depth:
        positions.append(FractalCoordinate(depth=current_depth, path=current_path))
        return positions

    if current_depth > target_depth:
        return []

    child_triangles, _ = subdivide_triangle(current_triangle_vertices)
    for i, child_v in enumerate(child_triangles):
        new_path = current_path + (i,)
        positions.extend(get_fractal_positions_recursive(child_v, current_depth + 1, target_depth, new_path))
    return positions

def get_fractal_positions(depth: int, initial_triad: TriangleVertices = GENESIS_TRIAD_VERTICES) -> List[FractalCoordinate]:
    """
    Generates all valid fractal coordinates (referring to solid triangles) up to a certain depth.
    A coordinate at depth D means it's one of the 3^D smallest triangles.
    """
    if depth < 0:
        return []
    if depth == 0:
        # Represents the initial Triad itself, or perhaps its vertices?
        # For now, let's say depth 0 is a single entity, the Genesis Triad.
        # Path is empty for the Genesis Triad.
        return [FractalCoordinate(depth=0, path=())]

    # The problem defines fractal coordinate with path from Genesis.
    # So, a depth 'd' coordinate will have a path of length 'd'.
    # We start subdividing from the Genesis Triad.
    return get_fractal_positions_recursive(initial_triad, 0, depth, ())


# --- Parent-Child and Sibling Relationships ---

def get_parent(coord: FractalCoordinate) -> Optional[FractalCoordinate]:
    """
    Calculates the parent of a given fractal coordinate.
    The parent is at depth-1 and has the path except for the last element.
    """
    if coord.depth == 0: # Genesis Triad has no parent
        return None
    if not coord.path or len(coord.path) != coord.depth: # Path should match depth
        return None

    parent_depth = coord.depth - 1
    parent_path = coord.path[:-1]
    return FractalCoordinate(depth=parent_depth, path=parent_path)

def get_children(coord: FractalCoordinate, max_depth_limit: Optional[int] = None) -> List[FractalCoordinate]:
    """
    Calculates the children of a given fractal coordinate.
    Children are at depth+1, with paths extending the parent's path by 0, 1, or 2.
    """
    if max_depth_limit is not None and coord.depth >= max_depth_limit:
        return []

    children_coords = []
    child_depth = coord.depth + 1
    for i in range(3): # Each triangle subdivides into 3 children (0, 1, 2)
        child_path = coord.path + (i,)
        children_coords.append(FractalCoordinate(depth=child_depth, path=child_path))
    return children_coords

def get_siblings(coord: FractalCoordinate) -> List[FractalCoordinate]:
    """
    Calculates the siblings of a given fractal coordinate.
    Siblings share the same parent (same path prefix and depth).
    """
    if coord.depth == 0: # Genesis Triad has no siblings
        return []

    parent = get_parent(coord)
    if not parent: # Should not happen if depth > 0 and path is valid
        return []

    # Siblings are children of the same parent, excluding the coordinate itself.
    siblings = []
    # Parent's path is coord.path[:-1]. Children append 0, 1, or 2.
    last_digit_of_coord = coord.path[-1]

    for i in range(3): # Children indices are 0, 1, 2
        if i != last_digit_of_coord:
            sibling_path = parent.path + (i,)
            siblings.append(FractalCoordinate(depth=coord.depth, path=sibling_path))
    return siblings

# --- Validation Functions ---

def is_valid_fractal_coordinate(coord: FractalCoordinate, initial_triad: TriangleVertices = GENESIS_TRIAD_VERTICES) -> bool:
    """
    Validates if a fractal coordinate is geometrically valid (i.e., maps to an actual triangle).
    """
    if coord.depth < 0: return False
    if len(coord.path) != coord.depth: return False
    for path_element in coord.path:
        if not (0 <= path_element <= 2): # Path elements must be 0, 1, or 2 for children
            return False
    # Check if it can be derived
    return get_triangle_for_fractal_coord(coord, initial_triad) is not None


def is_valid_child_relationship(parent_coord: FractalCoordinate, child_coord: FractalCoordinate) -> bool:
    """Checks if child_coord is a valid child of parent_coord."""
    if child_coord.depth != parent_coord.depth + 1:
        return False
    if len(child_coord.path) != child_coord.depth:
        return False
    if not child_coord.path[:-1] == parent_coord.path:
        return False
    if not (0 <= child_coord.path[-1] <= 2): # Last part of path must be 0, 1 or 2
        return False
    return True

def are_siblings(coord1: FractalCoordinate, coord2: FractalCoordinate) -> bool:
    """Checks if two fractal coordinates are siblings."""
    if coord1.depth != coord2.depth or coord1.depth == 0:
        return False
    if coord1.path == coord2.path: # Cannot be sibling of itself
        return False

    # Ensure path lengths match depths (get_parent also checks this, but good for early exit)
    if len(coord1.path) != coord1.depth or len(coord2.path) != coord2.depth:
        return False

    # Ensure path elements themselves are valid (0, 1, or 2)
    # This is crucial because get_parent doesn't check value of last path element of its input.
    for path_element in coord1.path:
        if not (0 <= path_element <= 2):
            return False
    for path_element in coord2.path:
        if not (0 <= path_element <= 2):
            return False

    parent1 = get_parent(coord1)
    parent2 = get_parent(coord2)

    # After the checks above, parent1 and parent2 should be non-None if depth > 0.
    # And they should be actual FractalCoordinate objects.
    return parent1 == parent2

if __name__ == '__main__':
    # Example Usages & Basic Tests (Not unit tests, just for demonstration)
    print("Genesis Triad Vertices:", GENESIS_TRIAD_VERTICES)

    # Subdivide Genesis Triad
    children_of_genesis, void_of_genesis = subdivide_triangle(GENESIS_TRIAD_VERTICES)
    print(f"\nGenesis Triad subdivided into {len(children_of_genesis)} children and 1 void.")
    # print("First child triangle vertices:", children_of_genesis[0])
    # print("Void triangle vertices:", void_of_genesis)

    # Fractal Coordinates
    genesis_coord = FractalCoordinate(depth=0, path=())
    print(f"\nGenesis Coordinate: {genesis_coord}")
    print(f"Is Genesis Coord Valid? {is_valid_fractal_coordinate(genesis_coord)}")

    # Children of Genesis
    children_coords_depth1 = get_children(genesis_coord)
    print(f"Children of Genesis: {children_coords_depth1}")

    if children_coords_depth1:
        child0 = children_coords_depth1[0] # (depth=1, path=(0,))
        print(f"First child of Genesis: {child0}")
        print(f"Is {child0} valid? {is_valid_fractal_coordinate(child0)}")

        # Parent of child0
        parent_of_child0 = get_parent(child0)
        print(f"Parent of {child0}: {parent_of_child0}")
        assert parent_of_child0 == genesis_coord

        # Siblings of child0
        siblings_of_child0 = get_siblings(child0)
        print(f"Siblings of {child0}: {siblings_of_child0}")
        assert len(siblings_of_child0) == 2
        assert FractalCoordinate(depth=1, path=(1,)) in siblings_of_child0
        assert FractalCoordinate(depth=1, path=(2,)) in siblings_of_child0

        # Validate child relationship
        print(f"Is {child0} a valid child of {genesis_coord}? {is_valid_child_relationship(genesis_coord, child0)}")

        # Grandchildren (children of child0)
        grandchildren_coords = get_children(child0)
        print(f"Children of {child0} (Grandchildren of Genesis): {grandchildren_coords}")
        if grandchildren_coords:
            grandchild0_0 = grandchildren_coords[0] # (depth=2, path=(0,0))
            print(f"First grandchild ({grandchild0_0}):")
            print(f"  Is valid? {is_valid_fractal_coordinate(grandchild0_0)}")
            parent_of_grandchild = get_parent(grandchild0_0)
            print(f"  Parent: {parent_of_grandchild}")
            assert parent_of_grandchild == child0

            # Cartesian representation of grandchild0_0 centroid
            cartesian_grandchild0_0 = fractal_to_cartesian(grandchild0_0)
            print(f"  Centroid (Cartesian): {cartesian_grandchild0_0}")

            # Get triangle for grandchild0_0
            triangle_grandchild0_0 = get_triangle_for_fractal_coord(grandchild0_0)
            # print(f"  Triangle Vertices: {triangle_grandchild0_0}")


    # Generate positions at depth 2
    print("\nFractal positions at depth 2:")
    depth2_positions = get_fractal_positions(depth=2)
    # for pos in depth2_positions:
    #     print(pos)
    print(f"Total positions at depth 2: {len(depth2_positions)} (expected 3^2 = 9)")
    assert len(depth2_positions) == 9

    # Generate positions at depth 0
    depth0_positions = get_fractal_positions(depth=0)
    print(f"Total positions at depth 0: {len(depth0_positions)} (expected 1)")
    assert len(depth0_positions) == 1
    assert depth0_positions[0] == FractalCoordinate(depth=0, path=())

    # Test cartesian_to_fractal (placeholder, will return None)
    # test_point = CartesianPoint(x=0, y=HEIGHT * 0.5) # A point near the top
    # print(f"\nAttempting to convert {test_point} to fractal coordinate (placeholder):")
    # print(cartesian_to_fractal(test_point, max_depth=2))

    print("\nBasic implementation of Prompt 1 elements seems to be in place.")
    print("Further work: Robust cartesian_to_fractal, more geometry tests.")


# --- Additional Geometric Helper Functions ---

def distance_sq(p1: CartesianPoint, p2: CartesianPoint) -> float:
    """Calculates the squared Euclidean distance between two points."""
    return (p1.x - p2.x)**2 + (p1.y - p2.y)**2

def distance(p1: CartesianPoint, p2: CartesianPoint) -> float:
    """Calculates the Euclidean distance between two points."""
    return math.sqrt(distance_sq(p1, p2))

def is_point_on_line_segment(p: CartesianPoint, a: CartesianPoint, b: CartesianPoint, tolerance=1e-9) -> bool:
    """
    Checks if point p lies on the line segment 'ab'.
    """
    # If segment is degenerate (a point)
    if points_are_close(a, b, tolerance):
        return points_are_close(p, a, tolerance)

    # Check for collinearity: cross product (P - A) x (B - A) should be ~0
    # (p.y - a.y) * (b.x - a.x) - (p.x - a.x) * (b.y - a.y)
    # Note: tolerance for cross_product might need to be scaled if coordinates are very large.
    # For typical geometric ranges, a small absolute tolerance should be fine.
    cross_product = (p.y - a.y) * (b.x - a.x) - (p.x - a.x) * (b.y - a.y)
    if abs(cross_product) > tolerance:
        return False # Not collinear

    # Check if p's projection onto the line ab lies within the segment ab.
    # This is done by checking if p is within the "range" of a and b using dot products.
    # (p - a) . (b - a) must be >= 0
    dot_product_pa_ba = (p.x - a.x) * (b.x - a.x) + (p.y - a.y) * (b.y - a.y)
    if dot_product_pa_ba < -tolerance: # p is "behind" a (allowing for small float errors)
        return False

    # (p - b) . (a - b) must be >= 0. This is equivalent to (p-a).(b-a) <= (b-a).(b-a)
    # So, dot_product_pa_ba must be <= squared_length_ab
    squared_length_ab = distance_sq(a, b) # distance_sq(a,b) will be > 0 here due to first check
    if dot_product_pa_ba > squared_length_ab + tolerance: # p is "beyond" b (allowing for small float errors)
        return False

    return True

def points_are_close(p1: CartesianPoint, p2: CartesianPoint, tolerance=1e-9) -> bool:
    """Checks if two points are within a given tolerance of each other."""
    return distance_sq(p1, p2) < tolerance**2
