from typing import List, Tuple, Optional

from fractal_blockchain.core.addressing import AddressedFractalCoordinate
from fractal_blockchain.core.geometry_validator import is_valid_addressed_coordinate, get_neighbors

# --- Configuration for Path Assessment ---
BASE_PATH_REWARD = 100.0  # Base reward for any valid submitted path
PER_HOP_PENALTY = 1.0    # Penalty for each hop in the path (incentivizes shorter paths)
DEEP_LEVEL_BONUS_THRESHOLD = 5 # Depth at which bonus starts applying
DEEP_LEVEL_BONUS_FACTOR = 1.5  # Multiplier for paths reaching deep levels
MIN_PATH_REWARD = 5.0      # Minimum reward for any qualifying path

class SierpinskiPathAssessor:
    def __init__(self,
                 base_reward: float = BASE_PATH_REWARD,
                 hop_penalty: float = PER_HOP_PENALTY,
                 deep_level_threshold: int = DEEP_LEVEL_BONUS_THRESHOLD,
                 deep_level_factor: float = DEEP_LEVEL_BONUS_FACTOR,
                 min_reward: float = MIN_PATH_REWARD):

        self.base_reward = base_reward
        self.hop_penalty = hop_penalty
        self.deep_level_threshold = deep_level_threshold
        self.deep_level_factor = deep_level_factor
        self.min_reward = min_reward

    def validate_path_connectivity(self, path: List[AddressedFractalCoordinate]) -> bool:
        """
        Validates if the path is geometrically connected according to get_neighbors.
        Also checks if all coordinates are valid and solid.
        """
        if not path: # Handle empty path first
            print("[PathAssessor] Path validation failed: Path is empty.")
            return False

        if len(path) == 1: # Handle single-point path
            coord = path[0]
            if not is_valid_addressed_coordinate(coord) or not coord.is_solid_path():
                print(f"[PathAssessor] Invalid single-point path: {coord} not valid or not solid.")
                return False
            # A single valid solid point is considered a "valid path" of length 1 for scoring purposes,
            # though it doesn't have "connectivity" in the sense of multiple points.
            # The validate_path_connectivity function's name implies checking connections.
            # However, the scoring logic handles len(path)==1. Let's align:
            # For connectivity, a path of 1 has no connections to check beyond its own validity.
            # The original code returned True here. Let's keep that for now,
            # as calculate_path_bonus relies on this for single-point paths.
            return True

        # Path has 2 or more coordinates, proceed with full validation
        for i, coord in enumerate(path):
            # Check individual coordinate validity and type
            if not is_valid_addressed_coordinate(coord):
                print(f"[PathAssessor] Path validation failed: Coordinate {coord} at index {i} is not valid.")
                return False
            if not coord.is_solid_path():
                print(f"[PathAssessor] Path validation failed: Coordinate {coord} at index {i} is a void path.")
                return False

            # Check connectivity to the next coordinate
            if i < len(path) - 1:
                current_coord = path[i]
                next_coord = path[i+1]

                # Get neighbors of current_coord. Note: get_neighbors is currently a placeholder
                # and might be very restrictive (e.g., only siblings).
                # This will heavily influence what paths are considered "connected".
                neighbors_of_current = get_neighbors(current_coord)

                if next_coord not in neighbors_of_current:
                    print(f"[PathAssessor] Path connectivity failed: {next_coord} is not a direct neighbor of {current_coord} (Neighbors: {neighbors_of_current}).")
                    return False
        return True

    def score_path(self, path: List[AddressedFractalCoordinate],
                   strategic_start: Optional[AddressedFractalCoordinate] = None,
                   strategic_end: Optional[AddressedFractalCoordinate] = None) -> float:
        """
        Scores a validated path based on length, depth, and strategic connections.
        Assumes path has already passed validate_path_connectivity.
        """
        if not path: # Should be caught by validation if connectivity requires len >= 2
            return 0.0

        if len(path) == 1: # Single point path
            # Potentially give a small score if it's a strategic point itself?
            # For now, focus on paths with length > 1 for scoring bonuses related to connections.
            # If it's a strategic point, that could be handled by strategic_start/end checks.
            score = self.base_reward
            if path[0] == strategic_start and strategic_start == strategic_end : # Path is just one strategic point
                 score *= 1.2 # Small bonus for identifying a single strategic point

            max_depth_in_path = path[0].depth
            if max_depth_in_path >= self.deep_level_threshold:
                score *= self.deep_level_factor
            return max(0, score)


        num_hops = len(path) - 1
        score = self.base_reward - (num_hops * self.hop_penalty)

        # Bonus for reaching deep levels
        max_depth_in_path = 0
        for coord in path:
            if coord.depth > max_depth_in_path:
                max_depth_in_path = coord.depth

        if max_depth_in_path >= self.deep_level_threshold:
            score *= self.deep_level_factor

        # Bonus for connecting strategic start/end points (if provided)
        if strategic_start and path[0] == strategic_start:
            score *= 1.2 # 20% bonus for starting at a strategic point
        if strategic_end and path[-1] == strategic_end:
            score *= 1.2 # 20% bonus for ending at a strategic point
        if strategic_start and path[0] == strategic_start and \
           strategic_end and path[-1] == strategic_end and len(path)>1:
            score *= 1.1 # Additional 10% for connecting both

        return max(0, score) # Ensure score is not negative

    def calculate_path_bonus(self, path: List[AddressedFractalCoordinate],
                             strategic_start: Optional[AddressedFractalCoordinate] = None,
                             strategic_end: Optional[AddressedFractalCoordinate] = None) -> float:
        """
        Calculates the bonus reward for a given path if it's valid and meets criteria.
        """
        if not self.validate_path_connectivity(path):
            return 0.0

        score = self.score_path(path, strategic_start, strategic_end)

        # The score is effectively the reward before ensuring minimum.
        # This can be adjusted based on how "score" vs "reward" is defined.
        # For now, let's say the score is the calculated reward.
        calculated_reward = score

        # Ensure minimum reward if any reward is due
        if calculated_reward > 0:
            final_reward = max(calculated_reward, self.min_reward)
        else:
            final_reward = 0.0

        return round(final_reward, 8)


