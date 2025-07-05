import time
import math

# Placeholder for FractalCoordinate, assuming it has 'depth'
# from fractal_blockchain.mining.randomx_adapter import FractalCoordinate

TARGET_BLOCK_TIME_SECONDS = 60  # Target time to find a block at a given fractal level (e.g., 1 minute)
DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS = 10  # How often to adjust difficulty (e.g., every 10 blocks at a level)
MIN_DIFFICULTY = 1
MAX_DIFFICULTY_INCREASE_FACTOR = 2.0  # Max increase in one adjustment (e.g., 2x)
MAX_DIFFICULTY_DECREASE_FACTOR = 0.5  # Max decrease in one adjustment (e.g., 0.5x)

# Base difficulty scaling factor per depth level.
# e.g. depth 0 = base, depth 1 = base * DEPTH_DIFFICULTY_SCALING, depth 2 = base * DEPTH_DIFFICULTY_SCALING^2
DEPTH_DIFFICULTY_SCALING_FACTOR = 1.2

class DifficultyAdjuster:
    def __init__(self):
        # In a real system, these would be persisted or loaded from blockchain state
        # For simulation, we'll keep them in memory.
        # Key: fractal_depth (int), Value: list of block timestamps for that depth
        self.block_timestamps_per_depth: dict[int, list[float]] = {}
        # Key: fractal_depth (int), Value: current_difficulty_for_that_depth
        self.current_difficulty_per_depth: dict[int, float] = {}
        # Key: fractal_coord_path_str, Value: recent_hash_rate_metric (e.g. blocks found)
        # This is for the "geometric hash distribution" part, highly simplified here
        self.geometric_hash_metrics: dict[str, int] = {}


    def get_base_difficulty_for_depth(self, depth: int) -> float:
        """
        Calculates a base difficulty component based on fractal depth.
        Deeper levels are inherently more difficult.
        """
        if depth < 0:
            depth = 0 # Or raise error
        return MIN_DIFFICULTY * (DEPTH_DIFFICULTY_SCALING_FACTOR ** depth)

    def get_current_difficulty(self, fractal_depth: int, fractal_coord_path_str: str = None) -> float:
        """
        Gets the current difficulty for a given fractal depth, potentially adjusted by geometric factors.
        """
        base_difficulty_for_depth = self.get_base_difficulty_for_depth(fractal_depth)

        difficulty = self.current_difficulty_per_depth.get(fractal_depth, base_difficulty_for_depth)

        # Simplified geometric adjustment: if a specific coordinate path shows unusually high activity,
        # slightly increase its difficulty relative to others at the same depth.
        # This is a placeholder for a more sophisticated geometric distribution analysis.
        if fractal_coord_path_str:
            activity_metric = self.geometric_hash_metrics.get(fractal_coord_path_str, 0)
            # Example: if a coordinate has > X recent blocks compared to an average (not implemented here)
            # For now, just a small fixed penalty if it's active at all.
            if activity_metric > (DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS / 2): # Arbitrary threshold
                 difficulty *= 1.05 # Small penalty for very active specific coordinates

        return max(MIN_DIFFICULTY, difficulty)


    def record_block_found(self, fractal_depth: int, timestamp: float, fractal_coord_path_str: str):
        """
        Records that a block was found at a given fractal depth and timestamp.
        This data is used for difficulty adjustment.
        """
        if fractal_depth not in self.block_timestamps_per_depth:
            self.block_timestamps_per_depth[fractal_depth] = []
        self.block_timestamps_per_depth[fractal_depth].append(timestamp)

        # Update geometric metrics (simplified)
        self.geometric_hash_metrics[fractal_coord_path_str] = self.geometric_hash_metrics.get(fractal_coord_path_str, 0) + 1


        # Perform adjustment if enough blocks have been recorded for this depth
        if len(self.block_timestamps_per_depth[fractal_depth]) % DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS == 0:
            self.adjust_difficulty(fractal_depth)
            # Reset geometric metrics for this path after adjustment cycle for it, or use a sliding window
            # For simplicity, we can just reduce it or clear it if it was part of this depth's adjustment
            # This part needs more thought for a robust geometric balancing.
            # For now, let's just reset metrics for paths within this depth that were involved.
            # This is overly simplistic. A better approach would be a sliding window or averaging.
            related_paths_to_reset = [path for path in self.geometric_hash_metrics.keys() if path.startswith(f"D:{fractal_depth}")] # Assuming path includes depth info
            for path in related_paths_to_reset: # This is not quite right, needs better linking
                 # A more robust solution would associate metrics with adjustment windows
                 # For now, just dampening the effect after adjustment
                 # self.geometric_hash_metrics[path] = max(0, self.geometric_hash_metrics[path] - DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS // 2)
                 pass # This part is tricky without more context on fractal_coord_path_str structure and overall strategy


    def adjust_difficulty(self, fractal_depth: int):
        """
        Adjusts the mining difficulty for a given fractal depth based on actual block times.
        """
        timestamps = self.block_timestamps_per_depth.get(fractal_depth, [])
        if len(timestamps) < DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS:
            # Not enough data to adjust yet for this depth
            return

        # Consider the last N blocks for adjustment
        # For simplicity, let's use the last DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS blocks
        # In a real system, you might use a more sophisticated window or average.
        last_n_timestamps = timestamps[-DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS:]

        if len(last_n_timestamps) < 2: # Need at least two timestamps to calculate a duration
            return

        actual_time_taken_for_n_blocks = last_n_timestamps[-1] - last_n_timestamps[0]
        average_block_time = actual_time_taken_for_n_blocks / (DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS -1) # -1 because N timestamps give N-1 intervals

        # Target time for N-1 blocks
        target_time_for_n_blocks = TARGET_BLOCK_TIME_SECONDS * (DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS -1)

        current_difficulty_for_depth = self.current_difficulty_per_depth.get(
            fractal_depth,
            self.get_base_difficulty_for_depth(fractal_depth)
        )

        new_difficulty = current_difficulty_for_depth

        if average_block_time < 1: average_block_time = 1 # Avoid division by zero or extreme values

        # Ratio of target time to actual time.
        # If actual time is less than target (blocks too fast), ratio > 1, difficulty should increase.
        # If actual time is greater than target (blocks too slow), ratio < 1, difficulty should decrease.
        adjustment_ratio = TARGET_BLOCK_TIME_SECONDS / average_block_time

        # Apply caps to prevent extreme swings
        adjustment_ratio = min(adjustment_ratio, MAX_DIFFICULTY_INCREASE_FACTOR)
        adjustment_ratio = max(adjustment_ratio, MAX_DIFFICULTY_DECREASE_FACTOR)

        new_difficulty *= adjustment_ratio

        # Ensure difficulty does not go below a minimum (e.g., derived from base depth difficulty or global min)
        min_difficulty_for_depth = self.get_base_difficulty_for_depth(fractal_depth) # Or just MIN_DIFFICULTY
        new_difficulty = max(min_difficulty_for_depth, new_difficulty)
        # Could also add an absolute max difficulty if needed

        print(f"[Depth {fractal_depth}] Avg Block Time: {average_block_time:.2f}s. Target: {TARGET_BLOCK_TIME_SECONDS}s. "
              f"Old Diff: {current_difficulty_for_depth:.4f}. Adjustment Ratio: {adjustment_ratio:.4f}. New Diff: {new_difficulty:.4f}")

        self.current_difficulty_per_depth[fractal_depth] = new_difficulty

        # Optional: Prune older timestamps to save memory if list grows too large
        # self.block_timestamps_per_depth[fractal_depth] = self.block_timestamps_per_depth[fractal_depth][-SOME_MAX_HISTORY:]


