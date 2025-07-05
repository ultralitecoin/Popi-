import unittest
from fractal_blockchain.consensus.difficulty_calculator import DepthCalculator

class TestDepthCalculator(unittest.TestCase):

    def test_constructor_validation(self):
        with self.assertRaises(ValueError):
            DepthCalculator(base_difficulty=0)
        with self.assertRaises(ValueError):
            DepthCalculator(difficulty_exp_factor=0)
        with self.assertRaises(ValueError):
            DepthCalculator(base_reward=-10)
        with self.assertRaises(ValueError):
            DepthCalculator(reward_halving_interval=0)
        with self.assertRaises(ValueError):
            DepthCalculator(reward_min_value=-1)

        # Valid constructor
        try:
            DepthCalculator(base_difficulty=1, difficulty_exp_factor=1.1, base_reward=1, reward_halving_interval=1, reward_min_value=0)
        except ValueError:
            self.fail("Valid DepthCalculator constructor raised ValueError unexpectedly.")

    def test_calculate_difficulty(self):
        calc = DepthCalculator(base_difficulty=10.0, difficulty_exp_factor=2.0)

        self.assertEqual(calc.calculate_difficulty(0), 10.0) # base * (2^0)
        self.assertEqual(calc.calculate_difficulty(1), 20.0) # base * (2^1)
        self.assertEqual(calc.calculate_difficulty(2), 40.0) # base * (2^2)
        self.assertEqual(calc.calculate_difficulty(3), 80.0) # base * (2^3)

        # Test with a different factor
        calc_factor_1_5 = DepthCalculator(base_difficulty=10.0, difficulty_exp_factor=1.5)
        self.assertAlmostEqual(calc_factor_1_5.calculate_difficulty(0), 10.0)
        self.assertAlmostEqual(calc_factor_1_5.calculate_difficulty(1), 15.0) # 10 * 1.5
        self.assertAlmostEqual(calc_factor_1_5.calculate_difficulty(2), 22.5) # 10 * 1.5 * 1.5

        with self.assertRaises(ValueError):
            calc.calculate_difficulty(-1)

        # Test adaptive hashrate parameter (should not change output for now)
        self.assertEqual(calc.calculate_difficulty(2, current_network_hashrate_at_depth=1000), 40.0)


    def test_calculate_reward(self):
        calc = DepthCalculator(base_reward=100.0, reward_halving_interval=2, reward_min_value=0.1)

        # Depths 0, 1: 0 halvings
        self.assertEqual(calc.calculate_reward(0), 100.0) # 100 / (2^0)
        self.assertEqual(calc.calculate_reward(1), 100.0)

        # Depths 2, 3: 1 halving (2//2 = 1, 3//2 = 1)
        self.assertEqual(calc.calculate_reward(2), 50.0)  # 100 / (2^1)
        self.assertEqual(calc.calculate_reward(3), 50.0)

        # Depths 4, 5: 2 halvings (4//2 = 2, 5//2 = 2)
        self.assertEqual(calc.calculate_reward(4), 25.0)  # 100 / (2^2)
        self.assertEqual(calc.calculate_reward(5), 25.0)

        # Test minimum reward clamping
        # For interval 2, base 100:
        # Depth 0: 100
        # Depth 2: 50
        # Depth 4: 25
        # Depth 6: 12.5
        # Depth 8: 6.25
        # Depth 10: 3.125
        # Depth 12: 1.5625
        # Depth 14: 0.78125
        # Depth 16: 0.390625
        # Depth 18: 0.1953125
        # Depth 20: 0.09765625 -> clamped to 0.1
        self.assertEqual(calc.calculate_reward(18), 0.1953125)
        self.assertEqual(calc.calculate_reward(20), 0.1) # Clamped
        self.assertEqual(calc.calculate_reward(22), 0.1) # Stays clamped

        with self.assertRaises(ValueError):
            calc.calculate_reward(-1)

        # Test with halving interval 1
        calc_halve_every_1 = DepthCalculator(base_reward=64.0, reward_halving_interval=1, reward_min_value=0)
        self.assertEqual(calc_halve_every_1.calculate_reward(0), 64.0)
        self.assertEqual(calc_halve_every_1.calculate_reward(1), 32.0)
        self.assertEqual(calc_halve_every_1.calculate_reward(2), 16.0)
        self.assertEqual(calc_halve_every_1.calculate_reward(3), 8.0)


    def test_get_difficulty_and_reward(self):
        calc = DepthCalculator(
            base_difficulty=10.0, difficulty_exp_factor=2.0,
            base_reward=100.0, reward_halving_interval=2, reward_min_value=0.1
        )

        diff, rew = calc.get_difficulty_and_reward(0)
        self.assertEqual(diff, 10.0)
        self.assertEqual(rew, 100.0)

        diff, rew = calc.get_difficulty_and_reward(2)
        self.assertEqual(diff, 40.0)
        self.assertEqual(rew, 50.0)

        # Test with hashrate param (no effect currently)
        diff_adaptive, rew_adaptive = calc.get_difficulty_and_reward(2, current_network_hashrate_at_depth="dummy")
        self.assertEqual(diff_adaptive, 40.0)
        self.assertEqual(rew_adaptive, 50.0)

        with self.assertRaises(ValueError):
            calc.get_difficulty_and_reward(-5)

if __name__ == '__main__':
    unittest.main()
