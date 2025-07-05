import unittest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.difficulty_adjuster import (
    DifficultyAdjuster,
    TARGET_BLOCK_TIME_SECONDS,
    DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS,
    DEPTH_DIFFICULTY_SCALING_FACTOR,
    MIN_DIFFICULTY,
    MAX_DIFFICULTY_INCREASE_FACTOR,
    MAX_DIFFICULTY_DECREASE_FACTOR
)

class TestDifficultyAdjuster(unittest.TestCase):

    def setUp(self):
        self.adjuster = DifficultyAdjuster()
        # Reset time for consistent tests
        self.current_time = time.time()

    def _simulate_blocks(self, depth, count, time_interval_seconds, coord_path_prefix="DUMMY_PATH"):
        for i in range(count):
            self.current_time += time_interval_seconds
            # Create unique paths to avoid unintended interactions with geometric metrics in basic tests
            coord_path = f"{coord_path_prefix}_{i}"
            self.adjuster.record_block_found(depth, self.current_time, coord_path)

    def test_initial_difficulty_based_on_depth(self):
        """Test that initial difficulty scales with depth."""
        diff_depth0 = self.adjuster.get_current_difficulty(0)
        diff_depth1 = self.adjuster.get_current_difficulty(1)
        diff_depth2 = self.adjuster.get_current_difficulty(2)

        self.assertEqual(diff_depth0, MIN_DIFFICULTY * (DEPTH_DIFFICULTY_SCALING_FACTOR ** 0))
        self.assertAlmostEqual(diff_depth1, MIN_DIFFICULTY * (DEPTH_DIFFICULTY_SCALING_FACTOR ** 1))
        self.assertAlmostEqual(diff_depth2, MIN_DIFFICULTY * (DEPTH_DIFFICULTY_SCALING_FACTOR ** 2))
        self.assertTrue(diff_depth2 > diff_depth1 > diff_depth0)

    def test_difficulty_increases_when_blocks_are_too_fast(self):
        """Test difficulty increases if blocks are found faster than target."""
        depth = 1
        initial_difficulty = self.adjuster.get_current_difficulty(depth)

        # Simulate finding blocks twice as fast as target
        fast_interval = TARGET_BLOCK_TIME_SECONDS / 2
        self._simulate_blocks(depth, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS, fast_interval)

        new_difficulty = self.adjuster.get_current_difficulty(depth)
        self.assertGreater(new_difficulty, initial_difficulty)

        # Check against theoretical max increase (approx, due to averaging over N-1 intervals)
        # Expected ratio is TARGET_BLOCK_TIME_SECONDS / (TARGET_BLOCK_TIME_SECONDS / 2) = 2
        # This should be capped by MAX_DIFFICULTY_INCREASE_FACTOR
        expected_max_increase = initial_difficulty * MAX_DIFFICULTY_INCREASE_FACTOR
        self.assertLessEqual(new_difficulty, expected_max_increase * 1.001) # allow small tolerance

    def test_difficulty_decreases_when_blocks_are_too_slow(self):
        """Test difficulty decreases if blocks are found slower than target."""
        depth = 1
        # Set a higher initial difficulty for this depth to better see a decrease
        self.adjuster.current_difficulty_per_depth[depth] = 100.0
        initial_difficulty_set = self.adjuster.get_current_difficulty(depth)

        # Simulate finding blocks twice as slow as target
        slow_interval = TARGET_BLOCK_TIME_SECONDS * 2
        self._simulate_blocks(depth, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS, slow_interval)

        new_difficulty = self.adjuster.get_current_difficulty(depth)
        self.assertLess(new_difficulty, initial_difficulty_set)

        # Check against theoretical max decrease
        # Expected ratio is TARGET_BLOCK_TIME_SECONDS / (TARGET_BLOCK_TIME_SECONDS * 2) = 0.5
        # This should be capped by MAX_DIFFICULTY_DECREASE_FACTOR
        expected_max_decrease = initial_difficulty_set * MAX_DIFFICULTY_DECREASE_FACTOR
        # Difficulty should not go below base for depth or MIN_DIFFICULTY
        min_possible_diff = max(self.adjuster.get_base_difficulty_for_depth(depth), expected_max_decrease)
        self.assertGreaterEqual(new_difficulty, min_possible_diff * 0.999) # allow small tolerance


    def test_no_adjustment_if_not_enough_blocks(self):
        """Test that difficulty does not adjust if fewer than INTERVAL blocks are found."""
        depth = 0
        initial_difficulty = self.adjuster.get_current_difficulty(depth)

        self._simulate_blocks(depth, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS - 1, TARGET_BLOCK_TIME_SECONDS / 2)

        new_difficulty = self.adjuster.get_current_difficulty(depth)
        self.assertEqual(new_difficulty, initial_difficulty)

    def test_difficulty_adjustment_caps(self):
        """Test that difficulty adjustments are capped by MAX_INCREASE/DECREASE_FACTOR."""
        depth = 2
        initial_difficulty = self.adjuster.get_current_difficulty(depth)
        self.adjuster.current_difficulty_per_depth[depth] = initial_difficulty # Ensure it's set

        # Simulate extremely fast blocks (e.g., 10x faster)
        self._simulate_blocks(depth, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS, TARGET_BLOCK_TIME_SECONDS / 10)
        diff_after_fast = self.adjuster.get_current_difficulty(depth)
        self.assertAlmostEqual(diff_after_fast, initial_difficulty * MAX_DIFFICULTY_INCREASE_FACTOR, delta=initial_difficulty*0.01)

        # Reset for slow simulation, start from a higher difficulty to see decrease clearly
        self.adjuster.current_difficulty_per_depth[depth] = initial_difficulty * MAX_DIFFICULTY_INCREASE_FACTOR * 2 # Start high
        current_high_diff = self.adjuster.get_current_difficulty(depth)

        # Simulate extremely slow blocks (e.g., 10x slower)
        self.current_time = time.time() # Reset time to avoid compounding from previous simulation
        self.adjuster.block_timestamps_per_depth[depth] = [] # Clear previous timestamps for this depth
        self._simulate_blocks(depth, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS, TARGET_BLOCK_TIME_SECONDS * 10)
        diff_after_slow = self.adjuster.get_current_difficulty(depth)

        expected_diff_after_slow = current_high_diff * MAX_DIFFICULTY_DECREASE_FACTOR
        min_depth_diff = self.adjuster.get_base_difficulty_for_depth(depth)
        expected_diff_clamped = max(expected_diff_after_slow, min_depth_diff)

        self.assertAlmostEqual(diff_after_slow, expected_diff_clamped, delta=expected_diff_clamped*0.01)


    def test_difficulty_does_not_fall_below_base_for_depth(self):
        """Test that difficulty does not fall below the base difficulty for its depth."""
        depth = 3
        base_diff_depth3 = self.adjuster.get_base_difficulty_for_depth(depth)
        # Set current difficulty just slightly above base to ensure decrease would try to go below
        self.adjuster.current_difficulty_per_depth[depth] = base_diff_depth3 * 1.01

        # Simulate very slow blocks to trigger max decrease
        self._simulate_blocks(depth, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS, TARGET_BLOCK_TIME_SECONDS * 10)

        new_difficulty = self.adjuster.get_current_difficulty(depth)
        self.assertGreaterEqual(new_difficulty, base_diff_depth3)
        # It should be very close to base_diff_depth3 if the decrease factor was large enough
        self.assertAlmostEqual(new_difficulty, base_diff_depth3, delta=base_diff_depth3*0.01)

    def test_geometric_hash_metrics_influence(self):
        """
        Test the (simplified) influence of geometric hash metrics.
        This test is very basic due to the simplified nature of geometric influence in the code.
        """
        depth = 1
        coord_path_active = "D:1-P:0.0_active"
        coord_path_inactive = "D:1-P:0.1_inactive"

        # Simulate high activity on one path
        # Fill up geometric_hash_metrics for coord_path_active to trigger the multiplier
        # The threshold is DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS / 2
        # We need to call record_block_found enough times for this specific path
        # For this test, let's manually set it to simulate prior activity
        self.adjuster.geometric_hash_metrics[coord_path_active] = DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS

        # No adjustment cycle has run yet, so difficulties should be based on depth + geometric hint
        diff_active_no_adjust = self.adjuster.get_current_difficulty(depth, coord_path_active)
        diff_inactive_no_adjust = self.adjuster.get_current_difficulty(depth, coord_path_inactive)

        base_depth_diff = self.adjuster.get_base_difficulty_for_depth(depth)
        self.assertAlmostEqual(diff_active_no_adjust, base_depth_diff * 1.05) # 5% penalty
        self.assertAlmostEqual(diff_inactive_no_adjust, base_depth_diff)
        self.assertGreater(diff_active_no_adjust, diff_inactive_no_adjust)

        # Now, simulate an adjustment cycle for this depth.
        # The geometric influence in the current get_current_difficulty is applied on top of
        # the depth's overall adjusted difficulty.
        # Let's make blocks fast to increase the base difficulty for the depth.
        self.adjuster.current_difficulty_per_depth[depth] = base_depth_diff # Start from base
        self._simulate_blocks(depth, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS, TARGET_BLOCK_TIME_SECONDS / 2, coord_path_prefix=f"D:{depth}-P:X")

        adjusted_depth_difficulty = self.adjuster.current_difficulty_per_depth[depth] # This is now higher

        diff_active_post_adjust = self.adjuster.get_current_difficulty(depth, coord_path_active)
        diff_inactive_post_adjust = self.adjuster.get_current_difficulty(depth, coord_path_inactive)

        # The active path should still have the 5% geometric penalty on top of the new adjusted_depth_difficulty
        self.assertAlmostEqual(diff_active_post_adjust, adjusted_depth_difficulty * 1.05, delta=adjusted_depth_difficulty*0.01)
        self.assertAlmostEqual(diff_inactive_post_adjust, adjusted_depth_difficulty, delta=adjusted_depth_difficulty*0.01)
        self.assertTrue(diff_active_post_adjust > diff_inactive_post_adjust)


    def test_multiple_depths_independent_adjustment(self):
        """Test that difficulty adjustments for different depths are independent."""
        depth0 = 0
        depth1 = 1

        initial_diff0 = self.adjuster.get_current_difficulty(depth0)
        initial_diff1 = self.adjuster.get_current_difficulty(depth1)

        # Make depth0 blocks fast
        self._simulate_blocks(depth0, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS, TARGET_BLOCK_TIME_SECONDS / 2, coord_path_prefix="D0PATH")

        # Make depth1 blocks slow
        # Need to ensure its initial difficulty is high enough to decrease meaningfully
        self.adjuster.current_difficulty_per_depth[depth1] = initial_diff1 * 3
        initial_diff1_high = self.adjuster.get_current_difficulty(depth1)
        self._simulate_blocks(depth1, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS, TARGET_BLOCK_TIME_SECONDS * 2, coord_path_prefix="D1PATH")

        final_diff0 = self.adjuster.get_current_difficulty(depth0)
        final_diff1 = self.adjuster.get_current_difficulty(depth1)

        self.assertGreater(final_diff0, initial_diff0) # Depth 0 difficulty increased
        self.assertLess(final_diff1, initial_diff1_high)   # Depth 1 difficulty decreased


if __name__ == '__main__':
    unittest.main()
