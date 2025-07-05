import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.sierpinski_path_assessor import SierpinskiPathAssessor, BASE_PATH_REWARD, PER_HOP_PENALTY, DEEP_LEVEL_BONUS_THRESHOLD, DEEP_LEVEL_BONUS_FACTOR, MIN_PATH_REWARD
from fractal_blockchain.core.addressing import AddressedFractalCoordinate
# We need get_neighbors for the assessor to work, and it's called internally.
# For isolated testing of assessor logic, we might sometimes mock get_neighbors if its behavior is complex.
# However, the current get_neighbors is simple (siblings), so direct use is okay for now.
from fractal_blockchain.core.geometry_validator import get_neighbors

class TestSierpinskiPathAssessor(unittest.TestCase):

    def setUp(self):
        self.assessor = SierpinskiPathAssessor()
        # Define common coordinates for tests
        self.coord_d1p0 = AddressedFractalCoordinate(depth=1, path=(0,))
        self.coord_d1p1 = AddressedFractalCoordinate(depth=1, path=(1,))
        self.coord_d1p2 = AddressedFractalCoordinate(depth=1, path=(2,))
        self.coord_d1p3_void = AddressedFractalCoordinate(depth=1, path=(3,))
        self.coord_d2p00 = AddressedFractalCoordinate(depth=2, path=(0,0))

        self.deep_coord_d5p0 = AddressedFractalCoordinate(depth=DEEP_LEVEL_BONUS_THRESHOLD, path=(0,)*DEEP_LEVEL_BONUS_THRESHOLD)
        self.deep_coord_d5p1 = AddressedFractalCoordinate(depth=DEEP_LEVEL_BONUS_THRESHOLD, path=((0,)*(DEEP_LEVEL_BONUS_THRESHOLD-1)) + (1,))


    def test_valid_simple_sibling_path(self):
        path = [self.coord_d1p0, self.coord_d1p1]
        self.assertTrue(self.assessor.validate_path_connectivity(path))
        expected_reward = max(BASE_PATH_REWARD - 1 * PER_HOP_PENALTY, MIN_PATH_REWARD)
        self.assertAlmostEqual(self.assessor.calculate_path_bonus(path), expected_reward)

    def test_valid_longer_sibling_path(self):
        path = [self.coord_d1p0, self.coord_d1p1, self.coord_d1p2]
        self.assertTrue(self.assessor.validate_path_connectivity(path))
        expected_reward = max(BASE_PATH_REWARD - 2 * PER_HOP_PENALTY, MIN_PATH_REWARD)
        self.assertAlmostEqual(self.assessor.calculate_path_bonus(path), expected_reward)

    def test_invalid_path_non_neighbor(self):
        path = [self.coord_d1p0, self.coord_d2p00] # d2p00 is not a direct neighbor of d1p0 by current get_neighbors
        self.assertFalse(self.assessor.validate_path_connectivity(path))
        self.assertEqual(self.assessor.calculate_path_bonus(path), 0.0)

    def test_invalid_path_contains_void(self):
        path = [self.coord_d1p0, self.coord_d1p3_void, self.coord_d1p1]
        self.assertFalse(self.assessor.validate_path_connectivity(path)) # Fails due to void coord not being solid
        self.assertEqual(self.assessor.calculate_path_bonus(path), 0.0)

    def test_invalid_path_single_void_coord(self):
        path = [self.coord_d1p3_void]
        self.assertFalse(self.assessor.validate_path_connectivity(path))
        self.assertEqual(self.assessor.calculate_path_bonus(path), 0.0)

    def test_invalid_path_single_invalid_coord(self):
        # is_valid_addressed_coordinate will be false for this if constructor doesn't catch it
        try:
            invalid_syntax_coord = AddressedFractalCoordinate(depth=1, path=(7,)) # Should raise ValueError
            path = [invalid_syntax_coord]
            # If AddressedFractalCoordinate allows construction, then validate_path_connectivity should catch it
            self.assertFalse(self.assessor.validate_path_connectivity(path))
            self.assertEqual(self.assessor.calculate_path_bonus(path), 0.0)
        except ValueError:
            pass # Correctly caught by AddressedFractalCoordinate constructor

    def test_deep_level_path_bonus(self):
        path = [self.deep_coord_d5p0, self.deep_coord_d5p1]
        self.assertTrue(self.assessor.validate_path_connectivity(path))
        base_score = BASE_PATH_REWARD - 1 * PER_HOP_PENALTY
        expected_reward = max(base_score * DEEP_LEVEL_BONUS_FACTOR, MIN_PATH_REWARD)
        self.assertAlmostEqual(self.assessor.calculate_path_bonus(path), expected_reward)

    def test_strategic_connection_bonus(self):
        path = [self.coord_d1p0, self.coord_d1p1, self.coord_d1p2]
        self.assertTrue(self.assessor.validate_path_connectivity(path))

        base_score = BASE_PATH_REWARD - 2 * PER_HOP_PENALTY # 98
        score_with_bonuses = base_score * 1.2 * 1.2 * 1.1 # Start, End, Both
        expected_reward = max(score_with_bonuses, MIN_PATH_REWARD)

        bonus = self.assessor.calculate_path_bonus(path, strategic_start=self.coord_d1p0, strategic_end=self.coord_d1p2)
        self.assertAlmostEqual(bonus, expected_reward)

    def test_strategic_start_only(self):
        path = [self.coord_d1p0, self.coord_d1p1]
        base_score = BASE_PATH_REWARD - 1 * PER_HOP_PENALTY
        expected_reward = max(base_score * 1.2, MIN_PATH_REWARD)
        bonus = self.assessor.calculate_path_bonus(path, strategic_start=self.coord_d1p0)
        self.assertAlmostEqual(bonus, expected_reward)

    def test_strategic_end_only(self):
        path = [self.coord_d1p0, self.coord_d1p1]
        base_score = BASE_PATH_REWARD - 1 * PER_HOP_PENALTY
        expected_reward = max(base_score * 1.2, MIN_PATH_REWARD)
        bonus = self.assessor.calculate_path_bonus(path, strategic_end=self.coord_d1p1)
        self.assertAlmostEqual(bonus, expected_reward)

    def test_min_reward_enforcement(self):
        assessor_low_base = SierpinskiPathAssessor(base_reward=10, hop_penalty=3, min_reward=5)
        path = [self.coord_d1p0, self.coord_d1p1, self.coord_d1p2] # 2 hops. Score = 10 - 2*3 = 4
        self.assertTrue(assessor_low_base.validate_path_connectivity(path))
        # Calculated score is 4, which is less than min_reward 5. So, 5 should be returned.
        self.assertAlmostEqual(assessor_low_base.calculate_path_bonus(path), 5.0)

    def test_empty_path(self):
        path = []
        # validate_path_connectivity for empty path is False based on current logic (len < 2)
        self.assertFalse(self.assessor.validate_path_connectivity(path))
        self.assertEqual(self.assessor.calculate_path_bonus(path), 0.0)

    def test_single_point_path_valid(self):
        path = [self.coord_d1p0]
        self.assertTrue(self.assessor.validate_path_connectivity(path))
        # Score: base_reward * (no deep level bonus as depth 1 < 5)
        expected_reward = max(BASE_PATH_REWARD, MIN_PATH_REWARD)
        self.assertAlmostEqual(self.assessor.calculate_path_bonus(path), expected_reward)

    def test_single_point_path_deep_strategic(self):
        # A single point path at deep level that is also strategic start & end
        deep_single_coord = AddressedFractalCoordinate(depth=DEEP_LEVEL_BONUS_THRESHOLD, path=(0,)*DEEP_LEVEL_BONUS_THRESHOLD)
        path = [deep_single_coord]
        self.assertTrue(self.assessor.validate_path_connectivity(path))

        # score = base_reward (100)
        # score *= 1.2 (strategic single point) -> 120
        # score *= deep_level_factor (1.5) -> 120 * 1.5 = 180
        expected_reward = max(BASE_PATH_REWARD * 1.2 * DEEP_LEVEL_BONUS_FACTOR, MIN_PATH_REWARD)
        bonus = self.assessor.calculate_path_bonus(path, strategic_start=deep_single_coord, strategic_end=deep_single_coord)
        self.assertAlmostEqual(bonus, expected_reward)

    def test_path_score_goes_to_zero_then_min_reward(self):
        # Test case where penalties reduce score below min_reward but not to/below zero
        # Base=100, Penalty=1, MinReward=5. Path of 98 hops.
        # Score = 100 - 98*1 = 2. Expected reward = 5 (MinReward)
        # This is hard to construct with sibling-only paths.
        # Instead, use custom assessor settings.
        assessor_custom = SierpinskiPathAssessor(base_reward=20, hop_penalty=5, min_reward=10)
        path = [self.coord_d1p0, self.coord_d1p1, self.coord_d1p2] # 2 hops. Score = 20 - 2*5 = 10
        self.assertTrue(assessor_custom.validate_path_connectivity(path))
        self.assertAlmostEqual(assessor_custom.calculate_path_bonus(path), 10.0) # Score is 10, min is 10.

        # Path of 3 hops: [c0,c1,c2,c0_again_for_path_length] - need a 4-coord path.
        # This requires a neighbor of c2 that can lead back or further.
        # For simplicity, let's assume a path like [c0,c1,c2,c1_again_but_as_new_step] if get_neighbors(c2) includes c1.
        # get_neighbors(d1p2) = [d1p0, d1p1]. So [d1p0,d1p1,d1p2,d1p1] is valid. 3 hops.
        path_3hops = [self.coord_d1p0, self.coord_d1p1, self.coord_d1p2, self.coord_d1p1]
        self.assertTrue(assessor_custom.validate_path_connectivity(path_3hops))
        # Score = 20 - 3*5 = 5. Expected reward = 10 (MinReward)
        self.assertAlmostEqual(assessor_custom.calculate_path_bonus(path_3hops), 10.0)

    def test_path_score_goes_negative_then_zero_reward(self):
        # Test case where penalties reduce score to negative, should yield 0 reward if min_reward is 0
        assessor_custom = SierpinskiPathAssessor(base_reward=10, hop_penalty=5, min_reward=0)
        path_3hops = [self.coord_d1p0, self.coord_d1p1, self.coord_d1p2, self.coord_d1p1] # 3 hops
        self.assertTrue(assessor_custom.validate_path_connectivity(path_3hops))
        # Score = 10 - 3*5 = -5. Expected reward = 0 (MinReward is 0, score is <0)
        self.assertAlmostEqual(assessor_custom.calculate_path_bonus(path_3hops), 0.0)


if __name__ == '__main__':
    unittest.main()
