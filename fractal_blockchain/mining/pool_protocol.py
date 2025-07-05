from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
import time
import hashlib

from fractal_blockchain.core.addressing import AddressedFractalCoordinate, coord_to_string
from fractal_blockchain.mining.reward_system import FractalRewardSystem # For block rewards
from fractal_blockchain.mining.difficulty_adjuster import DifficultyAdjuster # For understanding network difficulty


# --- Pool Configuration & Data Structures ---

# Pool difficulty is typically much lower than network difficulty.
# For simulation, let's assume a pool sets a fixed "number of leading zeros" target for shares.
# This can be varied per fractal depth by the pool.
DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX = "0" # Very easy for shares, e.g., hash must start with "0"

@dataclass(frozen=True)
class PoolShare:
    """Represents a share submitted by a miner to the pool."""
    miner_id: str
    fractal_coord: AddressedFractalCoordinate # The coordinate this share is for
    nonce: int
    mined_hash: str # The hash found by the miner for this share
    timestamp: float = field(default_factory=time.time)
    # The pool might assign a 'weight' or 'value' to this share based on fractal_coord and pool's target for it.
    share_weight: float = 1.0 # Default weight, can be adjusted by pool based on share's origin

@dataclass
class MinerContribution:
    """Tracks a miner's contribution to the pool."""
    miner_id: str
    total_weighted_shares: float = 0.0
    # For PPLNS, would also store recent shares. For PPS, might store unpaid amount.
    # For proportional, total_weighted_shares in the current round is key.

    def add_share_weight(self, weight: float):
        self.total_weighted_shares += weight

    def reset_for_round(self):
        self.total_weighted_shares = 0.0