if __name__ == '__main__':
    assessor = SierpinskiPathAssessor()

    # Test coordinates - need a get_neighbors that allows some paths.
    # The current get_neighbors in geometry_validator.py only returns siblings.
    # So, paths will be very simple for now.

    # Path 1: Simple valid sibling path
    coord_d1p0 = AddressedFractalCoordinate(depth=1, path=(0,))
    coord_d1p1 = AddressedFractalCoordinate(depth=1, path=(1,))
    coord_d1p2 = AddressedFractalCoordinate(depth=1, path=(2,))

    simple_path = [coord_d1p0, coord_d1p1] # Hop: d1p0 -> d1p1
    print(f"--- Path 1: {simple_path} ---")
    is_valid_conn = assessor.validate_path_connectivity(simple_path)
    print(f"Connectivity valid: {is_valid_conn}")
    assert is_valid_conn
    bonus1 = assessor.calculate_path_bonus(simple_path)
    print(f"Bonus for path 1: {bonus1:.4f}")
    # Expected: Base (100) - 1*HopPenalty(1) = 99. Max(99, MinReward(5)) = 99.

    # Path 2: Longer sibling path
    long_sibling_path = [coord_d1p0, coord_d1p1, coord_d1p2] # Hops: d1p0->d1p1, d1p1->d1p2
    print(f"\n--- Path 2: {long_sibling_path} ---")
    # Note: get_neighbors(d1p1) includes d1p0 and d1p2, so d1p1->d1p2 is valid.
    is_valid_conn2 = assessor.validate_path_connectivity(long_sibling_path)
    print(f"Connectivity valid: {is_valid_conn2}")
    assert is_valid_conn2
    bonus2 = assessor.calculate_path_bonus(long_sibling_path)
    print(f"Bonus for path 2: {bonus2:.4f}")
    # Expected: Base (100) - 2*HopPenalty(1) = 98. Max(98, MinReward(5)) = 98.

    # Path 3: Invalid path (non-neighbor)
    coord_d2p00 = AddressedFractalCoordinate(depth=2, path=(0,0)) # Not a sibling of d1p1
    invalid_path = [coord_d1p0, coord_d2p00]
    print(f"\n--- Path 3: {invalid_path} (expected invalid connectivity) ---")
    is_valid_conn3 = assessor.validate_path_connectivity(invalid_path)
    print(f"Connectivity valid: {is_valid_conn3}")
    assert not is_valid_conn3
    bonus3 = assessor.calculate_path_bonus(invalid_path)
    print(f"Bonus for path 3: {bonus3:.4f}")
    assert bonus3 == 0.0

    # Path 4: Path with a void coordinate
    coord_d1p3_void = AddressedFractalCoordinate(depth=1, path=(3,))
    path_with_void = [coord_d1p0, coord_d1p3_void, coord_d1p1]
    print(f"\n--- Path 4: {path_with_void} (contains void) ---")
    is_valid_conn4 = assessor.validate_path_connectivity(path_with_void)
    print(f"Connectivity valid: {is_valid_conn4}") # Will fail because d1p3_void is not solid
    assert not is_valid_conn4
    bonus4 = assessor.calculate_path_bonus(path_with_void)
    print(f"Bonus for path 4: {bonus4:.4f}")
    assert bonus4 == 0.0

    # Path 5: Deep level bonus
    # Need coordinates at depth >= DEEP_LEVEL_BONUS_THRESHOLD (5)
    # And a get_neighbors that works there. For now, can only test siblings.
    coord_d5p0 = AddressedFractalCoordinate(depth=DEEP_LEVEL_BONUS_THRESHOLD, path=(0,)*DEEP_LEVEL_BONUS_THRESHOLD)
    coord_d5p1 = AddressedFractalCoordinate(depth=DEEP_LEVEL_BONUS_THRESHOLD, path=((0,)*(DEEP_LEVEL_BONUS_THRESHOLD-1)) + (1,))
    deep_path = [coord_d5p0, coord_d5p1]
    print(f"\n--- Path 5: {deep_path} (deep path) ---")
    is_valid_conn5 = assessor.validate_path_connectivity(deep_path)
    print(f"Connectivity valid: {is_valid_conn5}")
    assert is_valid_conn5
    bonus5 = assessor.calculate_path_bonus(deep_path)
    print(f"Bonus for path 5: {bonus5:.4f}")
    # Expected: (Base(100) - 1*HopPenalty(1)) * DeepFactor(1.5) = 99 * 1.5 = 148.5. Max(148.5, MinReward(5)) = 148.5

    # Path 6: Strategic connection
    strat_start = coord_d1p0
    strat_end = coord_d1p2
    strategic_path = [coord_d1p0, coord_d1p1, coord_d1p2] # Same as long_sibling_path
    print(f"\n--- Path 6: {strategic_path} (strategic connection) ---")
    bonus6 = assessor.calculate_path_bonus(strategic_path, strategic_start=strat_start, strategic_end=strat_end)
    print(f"Bonus for path 6: {bonus6:.4f}")
    # Expected: (Base(100) - 2*HopPenalty(1)) * StartBonus(1.2) * EndBonus(1.2) * BothBonus(1.1)
    # = 98 * 1.2 * 1.2 * 1.1 = 98 * 1.584 = 155.232. Max(155.232, MinReward(5)) = 155.232

    # Path 7: Path so long penalty makes reward less than min_reward
    # Needs a path of many hops. Max hops before base reward is exhausted by penalty: Base/Penalty = 100/1 = 100 hops.
    # This is hard to construct with current sibling-only get_neighbors.
    # Let's adjust parameters for this test:
    assessor_low_base = SierpinskiPathAssessor(base_reward=10, hop_penalty=3, min_reward=5)
    # Path with 2 hops: [c0,c1,c2]. Reward = 10 - 2*3 = 4. Should become 5.
    bonus7 = assessor_low_base.calculate_path_bonus(long_sibling_path)
    print(f"\n--- Path 7: {long_sibling_path} (low base, testing min_reward) ---")
    print(f"Bonus for path 7: {bonus7:.4f}")
    assert bonus7 == assessor_low_base.min_reward # Expected 5.0

    # Path 8: Single point path (valid)
    single_point_path = [coord_d1p0]
    print(f"\n--- Path 8: {single_point_path} (single point path) ---")
    bonus8 = assessor.calculate_path_bonus(single_point_path)
    print(f"Bonus for Path 8: {bonus8:.4f}")
    # Expected: Base (100). Max(100, MinReward(5)) = 100
    assert bonus8 == assessor.base_reward

    # Path 9: Single point path (strategic)
    bonus9 = assessor.calculate_path_bonus(single_point_path, strategic_start=coord_d1p0, strategic_end=coord_d1p0)
    print(f"\n--- Path 9: {single_point_path} (single strategic point path) ---")
    print(f"Bonus for Path 9: {bonus9:.4f}")
    # Expected: Base (100) * SingleStrategicBonus (1.2) = 120. Max(120, MinReward(5)) = 120
    assert bonus9 == round(assessor.base_reward * 1.2, 8)

    print("\nSierpinskiPathAssessor basic tests finished.")
