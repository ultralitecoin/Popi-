import unittest
from typing import List, Dict, Set
from fractal_blockchain.core.addressing import AddressedFractalCoordinate
from fractal_blockchain.routing.path_finder import find_path_dijkstra, get_edge_cost

# For testing, we need a mockable or more controllable get_geometric_neighbors
# The one from geometry_validator is a placeholder.
# Let's define a mock neighbor function for testing purposes.

MOCK_ADJACENCY_MAP: Dict[AddressedFractalCoordinate, List[AddressedFractalCoordinate]] = {}

def mock_get_geometric_neighbors(coord: AddressedFractalCoordinate) -> List[AddressedFractalCoordinate]:
    return MOCK_ADJACENCY_MAP.get(coord, [])

class TestFractalPathFinder(unittest.TestCase):

    original_get_neighbors = None

    @classmethod
    def setUpClass(cls):
        # Monkey patch the get_geometric_neighbors used by path_finder
        # Important: path_finder.py needs to import get_neighbors in a way that's patchable.
        # It now imports `from fractal_blockchain.core.geometry_validator import get_neighbors`
        # So we patch `fractal_blockchain.routing.path_finder.get_neighbors`
        import fractal_blockchain.routing.path_finder as pf_module
        cls.original_get_neighbors = pf_module.get_neighbors # Store the original
        pf_module.get_neighbors = mock_get_geometric_neighbors # Apply mock


    @classmethod
    def tearDownClass(cls):
        # Restore original function
        import fractal_blockchain.routing.path_finder as pf_module
        pf_module.get_neighbors = cls.original_get_neighbors # Restore

    def setUp(self):
        # Clear mock adjacency map before each test
        MOCK_ADJACENCY_MAP.clear()

    def test_get_edge_cost(self):
        c1 = AddressedFractalCoordinate(1, (0,))
        c2 = AddressedFractalCoordinate(1, (1,))
        self.assertEqual(get_edge_cost(c1, c2), 1.0) # Default cost

    def test_find_path_dijkstra_simple_path(self):
        start = AddressedFractalCoordinate(1, (0,))
        middle = AddressedFractalCoordinate(1, (1,))
        end = AddressedFractalCoordinate(1, (2,))

        MOCK_ADJACENCY_MAP[start] = [middle]
        MOCK_ADJACENCY_MAP[middle] = [start, end]
        MOCK_ADJACENCY_MAP[end] = [middle]

        path = find_path_dijkstra(start, end)
        self.assertIsNotNone(path)
        self.assertEqual(path, [start, middle, end])

    def test_find_path_dijkstra_no_path(self):
        start = AddressedFractalCoordinate(1, (0,))
        end = AddressedFractalCoordinate(1, (2,)) # No connection defined

        MOCK_ADJACENCY_MAP[start] = [AddressedFractalCoordinate(1, (1,))]
        # No path from start to end

        path = find_path_dijkstra(start, end)
        self.assertIsNone(path)

    def test_find_path_dijkstra_start_equals_end(self):
        start = AddressedFractalCoordinate(1, (0,))
        path = find_path_dijkstra(start, start)
        self.assertIsNotNone(path)
        self.assertEqual(path, [start])

    def test_find_path_dijkstra_path_through_voids_not_allowed_by_default(self):
        start = AddressedFractalCoordinate(1, (0,))
        void_neighbor = AddressedFractalCoordinate(1, (3,)) # A void
        end = AddressedFractalCoordinate(1, (1,))

        MOCK_ADJACENCY_MAP[start] = [void_neighbor]
        MOCK_ADJACENCY_MAP[void_neighbor] = [start, end] # Path from void to end
        MOCK_ADJACENCY_MAP[end] = [void_neighbor]

        # Default find_path_dijkstra should not traverse the void_neighbor if it's marked as void
        # and if it's not explicitly handled by get_edge_cost or neighbor filtering.
        # The current find_path_dijkstra has `if neighbor_coord.is_void_path(): continue`
        path = find_path_dijkstra(start, end)
        self.assertIsNone(path, "Path should not be found if it must go through a void and voids are filtered.")

    def test_find_path_dijkstra_target_is_void(self):
        start = AddressedFractalCoordinate(1, (0,))
        void_target = AddressedFractalCoordinate(1, (3,)) # Target is a void

        MOCK_ADJACENCY_MAP[start] = [void_target] # Direct connection for testing graph logic

        # find_path_dijkstra itself checks if start_coord or end_coord is_void_path()
        path = find_path_dijkstra(start, void_target)
        self.assertIsNone(path)

    def test_find_path_dijkstra_start_is_void(self):
        void_start = AddressedFractalCoordinate(1, (3,)) # Start is a void
        end = AddressedFractalCoordinate(1, (0,))

        MOCK_ADJACENCY_MAP[void_start] = [end]

        path = find_path_dijkstra(void_start, end)
        self.assertIsNone(path)

    def test_find_path_dijkstra_cycle_handling(self):
        # A -> B -> C
        # A -> D -> C
        # B -> D (cycle B-D)
        a = AddressedFractalCoordinate(0, tuple()) # Using depth 0 for simplicity of naming
        b = AddressedFractalCoordinate(1, (0,))
        c = AddressedFractalCoordinate(1, (1,))
        d = AddressedFractalCoordinate(1, (2,))

        MOCK_ADJACENCY_MAP[a] = [b, d]
        MOCK_ADJACENCY_MAP[b] = [a, c, d]
        MOCK_ADJACENCY_MAP[c] = [b, d]
        MOCK_ADJACENCY_MAP[d] = [a, b, c]

        # Path A to C. Expected A -> B -> C (cost 2) or A -> D -> C (cost 2)
        # Dijkstra should find one of these.
        path = find_path_dijkstra(a,c)
        self.assertIsNotNone(path)
        self.assertTrue(path == [a,b,c] or path == [a,d,c])
        self.assertEqual(len(path), 3) # Cost is 2 (2 edges)

    def test_find_path_dijkstra_max_depth_constraint(self):
        # Path: d0p -> d1p0 -> d2p00 -> d3p000
        d0 = AddressedFractalCoordinate(0, tuple())
        d1 = AddressedFractalCoordinate(1, (0,))
        d2 = AddressedFractalCoordinate(2, (0,0))
        d3 = AddressedFractalCoordinate(3, (0,0,0))

        MOCK_ADJACENCY_MAP[d0] = [d1]
        MOCK_ADJACENCY_MAP[d1] = [d0, d2]
        MOCK_ADJACENCY_MAP[d2] = [d1, d3]
        MOCK_ADJACENCY_MAP[d3] = [d2]

        # Full path without depth constraint
        path_full = find_path_dijkstra(d0, d3)
        self.assertEqual(path_full, [d0, d1, d2, d3])

        # Constrain pathfinding to max_depth 1
        # Path should not reach d2 or d3
        path_depth1 = find_path_dijkstra(d0, d3, max_depth_for_pathfinding=1)
        self.assertIsNone(path_depth1, "Path should not be found if it exceeds max_depth")

        path_to_d1_depth1 = find_path_dijkstra(d0, d1, max_depth_for_pathfinding=1)
        self.assertEqual(path_to_d1_depth1, [d0,d1])

        path_to_d2_depth1 = find_path_dijkstra(d0, d2, max_depth_for_pathfinding=1)
        self.assertIsNone(path_to_d2_depth1) # d2 is at depth 2, neighbor of d1

        path_to_d2_depth2 = find_path_dijkstra(d0, d2, max_depth_for_pathfinding=2)
        self.assertEqual(path_to_d2_depth2, [d0, d1, d2])


if __name__ == '__main__':
    unittest.main()
