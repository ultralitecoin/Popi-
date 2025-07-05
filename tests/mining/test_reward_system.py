import unittest
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.reward_system import FractalRewardSystem, BASE_REWARD, DEPTH_REWARD_MULTIPLIER, MAX_REWARD_CALCULATION_DEPTH, MINIMUM_REWARD

class TestFractalRewardSystem(unittest.TestCase):

    def test_reward_at_depth_zero(self):
        """Test reward calculation at depth 0."""
        system = FractalRewardSystem(base_reward=50, depth_multiplier=1.1, min_reward=1)
        expected_reward = max(50 * (1.1**0), 1)
        self.assertAlmostEqual(system.calculate_block_reward(0), expected_reward)

    def test_reward_increases_exponentially_with_depth(self):
        """Test that reward increases exponentially as depth increases."""
        system = FractalRewardSystem(base_reward=10, depth_multiplier=1.2, min_reward=0)
        reward_d0 = system.calculate_block_reward(0) # 10 * 1.2^0 = 10
        reward_d1 = system.calculate_block_reward(1) # 10 * 1.2^1 = 12
        reward_d2 = system.calculate_block_reward(2) # 10 * 1.2^2 = 14.4
        reward_d5 = system.calculate_block_reward(5) # 10 * 1.2^5

        self.assertAlmostEqual(reward_d0, 10.0)
        self.assertAlmostEqual(reward_d1, 12.0)
        self.assertAlmostEqual(reward_d2, 14.4)
        self.assertGreater(reward_d5, reward_d2)
        self.assertAlmostEqual(reward_d5, 10 * (1.2**5))

        # Check if r(d+1)/r(d) is approx multiplier for depths < max_calc_depth
        # (accounting for potential minimum reward floor)
        if reward_d0 > system.min_reward and reward_d1 > system.min_reward :
             self.assertAlmostEqual(reward_d1 / reward_d0, system.depth_multiplier)
        if reward_d1 > system.min_reward and reward_d2 > system.min_reward :
             self.assertAlmostEqual(reward_d2 / reward_d1, system.depth_multiplier)


    def test_reward_capping_at_max_calculation_depth(self):
        """Test that reward growth is capped at MAX_REWARD_CALCULATION_DEPTH."""
        base = 10
        mult = 1.1
        max_depth = 20 # Use a custom max_depth for this test
        min_r = 0
        system = FractalRewardSystem(base_reward=base, depth_multiplier=mult, max_calc_depth=max_depth, min_reward=min_r)

        reward_at_max_depth = system.calculate_block_reward(max_depth)
        expected_at_max_depth = base * (mult**max_depth)
        self.assertAlmostEqual(reward_at_max_depth, expected_at_max_depth)

        reward_beyond_max_depth1 = system.calculate_block_reward(max_depth + 1)
        reward_beyond_max_depth10 = system.calculate_block_reward(max_depth + 10)

        # Current implementation caps reward value at the value of max_calc_depth
        self.assertAlmostEqual(reward_beyond_max_depth1, expected_at_max_depth,
                               msg="Reward beyond max_calc_depth should be same as at max_calc_depth")
        self.assertAlmostEqual(reward_beyond_max_depth10, expected_at_max_depth,
                               msg="Reward far beyond max_calc_depth should be same as at max_calc_depth")

    def test_minimum_reward_enforcement(self):
        """Test that reward does not fall below MINIMUM_REWARD."""
        min_r = 5.0
        # Choose base and multiplier such that calculated reward would be less than min_r for depth 0
        system = FractalRewardSystem(base_reward=1.0, depth_multiplier=1.0, min_reward=min_r)

        reward_d0 = system.calculate_block_reward(0) # Calculated: 1.0 * 1.0^0 = 1.0
        self.assertAlmostEqual(reward_d0, min_r)

        reward_d1 = system.calculate_block_reward(1) # Calculated: 1.0 * 1.0^1 = 1.0
        self.assertAlmostEqual(reward_d1, min_r)

        # Test case where calculated reward is initially higher but then might conceptually fall below min_reward
        # (e.g. if multiplier was < 1, which is not the primary design but good to be robust)
        system_decreasing = FractalRewardSystem(base_reward=100.0, depth_multiplier=0.5, min_reward=min_r)
        reward_decreasing_d0 = system_decreasing.calculate_block_reward(0) # 100
        reward_decreasing_d5 = system_decreasing.calculate_block_reward(5) # 100 * 0.5^5 = 3.125
        reward_decreasing_d6 = system_decreasing.calculate_block_reward(6) # 100 * 0.5^6 = 1.5625

        self.assertAlmostEqual(reward_decreasing_d0, 100.0)
        self.assertAlmostEqual(reward_decreasing_d5, min_r) # 3.125 is less than 5.0 min_reward
        self.assertAlmostEqual(reward_decreasing_d6, min_r) # 1.5625 is less than 5.0 min_reward


    def test_negative_depth_handling(self):
        """Test that negative depth is handled gracefully (treated as depth 0)."""
        system = FractalRewardSystem()
        reward_neg_depth = system.calculate_block_reward(-10)
        reward_zero_depth = system.calculate_block_reward(0)
        self.assertAlmostEqual(reward_neg_depth, reward_zero_depth)

    def test_initialization_with_invalid_parameters(self):
        """Test that FractalRewardSystem raises errors for invalid init parameters."""
        with self.assertRaises(ValueError):
            FractalRewardSystem(base_reward=0)
        with self.assertRaises(ValueError):
            FractalRewardSystem(base_reward=-10)
        with self.assertRaises(ValueError):
            FractalRewardSystem(depth_multiplier=0)
        with self.assertRaises(ValueError):
            FractalRewardSystem(depth_multiplier=-1.0)
        with self.assertRaises(ValueError):
            FractalRewardSystem(max_calc_depth=-1)
        with self.assertRaises(ValueError):
            FractalRewardSystem(min_reward=-1)

    def test_rounding(self):
        """Test that the reward is rounded to a reasonable number of decimal places."""
        # base_reward * multiplier^depth might result in many decimal places
        system = FractalRewardSystem(base_reward=10.0/3.0, depth_multiplier=1.0, min_reward=0) # Should be 3.33333333 after rounding
        reward = system.calculate_block_reward(0)

        # Check the value is correctly rounded
        self.assertAlmostEqual(reward, round(10.0/3.0, 8))

        # Check the string representation of the float has at most 8 decimal places
        # Note: str(float) might not always show trailing zeros, e.g. str(1.200) can be "1.2"
        # So we check the number of significant decimal digits after rounding.
        reward_str_parts = str(reward).split('.')
        if len(reward_str_parts) > 1:
            decimal_part_len = len(reward_str_parts[1])
            # Handle cases like "X.0" which might become "X" by str(), so decimal_part_len would be 0 if not split.
            # If it's like 3.0, it might be "3.0", then len is 1. If 3.123, len is 3.
            # The round() function ensures the precision internally.
            # For 10.0/3.0 rounded to 8 places, it's 3.33333333. str() of this is '3.33333333'. len is 8.
            self.assertLessEqual(decimal_part_len, 8, f"Number of decimal places ({decimal_part_len}) in '{str(reward)}' should be at most 8.")
        # else: it's an integer, so 0 decimal places, which is <= 8. This is fine.


if __name__ == '__main__':
    unittest.main()
