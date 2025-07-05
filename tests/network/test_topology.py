import unittest
from fractal_blockchain.network.topology import FractalTopologyMapper
from fractal_blockchain.core.addressing import AddressedFractalCoordinate

# As get_geometric_adjacencies is a placeholder from an unmocked module,
# its contribution to get_potential_peers will be based on that placeholder's behavior (solid siblings).

class TestFractalTopologyMapper(unittest.TestCase):

    def test_constructor_and_node_management(self):
        mapper_no_limit = FractalTopologyMapper()
        mapper_depth_limit = FractalTopologyMapper(max_network_depth=1)

        c0 = AddressedFractalCoordinate(0, tuple())
        c1 = AddressedFractalCoordinate(1, (0,))
        c2 = AddressedFractalCoordinate(2, (0,0))

        # No depth limit
        mapper_no_limit.add_network_node(c0, "info0")
        mapper_no_limit.add_network_node(c1, "info1")
        mapper_no_limit.add_network_node(c2, "info2")
        self.assertIn(c0, mapper_no_limit._active_nodes)
        self.assertIn(c1, mapper_no_limit._active_nodes)
        self.assertIn(c2, mapper_no_limit._active_nodes)
        self.assertEqual(len(mapper_no_limit.get_active_nodes_at_depth(0)), 1)
        self.assertEqual(len(mapper_no_limit.get_active_nodes_at_depth(1)), 1)
        self.assertEqual(len(mapper_no_limit.get_active_nodes_at_depth(2)), 1)

        mapper_no_limit.remove_network_node(c1)
        self.assertNotIn(c1, mapper_no_limit._active_nodes)
        self.assertEqual(len(mapper_no_limit.get_active_nodes_at_depth(1)), 0)


        # With depth limit
        mapper_depth_limit.add_network_node(c0, "info0_limit") # depth 0, OK
        mapper_depth_limit.add_network_node(c1, "info1_limit") # depth 1, OK
        mapper_depth_limit.add_network_node(c2, "info2_limit") # depth 2, exceeds limit 1

        self.assertIn(c0, mapper_depth_limit._active_nodes)
        self.assertIn(c1, mapper_depth_limit._active_nodes)
        self.assertNotIn(c2, mapper_depth_limit._active_nodes, "Node exceeding max_network_depth should not be added.")
        self.assertEqual(len(mapper_depth_limit.get_active_nodes_at_depth(2)), 0)


    def test_get_potential_peers_for_genesis(self):
        mapper = FractalTopologyMapper()
        genesis = AddressedFractalCoordinate(0, tuple())

        # Expected peers for Genesis:
        # Parent: None
        # Children (solid): d1p0, d1p1, d1p2
        # Child (void): d1p3
        # Siblings: None
        # Geometric Adjacencies (placeholder returns [] for depth 0)
        expected_peers = {
            AddressedFractalCoordinate(1, (0,)),
            AddressedFractalCoordinate(1, (1,)),
            AddressedFractalCoordinate(1, (2,)),
            AddressedFractalCoordinate(1, (3,)), # Void child
        }

        actual_peers = mapper.get_potential_peers(genesis)
        self.assertSetEqual(actual_peers, expected_peers)

    def test_get_potential_peers_for_solid_child(self):
        mapper = FractalTopologyMapper()
        # Solid child d1p0 (path (0,))
        coord_d1p0 = AddressedFractalCoordinate(1, (0,))

        # Expected peers for d1p0:
        # Parent: d0p ()
        # Children (solid): d2p00, d2p01, d2p02
        # Child (void): d2p03
        # Siblings (solid & void): d1p1, d1p2, d1p3
        # Geometric Adjacencies (placeholder for d1p0 returns solid siblings d1p1, d1p2)
        # Set will handle overlaps.
        expected_peers = {
            AddressedFractalCoordinate(0, tuple()),      # Parent
            AddressedFractalCoordinate(2, (0,0)),      # Child 0
            AddressedFractalCoordinate(2, (0,1)),      # Child 1
            AddressedFractalCoordinate(2, (0,2)),      # Child 2
            AddressedFractalCoordinate(2, (0,3)),      # Void Child of d1p0
            AddressedFractalCoordinate(1, (1,)),        # Sibling (solid/geometric)
            AddressedFractalCoordinate(1, (2,)),        # Sibling (solid/geometric)
            AddressedFractalCoordinate(1, (3,)),        # Sibling (void)
        }
        actual_peers = mapper.get_potential_peers(coord_d1p0)
        self.assertSetEqual(actual_peers, expected_peers)

    def test_get_potential_peers_for_void_coord(self):
        mapper = FractalTopologyMapper()
        # Void coordinate d1p3 (path (3,))
        coord_d1p3 = AddressedFractalCoordinate(1, (3,))

        # Expected peers for d1p3:
        # Parent: d0p ()
        # Children (if void can have children in this topology sense):
        #   Solid: d2p30, d2p31, d2p32
        #   Void: d2p33
        # Siblings (solid & void): d1p0, d1p1, d1p2
        # Geometric Adjacencies (placeholder for d1p3 returns [])
        expected_peers = {
            AddressedFractalCoordinate(0, tuple()),      # Parent
            AddressedFractalCoordinate(2, (3,0)),      # Child 0 of void
            AddressedFractalCoordinate(2, (3,1)),      # Child 1 of void
            AddressedFractalCoordinate(2, (3,2)),      # Child 2 of void
            AddressedFractalCoordinate(2, (3,3)),      # Void Child of void
            AddressedFractalCoordinate(1, (0,)),        # Sibling (solid)
            AddressedFractalCoordinate(1, (1,)),        # Sibling (solid)
            AddressedFractalCoordinate(1, (2,)),        # Sibling (solid)
        }
        actual_peers = mapper.get_potential_peers(coord_d1p3)
        self.assertSetEqual(actual_peers, expected_peers)

    def test_get_potential_peers_option_flags(self):
        mapper = FractalTopologyMapper()
        coord = AddressedFractalCoordinate(1, (0,)) # d1p0

        # Only parent
        peers_parent_only = mapper.get_potential_peers(coord,
            include_parent=True, include_children=False, include_siblings=False, include_geometric_adjacencies=False)
        self.assertSetEqual(peers_parent_only, {AddressedFractalCoordinate(0, tuple())})

        # Only children
        peers_children_only = mapper.get_potential_peers(coord,
            include_parent=False, include_children=True, include_siblings=False, include_geometric_adjacencies=False)
        expected_children = {
            AddressedFractalCoordinate(2, (0,0)), AddressedFractalCoordinate(2, (0,1)),
            AddressedFractalCoordinate(2, (0,2)), AddressedFractalCoordinate(2, (0,3)) # void child
        }
        self.assertSetEqual(peers_children_only, expected_children)

        # Only siblings
        peers_siblings_only = mapper.get_potential_peers(coord,
            include_parent=False, include_children=False, include_siblings=True, include_geometric_adjacencies=False)
        expected_siblings = {
            AddressedFractalCoordinate(1, (1,)), AddressedFractalCoordinate(1, (2,)),
            AddressedFractalCoordinate(1, (3,)) # void sibling
        }
        self.assertSetEqual(peers_siblings_only, expected_siblings)

        # Only geometric (placeholder returns solid siblings for d1p0)
        peers_geom_only = mapper.get_potential_peers(coord,
            include_parent=False, include_children=False, include_siblings=False, include_geometric_adjacencies=True)
        expected_geom = { AddressedFractalCoordinate(1, (1,)), AddressedFractalCoordinate(1, (2,)) }
        self.assertSetEqual(peers_geom_only, expected_geom)


    def test_get_potential_peers_with_max_depth_limit(self):
        # Test that children exceeding max_network_depth are not suggested if mapper has limit
        mapper_limit_d1 = FractalTopologyMapper(max_network_depth=1)
        coord_d0 = AddressedFractalCoordinate(0, tuple()) # Genesis

        # Potential peers for Genesis (d0)
        # Children are at depth 1 (d1p0, d1p1, d1p2, d1p3) - these are OK with limit 1
        # Parent: None
        # Siblings: None
        expected_peers_d0_limit_d1 = {
            AddressedFractalCoordinate(1, (0,)), AddressedFractalCoordinate(1, (1,)),
            AddressedFractalCoordinate(1, (2,)), AddressedFractalCoordinate(1, (3,))
        }
        actual_peers_d0_limit_d1 = mapper_limit_d1.get_potential_peers(coord_d0)
        self.assertSetEqual(actual_peers_d0_limit_d1, expected_peers_d0_limit_d1)

        # Now for coord_d1 (e.g. d1p0), its children are at depth 2.
        # If max_network_depth is 1, these children should not be included.
        coord_d1p0 = AddressedFractalCoordinate(1, (0,))
        # Expected peers for d1p0 with max_network_depth = 1:
        # Parent: d0p () (depth 0, OK)
        # Children (solid & void at depth 2): Should be excluded by max_network_depth of mapper for children.
        # Siblings (at depth 1): d1p1, d1p2, d1p3 (OK)
        # Geometric Adjacencies (placeholder for d1p0 returns solid siblings d1p1, d1p2 at depth 1, OK)
        expected_peers_d1p0_limit_d1 = {
            AddressedFractalCoordinate(0, tuple()),      # Parent
            AddressedFractalCoordinate(1, (1,)),        # Sibling (solid/geometric)
            AddressedFractalCoordinate(1, (2,)),        # Sibling (solid/geometric)
            AddressedFractalCoordinate(1, (3,)),        # Sibling (void)
        }
        actual_peers_d1p0_limit_d1 = mapper_limit_d1.get_potential_peers(coord_d1p0)
        self.assertSetEqual(actual_peers_d1p0_limit_d1, expected_peers_d1p0_limit_d1)


    def test_is_void_relay_candidate(self):
        mapper = FractalTopologyMapper()
        solid_coord = AddressedFractalCoordinate(1, (0,))
        void_path_coord1 = AddressedFractalCoordinate(1, (3,)) # Path is just (3,)
        void_path_coord2 = AddressedFractalCoordinate(2, (0,3)) # Path is (0,3) - contains void

        self.assertFalse(mapper.is_void_relay_candidate(solid_coord))
        self.assertTrue(mapper.is_void_relay_candidate(void_path_coord1))
        self.assertTrue(mapper.is_void_relay_candidate(void_path_coord2))


if __name__ == '__main__':
    unittest.main()
