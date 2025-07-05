import unittest

from fractal_blockchain.core.addressing import AddressedFractalCoordinate
from fractal_blockchain.core.mathematics.fractal_math import (
    GENESIS_TRIAD_VERTICES, subdivide_triangle
)
from fractal_blockchain.core.geometry_validator import (
    is_valid_addressed_coordinate,
    get_vertices_for_addressed_coord,
    get_neighbors,
    is_orphaned, # Currently relies on is_valid_addressed_coordinate
    is_on_boundary
)

class TestGeometryValidator(unittest.TestCase):

    def test_is_valid_addressed_coordinate(self):
        # Valid cases
        self.assertTrue(is_valid_addressed_coordinate(AddressedFractalCoordinate(0, tuple())))
        self.assertTrue(is_valid_addressed_coordinate(AddressedFractalCoordinate(1, (0,))))
        self.assertTrue(is_valid_addressed_coordinate(AddressedFractalCoordinate(1, (3,)))) # Void path
        self.assertTrue(is_valid_addressed_coordinate(AddressedFractalCoordinate(2, (0,1))))
        self.assertTrue(is_valid_addressed_coordinate(AddressedFractalCoordinate(2, (0,3)))) # Path into void
        self.assertTrue(is_valid_addressed_coordinate(AddressedFractalCoordinate(3, (0,3,1)))) # Path through void

        # Invalid cases (should be caught by AddressedFractalCoordinate constructor,
        # but is_valid_addressed_coordinate might have its own checks or rely on constructor)
        # The function itself doesn't explicitly raise errors for bad paths if constructor already did.
        # It's more about geometric traversability.
        # No direct invalid cases here as AddressedFractalCoordinate constructor would fail first for bad paths like (4,) or length mismatch.
        # is_valid_addressed_coordinate assumes a structurally valid AddressedFractalCoordinate input.
        # We can test that is_valid_addressed_coordinate itself doesn't break on valid inputs.
        pass # Covered by constructor tests for AddressedFractalCoordinate for structural validity.

    def test_get_vertices_for_addressed_coord(self):
        # Genesis
        genesis_coord = AddressedFractalCoordinate(0, tuple())
        self.assertEqual(get_vertices_for_addressed_coord(genesis_coord), GENESIS_TRIAD_VERTICES)

        # Child 0 of Genesis
        d1_c0 = AddressedFractalCoordinate(1, (0,))
        children_g, _ = subdivide_triangle(GENESIS_TRIAD_VERTICES)
        self.assertEqual(get_vertices_for_addressed_coord(d1_c0), children_g[0])

        # Void of Genesis (path (3,) at depth 1)
        d1_v3 = AddressedFractalCoordinate(1, (3,))
        _, void_g = subdivide_triangle(GENESIS_TRIAD_VERTICES)
        self.assertEqual(get_vertices_for_addressed_coord(d1_v3), void_g)

        # Void of Child 0 of Genesis (path (0,3) at depth 2)
        d2_p03 = AddressedFractalCoordinate(2, (0,3))
        _, void_of_child0 = subdivide_triangle(children_g[0])
        self.assertEqual(get_vertices_for_addressed_coord(d2_p03), void_of_child0)

        # Child 1 within the void of Child 0 of Genesis (path (0,3,1) at depth 3)
        d3_p031 = AddressedFractalCoordinate(3, (0,3,1))
        children_of_void_of_child0, _ = subdivide_triangle(void_of_child0)
        self.assertEqual(get_vertices_for_addressed_coord(d3_p031), children_of_void_of_child0[1])

        # Test with a coord that would fail AddressedFractalCoordinate construction (indirectly tests None return if error)
        # However, get_vertices_for_addressed_coord expects a valid AddressedFractalCoordinate object.
        # If we want to test its internal error handling for invalid paths if constructor was bypassed:
        # self.assertIsNone(get_vertices_for_addressed_coord(AddressedFractalCoordinate(depth=1, path=(4,)))) # This raises in constructor
        # So this aspect is more about how it handles already validated objects.
        # It should not return None for structurally valid AddressedFractalCoordinates.
        self.assertIsNotNone(get_vertices_for_addressed_coord(AddressedFractalCoordinate(2, (1,2))))


    def test_get_neighbors(self): # Renamed from test_get_neighbors_placeholder
        # Now returns all siblings (solid and void)

        # Genesis
        genesis_coord = AddressedFractalCoordinate(0, tuple())
        self.assertEqual(get_neighbors(genesis_coord), []) # Depth 0 has no siblings

        # Solid coord d1_c0 (path (0,))
        d1_c0 = AddressedFractalCoordinate(1, (0,))
        # Expected siblings: (1,), (2,), (3,)
        expected_neighbors_d1_c0 = [
            AddressedFractalCoordinate(1, (1,)), # Solid sibling
            AddressedFractalCoordinate(1, (2,)), # Solid sibling
            AddressedFractalCoordinate(1, (3,))  # Void sibling (central hole relative to parent)
        ]
        neighbors_d1_c0 = get_neighbors(d1_c0)
        self.assertCountEqual(neighbors_d1_c0, expected_neighbors_d1_c0)

        # Void coord d1_v3 (path (3,))
        d1_v3 = AddressedFractalCoordinate(1, (3,))
        # Expected siblings: (0,), (1,), (2,)
        expected_neighbors_d1_v3 = [
            AddressedFractalCoordinate(1, (0,)), # Solid sibling (boundary)
            AddressedFractalCoordinate(1, (1,)), # Solid sibling (boundary)
            AddressedFractalCoordinate(1, (2,))  # Solid sibling (boundary)
        ]
        neighbors_d1_v3 = get_neighbors(d1_v3)
        self.assertCountEqual(neighbors_d1_v3, expected_neighbors_d1_v3)

        # Solid coord d2_p01 (path (0,1))
        # Parent path (0,), child index 1.
        # Expected siblings: (0,0), (0,2), (0,3)
        d2_p01 = AddressedFractalCoordinate(2, (0,1))
        expected_neighbors_d2_p01 = [
            AddressedFractalCoordinate(2, (0,0)),
            AddressedFractalCoordinate(2, (0,2)),
            AddressedFractalCoordinate(2, (0,3)) # Void sibling
        ]
        neighbors_d2_p01 = get_neighbors(d2_p01)
        self.assertCountEqual(neighbors_d2_p01, expected_neighbors_d2_p01)

    def test_is_orphaned_placeholder(self):
        # Placeholder currently just checks is_valid_addressed_coordinate
        # Valid coordinate
        valid_coord = AddressedFractalCoordinate(1, (0,))
        self.assertFalse(is_orphaned(valid_coord)) # Valid coord is not orphaned

        # is_valid_addressed_coordinate itself doesn't raise error for already constructed invalid path,
        # it relies on constructor. So, this test mostly confirms it calls is_valid_addressed_coordinate.
        # Example: is_orphaned(AddressedFractalCoordinate(1, (4,))) would fail at constructor.

    def test_is_on_boundary(self): # Renamed from test_is_on_boundary_placeholder
        # Test new heuristic: path uses at most 2 distinct solid child indices (0,1,2)

        # Max depth 0
        g = AddressedFractalCoordinate(0, tuple())
        self.assertTrue(is_on_boundary(g, 0))
        self.assertFalse(is_on_boundary(g, 1), "Genesis not on boundary if max_depth is higher")

        # Max depth 1
        d1p0 = AddressedFractalCoordinate(1, (0,)) # 1 distinct element {0} -> boundary
        d1p1 = AddressedFractalCoordinate(1, (1,)) # 1 distinct element {1} -> boundary
        d1p2 = AddressedFractalCoordinate(1, (2,)) # 1 distinct element {2} -> boundary
        d1p3_void = AddressedFractalCoordinate(1, (3,)) # Void path

        self.assertTrue(is_on_boundary(d1p0, 1))
        self.assertTrue(is_on_boundary(d1p1, 1))
        self.assertTrue(is_on_boundary(d1p2, 1))
        self.assertFalse(is_on_boundary(d1p3_void, 1), "Void path should not be on boundary")
        self.assertFalse(is_on_boundary(d1p0, 0), "Not on boundary if depth > max_depth")
        self.assertFalse(is_on_boundary(d1p0, 2), "Not on boundary if depth < max_depth")

        # Max depth 2
        # Corners (1 distinct path element)
        d2p00 = AddressedFractalCoordinate(2, (0,0)) # {0}
        d2p11 = AddressedFractalCoordinate(2, (1,1)) # {1}
        d2p22 = AddressedFractalCoordinate(2, (2,2)) # {2}
        self.assertTrue(is_on_boundary(d2p00, 2))
        self.assertTrue(is_on_boundary(d2p11, 2))
        self.assertTrue(is_on_boundary(d2p22, 2))

        # Edges (2 distinct path elements)
        d2p01 = AddressedFractalCoordinate(2, (0,1)) # {0,1}
        d2p02 = AddressedFractalCoordinate(2, (0,2)) # {0,2}
        d2p10 = AddressedFractalCoordinate(2, (1,0)) # {1,0}
        d2p12 = AddressedFractalCoordinate(2, (1,2)) # {1,2}
        d2p20 = AddressedFractalCoordinate(2, (2,0)) # {2,0}
        d2p21 = AddressedFractalCoordinate(2, (2,1)) # {2,1}
        self.assertTrue(is_on_boundary(d2p01, 2))
        self.assertTrue(is_on_boundary(d2p02, 2))
        self.assertTrue(is_on_boundary(d2p10, 2))
        self.assertTrue(is_on_boundary(d2p12, 2))
        self.assertTrue(is_on_boundary(d2p20, 2))
        self.assertTrue(is_on_boundary(d2p21, 2))

        # Inner (3 distinct path elements) - Not possible at depth 2.
        # All 9 solid triangles at depth 2 are boundary triangles for a Sierpinski.
        # Our heuristic (1 or 2 distinct path elements) correctly identifies all 9 as boundary.

        # Max depth 3
        d3p000 = AddressedFractalCoordinate(3, (0,0,0)) # {0} -> Corner -> Boundary
        self.assertTrue(is_on_boundary(d3p000, 3))

        d3p001 = AddressedFractalCoordinate(3, (0,0,1)) # {0,1} -> Edge -> Boundary
        self.assertTrue(is_on_boundary(d3p001, 3))

        d3p011 = AddressedFractalCoordinate(3, (0,1,1)) # {0,1} -> Edge -> Boundary
        self.assertTrue(is_on_boundary(d3p011, 3))

        d3p012 = AddressedFractalCoordinate(3, (0,1,2)) # {0,1,2} -> Inner -> Not Boundary
        self.assertFalse(is_on_boundary(d3p012, 3))

        d3p102 = AddressedFractalCoordinate(3, (1,0,2)) # {0,1,2} -> Inner -> Not Boundary
        self.assertFalse(is_on_boundary(d3p102, 3))

        # Void path at max_depth
        d2p03_void = AddressedFractalCoordinate(2, (0,3))
        self.assertFalse(is_on_boundary(d2p03_void, 2), "Void path should not be on boundary")


if __name__ == '__main__':
    unittest.main()
