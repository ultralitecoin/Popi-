from collections import defaultdict
from typing import Dict, Tuple, List, Optional
import time

from fractal_blockchain.core.addressing import AddressedFractalCoordinate, coord_to_string

# Data structure to store hashrate-indicative metrics per coordinate string
# For simplicity, we'll track "events" which could be shares, blocks, etc.
# Using coordinate string as key: coord_to_string(fractal_coord)
CoordinateActivity = Dict[str, int] # coord_string -> count of events

# We might also want to aggregate by depth or other fractal properties
DepthActivity = Dict[int, int] # depth -> count of events

class HashrateMonitor:
    def __init__(self, time_window_seconds: int = 3600, aggregation_level: int = 2):
        """
        Monitors activity across fractal coordinates as a proxy for hashrate.

        Args:
            time_window_seconds: The time window for which to keep detailed event logs (not fully implemented here, using cumulative for now).
            aggregation_level: The depth to which full coordinate paths are tracked before aggregating.
                               E.g., level 2 means "d2p01" is tracked, but deeper paths might be grouped under "d2p01*".
        """
        self.activity_by_coordinate: CoordinateActivity = defaultdict(int)
        self.activity_by_depth: DepthActivity = defaultdict(int)

        # For more advanced monitoring, store timestamps of events to enable time-window analysis
        self.event_log: List[Tuple[float, AddressedFractalCoordinate]] = []
        self.time_window_seconds = time_window_seconds # For future use
        self.aggregation_level = aggregation_level


    def _get_aggregated_coord_string(self, coord: AddressedFractalCoordinate) -> str:
        """Returns a coordinate string, possibly truncated/aggregated based on self.aggregation_level."""
        if coord.depth <= self.aggregation_level:
            return coord_to_string(coord)
        else:
            # Aggregate: use path up to aggregation_level, then add a wildcard or summary
            aggregated_path = coord.path[:self.aggregation_level]
            # Create a temporary coordinate for string conversion if needed, or manually construct string
            # This string indicates it's an aggregation of deeper coordinates.
            return f"d{self.aggregation_level}p{''.join(map(str, aggregated_path))}*"


    def record_activity(self, fractal_coord: AddressedFractalCoordinate, count: int = 1, timestamp: Optional[float] = None):
        """
        Records an activity/event (e.g., share submitted, block found) for a given fractal coordinate.
        """
        if not timestamp:
            timestamp = time.time()

        # Store detailed event for potential time-window analysis (simplified for now)
        self.event_log.append((timestamp, fractal_coord))

        # Aggregate activity by full coordinate string (or aggregated string)
        # For this example, let's use the exact coordinate string for activity_by_coordinate
        # and a separate logic for aggregation if needed for reporting.
        exact_coord_str = coord_to_string(fractal_coord)
        self.activity_by_coordinate[exact_coord_str] += count

        # Aggregate activity by depth
        self.activity_by_depth[fractal_coord.depth] += count

        # Prune old event_log entries if implementing time window strictly (not done in this pass)

    def get_activity_report(self) -> Tuple[CoordinateActivity, DepthActivity]:
        """Returns the current aggregated activity."""
        # In a real system, this might filter self.event_log by time_window_seconds
        # before re-calculating activity_by_coordinate and activity_by_depth.
        # For this simulation, we are using cumulative counts.
        return self.activity_by_coordinate, self.activity_by_depth

    def find_hotspots(self, threshold_factor: float = 2.0) -> Tuple[List[str], List[int]]:
        """
        Identifies coordinates or depths with activity significantly above average.
        This is a simplified hotspot detection.

        Args:
            threshold_factor: How many times above average activity must be to be a hotspot.

        Returns:
            A tuple of (hotspot_coordinate_strings, hotspot_depths).
        """
        hotspot_coords: List[str] = []
        hotspot_depths: List[int] = []

        if not self.activity_by_coordinate and not self.activity_by_depth:
            return hotspot_coords, hotspot_depths

        # Coordinate hotspots
        if self.activity_by_coordinate:
            total_coord_activity = sum(self.activity_by_coordinate.values())
            average_coord_activity = total_coord_activity / len(self.activity_by_coordinate) if self.activity_by_coordinate else 0
            coord_threshold = average_coord_activity * threshold_factor
            if coord_threshold > 0 : # Only find hotspots if there's meaningful activity
                for coord_str, activity in self.activity_by_coordinate.items():
                    if activity > coord_threshold:
                        hotspot_coords.append(coord_str)

        # Depth hotspots
        if self.activity_by_depth:
            total_depth_activity = sum(self.activity_by_depth.values())
            average_depth_activity = total_depth_activity / len(self.activity_by_depth) if self.activity_by_depth else 0
            depth_threshold = average_depth_activity * threshold_factor
            if depth_threshold > 0:
                for depth, activity in self.activity_by_depth.items():
                    if activity > depth_threshold:
                        hotspot_depths.append(depth)

        return hotspot_coords, hotspot_depths

    def clear_activity(self):
        """Clears all recorded activity."""
        self.activity_by_coordinate.clear()
        self.activity_by_depth.clear()
        self.event_log = []


if __name__ == '__main__':
    monitor = HashrateMonitor(aggregation_level=1)

    # Simulate some activity
    coord_d0 = AddressedFractalCoordinate(depth=0, path=())
    coord_d1p0 = AddressedFractalCoordinate(depth=1, path=(0,))
    coord_d1p1 = AddressedFractalCoordinate(depth=1, path=(1,))
    coord_d2p00 = AddressedFractalCoordinate(depth=2, path=(0,0))
    coord_d2p01 = AddressedFractalCoordinate(depth=2, path=(0,1)) # Sibling of d2p00

    monitor.record_activity(coord_d0, 10) # Depth 0 is popular
    monitor.record_activity(coord_d1p0, 5)
    monitor.record_activity(coord_d1p1, 25) # d1p1 is very popular
    monitor.record_activity(coord_d2p00, 3)
    monitor.record_activity(coord_d2p01, 2)
    monitor.record_activity(coord_d1p1, 10) # More activity on d1p1

    full_activity, depth_activity = monitor.get_activity_report()
    print("--- Activity Report ---")
    print("By Coordinate:")
    for c, a in sorted(full_activity.items()):
        print(f"  {c}: {a}")
    print("By Depth:")
    for d, a in sorted(depth_activity.items()):
        print(f"  Depth {d}: {a}")

    hot_coords, hot_depths = monitor.find_hotspots(threshold_factor=1.5) # Lower threshold for demo
    print("\n--- Hotspots (Factor > 1.5x Average) ---")
    print(f"Hotspot Coordinates: {hot_coords}")
    print(f"Hotspot Depths: {hot_depths}")

    # Example of aggregated coord string (not directly used in current activity_by_coordinate)
    # print(f"\nAggregated string for {coord_d2p00} (agg_level=1): {monitor._get_aggregated_coord_string(coord_d2p00)}")
    # print(f"Aggregated string for {coord_d1p0} (agg_level=1): {monitor._get_aggregated_coord_string(coord_d1p0)}")


    monitor.clear_activity()
    print("\n--- Activity After Clear ---")
    full_activity_cleared, depth_activity_cleared = monitor.get_activity_report()
    print(f"By Coordinate (cleared): {full_activity_cleared}")
    print(f"By Depth (cleared): {depth_activity_cleared}")

    print("\nHashrateMonitor basic simulation finished.")
