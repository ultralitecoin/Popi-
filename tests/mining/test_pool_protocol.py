import unittest
from unittest.mock import MagicMock
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.pool_protocol import FractalMiningPool, PoolShare, MinerContribution, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX
from fractal_blockchain.mining.reward_system import FractalRewardSystem
from fractal_blockchain.mining.difficulty_adjuster import DifficultyAdjuster, TARGET_BLOCK_TIME_SECONDS, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS
from fractal_blockchain.core.addressing import AddressedFractalCoordinate

class TestFractalMiningPool(unittest.TestCase):

    def setUp(self):
        self.mock_reward_system = MagicMock(spec=FractalRewardSystem)
        self.mock_difficulty_adjuster = MagicMock(spec=DifficultyAdjuster)

        # Configure default return values for mocks to avoid TypeErrors if methods are called unexpectedly
        self.mock_reward_system.calculate_block_reward.return_value = 100.0 # Default block reward for tests
        self.mock_difficulty_adjuster.get_current_difficulty.return_value = 10.0 # Default network difficulty metric

        self.pool = FractalMiningPool(
            reward_system=self.mock_reward_system,
            difficulty_adjuster=self.mock_difficulty_adjuster
        )
        self.pool.register_miner("miner1")
        self.pool.register_miner("miner2")

        self.coord_d0 = AddressedFractalCoordinate(depth=0, path=())
        self.coord_d1 = AddressedFractalCoordinate(depth=1, path=(0,))
        self.coord_d2 = AddressedFractalCoordinate(depth=2, path=(0,0))

    def test_miner_registration(self):
        self.assertIn("miner1", self.pool.miners)
        self.assertIsInstance(self.pool.miners["miner1"], MinerContribution)
        # Test re-registering (should not create new entry or error)
        self.pool.register_miner("miner1")
        self.assertEqual(len(self.pool.miners), 2) # Still 2 miners

    def test_submit_valid_share(self):
        # Mock calculate_share_weight to return a predictable weight
        self.pool.calculate_share_weight = MagicMock(return_value=2.5)

        share_accepted = self.pool.submit_share("miner1", self.coord_d1, 123, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX + "hash")

        self.assertTrue(share_accepted)
        self.assertEqual(len(self.pool.current_round_shares), 1)
        self.assertEqual(self.pool.miners["miner1"].total_weighted_shares, 2.5)
        self.assertEqual(self.pool.total_weighted_shares_this_round, 2.5)
        self.pool.calculate_share_weight.assert_called_with(self.coord_d1)

    def test_submit_invalid_share_wrong_difficulty(self):
        share_accepted = self.pool.submit_share("miner1", self.coord_d0, 124, "1hash_nodiffprefix") # Does not meet "0" prefix
        self.assertFalse(share_accepted)
        self.assertEqual(len(self.pool.current_round_shares), 0)
        self.assertEqual(self.pool.miners["miner1"].total_weighted_shares, 0)

    def test_submit_share_unregistered_miner(self):
        share_accepted = self.pool.submit_share("miner3_unreg", self.coord_d0, 125, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX + "hash")
        self.assertFalse(share_accepted)

    def test_calculate_share_weight_increases_with_depth(self):
        # This tests the default implementation of calculate_share_weight
        # If it's mocked in other tests, ensure this test uses the real one or a controlled mock.
        pool_for_weight_test = FractalMiningPool(self.mock_reward_system, self.mock_difficulty_adjuster)

        # Mock get_current_difficulty to control its output for weight calculation
        def mock_get_diff(depth, coord_str):
            return 1.0 + depth * 10 # e.g., D0=1, D1=11, D2=21
        pool_for_weight_test.difficulty_adjuster.get_current_difficulty = MagicMock(side_effect=mock_get_diff)

        weight_d0 = pool_for_weight_test.calculate_share_weight(self.coord_d0)
        weight_d1 = pool_for_weight_test.calculate_share_weight(self.coord_d1)
        weight_d2 = pool_for_weight_test.calculate_share_weight(self.coord_d2)

        # Default logic: 1.0 + depth * 0.5 OR uses difficulty_adjuster.
        # The current pool_protocol.py's calculate_share_weight uses: 1.0 + (share_coord.depth * 0.5)
        # Let's test that default logic if not overridden by mock.
        # For self.pool, it's not mocked in setUp, so it uses the real one.
        weight_d0_actual = self.pool.calculate_share_weight(self.coord_d0)
        weight_d1_actual = self.pool.calculate_share_weight(self.coord_d1)
        weight_d2_actual = self.pool.calculate_share_weight(self.coord_d2)

        self.assertAlmostEqual(weight_d0_actual, 1.0 + 0 * 0.5)
        self.assertAlmostEqual(weight_d1_actual, 1.0 + 1 * 0.5)
        self.assertAlmostEqual(weight_d2_actual, 1.0 + 2 * 0.5)
        self.assertTrue(weight_d2_actual > weight_d1_actual > weight_d0_actual)


    def test_block_found_and_reward_distribution_proportional(self):
        # Miner1: 2 shares at depth0 (weight 1.0 each default logic) = 2.0
        # Miner2: 1 share at depth2 (weight 1.0 + 2*0.5 = 2.0 default logic) = 2.0
        self.pool.submit_share("miner1", self.coord_d0, 1, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX + "h1")
        self.pool.submit_share("miner1", self.coord_d0, 2, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX + "h2")
        self.pool.submit_share("miner2", self.coord_d2, 3, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX + "h3")

        total_shares_weight = (1.0 + 0*0.5)*2 + (1.0 + 2*0.5) # 2*1.0 + 2.0 = 4.0
        self.assertAlmostEqual(self.pool.total_weighted_shares_this_round, total_shares_weight)
        self.assertAlmostEqual(self.pool.miners["miner1"].total_weighted_shares, 2.0)
        self.assertAlmostEqual(self.pool.miners["miner2"].total_weighted_shares, 2.0)

        block_coord = self.coord_d2 # Block found at depth 2
        mock_block_reward = 200.0
        self.mock_reward_system.calculate_block_reward.return_value = mock_block_reward

        self.pool.block_found_by_pool(block_fractal_coord=block_coord, block_finder_miner_id="miner2")

        self.mock_reward_system.calculate_block_reward.assert_called_with(block_coord.depth)

        expected_miner1_reward = mock_block_reward * (2.0 / total_shares_weight) # 200 * (2/4) = 100
        expected_miner2_reward = mock_block_reward * (2.0 / total_shares_weight) # 200 * (2/4) = 100

        self.assertAlmostEqual(self.pool.get_miner_payouts("miner1"), expected_miner1_reward)
        self.assertAlmostEqual(self.pool.get_miner_payouts("miner2"), expected_miner2_reward)

        # Check if round was reset
        self.assertEqual(len(self.pool.current_round_shares), 0)
        self.assertEqual(self.pool.total_weighted_shares_this_round, 0.0)
        self.assertEqual(self.pool.miners["miner1"].total_weighted_shares, 0.0)
        self.assertEqual(self.pool.miners["miner2"].total_weighted_shares, 0.0)

    def test_block_found_no_shares_in_round(self):
        self.assertEqual(self.pool.total_weighted_shares_this_round, 0)
        block_coord = self.coord_d0
        mock_block_reward = 50.0
        self.mock_reward_system.calculate_block_reward.return_value = mock_block_reward

        self.pool.block_found_by_pool(block_fractal_coord=block_coord, block_finder_miner_id=None)

        # No payouts should occur if no shares
        self.assertEqual(self.pool.get_miner_payouts("miner1"), 0.0)
        self.assertEqual(self.pool.get_miner_payouts("miner2"), 0.0)

        # Round should still reset (though it was already empty)
        self.assertEqual(len(self.pool.current_round_shares), 0)


    def test_payouts_are_cumulative(self):
        # Round 1
        self.pool.submit_share("miner1", self.coord_d0, 1, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX + "h_r1m1")
        self.pool.block_found_by_pool(self.coord_d0, "miner1") # Reward 100, all to miner1
        self.assertAlmostEqual(self.pool.get_miner_payouts("miner1"), 100.0)

        # Round 2
        self.mock_reward_system.calculate_block_reward.return_value = 50.0 # New block reward for round 2
        self.pool.submit_share("miner1", self.coord_d1, 2, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX + "h_r2m1")
        self.pool.block_found_by_pool(self.coord_d1, "miner1") # Reward 50, all to miner1

        self.assertAlmostEqual(self.pool.get_miner_payouts("miner1"), 100.0 + 50.0) # Cumulative


if __name__ == '__main__':
    unittest.main()
