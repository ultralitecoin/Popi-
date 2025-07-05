import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.anti_asic_miner import AntiASICMiner, AVAILABLE_ALGORITHMS, ALGORITHM_PARAMS
from fractal_blockchain.mining.randomx_adapter import FractalCoordinate

class TestAntiASICMiner(unittest.TestCase):

    def setUp(self):
        self.miner = AntiASICMiner()
        self.sample_block_data = b"test_block_data"

    def test_algorithm_selection_varies_with_coordinate(self):
        """Test that algorithm selection changes based on fractal coordinate."""
        coord1 = FractalCoordinate(depth=1, path=[0])
        coord2 = FractalCoordinate(depth=2, path=[1])
        coord3 = FractalCoordinate(depth=1, path=[0]) # Same as coord1

        algo_name1, _, params1 = self.miner.select_algorithm_and_params(coord1)
        algo_name2, _, params2 = self.miner.select_algorithm_and_params(coord2)
        algo_name3, _, params3 = self.miner.select_algorithm_and_params(coord3)

        # Algo name or params should differ for coord1 and coord2
        self.assertTrue(algo_name1 != algo_name2 or params1 != params2,
                        "Algorithm or params should differ for different coordinates")

        # Algo name and params should be the same for identical coordinates
        self.assertEqual(algo_name1, algo_name3, "Algorithm should be same for identical coordinates")
        self.assertEqual(params1, params3, "Params should be same for identical coordinates")

        # Test a few more coordinates to ensure variety if possible (depends on selection logic)
        # This is probabilistic, given the modulo arithmetic in selection
        seen_algos = set()
        seen_params = set()
        for d in range(len(AVAILABLE_ALGORITHMS) + 2): # Iterate enough to likely see all algos
            for p_val in range(3):
                coord = FractalCoordinate(depth=d, path=[p_val, (d+p_val)%3])
                name, _, params = self.miner.select_algorithm_and_params(coord)
                seen_algos.add(name)
                seen_params.add(f"{name}_{str(sorted(params.items()))}") # Param variation check

        # Depending on the number of algos and selection logic, we expect to see multiple algos/params
        self.assertGreater(len(seen_algos), 1, "Should select more than one algorithm type over various coords")
        self.assertGreater(len(seen_params), len(AVAILABLE_ALGORITHMS) -1, "Should see multiple parameter variations")


    def test_parameter_variation(self):
        """Test that parameters for a *given* algorithm vary with coordinates."""
        target_algo_name = "RandomX_Sim" # The algorithm we want to test parameter variation for

        if target_algo_name not in AVAILABLE_ALGORITHMS:
            self.skipTest(f"Algorithm {target_algo_name} not found in AVAILABLE_ALGORITHMS.")

        target_algo_index = list(AVAILABLE_ALGORITHMS.keys()).index(target_algo_name)
        num_algos = len(AVAILABLE_ALGORITHMS)

        coord1 = None
        # Find a first coordinate that selects the target_algo_name
        for d_base in range(num_algos * 2): # Search a reasonable range of depths
            for ps_base in range(num_algos * 2): # Search a reasonable range of path sums
                # Construct a simple path that gives ps_base: e.g., [ps_base] if small, or more complex
                path_base = [ps_base] if ps_base < 10 else [ps_base // 2, ps_base - (ps_base // 2)]
                if (d_base + ps_base) % num_algos == target_algo_index:
                    coord1 = FractalCoordinate(depth=d_base, path=path_base)
                    break
            if coord1:
                break

        self.assertIsNotNone(coord1, f"Could not find a coordinate that selects {target_algo_name} for param test (coord1).")
        name1, _, params1 = self.miner.select_algorithm_and_params(coord1)
        self.assertEqual(name1, target_algo_name, f"coord1 {coord1} (depth {coord1.depth}, path_sum {sum(coord1.path)}) did not select {target_algo_name} as expected. Algo_idx was {(coord1.depth + sum(coord1.path)) % num_algos} vs target {target_algo_index}")

        # Find a second coordinate (coord2) that also selects target_algo_name but aims for different params.
        # We'll change the depth and adjust path_sum to maintain the same algo selection.
        d2 = coord1.depth + 1 # Change depth to encourage parameter change.

        # We need (d2 + ps2) % num_algos == target_algo_index
        # So, ps2 % num_algos = (target_algo_index - d2 % num_algos + num_algos) % num_algos
        required_ps2_mod_num_algos = (target_algo_index - (d2 % num_algos) + num_algos) % num_algos

        # Choose ps2 to satisfy the modulo, and try to make it different from sum(coord1.path)
        # if ps2 would be same as sum(coord1.path) and d2 is same as d1 (not the case here), add num_algos
        ps2 = required_ps2_mod_num_algos
        if ps2 == sum(coord1.path) and d2 == coord1.depth: # Should not happen with d2 = d1+1
            ps2 += num_algos
        if ps2 == 0 and sum(coord1.path) == 0 and d2 == coord1.depth: # handle case where path_sum is 0
             ps2 += num_algos # ensure ps2 is different if all else is same (not strictly needed here as d2!=d1)


        # Construct a simple path for ps2
        path2 = [ps2] if ps2 < 10 else [ps2 // 2, ps2 - (ps2 // 2)]
        if ps2 == 0 : path2 = [0] # Handle case where path_sum is 0

        coord2 = FractalCoordinate(depth=d2, path=path2)

        name2, _, params2 = self.miner.select_algorithm_and_params(coord2)

        self.assertEqual(name2, target_algo_name,
                         f"coord2 {coord2} (depth {d2}, path_sum {sum(path2)}) did not select {target_algo_name}. "
                         f"Expected algo_idx {target_algo_index}, but got {(d2 + sum(path2)) % num_algos}. "
                         f"Coord1 was {coord1} (depth {coord1.depth}, path_sum {sum(coord1.path)}).")

        # It's possible, though less likely with changed depth and path_sum, for params to be identical
        # if the parameter generation logic is simple. If this fails often, param generation might need more entropy.
        self.assertNotEqual(params1, params2,
                            f"Parameters for {target_algo_name} should vary. C1: {coord1}, P1: {params1}. C2: {coord2}, P2: {params2}")

    def test_mine_block_attempt_produces_hash(self):
        """Test that a single mining attempt returns a hash."""
        coord = FractalCoordinate(depth=0, path=[])
        computed_hash, algo_name, params = self.miner.mine_block_attempt(self.sample_block_data, coord, nonce=0)

        self.assertIsInstance(computed_hash, str)
        self.assertGreater(len(computed_hash), 32) # SHA256 hex is 64 chars
        self.assertIn(algo_name, AVAILABLE_ALGORITHMS.keys())
        self.assertIsNotNone(params)

    def test_find_valid_hash_success(self):
        """Test finding a hash that meets a simple difficulty target."""
        coord = FractalCoordinate(depth=1, path=[1])
        # Use an easy target that should be found quickly
        # The hash output is hex, so "0" means the first char must be "0"
        difficulty_target_prefix = "0"

        # Max_nonce should be high enough for a "0" prefix with hex output (1/16 chance per attempt)
        result = self.miner.find_valid_hash(self.sample_block_data, coord, difficulty_target_prefix, max_nonce=100)

        self.assertIsNotNone(result, f"Should find a hash starting with '{difficulty_target_prefix}' within 100 nonces")
        found_hash, nonce, algo_name, params = result
        self.assertTrue(found_hash.startswith(difficulty_target_prefix))
        self.assertGreaterEqual(nonce, 0)
        self.assertIn(algo_name, AVAILABLE_ALGORITHMS.keys())

    def test_find_valid_hash_failure(self):
        """Test that it returns None if no valid hash is found within max_nonce."""
        coord = FractalCoordinate(depth=1, path=[2])
        # Use an impossibly hard target for few nonces
        difficulty_target_prefix = "00000000000" # Extremely unlikely

        result = self.miner.find_valid_hash(self.sample_block_data, coord, difficulty_target_prefix, max_nonce=10)
        self.assertIsNone(result, "Should not find such a difficult hash in so few nonces")

    def test_nonce_incorporation(self):
        """Test that different nonces produce different hashes for the same data and coord."""
        coord = FractalCoordinate(depth=3, path=[0,2,1])
        hash1, _, _ = self.miner.mine_block_attempt(self.sample_block_data, coord, nonce=10)
        hash2, _, _ = self.miner.mine_block_attempt(self.sample_block_data, coord, nonce=11)
        self.assertNotEqual(hash1, hash2)

    def test_conceptual_asic_detection_mitigation_runs(self):
        """ Test that the conceptual discussion method runs without error. """
        try:
            self.miner.conceptual_asic_detection_mitigation()
        except Exception as e:
            self.fail(f"conceptual_asic_detection_mitigation() raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()
