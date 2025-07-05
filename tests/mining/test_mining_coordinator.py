import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.mining_coordinator import MiningCoordinator
from fractal_blockchain.mining.difficulty_adjuster import DifficultyAdjuster, TARGET_BLOCK_TIME_SECONDS, DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS
from fractal_blockchain.mining.anti_asic_miner import AntiASICMiner
from fractal_blockchain.core.addressing import AddressedFractalCoordinate, coord_to_string
from fractal_blockchain.blockchain.block_header import MinimalBlockHeader
from fractal_blockchain.core.geometry_validator import is_valid_addressed_coordinate


class TestMiningCoordinator(unittest.TestCase):

    def setUp(self):
        self.mock_difficulty_adjuster = MagicMock(spec=DifficultyAdjuster)
        # Configure default return for get_current_difficulty to avoid issues if not specifically set
        self.mock_difficulty_adjuster.get_current_difficulty.return_value = 1.0

        self.coordinator = MiningCoordinator(difficulty_adjuster=self.mock_difficulty_adjuster)

        # It's useful to have a real AntiASICMiner for some tests to ensure integration,
        # but for others, mocking its find_valid_hash might be better to speed up tests
        # and control outcomes. For now, use the real one.

    def test_mine_on_valid_solid_coordinate_success(self):
        """Test successful mining on a valid, solid coordinate."""
        valid_coord = AddressedFractalCoordinate(depth=1, path=(0,))
        self.mock_difficulty_adjuster.get_current_difficulty.return_value = 1.0 # Makes target "0" likely

        # Mocking AntiASICMiner's find_valid_hash for controlled success
        mock_miner_instance = MagicMock(spec=AntiASICMiner)
        mock_miner_instance.find_valid_hash.return_value = ("0abcdef", 123, "TestAlgo", {"param":1}) # hash, nonce, algo, params

        with patch('fractal_blockchain.mining.mining_coordinator.AntiASICMiner', return_value=mock_miner_instance):
            coordinator_with_mock_miner = MiningCoordinator(difficulty_adjuster=self.mock_difficulty_adjuster)
            result = coordinator_with_mock_miner.mine_on_coordinate(valid_coord, max_nonce_attempts=1000)

        self.assertIsNotNone(result)
        found_hash, nonce, algo_name, header = result

        self.assertEqual(found_hash, "0abcdef")
        self.assertEqual(nonce, 123)
        self.assertEqual(algo_name, "TestAlgo")
        self.assertIsInstance(header, MinimalBlockHeader)
        self.assertEqual(header.fractal_coord_str, coord_to_string(valid_coord))

        # Check that geometry_validator was conceptually called (it's directly called in the code)
        # Check that difficulty was fetched
        self.mock_difficulty_adjuster.get_current_difficulty.assert_called_with(valid_coord.depth, coord_to_string(valid_coord))
        # Check that miner's find_valid_hash was called with correct header data and coord object
        # The first arg to find_valid_hash is block_data_to_hash
        # The second is the target_coord object
        expected_header = MinimalBlockHeader.create_example(
            prev_hash=coordinator_with_mock_miner.previous_block_hash_fetcher(valid_coord), # Get expected prev_hash
            coord=valid_coord,
            example_timestamp=1678886400 # Default timestamp used in mine_on_coordinate
        )
        expected_block_data_to_hash = expected_header.serialize_for_hashing()

        mock_miner_instance.find_valid_hash.assert_called_once_with(
            expected_block_data_to_hash,
            valid_coord,
            "0", # Current simplified target_prefix
            max_nonce=1000
        )


    @patch('fractal_blockchain.mining.mining_coordinator.is_valid_addressed_coordinate', return_value=False)
    def test_mine_on_geometrically_invalid_coordinate(self, mock_is_valid):
        """Test mining attempt on a coordinate deemed geometrically invalid."""
        invalid_coord = AddressedFractalCoordinate(depth=1, path=(0,)) # Path itself is fine
        result = self.coordinator.mine_on_coordinate(invalid_coord)
        self.assertIsNone(result)
        mock_is_valid.assert_called_with(invalid_coord)
        self.mock_difficulty_adjuster.get_current_difficulty.assert_not_called()


    def test_mine_on_void_path_coordinate(self):
        """Test mining attempt on a validly structured void path (should be rejected for mining)."""
        # is_valid_addressed_coordinate will return True for this path structure
        void_coord = AddressedFractalCoordinate(depth=1, path=(3,))

        # Ensure is_valid_addressed_coordinate is called and returns True for this setup
        with patch('fractal_blockchain.mining.mining_coordinator.is_valid_addressed_coordinate', return_value=True) as mock_is_valid:
            result = self.coordinator.mine_on_coordinate(void_coord)
            mock_is_valid.assert_called_with(void_coord)

        self.assertIsNone(result)
        self.mock_difficulty_adjuster.get_current_difficulty.assert_not_called()


    def test_mining_fails_if_no_hash_found(self):
        """Test that coordinator returns None if AntiASICMiner doesn't find a hash."""
        valid_coord = AddressedFractalCoordinate(depth=1, path=(1,))
        self.mock_difficulty_adjuster.get_current_difficulty.return_value = 1000.0 # Hard target

        mock_miner_instance = MagicMock(spec=AntiASICMiner)
        mock_miner_instance.find_valid_hash.return_value = None # Simulate no hash found

        with patch('fractal_blockchain.mining.mining_coordinator.AntiASICMiner', return_value=mock_miner_instance):
            coordinator_with_mock_miner = MiningCoordinator(difficulty_adjuster=self.mock_difficulty_adjuster)
            result = coordinator_with_mock_miner.mine_on_coordinate(valid_coord, max_nonce_attempts=10)

        self.assertIsNone(result)
        mock_miner_instance.find_valid_hash.assert_called_once()


    def test_constructor_default_prev_hash_fetcher(self):
        """ Test that the default previous_block_hash_fetcher works. """
        coord = AddressedFractalCoordinate(depth=0, path=())
        default_coordinator = MiningCoordinator(self.mock_difficulty_adjuster)
        # Accessing it directly for test, normally it's used internally
        prev_hash = default_coordinator.previous_block_hash_fetcher(coord)
        from fractal_blockchain.mining.mining_coordinator import PREVIOUS_BLOCK_HASH_STORE
        self.assertEqual(prev_hash, PREVIOUS_BLOCK_HASH_STORE["main"])

    def test_constructor_custom_prev_hash_fetcher(self):
        """ Test with a custom previous_block_hash_fetcher. """
        coord = AddressedFractalCoordinate(depth=1, path=(0,))
        custom_fetcher = MagicMock(return_value="custom_hash_123")
        custom_coordinator = MiningCoordinator(self.mock_difficulty_adjuster, previous_block_hash_fetcher=custom_fetcher)

        # This will be called internally when creating the header if mining proceeds
        # For direct test:
        prev_hash = custom_coordinator.previous_block_hash_fetcher(coord)
        custom_fetcher.assert_called_with(coord)
        self.assertEqual(prev_hash, "custom_hash_123")

if __name__ == '__main__':
    unittest.main()
