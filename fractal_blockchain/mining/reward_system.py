import math

# --- Configuration for Reward System ---

# The base reward for mining a block at depth 0.
BASE_REWARD = 50.0  # Example: 50 units of the cryptocurrency

# The multiplier applied to the reward for each successive depth level.
# A value of 1.1 means each depth level gets 10% more reward than the previous level's base.
# This creates the exponential increase.
DEPTH_REWARD_MULTIPLIER = 1.1

# Maximum depth to cap the exponential reward growth, to prevent runaway inflation
# and to keep rewards within a manageable range. After this depth, reward might become constant
# or increase much more slowly. This helps with "economic balance".
MAX_REWARD_CALCULATION_DEPTH = 100 # Example: After depth 100, reward calculation changes.

# Optional: A minimum reward, regardless of depth (e.g. for very shallow, less incentivized depths if multiplier was <1)
MINIMUM_REWARD = 1.0


class FractalRewardSystem:
    def __init__(self,
                 base_reward: float = BASE_REWARD,
                 depth_multiplier: float = DEPTH_REWARD_MULTIPLIER,
                 max_calc_depth: int = MAX_REWARD_CALCULATION_DEPTH,
                 min_reward: float = MINIMUM_REWARD):
        if base_reward <= 0:
            raise ValueError("Base reward must be positive.")
        if depth_multiplier <= 0: # Could be 1 for flat, but <1 would decrease with depth
            raise ValueError("Depth multiplier must be positive.")
        if max_calc_depth < 0:
            raise ValueError("Max calculation depth cannot be negative.")
        if min_reward < 0: # Can be 0 if no minimum is desired
            raise ValueError("Minimum reward cannot be negative.")

        self.base_reward = base_reward
        self.depth_multiplier = depth_multiplier
        self.max_calc_depth = max_calc_depth
        self.min_reward = min_reward

    def calculate_block_reward(self, fractal_depth: int) -> float:
        """
        Calculates the mining reward for a block found at a given fractal_depth.

        Args:
            fractal_depth: The depth of the fractal coordinate where the block was mined.
                           Depth 0 is the Genesis Triad level.

        Returns:
            The calculated reward amount.
        """
        if fractal_depth < 0:
            # Or raise ValueError, but typically depth is non-negative
            effective_depth = 0
        else:
            effective_depth = fractal_depth

        # Apply exponential increase up to max_calc_depth
        # Reward = BASE_REWARD * (MULTIPLIER ^ effective_depth_for_calculation)

        depth_for_calculation = min(effective_depth, self.max_calc_depth)

        current_reward = self.base_reward * (self.depth_multiplier ** depth_for_calculation)

        # If actual depth exceeds max_calc_depth, we might apply a different rule.
        # For example, a slower increase or a constant addition.
        # Here, we'll just use the reward calculated at max_calc_depth for any depth beyond it.
        # This helps in maintaining some economic balance by capping unbounded exponential growth.
        if effective_depth > self.max_calc_depth:
            # Option 1: Cap at max_calc_depth's reward (as implemented by min() above)
            # Option 2: Add a small flat bonus for depths beyond max_calc_depth
            #   reward_at_max_cap = self.base_reward * (self.depth_multiplier ** self.max_calc_depth)
            #   extra_depth_bonus = (effective_depth - self.max_calc_depth) * 0.1 # Small linear bonus
            #   current_reward = reward_at_max_cap + extra_depth_bonus
            pass # Current logic already handles capping due to depth_for_calculation


        # Ensure reward does not fall below a minimum.
        final_reward = max(current_reward, self.min_reward)

        # For very deep levels where multiplier^depth could become astronomically large,
        # further capping might be needed, e.g. MAX_POSSIBLE_REWARD.
        # Python floats handle large numbers, but for blockchain consistency, fixed-point arithmetic is better.
        # This is a simulation, so float is fine.

        return round(final_reward, 8) # Round to a typical number of decimal places for crypto


if __name__ == '__main__':
    reward_system = FractalRewardSystem()

    print(f"Reward System Config: Base={reward_system.base_reward}, Multiplier={reward_system.depth_multiplier}, MaxCalcDepth={reward_system.max_calc_depth}\n")

    depths_to_test = [0, 1, 2, 5, 10, 50, reward_system.max_calc_depth, reward_system.max_calc_depth + 1, reward_system.max_calc_depth + 20]
    for depth in depths_to_test:
        reward = reward_system.calculate_block_reward(depth)
        print(f"Calculated reward for depth {depth:3}: {reward:.4f}")

    print("\n--- Test with different multiplier (e.g., higher) ---")
    reward_system_high_mul = FractalRewardSystem(depth_multiplier=1.5)
    for depth in [0, 1, 2, 3, 5, 10]: # Max depth will be reached quickly
        reward = reward_system_high_mul.calculate_block_reward(depth)
        print(f"Calculated reward for depth {depth:3} (mul={reward_system_high_mul.depth_multiplier}): {reward:.4f}")

    print("\n--- Test with very low base reward and multiplier to check MINIMUM_REWARD ---")
    reward_system_low = FractalRewardSystem(base_reward=0.1, depth_multiplier=1.01, min_reward=1.0) # min_reward is 1.0
    for depth in [0, 1, 10, 50]:
        reward = reward_system_low.calculate_block_reward(depth)
        print(f"Calculated reward for depth {depth:3} (low settings): {reward:.4f}")

    print("\n--- Test with negative depth (should default to depth 0 behavior) ---")
    reward_neg_depth = reward_system.calculate_block_reward(-5)
    reward_zero_depth = reward_system.calculate_block_reward(0)
    print(f"Calculated reward for depth -5: {reward_neg_depth:.4f} (should be same as depth 0: {reward_zero_depth:.4f})")