class FractalMiningPool:
    def __init__(self, reward_system: FractalRewardSystem, difficulty_adjuster: DifficultyAdjuster, pool_id: str = "default_pool"):
        self.pool_id = pool_id
        self.reward_system = reward_system
        self.difficulty_adjuster = difficulty_adjuster # To understand network difficulty context

        self.miners: Dict[str, MinerContribution] = {} # miner_id -> MinerContribution

        # For a Proportional or PPLNS system, shares are typically tracked per "round"
        # A round ends when the pool finds a block.
        self.current_round_shares: List[PoolShare] = []
        self.total_weighted_shares_this_round: float = 0.0

        # Pool's target difficulty for shares (can be dynamic per fractal coordinate)
        # For simplicity, a function that returns a prefix string like "0", "00"
        self.pool_share_difficulty_target_func = lambda coord: DEFAULT_POOL_SHARE_DIFFICULTY_PREFIX

        # Store of payouts (simplified)
        self.payouts: Dict[str, float] = {} # miner_id -> total_paid_out

    def register_miner(self, miner_id: str):
        if miner_id not in self.miners:
            self.miners[miner_id] = MinerContribution(miner_id=miner_id)
            print(f"[Pool-{self.pool_id}] Miner {miner_id} registered.")
        else:
            print(f"[Pool-{self.pool_id}] Miner {miner_id} already registered.")

    def get_pool_share_difficulty_prefix(self, fractal_coord: AddressedFractalCoordinate) -> str:
        """
        Determines the pool's target difficulty (as a hash prefix) for shares on a given fractal coordinate.
        Pools can set this dynamically. Deeper/harder fractal levels might have easier share targets
        to encourage participation, or harder ones if they only want high-quality shares.
        """
        # Example: Deeper coordinates might have slightly easier share targets at the pool level
        # to ensure miners can submit shares even if network difficulty is high.
        # This is a placeholder for more complex pool-side difficulty logic.
        base_prefix = self.pool_share_difficulty_target_func(fractal_coord)
        # if fractal_coord.depth > 5:
        #     return base_prefix # No change, or could make it easier like removing a '0' if base_prefix is "00"
        return base_prefix

    def calculate_share_weight(self, share_coord: AddressedFractalCoordinate) -> float:
        """
        Calculates the weight/value of a share based on its fractal coordinate.
        Shares from deeper/harder coordinates should contribute more.
        This could be proportional to the network difficulty of the share's coordinate.
        """
        # Using difficulty_adjuster to get an idea of the network difficulty for this coordinate's depth
        # This is a proxy for the "value" of work done at this coordinate.
        # A share's weight could be proportional to the network difficulty of its coordinate.
        # network_diff_at_coord = self.difficulty_adjuster.get_current_difficulty(share_coord.depth, coord_to_string(share_coord))
        # For simulation, let's use a simpler scheme: base weight + bonus for depth.
        # Weight = 1.0 for depth 0, +0.1 for each depth level.
        weight = 1.0 + (share_coord.depth * 0.5) # Example: Deeper shares are linearly more valuable to the pool
        # This should ideally be tied to the actual network difficulty target for that coordinate.
        # A share represents 1 / PoolDifficulty work. Its value in finding a block is related to NetworkDifficulty.
        # So, value ~ NetworkDifficulty / PoolDifficulty.
        # If PoolDifficulty is uniform (e.g. "0" prefix for all shares), then value ~ NetworkDifficulty.
        # The network_diff_at_coord from difficulty_adjuster is a good proxy.
        network_difficulty_metric = self.difficulty_adjuster.get_current_difficulty(share_coord.depth, coord_to_string(share_coord))
        # Normalize or scale this metric. Let's assume it's > 0. A base difficulty (e.g. depth 0) might be 1.0.
        # Weight could be network_difficulty_metric / base_pool_difficulty_reference
        # For now, using the simpler depth-based weight:
        return max(0.1, weight) # Ensure non-zero weight


    def submit_share(self, miner_id: str, fractal_coord: AddressedFractalCoordinate, nonce: int, mined_hash: str):
        if miner_id not in self.miners:
            print(f"[Pool-{self.pool_id}] Miner {miner_id} not registered. Share rejected.")
            return False

        # 1. Validate the share against the pool's difficulty target for this coordinate
        share_target_prefix = self.get_pool_share_difficulty_prefix(fractal_coord)
        if not mined_hash.startswith(share_target_prefix):
            print(f"[Pool-{self.pool_id}] Share from {miner_id} for {fractal_coord} (hash: {mined_hash}) rejected: Does not meet pool difficulty '{share_target_prefix}'.")
            return False

        # (Optional) Further validation: was this nonce+coord already submitted? Is coord valid for pool targeting?

        # 2. Calculate share weight
        weight = self.calculate_share_weight(fractal_coord)

        share = PoolShare(miner_id=miner_id, fractal_coord=fractal_coord, nonce=nonce, mined_hash=mined_hash, share_weight=weight)

        self.current_round_shares.append(share)
        self.miners[miner_id].add_share_weight(weight)
        self.total_weighted_shares_this_round += weight

        print(f"[Pool-{self.pool_id}] Valid share accepted from {miner_id} for {fractal_coord} (Hash: {mined_hash}, Weight: {weight:.2f}). Total round shares: {self.total_weighted_shares_this_round:.2f}.")
        return True

    def block_found_by_pool(self, block_fractal_coord: AddressedFractalCoordinate, block_finder_miner_id: Optional[str]):
        """
        Called when the pool (one of its miners) successfully mines a network block.
        Distributes rewards for the current round and starts a new round.
        """
        actual_block_reward = self.reward_system.calculate_block_reward(block_fractal_coord.depth)
        print(f"\n[Pool-{self.pool_id}] BLOCK FOUND on {block_fractal_coord}! Total network reward: {actual_block_reward:.4f}")
        print(f"  Block likely found by share from miner: {block_finder_miner_id if block_finder_miner_id else 'Pool directly (solo effort within pool)'}")
        print(f"  Distributing reward based on {self.total_weighted_shares_this_round:.2f} total weighted shares this round.")

        if self.total_weighted_shares_this_round == 0:
            print(f"[Pool-{self.pool_id}] No shares in this round. Reward not distributed (or goes to pool operator).")
            self._start_new_round()
            return

        # Proportional reward distribution
        for miner_id, contribution_data in self.miners.items():
            if contribution_data.total_weighted_shares > 0:
                proportion = contribution_data.total_weighted_shares / self.total_weighted_shares_this_round
                miner_reward = actual_block_reward * proportion

                # Simulate payout (in a real system, this would go to balances/wallets)
                self.payouts[miner_id] = self.payouts.get(miner_id, 0.0) + miner_reward
                print(f"  - Miner {miner_id}: {contribution_data.total_weighted_shares:.2f} weighted shares ({proportion*100:.2f}%) -> Reward: {miner_reward:.4f}")

        self._start_new_round()

    def _start_new_round(self):
        print(f"[Pool-{self.pool_id}] Starting new mining round.")
        self.current_round_shares = []
        self.total_weighted_shares_this_round = 0.0
        for miner_id in self.miners:
            self.miners[miner_id].reset_for_round()

    def get_miner_payouts(self, miner_id: str) -> float:
        return self.payouts.get(miner_id, 0.0)


