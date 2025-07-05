import time # For __main__ block example
import math # For potential difficulty conversion later

from fractal_blockchain.core.addressing import AddressedFractalCoordinate, string_to_coord, coord_to_string
from fractal_blockchain.core.geometry_validator import is_valid_addressed_coordinate
from fractal_blockchain.blockchain.block_header import MinimalBlockHeader
from fractal_blockchain.mining.anti_asic_miner import AntiASICMiner
# Ensure all necessary constants are imported from difficulty_adjuster for the __main__ block
from fractal_blockchain.mining.difficulty_adjuster import (
    DifficultyAdjuster,
    DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS,
    TARGET_BLOCK_TIME_SECONDS
)

# For fetching previous block hash (highly simplified for now)
PREVIOUS_BLOCK_HASH_STORE = {"main": "0000000000000000000000000000000000000000000000000000000000000000"} # Genesis prev hash

class MiningCoordinator:
    def __init__(self, difficulty_adjuster: DifficultyAdjuster, previous_block_hash_fetcher=None):
        self.anti_asic_miner = AntiASICMiner()
        self.difficulty_adjuster = difficulty_adjuster

        self.previous_block_hash_fetcher = previous_block_hash_fetcher or (lambda coord: PREVIOUS_BLOCK_HASH_STORE["main"])

    def mine_on_coordinate(self, target_coord: AddressedFractalCoordinate,
                             example_timestamp: int = 1678886400, # Fixed for reproducibility
                             max_nonce_attempts: int = 2**20) -> tuple[str, int, str, MinimalBlockHeader] | None:
        """
        Coordinates the process of mining a block for a specific fractal coordinate.
        Returns: A tuple (found_hash, nonce, algo_name, block_header) if successful, else None.
        """

        # 1. Geometric Validation
        if not is_valid_addressed_coordinate(target_coord):
            print(f"[MiningCoordinator] Error: Target coordinate {target_coord} is not geometrically valid.")
            return None

        if not target_coord.is_solid_path():
            print(f"[MiningCoordinator] Error: Target coordinate {target_coord} is a void path. Mining occurs on solid paths.")
            return None

        print(f"[MiningCoordinator] Target coordinate {target_coord} is valid and solid. Proceeding.")

        # 2. Get Difficulty Target (Simplified)
        current_difficulty_value = self.difficulty_adjuster.get_current_difficulty(
            target_coord.depth,
            coord_to_string(target_coord)
        )
        difficulty_target_prefix = "0" # TODO: Derive this from current_difficulty_value properly
        print(f"[MiningCoordinator] Current difficulty for D:{target_coord.depth} P:{target_coord.path} is {current_difficulty_value:.4f}. Using target prefix: '{difficulty_target_prefix}' (SIMPLIFIED)")

        # 3. Create Block Header
        prev_hash = self.previous_block_hash_fetcher(target_coord)
        header = MinimalBlockHeader.create_example(
            prev_hash=prev_hash,
            coord=target_coord,
            example_timestamp=example_timestamp
        )

        block_data_to_hash = header.serialize_for_hashing()

        # 4. Mine using AntiASICMiner
        print(f"[MiningCoordinator] Starting mining for {target_coord} with header data (pre-nonce): {block_data_to_hash.decode()[:100]}...")

        mining_result = self.anti_asic_miner.find_valid_hash(
            block_data_to_hash,
            target_coord,
            difficulty_target_prefix,
            max_nonce=max_nonce_attempts
        )

        if mining_result:
            found_hash, nonce, algo_name, _ = mining_result
            print(f"[MiningCoordinator] SUCCESS: Found valid hash {found_hash} with nonce {nonce} using {algo_name} for {target_coord}.")
            return found_hash, nonce, algo_name, header
        else:
            print(f"[MiningCoordinator] FAILURE: Could not find valid hash for {target_coord} within {max_nonce_attempts} nonces.")
            return None

if __name__ == '__main__':
    difficulty_adjuster_instance = DifficultyAdjuster()

    sim_time = int(time.time())
    # Populate difficulty history for depth 1 (fast blocks -> higher difficulty)
    for i in range(DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS):
        difficulty_adjuster_instance.record_block_found(1, sim_time + (i * (TARGET_BLOCK_TIME_SECONDS // 2)), f"D:1-P:sim_fast{i}")
    # Populate difficulty history for depth 0 (slow blocks -> lower difficulty)
    for i in range(DIFFICULTY_ADJUSTMENT_INTERVAL_BLOCKS):
        difficulty_adjuster_instance.record_block_found(0, sim_time + (i * (TARGET_BLOCK_TIME_SECONDS * 2)), f"D:0-P:sim_slow{i}")

    coordinator = MiningCoordinator(difficulty_adjuster_instance)

    # Test 1: Valid, solid coordinate (depth 1)
    coord1_solid = AddressedFractalCoordinate(depth=1, path=(0,))
    print(f"\n--- Test Case 1: Mining on valid solid coordinate {coord1_solid} ---")
    result1 = coordinator.mine_on_coordinate(coord1_solid, max_nonce_attempts=65536)
    if result1:
        h, n, algo, head = result1
        print(f"Result 1: Hash={h}, Nonce={n}, Algo={algo}, HeaderTS={head.timestamp}")
    else:
        print("Result 1: Mining failed.")
    assert result1 is not None, "Test Case 1 Failed: Expected successful mining."

    # Test 2: Invalid coordinate (path element > 3, should be caught by AddressedFractalCoordinate)
    print(f"\n--- Test Case 2: Attempting to use structurally invalid coordinate path ---")
    try:
        coord2_invalid_path_element = AddressedFractalCoordinate(depth=1, path=(7,))
        # This next line should ideally not be reached if AFC constructor is robust.
        # If AFC allows it, is_valid_addressed_coordinate in the coordinator should catch it.
        result2 = coordinator.mine_on_coordinate(coord2_invalid_path_element)
        assert result2 is None, "Test Case 2 Failed: Expected mining to fail due to validation or AFC construction."
    except ValueError as e: # This is expected from AddressedFractalCoordinate constructor
        print(f"Correctly caught ValueError from AddressedFractalCoordinate constructor: {e}")
        assert "Path elements must be 0, 1, 2 (child) or 3 (void)" in str(e)

    # Test 3: Valid path but leads to a void (should be rejected by coordinator for mining)
    coord3_void = AddressedFractalCoordinate(depth=1, path=(3,))
    print(f"\n--- Test Case 3: Mining on a void coordinate {coord3_void} ---")
    result3 = coordinator.mine_on_coordinate(coord3_void)
    assert result3 is None, "Test Case 3 Failed: Expected mining to be rejected for void path."

    # Test 4: Valid, solid coordinate at depth 0
    coord4_solid_d0 = AddressedFractalCoordinate(depth=0, path=())
    print(f"\n--- Test Case 4: Mining on valid solid coordinate {coord4_solid_d0} (Depth 0) ---")
    result4 = coordinator.mine_on_coordinate(coord4_solid_d0, max_nonce_attempts=65536)
    if result4:
        h4, n4, algo4, head4 = result4
        print(f"Result 4: Hash={h4}, Nonce={n4}, Algo={algo4}, HeaderTS={head4.timestamp}")
    else:
        print("Result 4: Mining failed for Depth 0.")
    assert result4 is not None, "Test Case 4 Failed: Expected successful mining for Depth 0."

    print("\nMiningCoordinator tests finished.")
