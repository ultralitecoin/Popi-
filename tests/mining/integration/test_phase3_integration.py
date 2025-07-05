import unittest
import sys
import os
import time # For unique timestamps if needed

# Adjust path to import from the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from fractal_blockchain.core.addressing import AddressedFractalCoordinate, coord_to_string
from fractal_blockchain.core.geometry_validator import is_valid_addressed_coordinate # Direct import for clarity
from fractal_blockchain.blockchain.block_header import MinimalBlockHeader
from fractal_blockchain.mining.mining_coordinator import MiningCoordinator
from fractal_blockchain.mining.difficulty_adjuster import DifficultyAdjuster, TARGET_BLOCK_TIME_SECONDS, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS
from fractal_blockchain.mining.reward_system import FractalRewardSystem
from fractal_blockchain.mining.anti_asic_miner import AntiASICMiner
from fractal_blockchain.mining.pool_protocol import FractalMiningPool, DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX
from fractal_blockchain.mining.hashrate_monitor import HashrateMonitor
from fractal_blockchain.mining.hashrate_distribution_advisor import HashrateDistributionAdvisor

# No specific imports from randomx_adapter needed here as it's used by AntiASICMiner

class TestPhase3MiningIntegration(unittest.TestCase):

    def test_full_mining_flow_integration(self):
        """
        Tests the integration of MiningCoordinator, DifficultyAdjuster, AntiASICMiner,
        MinimalBlockHeader, and geometric validation for a single mining attempt.
        """
        print("\n--- Integration Test: Full Mining Flow ---")

        # 1. Setup components
        difficulty_adjuster = DifficultyAdjuster()
        reward_system = FractalRewardSystem() # Not directly used by mine_on_coordinate, but part of ecosystem
        mining_coordinator = MiningCoordinator(difficulty_adjuster=difficulty_adjuster)

        # 2. Define a target coordinate
        # Using depth 0, path () to select RandomX_Sim, which might be faster or more predictable
        # with controlled parameters if we could set them.
        target_coord = AddressedFractalCoordinate(depth=0, path=())
        print(f"Targeting coordinate: {target_coord}")

        # Pre-assertion: Ensure the coordinate is considered valid by the standalone validator
        # This also implicitly tests is_valid_addressed_coordinate from geometry_validator
        self.assertTrue(is_valid_addressed_coordinate(target_coord), "Target coordinate should be geometrically valid for test setup.")
        self.assertTrue(target_coord.is_solid_path(), "Target coordinate should be a solid path for mining.")

        # 3. Simulate some history for difficulty adjuster to ensure it has some data
        # (otherwise difficulty might be at its initial, possibly very high/low state)
        current_time = int(time.time())
        # Add blocks at target_coord's depth to influence its difficulty calculation
        for i in range(DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS):
            difficulty_adjuster.record_block_found(
                target_coord.depth,
                current_time + (i * TARGET_BLOCK_TIME_SECONDS // 2), # Faster than target
                f"D:{target_coord.depth}-P:sim_path{i}"
            )
        initial_difficulty = difficulty_adjuster.get_current_difficulty(target_coord.depth, coord_to_string(target_coord))
        print(f"Initial difficulty for {target_coord} (depth {target_coord.depth}): {initial_difficulty}")
        self.assertTrue(initial_difficulty > 0, "Difficulty should be positive.")

        # 4. Execute the mining operation via MiningCoordinator
        # The coordinator will use a simplified difficulty target prefix "0".
        # We need to ensure that the AntiASICMiner can find such a hash within reasonable nonces.
        # max_nonce_attempts should be high enough for a "0" prefix (1/16 per hash for random hex).
        # Hashing functions are deterministic, so it should find it if one exists in the range.
        # The internal AntiASICMiner's find_valid_hash prints progress.
        print("Attempting to mine on coordinate...")
        mining_result = mining_coordinator.mine_on_coordinate(
            target_coord=target_coord,
            example_timestamp=current_time + 1000, # Ensure a unique timestamp
            max_nonce_attempts=65536 # Generous nonce attempts for "0" prefix
        )

        # 5. Assertions
        self.assertIsNotNone(mining_result, "MiningCoordinator should successfully find a block.")

        found_hash, nonce, algo_name, header_obj = mining_result

        print(f"Mining successful: Hash={found_hash}, Nonce={nonce}, Algo={algo_name}")
        # MiningCoordinator uses "0" as the target prefix internally for this test's path
        self.assertTrue(found_hash.startswith("0"), f"Found hash {found_hash} should meet the simplified target prefix '0'.")
        self.assertGreaterEqual(nonce, 0)
        self.assertIsInstance(algo_name, str)
        self.assertTrue(len(algo_name) > 0)

        self.assertIsInstance(header_obj, MinimalBlockHeader)
        self.assertEqual(header_obj.fractal_coord_str, coord_to_string(target_coord))
        self.assertEqual(header_obj.timestamp, current_time + 1000)

        # Check if the block reward for this coord would be positive (sanity check for RewardSystem)
        block_reward = reward_system.calculate_block_reward(header_obj.get_fractal_coordinate().depth)
        print(f"Potential block reward for this coordinate's depth: {block_reward}")
        self.assertGreater(block_reward, 0)

        # Further check: The hash should be reproducible if we re-hash the header with the found nonce and algo
        # This requires knowing the exact parameters used by the AntiASICMiner for that attempt.
        # The `params_used` was returned by `find_valid_hash` but not propagated by `mine_on_coordinate`.
        # For this integration test, verifying the prefix is sufficient.
        # A deeper test would involve the `MiningCoordinator` returning the algo params used.

        print("Full Mining Flow integration test passed.")

    def test_pool_mining_integration(self):
        """
        Tests integration of FractalMiningPool with share submission and reward distribution,
        considering fractal coordinates and difficulty/reward systems.
        """
        print("\n--- Integration Test: Pool Mining ---")

        # 1. Setup components
        difficulty_adjuster = DifficultyAdjuster()
        reward_system = FractalRewardSystem()
        # For this test, we'll use the actual AntiASICMiner to generate potential share hashes
        # but we'll control nonces to ensure some meet pool difficulty.
        asic_miner = AntiASICMiner()
        pool = FractalMiningPool(reward_system=reward_system, difficulty_adjuster=difficulty_adjuster)

        pool.register_miner("pool_miner1")
        pool.register_miner("pool_miner2")

        # 2. Define coordinates and simulate some difficulty history
        coord_d0 = AddressedFractalCoordinate(depth=0, path=()) # Selects RandomX_Sim
        coord_d1 = AddressedFractalCoordinate(depth=1, path=(0,)) # Selects VariantA_ComputeHeavy

        current_time = int(time.time())
        for i in range(DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS):
            difficulty_adjuster.record_block_found(0, current_time + i * TARGET_BLOCK_TIME_SECONDS, coord_to_string(coord_d0))
            difficulty_adjuster.record_block_found(1, current_time + i * TARGET_BLOCK_TIME_SECONDS, coord_to_string(coord_d1))

        print(f"Difficulty D0: {difficulty_adjuster.get_current_difficulty(0, coord_to_string(coord_d0))}")
        print(f"Difficulty D1: {difficulty_adjuster.get_current_difficulty(1, coord_to_string(coord_d1))}")

        # 3. Simulate share submissions
        # We need a dummy block header data that miners would be working on.
        # The pool would typically provide this template.
        # For this test, let's create a common one.
        # In a real pool, this would be derived from the current chain tip the pool is trying to extend.
        dummy_prev_hash = "0000pool_prev_hash" + "0"*46
        header_template_d0 = MinimalBlockHeader.create_example(dummy_prev_hash, coord_d0, current_time)
        header_template_d1 = MinimalBlockHeader.create_example(dummy_prev_hash, coord_d1, current_time)

        data_to_hash_d0 = header_template_d0.serialize_for_hashing()
        data_to_hash_d1 = header_template_d1.serialize_for_hashing() # Not used if both mine on d0

        # Get pool's share difficulty for coord_d0
        pool_share_target_d0 = pool.get_pool_share_difficulty_prefix(coord_d0)

        shares_miner1 = 0
        shares_miner2 = 0
        found_block_share_details = None

        # Mock share generation for speed and reliability
        # Miner 1 submits 2 shares. Designate the second one as the "network block".
        share1_m1_nonce = 101
        share1_m1_hash = pool_share_target_d0 + "11111111111111111111111111111111" # Meets pool difficulty
        pool.submit_share("pool_miner1", coord_d0, share1_m1_nonce, share1_m1_hash)
        shares_miner1 = 1

        share2_m1_nonce = 102
        share2_m1_hash_block = "00" + "NET_BLOCK_HASH_FROM_M1" + "0"*28 # Meets "00" (network) and "0" (pool)
        pool.submit_share("pool_miner1", coord_d0, share2_m1_nonce, share2_m1_hash_block)
        shares_miner1 += 1
        found_block_share_details = {"coord": coord_d0, "miner": "pool_miner1", "hash": share2_m1_hash_block, "nonce": share2_m1_nonce}

        # Miner 2 submits 1 share
        share1_m2_nonce = 201
        share1_m2_hash = pool_share_target_d0 + "22222222222222222222222222222222" # Meets pool difficulty
        pool.submit_share("pool_miner2", coord_d0, share1_m2_nonce, share1_m2_hash)
        shares_miner2 = 1

        self.assertIsNotNone(found_block_share_details, "A share MUST be designated the network block for the test.")
        self.assertEqual(shares_miner1, 2, "Miner1 should have 2 shares.")
        self.assertEqual(shares_miner2, 1, "Miner2 should have 1 share.")

        print(f"Miner1 submitted {shares_miner1} shares. Miner2 submitted {shares_miner2} shares (all for coord_d0, with mocked hashes).")
        print(f"Block finding share details: {found_block_share_details}")
        self.assertTrue(pool.total_weighted_shares_this_round > 0)

        # 4. Pool "finds" a block
        block_coord = found_block_share_details["coord"]
        block_finder_id = found_block_share_details["miner"]

        expected_block_reward = reward_system.calculate_block_reward(block_coord.depth)
        print(f"Simulating block found on {block_coord} by {block_finder_id}. Expected network reward: {expected_block_reward}")

        # Capture contributions before reset for accurate assertion
        miner1_contrib_round = pool.miners["pool_miner1"].total_weighted_shares
        miner2_contrib_round = pool.miners["pool_miner2"].total_weighted_shares
        total_contrib_round = pool.total_weighted_shares_this_round # Sum of weights of submitted shares

        pool.block_found_by_pool(block_fractal_coord=block_coord, block_finder_miner_id=block_finder_id)

        # 5. Assertions
        payout_miner1 = pool.get_miner_payouts("pool_miner1")
        payout_miner2 = pool.get_miner_payouts("pool_miner2")

        # Calculate expected payouts based on captured contributions
        expected_payout_m1 = 0
        if total_contrib_round > 0:
            expected_payout_m1 = (miner1_contrib_round / total_contrib_round) * expected_block_reward

        expected_payout_m2 = 0
        if total_contrib_round > 0:
            expected_payout_m2 = (miner2_contrib_round / total_contrib_round) * expected_block_reward

        self.assertAlmostEqual(payout_miner1, expected_payout_m1, delta=0.0001)
        self.assertAlmostEqual(payout_miner2, expected_payout_m2, delta=0.0001)

        print(f"Payout Miner1: {payout_miner1:.4f} (Expected: {expected_payout_m1:.4f}), Payout Miner2: {payout_miner2:.4f} (Expected: {expected_payout_m2:.4f})")
        self.assertAlmostEqual(payout_miner1 + payout_miner2, expected_block_reward, delta=0.0001, msg="Sum of payouts should equal block reward")

        # Ensure round was reset
        self.assertEqual(len(pool.current_round_shares), 0, "Pool current round shares should be empty after block found")
        self.assertEqual(pool.total_weighted_shares_this_round, 0.0)
        print("Pool Mining integration test passed.")

    def test_hashrate_monitoring_advising_integration(self):
        """
        Tests integration of HashrateMonitor and HashrateDistributionAdvisor.
        Simulates activity, checks monitor's report, and advisor's response.
        """
        print("\n--- Integration Test: Hashrate Monitoring and Advising ---")

        # 1. Setup components
        # For this test, DifficultyAdjuster and RewardSystem are not strictly needed by the advisor's current logic,
        # but good to include for completeness if advisor's actions were more integrated.
        monitor = HashrateMonitor(aggregation_level=1) # Aggregate above depth 1 for easier testing of hotspots
        #difficulty_adjuster = DifficultyAdjuster() # Optional for current advisor
        #reward_system = FractalRewardSystem()       # Optional for current advisor
        advisor = HashrateDistributionAdvisor(monitor=monitor, difficulty_adjuster=None, reward_system=None)
        advisor.hotspot_threshold_factor = 1.5 # Lower threshold for easier hotspot trigger in test

        # 2. Simulate activity to create a hotspot
        coord_d0 = AddressedFractalCoordinate(depth=0, path=())
        coord_d1p0 = AddressedFractalCoordinate(depth=1, path=(0,))
        coord_d1p1 = AddressedFractalCoordinate(depth=1, path=(1,))
        coord_d2p00 = AddressedFractalCoordinate(depth=2, path=(0,0)) # Aggregates to d1p0*

        monitor.record_activity(coord_d0, 5)     # Low activity
        monitor.record_activity(coord_d1p0, 30)  # Hotspot coord (d1p0) and hot depth (1)
        monitor.record_activity(coord_d1p1, 6)     # Avg/Low activity
        monitor.record_activity(coord_d2p00, 2)  # Contributes to d1p0* if aggregation was used in hotspot, and depth 2
                                                # Current monitor.find_hotspots uses exact coord strings.

        # 3. Get report from monitor (optional step, mainly for verification if needed)
        coord_activity, depth_activity = monitor.get_activity_report()
        print(f"Monitor - Coord Activity: {coord_activity}")
        print(f"Monitor - Depth Activity: {depth_activity}")

        # Expected hotspots:
        # Coord d1p0 (activity 30) should be a hotspot.
        # Total coord activity = 5+30+6+2 = 43. Num distinct coords = 4. Avg = 10.75. Threshold = 10.75 * 1.5 = 16.125.
        # So, d1p0 (30) is a hotspot.
        # Depth 1 (activity 30+6=36) should be a hotspot.
        # Total depth activity = 43. Depths: 0 (5), 1 (36), 2 (2). Num depths = 3. Avg = 14.33. Threshold = 14.33 * 1.5 = 21.5.
        # So, Depth 1 (36) is a hotspot.

        # 4. Get advice from advisor
        advice_list = advisor.check_and_advise()
        print(f"Advisor generated {len(advice_list)} pieces of advice:")
        for ad in advice_list: print(f"  - {ad}")

        # 5. Assertions on the advice
        self.assertTrue(len(advice_list) > 0)

        # Check for coordinate hotspot advice
        coord_hotspot_info_found = False
        coord_hotspot_feedback_found = False
        expected_hot_coord_str = coord_to_string(coord_d1p0)

        for advice_item in advice_list:
            if advice_item.get("type") == "info_miners" and expected_hot_coord_str in advice_item.get("details", {}).get("hot_coordinates", []):
                coord_hotspot_info_found = True
            if advice_item.get("type") == "feedback_difficulty" and advice_item.get("target_coord_str") == expected_hot_coord_str:
                self.assertEqual(advice_item.get("reason"), "hashrate_centralization")
                coord_hotspot_feedback_found = True

        self.assertTrue(coord_hotspot_info_found, "Advisor should issue info about coordinate hotspot.")
        self.assertTrue(coord_hotspot_feedback_found, "Advisor should issue difficulty feedback for coordinate hotspot.")

        # Check for depth hotspot advice
        depth_hotspot_info_found = False
        depth_hotspot_feedback_found = False
        expected_hot_depth = 1

        for advice_item in advice_list:
            if advice_item.get("type") == "info_miners" and expected_hot_depth in advice_item.get("details", {}).get("hot_depths", []):
                depth_hotspot_info_found = True
            if advice_item.get("type") == "feedback_difficulty" and advice_item.get("target_depth") == expected_hot_depth:
                self.assertEqual(advice_item.get("reason"), "hashrate_centralization_at_depth")
                depth_hotspot_feedback_found = True

        self.assertTrue(depth_hotspot_info_found, "Advisor should issue info about depth hotspot.")
        self.assertTrue(depth_hotspot_feedback_found, "Advisor should issue difficulty feedback for depth hotspot.")

        print("Hashrate Monitoring and Advising integration test passed.")


if __name__ == '__main__':
    unittest.main()