if __name__ == '__main__':
    # Setup dependencies for pool
    reward_sys = FractalRewardSystem()
    diff_adj = DifficultyAdjuster() # Using default for simplicity

    # Simulate some difficulty history for diff_adj
    sim_time = int(time.time())
    for d in range(3): # Depths 0, 1, 2
        for i in range(10): # Some blocks
            diff_adj.record_block_found(d, sim_time + i*60, f"D:{d}-P:sim{i}")

    pool = FractalMiningPool(reward_system=reward_sys, difficulty_adjuster=diff_adj)

    # Register miners
    pool.register_miner("miner1")
    pool.register_miner("miner2")

    # Simulate share submissions
    coord_d0 = AddressedFractalCoordinate(depth=0, path=())
    coord_d1 = AddressedFractalCoordinate(depth=1, path=(0,))
    coord_d2 = AddressedFractalCoordinate(depth=2, path=(0,0))

    # Miner 1 submits shares mostly at depth 0 and 1
    pool.submit_share("miner1", coord_d0, 101, "0hash_m1_d0_s1") # Valid for prefix "0"
    pool.submit_share("miner1", coord_d0, 102, "0hash_m1_d0_s2")
    pool.submit_share("miner1", coord_d1, 201, "0hash_m1_d1_s1")
    pool.submit_share("miner1", coord_d1, 202, "1hash_m1_d1_s2_fail") # Invalid share (no "0" prefix)

    # Miner 2 submits shares mostly at depth 1 and 2
    pool.submit_share("miner2", coord_d1, 301, "0hash_m2_d1_s1")
    pool.submit_share("miner2", coord_d2, 401, "0hash_m2_d2_s1")
    pool.submit_share("miner2", coord_d2, 402, "0hash_m2_d2_s2")

    # Assume pool finds a block (e.g., one of miner2's shares for coord_d2 was also a network block solution)
    # The block_finder_miner_id is informational for this simulation.
    pool.block_found_by_pool(block_fractal_coord=coord_d2, block_finder_miner_id="miner2")

    print("\nMiner Payouts after round 1:")
    print(f"  Miner1: {pool.get_miner_payouts('miner1'):.4f}")
    print(f"  Miner2: {pool.get_miner_payouts('miner2'):.4f}")

    # Start a new round and submit more shares
    print("\n--- Round 2 ---")
    pool.submit_share("miner1", coord_d2, 501, "0hash_m1_d2_s3_r2") # Miner1 tries deeper
    pool.submit_share("miner2", coord_d0, 601, "0hash_m2_d0_s3_r2") # Miner2 tries shallower

    pool.block_found_by_pool(block_fractal_coord=coord_d0, block_finder_miner_id="miner2")

    print("\nMiner Payouts after round 2:")
    print(f"  Miner1: {pool.get_miner_payouts('miner1'):.4f}") # Should be cumulative
    print(f"  Miner2: {pool.get_miner_payouts('miner2'):.4f}")

    # Test share rejection for unregistered miner
    print("\n--- Test Unregistered Miner ---")
    pool.submit_share("miner3_unreg", coord_d0, 701, "0hash_m3_d0_s1")


    print("\nFractalMiningPool simulation finished.")
