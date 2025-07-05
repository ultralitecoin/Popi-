import unittest
import math

# Adjust the import path based on your project structure.
# If 'fractal_blockchain' is the root package and tests are run from the project root:
from fractal_blockchain.core.mathematics.fractal_math import (
    CartesianPoint, FractalCoordinate,
    GENESIS_TRIAD_VERTICES, SIDE_LENGTH, HEIGHT,
    get_midpoint, subdivide_triangle,
    get_triangle_for_fractal_coord,
    fractal_to_cartesian, cartesian_to_fractal, # Added cartesian_to_fractal
    get_fractal_positions,
    get_parent, get_children, get_siblings,
    is_valid_fractal_coordinate,
    is_valid_child_relationship, are_siblings
)

class TestFractalMath(unittest.TestCase):

    def assertCartesianPointAlmostEqual(self, p1: CartesianPoint, p2: CartesianPoint, places=7):
        self.assertAlmostEqual(p1.x, p2.x, places=places)
        self.assertAlmostEqual(p1.y, p2.y, places=places)

    def assertTriangleVerticesAlmostEqual(self, t1_verts, t2_verts, places=7):
        self.assertEqual(len(t1_verts), 3)
        self.assertEqual(len(t2_verts), 3)
        for i in range(3):
            self.assertCartesianPointAlmostEqual(t1_verts[i], t2_verts[i], places=places)

    def test_cartesian_point(self):
        p = CartesianPoint(1.0, 2.5)
        self.assertEqual(p.x, 1.0)
        self.assertEqual(p.y, 2.5)

    def test_fractal_coordinate(self):
        fc = FractalCoordinate(depth=2, path=(0, 1))
        self.assertEqual(fc.depth, 2)
        self.assertEqual(fc.path, (0, 1))

    def test_genesis_triad_properties(self):
        # Basic check on coordinates (assuming standard equilateral triangle setup)
        # Top vertex
        self.assertAlmostEqual(GENESIS_TRIAD_VERTICES[0].x, 0)
        self.assertAlmostEqual(GENESIS_TRIAD_VERTICES[0].y, (2/3) * HEIGHT)
        # Bottom-left
        self.assertAlmostEqual(GENESIS_TRIAD_VERTICES[1].x, -SIDE_LENGTH / 2)
        self.assertAlmostEqual(GENESIS_TRIAD_VERTICES[1].y, (-1/3) * HEIGHT)
        # Bottom-right
        self.assertAlmostEqual(GENESIS_TRIAD_VERTICES[2].x, SIDE_LENGTH / 2)
        self.assertAlmostEqual(GENESIS_TRIAD_VERTICES[2].y, (-1/3) * HEIGHT)

    def test_get_midpoint(self):
        p1 = CartesianPoint(0, 0)
        p2 = CartesianPoint(10, 20)
        mid = get_midpoint(p1, p2)
        self.assertCartesianPointAlmostEqual(mid, CartesianPoint(5, 10))

        p3 = CartesianPoint(-5, 5)
        p4 = CartesianPoint(5, -5)
        mid2 = get_midpoint(p3, p4)
        self.assertCartesianPointAlmostEqual(mid2, CartesianPoint(0, 0))

    def test_subdivide_triangle(self):
        # Using GENESIS_TRIAD_VERTICES for a concrete test
        children, void = subdivide_triangle(GENESIS_TRIAD_VERTICES)
        self.assertEqual(len(children), 3)

        # Expected midpoints based on GENESIS_TRIAD_VERTICES
        p_top, p_left_base, p_right_base = GENESIS_TRIAD_VERTICES
        m_top_left_expected = get_midpoint(p_top, p_left_base)
        m_top_right_expected = get_midpoint(p_top, p_right_base)
        m_left_right_base_expected = get_midpoint(p_left_base, p_right_base)

        # Child 0 (Top)
        expected_child0_verts = (p_top, m_top_left_expected, m_top_right_expected)
        self.assertTriangleVerticesAlmostEqual(children[0], expected_child0_verts)

        # Child 1 (Bottom-left)
        expected_child1_verts = (m_top_left_expected, p_left_base, m_left_right_base_expected)
        self.assertTriangleVerticesAlmostEqual(children[1], expected_child1_verts)

        # Child 2 (Bottom-right)
        expected_child2_verts = (m_top_right_expected, m_left_right_base_expected, p_right_base)
        self.assertTriangleVerticesAlmostEqual(children[2], expected_child2_verts)

        # Void Triangle
        expected_void_verts = (m_top_left_expected, m_left_right_base_expected, m_top_right_expected)
        self.assertTriangleVerticesAlmostEqual(void, expected_void_verts)

    def test_get_triangle_for_fractal_coord(self):
        # Depth 0 - the Genesis Triad itself
        coord_g = FractalCoordinate(depth=0, path=())
        tri_g = get_triangle_for_fractal_coord(coord_g)
        self.assertIsNotNone(tri_g)
        self.assertTriangleVerticesAlmostEqual(tri_g, GENESIS_TRIAD_VERTICES)

        # Depth 1, child 0
        coord_d1_c0 = FractalCoordinate(depth=1, path=(0,))
        tri_d1_c0 = get_triangle_for_fractal_coord(coord_d1_c0)
        self.assertIsNotNone(tri_d1_c0)

        # Expected vertices for child 0 of Genesis
        children_g, _ = subdivide_triangle(GENESIS_TRIAD_VERTICES)
        self.assertTriangleVerticesAlmostEqual(tri_d1_c0, children_g[0])

        # Depth 2, path (0,1)
        coord_d2_c01 = FractalCoordinate(depth=2, path=(0,1))
        tri_d2_c01 = get_triangle_for_fractal_coord(coord_d2_c01)
        self.assertIsNotNone(tri_d2_c01)

        # Expected: subdivide child 0 of Genesis, then take its 2nd child (index 1)
        children_d1_c0, _ = subdivide_triangle(children_g[0])
        self.assertTriangleVerticesAlmostEqual(tri_d2_c01, children_d1_c0[1])

        # Invalid coordinates
        self.assertIsNone(get_triangle_for_fractal_coord(FractalCoordinate(depth=-1, path=())))
        self.assertIsNone(get_triangle_for_fractal_coord(FractalCoordinate(depth=1, path=()))) # Path too short
        self.assertIsNone(get_triangle_for_fractal_coord(FractalCoordinate(depth=1, path=(3,)))) # Invalid path element
        self.assertIsNone(get_triangle_for_fractal_coord(FractalCoordinate(depth=0, path=(0,)))) # Path too long for depth 0

    def test_fractal_to_cartesian_centroid(self):
        # Centroid of Genesis Triad
        coord_g = FractalCoordinate(depth=0, path=())
        centroid_g = fractal_to_cartesian(coord_g)
        self.assertIsNotNone(centroid_g)
        expected_centroid_g_x = (GENESIS_TRIAD_VERTICES[0].x + GENESIS_TRIAD_VERTICES[1].x + GENESIS_TRIAD_VERTICES[2].x) / 3
        expected_centroid_g_y = (GENESIS_TRIAD_VERTICES[0].y + GENESIS_TRIAD_VERTICES[1].y + GENESIS_TRIAD_VERTICES[2].y) / 3
        self.assertCartesianPointAlmostEqual(centroid_g, CartesianPoint(expected_centroid_g_x, expected_centroid_g_y))

        # Centroid of first child of Genesis
        coord_d1_c0 = FractalCoordinate(depth=1, path=(0,))
        centroid_d1_c0 = fractal_to_cartesian(coord_d1_c0)
        self.assertIsNotNone(centroid_d1_c0)

        tri_d1_c0_verts = get_triangle_for_fractal_coord(coord_d1_c0)
        expected_centroid_d1_c0_x = (tri_d1_c0_verts[0].x + tri_d1_c0_verts[1].x + tri_d1_c0_verts[2].x) / 3
        expected_centroid_d1_c0_y = (tri_d1_c0_verts[0].y + tri_d1_c0_verts[1].y + tri_d1_c0_verts[2].y) / 3
        self.assertCartesianPointAlmostEqual(centroid_d1_c0, CartesianPoint(expected_centroid_d1_c0_x, expected_centroid_d1_c0_y))

        # Invalid coord
        self.assertIsNone(fractal_to_cartesian(FractalCoordinate(depth=1, path=(7,))))

    def test_point_in_triangle_internal(self):
        # This tests the internal helper function if accessible, or logic via cartesian_to_fractal
        # For direct test, we'd need to expose point_in_triangle or test it implicitly.
        # Let's assume we can call it if it were part of the class or module.
        # Since it's a local helper in cartesian_to_fractal, we'll test its effects via the main function.
        # If we were to test it directly:
        # v1, v2, v3 = CartesianPoint(0,0), CartesianPoint(4,0), CartesianPoint(2,4)
        # self.assertTrue(point_in_triangle(CartesianPoint(2,1), v1, v2, v3)) # Inside
        # self.assertTrue(point_in_triangle(CartesianPoint(0,0), v1, v2, v3)) # Vertex
        # self.assertTrue(point_in_triangle(CartesianPoint(3,0), v1, v2, v3)) # Edge
        # self.assertFalse(point_in_triangle(CartesianPoint(5,1), v1, v2, v3)) # Outside
        pass # Tested via cartesian_to_fractal

    def test_cartesian_to_fractal(self):
        # Test case: Point at the centroid of Genesis Triad
        # Centroid of GENESIS_TRIAD_VERTICES
        g_v = GENESIS_TRIAD_VERTICES
        centroid_g_x = (g_v[0].x + g_v[1].x + g_v[2].x) / 3
        centroid_g_y = (g_v[0].y + g_v[1].y + g_v[2].y) / 3
        centroid_genesis = CartesianPoint(centroid_g_x, centroid_g_y)

        # At max_depth 0, a point inside Genesis should return depth 0, empty path
        coord_cg_d0 = cartesian_to_fractal(centroid_genesis, max_depth=0)
        self.assertIsNotNone(coord_cg_d0)
        self.assertEqual(coord_cg_d0.depth, 0)
        self.assertEqual(coord_cg_d0.path, tuple())

        # At max_depth 1, the centroid of Genesis is in the central void triangle (path (3,))
        coord_cg_d1 = cartesian_to_fractal(centroid_genesis, max_depth=1)
        self.assertIsNotNone(coord_cg_d1)
        self.assertEqual(coord_cg_d1.depth, 1)
        self.assertEqual(coord_cg_d1.path, (3,)) # Path to void

        # Test point known to be in the top child triangle of Genesis (child 0)
        # Top child (child 0) vertices: (p_top, m_top_left, m_top_right)
        p_top, p_left_base, p_right_base = g_v
        m_top_left = get_midpoint(p_top, p_left_base)
        m_top_right = get_midpoint(p_top, p_right_base)
        # Centroid of this top child triangle
        child0_centroid_x = (p_top.x + m_top_left.x + m_top_right.x) / 3
        child0_centroid_y = (p_top.y + m_top_left.y + m_top_right.y) / 3
        point_in_child0 = CartesianPoint(child0_centroid_x, child0_centroid_y)

        coord_pc0_d1 = cartesian_to_fractal(point_in_child0, max_depth=1)
        self.assertIsNotNone(coord_pc0_d1)
        self.assertEqual(coord_pc0_d1.depth, 1)
        self.assertEqual(coord_pc0_d1.path, (0,)) # Path to child 0

        coord_pc0_d2 = cartesian_to_fractal(point_in_child0, max_depth=2) # Deeper search
        self.assertIsNotNone(coord_pc0_d2)
        self.assertEqual(coord_pc0_d2.depth, 2) # Point is in the void of child 0
        self.assertEqual(coord_pc0_d2.path, (0,3))

        # Test point outside Genesis Triad
        point_outside = CartesianPoint(SIDE_LENGTH * 2, SIDE_LENGTH * 2)
        self.assertIsNone(cartesian_to_fractal(point_outside, max_depth=1))

        # Test point exactly on a vertex of Genesis (e.g., p_top)
        # This is tricky due to floating point and shared boundaries.
        # The current point_in_triangle includes edges/vertices.
        # p_top could belong to child 0, or be ambiguous if not handled carefully.
        # For p_top, it should ideally resolve to a path related to child 0 if subdivision makes sense.
        # Let's test a point very slightly perturbed from p_top into child 0.
        point_near_p_top_in_child0 = CartesianPoint(p_top.x, p_top.y - HEIGHT * 0.01) # Slightly below top vertex
                                                                                 # but still within child 0 region

        # This specific point_near_p_top_in_child0's actual location depends on how child0 is defined
        # Child0 is (p_top, m_top_left, m_top_right). Its y range is from m_top_left.y to p_top.y
        # m_top_left.y is (p_top.y + p_left_base.y)/2.
        # Example: p_top=(0, 577), p_left_base=(-500, -288). m_top_left.y = (577-288)/2 = 144.5
        # So child0 is from y=144.5 to y=577. Point (0, 577 - H*0.01) should be in child0.

        coord_near_ptop = cartesian_to_fractal(point_near_p_top_in_child0, max_depth=1)
        self.assertIsNotNone(coord_near_ptop, f"Point {point_near_p_top_in_child0} did not resolve.")
        if coord_near_ptop: # Check if not None before accessing attributes
            self.assertEqual(coord_near_ptop.depth, 1)
            self.assertEqual(coord_near_ptop.path, (0,))

        # Test point in a grandchild, e.g. child (1) of child (0) -> path (0,1)
        # Child 0 of G: (p_top, m_top_left, m_top_right)
        # Subdivide Child 0:
        children_of_child0, _ = subdivide_triangle((p_top, m_top_left, m_top_right))
        grandchild_0_1_vertices = children_of_child0[1] # Vertices of grandchild (0,1)
        # Centroid of this grandchild
        gc_0_1_centroid_x = (grandchild_0_1_vertices[0].x + grandchild_0_1_vertices[1].x + grandchild_0_1_vertices[2].x) / 3
        gc_0_1_centroid_y = (grandchild_0_1_vertices[0].y + grandchild_0_1_vertices[1].y + grandchild_0_1_vertices[2].y) / 3
        point_in_gc_0_1 = CartesianPoint(gc_0_1_centroid_x, gc_0_1_centroid_y)

        coord_pgc01_d2 = cartesian_to_fractal(point_in_gc_0_1, max_depth=2)
        self.assertIsNotNone(coord_pgc01_d2)
        if coord_pgc01_d2:
            self.assertEqual(coord_pgc01_d2.depth, 2)
            self.assertEqual(coord_pgc01_d2.path, (0,1))

        # Test deeper into the void of grandchild (0,1)
        coord_pgc01_d3 = cartesian_to_fractal(point_in_gc_0_1, max_depth=3)
        self.assertIsNotNone(coord_pgc01_d3)
        if coord_pgc01_d3:
            self.assertEqual(coord_pgc01_d3.depth, 3)
            self.assertEqual(coord_pgc01_d3.path, (0,1,3))


    def test_get_fractal_positions(self):
        # Depth 0
        pos_d0 = get_fractal_positions(depth=0)
        self.assertEqual(len(pos_d0), 1)
        self.assertEqual(pos_d0[0], FractalCoordinate(depth=0, path=()))

        # Depth 1
        pos_d1 = get_fractal_positions(depth=1)
        self.assertEqual(len(pos_d1), 3) # 3^1
        self.assertIn(FractalCoordinate(depth=1, path=(0,)), pos_d1)
        self.assertIn(FractalCoordinate(depth=1, path=(1,)), pos_d1)
        self.assertIn(FractalCoordinate(depth=1, path=(2,)), pos_d1)

        # Depth 2
        pos_d2 = get_fractal_positions(depth=2)
        self.assertEqual(len(pos_d2), 9) # 3^2
        # Check a few samples
        self.assertIn(FractalCoordinate(depth=2, path=(0,0)), pos_d2)
        self.assertIn(FractalCoordinate(depth=2, path=(1,2)), pos_d2)
        self.assertIn(FractalCoordinate(depth=2, path=(2,1)), pos_d2)

        # Invalid depth
        self.assertEqual(get_fractal_positions(depth=-1), [])


    def test_get_parent(self):
        coord_g = FractalCoordinate(depth=0, path=())
        self.assertIsNone(get_parent(coord_g)) # Genesis has no parent

        coord_d1_c0 = FractalCoordinate(depth=1, path=(0,))
        self.assertEqual(get_parent(coord_d1_c0), coord_g)

        coord_d2_c12 = FractalCoordinate(depth=2, path=(1,2))
        expected_parent_d2_c12 = FractalCoordinate(depth=1, path=(1,))
        self.assertEqual(get_parent(coord_d2_c12), expected_parent_d2_c12)

        # Invalid: path length doesn't match depth
        self.assertIsNone(get_parent(FractalCoordinate(depth=1, path=(0,1))))

    def test_get_children(self):
        coord_g = FractalCoordinate(depth=0, path=())
        children_g = get_children(coord_g)
        self.assertEqual(len(children_g), 3)
        self.assertIn(FractalCoordinate(depth=1, path=(0,)), children_g)
        self.assertIn(FractalCoordinate(depth=1, path=(1,)), children_g)
        self.assertIn(FractalCoordinate(depth=1, path=(2,)), children_g)

        coord_d1_c0 = FractalCoordinate(depth=1, path=(0,))
        children_d1_c0 = get_children(coord_d1_c0)
        self.assertEqual(len(children_d1_c0), 3)
        self.assertIn(FractalCoordinate(depth=2, path=(0,0)), children_d1_c0)
        self.assertIn(FractalCoordinate(depth=2, path=(0,1)), children_d1_c0)
        self.assertIn(FractalCoordinate(depth=2, path=(0,2)), children_d1_c0)

        # Test depth limit
        children_g_limit0 = get_children(coord_g, max_depth_limit=0)
        self.assertEqual(len(children_g_limit0), 0)

        children_g_limit1 = get_children(coord_g, max_depth_limit=1) # Children are at depth 1, so they are fine
        self.assertEqual(len(children_g_limit1), 3)

        children_d1_c0_limit1 = get_children(coord_d1_c0, max_depth_limit=1) # Children would be depth 2
        self.assertEqual(len(children_d1_c0_limit1), 0)


    def test_get_siblings(self):
        coord_g = FractalCoordinate(depth=0, path=())
        self.assertEqual(get_siblings(coord_g), []) # Genesis has no siblings

        coord_d1_c0 = FractalCoordinate(depth=1, path=(0,))
        siblings_d1_c0 = get_siblings(coord_d1_c0)
        self.assertEqual(len(siblings_d1_c0), 2)
        self.assertIn(FractalCoordinate(depth=1, path=(1,)), siblings_d1_c0)
        self.assertIn(FractalCoordinate(depth=1, path=(2,)), siblings_d1_c0)
        self.assertNotIn(coord_d1_c0, siblings_d1_c0)

        coord_d2_c12 = FractalCoordinate(depth=2, path=(1,2)) # Parent is (1,)
        siblings_d2_c12 = get_siblings(coord_d2_c12)
        self.assertEqual(len(siblings_d2_c12), 2)
        self.assertIn(FractalCoordinate(depth=2, path=(1,0)), siblings_d2_c12)
        self.assertIn(FractalCoordinate(depth=2, path=(1,1)), siblings_d2_c12)
        self.assertNotIn(coord_d2_c12, siblings_d2_c12)

        # Invalid coord (path too short)
        self.assertEqual(get_siblings(FractalCoordinate(depth=1, path=())), [])


    def test_is_valid_fractal_coordinate(self):
        self.assertTrue(is_valid_fractal_coordinate(FractalCoordinate(depth=0, path=())))
        self.assertTrue(is_valid_fractal_coordinate(FractalCoordinate(depth=1, path=(0,))))
        self.assertTrue(is_valid_fractal_coordinate(FractalCoordinate(depth=2, path=(1,2))))

        self.assertFalse(is_valid_fractal_coordinate(FractalCoordinate(depth=-1, path=())))
        self.assertFalse(is_valid_fractal_coordinate(FractalCoordinate(depth=1, path=()))) # Path too short
        self.assertFalse(is_valid_fractal_coordinate(FractalCoordinate(depth=0, path=(0,)))) # Path too long
        self.assertFalse(is_valid_fractal_coordinate(FractalCoordinate(depth=1, path=(3,)))) # Invalid path element
        self.assertFalse(is_valid_fractal_coordinate(FractalCoordinate(depth=1, path=(0,1)))) # Path too long for depth


    def test_is_valid_child_relationship(self):
        parent_g = FractalCoordinate(depth=0, path=())
        child_d1_c0 = FractalCoordinate(depth=1, path=(0,))
        child_d1_c1 = FractalCoordinate(depth=1, path=(1,))
        not_child_d2 = FractalCoordinate(depth=2, path=(0,0))
        not_child_diff_parent = FractalCoordinate(depth=1, path=(0,)) # Same as child_d1_c0

        self.assertTrue(is_valid_child_relationship(parent_g, child_d1_c0))
        self.assertTrue(is_valid_child_relationship(parent_g, child_d1_c1))

        # Wrong depth
        self.assertFalse(is_valid_child_relationship(parent_g, not_child_d2))
        self.assertFalse(is_valid_child_relationship(child_d1_c0, parent_g))

        # Wrong parent path
        parent_d1_c1 = FractalCoordinate(depth=1, path=(1,))
        self.assertFalse(is_valid_child_relationship(parent_d1_c1, FractalCoordinate(depth=2, path=(0,0)))) # child's parent path is (0,) not (1,)

        # Invalid child path component
        self.assertFalse(is_valid_child_relationship(parent_g, FractalCoordinate(depth=1, path=(3,))))

        # Invalid child path length
        self.assertFalse(is_valid_child_relationship(parent_g, FractalCoordinate(depth=1, path=(0,0))))


    def test_are_siblings(self):
        coord_d1_c0 = FractalCoordinate(depth=1, path=(0,))
        coord_d1_c1 = FractalCoordinate(depth=1, path=(1,))
        coord_d1_c2 = FractalCoordinate(depth=1, path=(2,))

        self.assertTrue(are_siblings(coord_d1_c0, coord_d1_c1))
        self.assertTrue(are_siblings(coord_d1_c1, coord_d1_c2))
        self.assertFalse(are_siblings(coord_d1_c0, coord_d1_c0)) # Not sibling of itself

        coord_g = FractalCoordinate(depth=0, path=())
        self.assertFalse(are_siblings(coord_g, coord_g)) # Genesis has no siblings

        coord_d2_c00 = FractalCoordinate(depth=2, path=(0,0))
        coord_d2_c01 = FractalCoordinate(depth=2, path=(0,1))
        coord_d2_c10 = FractalCoordinate(depth=2, path=(1,0))

        self.assertTrue(are_siblings(coord_d2_c00, coord_d2_c01))
        self.assertFalse(are_siblings(coord_d2_c00, coord_d2_c10)) # Different parents

        # Different depths
        self.assertFalse(are_siblings(coord_d1_c0, coord_d2_c00))

        # Invalid coord
        self.assertFalse(are_siblings(FractalCoordinate(depth=1, path=(7,)), coord_d1_c0))


if __name__ == '__main__':
    # To run these tests from the project root directory (e.g., 'fractal_blockchain_project'):
    # Ensure 'fractal_blockchain_project' is in PYTHONPATH or run with:
    # python -m unittest tests.core.mathematics.test_fractal_math
    unittest.main()
