import unittest
import time
from fractal_blockchain.core.synchronization import FractalTimestampManager, simulate_timestamp_cascade
from fractal_blockchain.core.addressing import AddressedFractalCoordinate

class TestFractalTimestampManager(unittest.TestCase):

    def test_record_and_get_heartbeat(self):
        manager = FractalTimestampManager()
        coord1 = AddressedFractalCoordinate(1, (0,))
        level_key = "Depth1_Overall"

        # Test with default timestamp (current time)
        t_before = time.time()
        manager.record_heartbeat(coord1)
        t_after = time.time()
        hb_coord1 = manager.get_last_heartbeat(coord1)
        self.assertIsNotNone(hb_coord1)
        self.assertTrue(t_before <= hb_coord1 <= t_after)

        # Test with specified timestamp
        fixed_ts = time.time() - 1000
        manager.record_heartbeat(level_key, timestamp=fixed_ts)
        self.assertEqual(manager.get_last_heartbeat(level_key), fixed_ts)

        # Get heartbeat for non-existent key
        self.assertIsNone(manager.get_last_heartbeat("NonExistentKey"))

    def test_cascade_and_get_timestamp(self):
        manager = FractalTimestampManager()
        coord1 = AddressedFractalCoordinate(1, (0,))
        coord2 = AddressedFractalCoordinate(2, (0,1))
        source = AddressedFractalCoordinate(0, tuple())

        ts1 = time.time()
        manager.cascade_timestamp(coord1, ts1, source_coord=source)
        self.assertEqual(manager.get_cascaded_timestamp(coord1), ts1)

        # No timestamp for another coordinate yet
        self.assertIsNone(manager.get_cascaded_timestamp(coord2))

        # Overwrite timestamp
        ts2 = time.time() + 10
        manager.cascade_timestamp(coord1, ts2, source_coord=source)
        self.assertEqual(manager.get_cascaded_timestamp(coord1), ts2)

    def test_get_effective_time(self):
        manager = FractalTimestampManager()
        coord = AddressedFractalCoordinate(1, (0,))

        # No timestamp initially
        self.assertIsNone(manager.get_effective_time(coord))

        # After cascading a timestamp
        ts = time.time()
        manager.cascade_timestamp(coord, ts)
        self.assertEqual(manager.get_effective_time(coord), ts)

        # (Further tests would involve more complex logic if get_effective_time
        #  had fallbacks, e.g., to parent's time, which is not implemented yet)

    def test_simulate_timestamp_cascade(self):
        manager = FractalTimestampManager()
        genesis_coord = AddressedFractalCoordinate(0, tuple())
        start_time = time.time()
        max_depth_sim = 2

        simulate_timestamp_cascade(manager, genesis_coord, start_time, max_depth=max_depth_sim)

        # Check Genesis
        self.assertEqual(manager.get_cascaded_timestamp(genesis_coord), start_time)

        # Check some children at depth 1
        c_d1p0 = AddressedFractalCoordinate(1, (0,))
        c_d1p1 = AddressedFractalCoordinate(1, (1,))
        ts_d1p0 = manager.get_cascaded_timestamp(c_d1p0)
        ts_d1p1 = manager.get_cascaded_timestamp(c_d1p1)
        self.assertIsNotNone(ts_d1p0)
        self.assertIsNotNone(ts_d1p1)
        self.assertTrue(ts_d1p0 > start_time) # Simulated delay increases timestamp
        self.assertTrue(ts_d1p1 > start_time)
        # Timestamps for siblings at same depth should be very close (based on simple +0.001*depth logic)
        self.assertAlmostEqual(ts_d1p0, start_time + 0.001 * 1, delta=0.0001)


        # Check some grandchildren at depth 2
        c_d2p00 = AddressedFractalCoordinate(2, (0,0))
        c_d2p12 = AddressedFractalCoordinate(2, (1,2)) # child 2 of parent (1,)
        ts_d2p00 = manager.get_cascaded_timestamp(c_d2p00)
        ts_d2p12 = manager.get_cascaded_timestamp(c_d2p12)
        self.assertIsNotNone(ts_d2p00)
        self.assertIsNotNone(ts_d2p12)
        self.assertTrue(ts_d2p00 > ts_d1p0) # Child timestamp should be greater than parent's

        # Expected timestamp for c_d2p00 (child of c_d1p0)
        # ts_c_d1p0 = start_time + 0.001 * 1
        # ts_c_d2p00 = ts_c_d1p0 + 0.001 * 2 = start_time + 0.001 + 0.002 = start_time + 0.003
        # This interpretation of the simple delay logic in simulate_timestamp_cascade
        # current_coord_ts + 0.001 * (current_coord.depth + 1)
        # For c_d1p0 (depth 0 parent): initial_timestamp = start_time. child_timestamp (for d1) = start_time + 0.001 * (0+1)
        # For c_d2p00 (depth 1 parent c_d1p0): initial_timestamp = ts_d1p0. child_timestamp (for d2) = ts_d1p0 + 0.001 * (1+1)
        expected_ts_d1p0 = start_time + 0.001 * 1
        expected_ts_d2p00 = expected_ts_d1p0 + 0.001 * 2
        self.assertAlmostEqual(ts_d2p00, expected_ts_d2p00, delta=0.0001)


        # Check coordinate beyond max_depth
        c_d3p000 = AddressedFractalCoordinate(3, (0,0,0)) # Depth 3
        self.assertIsNone(manager.get_cascaded_timestamp(c_d3p000),
                          "Timestamp should not be set for coords beyond max_depth in simulation.")


if __name__ == '__main__':
    unittest.main()
