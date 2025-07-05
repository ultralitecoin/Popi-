import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.hashrate_distribution_advisor import HashrateDistributionAdvisor
from fractal_blockchain.mining.hashrate_monitor import HashrateMonitor
from fractal_blockchain.mining.difficulty_adjuster import DifficultyAdjuster
from fractal_blockchain.mining.reward_system import FractalRewardSystem
from fractal_blockchain.core.addressing import AddressedFractalCoordinate, coord_to_string

class TestHashrateDistributionAdvisor(unittest.TestCase):

    def setUp(self):
        self.mock_monitor = MagicMock(spec=HashrateMonitor)
        # Optional dependencies, can be None if advisor handles it
        self.mock_difficulty_adjuster = MagicMock(spec=DifficultyAdjuster)
        self.mock_reward_system = MagicMock(spec=FractalRewardSystem)

        self.advisor = HashrateDistributionAdvisor(
            monitor=self.mock_monitor,
            difficulty_adjuster=self.mock_difficulty_adjuster,
            reward_system=self.mock_reward_system
        )

    def test_check_and_advise_balanced_hashrate(self):
        """Test advisor's response when hashrate is balanced."""
        self.mock_monitor.find_hotspots.return_value = ([], []) # No hotspots

        advice = self.advisor.check_and_advise()

        self.assertEqual(len(advice), 1)
        self.assertEqual(advice[0]['type'], "info_system")
        self.assertEqual(advice[0]['level'], "info")
        self.assertIn("balanced", advice[0]['message'])
        self.mock_monitor.find_hotspots.assert_called_once_with(threshold_factor=self.advisor.hotspot_threshold_factor)

    def test_check_and_advise_coord_hotspots(self):
        """Test advisor's response when coordinate hotspots are detected."""
        hot_coords = [coord_to_string(AddressedFractalCoordinate(1,(0,))), coord_to_string(AddressedFractalCoordinate(2,(1,1)))]
        self.mock_monitor.find_hotspots.return_value = (hot_coords, []) # Only coord hotspots

        advice = self.advisor.check_and_advise()

        self.assertTrue(len(advice) >= 1)

        info_miners_advice = next((a for a in advice if a['type'] == "info_miners" and "hot_coordinates" in a['details']), None)
        self.assertIsNotNone(info_miners_advice)
        self.assertEqual(info_miners_advice['details']['hot_coordinates'], hot_coords)

        feedback_difficulty_advice_count = sum(1 for a in advice if a['type'] == "feedback_difficulty" and "target_coord_str" in a)
        self.assertEqual(feedback_difficulty_advice_count, len(hot_coords))

        for hc in hot_coords:
            self.assertTrue(any(a['type'] == "feedback_difficulty" and a['target_coord_str'] == hc for a in advice))

    def test_check_and_advise_depth_hotspots(self):
        """Test advisor's response when depth hotspots are detected."""
        hot_depths = [0, 3]
        self.mock_monitor.find_hotspots.return_value = ([], hot_depths) # Only depth hotspots

        advice = self.advisor.check_and_advise()
        self.assertTrue(len(advice) >= 1)

        info_miners_advice = next((a for a in advice if a['type'] == "info_miners" and "hot_depths" in a['details']), None)
        self.assertIsNotNone(info_miners_advice)
        self.assertEqual(info_miners_advice['details']['hot_depths'], hot_depths)

        feedback_difficulty_advice_count = sum(1 for a in advice if a['type'] == "feedback_difficulty" and "target_depth" in a)
        self.assertEqual(feedback_difficulty_advice_count, len(hot_depths))

        for hd in hot_depths:
            self.assertTrue(any(a['type'] == "feedback_difficulty" and a['target_depth'] == hd for a in advice))


    def test_check_and_advise_both_coord_and_depth_hotspots(self):
        """Test advisor's response with both coordinate and depth hotspots."""
        hot_coords = [coord_to_string(AddressedFractalCoordinate(1,(0,)))]
        hot_depths = [1] # Depth 1 is also a hotspot
        self.mock_monitor.find_hotspots.return_value = (hot_coords, hot_depths)

        advice = self.advisor.check_and_advise()

        # Expected: 1 info_miners for coords, 1 feedback_difficulty for that coord
        #           1 info_miners for depths, 1 feedback_difficulty for that depth
        # Total should be 4 advice items if distinct, or fewer if messages are combined (current impl makes them distinct)

        self.assertTrue(any(a['type'] == "info_miners" and a['details'].get('hot_coordinates') == hot_coords for a in advice))
        self.assertTrue(any(a['type'] == "feedback_difficulty" and a.get('target_coord_str') == hot_coords[0] for a in advice))

        self.assertTrue(any(a['type'] == "info_miners" and a['details'].get('hot_depths') == hot_depths for a in advice))
        self.assertTrue(any(a['type'] == "feedback_difficulty" and a.get('target_depth') == hot_depths[0] for a in advice))


    def test_discuss_security_measures(self):
        """Test that discuss_security_measures returns a list of strings."""
        measures = self.advisor.discuss_security_measures()
        self.assertIsInstance(measures, list)
        self.assertTrue(len(measures) > 0)
        for measure in measures:
            self.assertIsInstance(measure, str)

    def test_advisor_init_with_none_dependencies(self):
        """Test that advisor can be initialized with None for optional dependencies."""
        try:
            HashrateDistributionAdvisor(monitor=self.mock_monitor, difficulty_adjuster=None, reward_system=None)
        except Exception as e:
            self.fail(f"Advisor initialization with None dependencies failed: {e}")


if __name__ == '__main__':
    unittest.main()
