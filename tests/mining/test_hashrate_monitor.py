import unittest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.hashrate_monitor import HashrateMonitor
from fractal_blockchain.core.addressing import AddressedFractalCoordinate, coord_to_string

class TestHashrateMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = HashrateMonitor(time_window_seconds=3600, aggregation_level=1)
        self.coord_d0 = AddressedFractalCoordinate(depth=0, path=())
        self.coord_d1p0 = AddressedFractalCoordinate(depth=1, path=(0,))
        self.coord_d1p1 = AddressedFractalCoordinate(depth=1, path=(1,))
        self.coord_d2p00 = AddressedFractalCoordinate(depth=2, path=(0,0)) # Will be aggregated to d1p0* by _get_aggregated_coord_string
        self.coord_d2p10 = AddressedFractalCoordinate(depth=2, path=(1,0)) # Will be aggregated to d1p1*

    def test_record_activity_and_get_report(self):
        self.monitor.record_activity(self.coord_d0, 5)
        self.monitor.record_activity(self.coord_d1p0, 10)
        self.monitor.record_activity(self.coord_d0, 3) # More activity on d0

        coord_activity, depth_activity = self.monitor.get_activity_report()

        self.assertEqual(coord_activity.get(coord_to_string(self.coord_d0)), 8)
        self.assertEqual(coord_activity.get(coord_to_string(self.coord_d1p0)), 10)
        self.assertEqual(depth_activity.get(0), 8)
        self.assertEqual(depth_activity.get(1), 10)
        self.assertEqual(len(self.monitor.event_log), 3)

    def test_clear_activity(self):
        self.monitor.record_activity(self.coord_d0, 5)
        self.monitor.clear_activity()
        coord_activity, depth_activity = self.monitor.get_activity_report()
        self.assertEqual(len(coord_activity), 0)
        self.assertEqual(len(depth_activity), 0)
        self.assertEqual(len(self.monitor.event_log), 0)

    def test_get_aggregated_coord_string(self):
        monitor_agg0 = HashrateMonitor(aggregation_level=0)
        monitor_agg1 = HashrateMonitor(aggregation_level=1)
        monitor_agg2 = HashrateMonitor(aggregation_level=2)

        # Depth 0 coord
        self.assertEqual(monitor_agg0._get_aggregated_coord_string(self.coord_d0), "d0p")
        self.assertEqual(monitor_agg1._get_aggregated_coord_string(self.coord_d0), "d0p")

        # Depth 1 coord
        self.assertEqual(monitor_agg0._get_aggregated_coord_string(self.coord_d1p0), "d0p*")
        self.assertEqual(monitor_agg1._get_aggregated_coord_string(self.coord_d1p0), "d1p0")
        self.assertEqual(monitor_agg2._get_aggregated_coord_string(self.coord_d1p0), "d1p0")

        # Depth 2 coord
        self.assertEqual(monitor_agg0._get_aggregated_coord_string(self.coord_d2p00), "d0p*")
        self.assertEqual(monitor_agg1._get_aggregated_coord_string(self.coord_d2p00), "d1p0*")
        self.assertEqual(monitor_agg2._get_aggregated_coord_string(self.coord_d2p00), "d2p00")


    def test_find_hotspots_no_activity(self):
        hot_coords, hot_depths = self.monitor.find_hotspots()
        self.assertEqual(len(hot_coords), 0)
        self.assertEqual(len(hot_depths), 0)

    def test_find_hotspots_with_activity(self):
        self.monitor.record_activity(self.coord_d0, 100) # Hot
        self.monitor.record_activity(self.coord_d1p0, 10) # Avg
        self.monitor.record_activity(self.coord_d1p1, 5)  # Low
        self.monitor.record_activity(self.coord_d2p00, 12) # Avg-ish for its depth if d2 is only this

        # Total coord activity = 100+10+5+12 = 127. Num coords = 4. Avg = 127/4 = 31.75
        # Threshold (factor 2.0) = 31.75 * 2 = 63.5. So, d0p (100) is a hotspot.

        # Total depth activity: D0:100, D1:15 (10+5), D2:12. Sum = 127. Num depths = 3. Avg = 127/3 = 42.33
        # Threshold (factor 2.0) = 42.33 * 2 = 84.66. So, D0 (100) is a hotspot.

        hot_coords, hot_depths = self.monitor.find_hotspots(threshold_factor=2.0)

        self.assertIn(coord_to_string(self.coord_d0), hot_coords)
        self.assertEqual(len(hot_coords), 1)
        self.assertIn(0, hot_depths) # Depth 0
        self.assertEqual(len(hot_depths), 1)

    def test_find_hotspots_balanced_activity(self):
        self.monitor.record_activity(self.coord_d0, 20)
        self.monitor.record_activity(self.coord_d1p0, 22)
        self.monitor.record_activity(self.coord_d1p1, 18)

        # Total coord activity = 60. Num coords = 3. Avg = 20.
        # Threshold (factor 2.0) = 40. No coord hotspot.
        # Total depth activity: D0:20, D1:40. Sum = 60. Num depths = 2. Avg = 30.
        # Threshold (factor 2.0) = 60. No depth hotspot.

        hot_coords, hot_depths = self.monitor.find_hotspots(threshold_factor=2.0)
        self.assertEqual(len(hot_coords), 0)
        self.assertEqual(len(hot_depths), 0)

    def test_event_log_timestamping(self):
        # Test that event log captures timestamps, even if not fully used by current reports
        ts_before = time.time()
        self.monitor.record_activity(self.coord_d0, 1)
        ts_after = time.time()

        self.assertEqual(len(self.monitor.event_log), 1)
        event_ts, event_coord = self.monitor.event_log[0]
        self.assertGreaterEqual(event_ts, ts_before)
        self.assertLessEqual(event_ts, ts_after)
        self.assertEqual(event_coord, self.coord_d0)


if __name__ == '__main__':
    unittest.main()