if __name__ == '__main__':
    adjuster = DifficultyAdjuster()

    # Simulate block finding at depth 2
    depth_2 = 2
    coord_path_d2_a = "D:2-P:0.0" # Example path strings
    coord_path_d2_b = "D:2-P:0.1"

    print(f"Initial difficulty for depth {depth_2}: {adjuster.get_current_difficulty(depth_2, coord_path_d2_a):.4f}")

    # Simulate finding blocks faster than target
    current_time = time.time()
    for i in range(DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS):
        # Assume blocks are found every 30 seconds (faster than 60s target)
        current_time += (TARGET_BLOCK_TIME_SECONDS / 2)
        # Alternate between two paths for geometric metrics (very simplified)
        path_to_record = coord_path_d2_a if i % 2 == 0 else coord_path_d2_b
        adjuster.record_block_found(depth_2, current_time, path_to_record)
        if (i + 1) % DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS == 0:
            print(f"--> Difficulty after {i+1} blocks at depth {depth_2}: {adjuster.get_current_difficulty(depth_2, path_to_record):.4f}")

    print(f"\nGeometric metrics (simplified): {adjuster.geometric_hash_metrics}")
    print(f"Difficulty for {coord_path_d2_a}: {adjuster.get_current_difficulty(depth_2, coord_path_d2_a):.4f}")
    print(f"Difficulty for {coord_path_d2_b}: {adjuster.get_current_difficulty(depth_2, coord_path_d2_b):.4f}")


    # Simulate finding blocks slower than target at depth 2
    print("\nSimulating slower block times for depth 2...")
    # First, let current difficulty be the one from previous adjustment
    # To trigger another adjustment, we need to log DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS more blocks
    for i in range(DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS):
        current_time += (TARGET_BLOCK_TIME_SECONDS * 1.5) # Slower
        path_to_record = coord_path_d2_a if i % 2 == 0 else coord_path_d2_b
        adjuster.record_block_found(depth_2, current_time, path_to_record)
        if (i + 1) % DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS == 0:
             print(f"--> Difficulty after {i+1} (total { (i+1) + DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS}) blocks at depth {depth_2}: {adjuster.get_current_difficulty(depth_2, path_to_record):.4f}")


    # Simulate for a different depth (e.g., depth 5)
    depth_5 = 5
    coord_path_d5 = "D:5-P:1.0.1.0.1"
    print(f"\nInitial difficulty for depth {depth_5}: {adjuster.get_current_difficulty(depth_5, coord_path_d5):.4f}")
    current_time = time.time() # Reset time base for this depth
    for i in range(DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS):
        current_time += (TARGET_BLOCK_TIME_SECONDS / 1.5) # Slightly faster
        adjuster.record_block_found(depth_5, current_time, coord_path_d5)
        if (i + 1) % DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS == 0:
            print(f"--> Difficulty after {i+1} blocks at depth {depth_5}: {adjuster.get_current_difficulty(depth_5, coord_path_d5):.4f}")

    print(f"\nFinal difficulties:")
    print(f"  Depth {depth_2} ({coord_path_d2_a}): {adjuster.get_current_difficulty(depth_2, coord_path_d2_a):.4f}")
    print(f"  Depth {depth_5} ({coord_path_d5}): {adjuster.get_current_difficulty(depth_5, coord_path_d5):.4f}")

    # Test get_base_difficulty_for_depth
    print("\nBase difficulties:")
    for d in range(4):
        print(f"  Base difficulty for depth {d}: {adjuster.get_base_difficulty_for_depth(d):.4f}")
