# Fractal Depth Calculator for Difficulty and Rewards

from typing import Any

# Prompt 4: Implement fractal depth calculator.
# - Algorithm to calculate mining difficulty and reward scaling based on depth from Genesis.
# - Exponential increase in difficulty and reward halving at set depth intervals.
# - Implement formulas (e.g., `difficulty = base_difficulty * factor^depth`).
# - Adaptive adjustment based on hash rate distribution (more complex, might be a placeholder function signature initially).
# - Reward halving and dynamic adjustment for tokenomics.

class DepthCalculator:
    def __init__(self,
                 base_difficulty: float = 1.0,
                 difficulty_exp_factor: float = 2.0, # Difficulty doubles each depth level
                 base_reward: float = 50.0,
                 reward_halving_interval: int = 4, # Reward halves every N levels of depth
                 reward_min_value: float = 0.00000001 # Smallest possible reward
                ):
        if base_difficulty <= 0:
            raise ValueError("Base difficulty must be positive.")
        if difficulty_exp_factor <= 0:
            raise ValueError("Difficulty exponential factor must be positive.")
        if base_reward < 0:
            raise ValueError("Base reward cannot be negative.")
        if reward_halving_interval <= 0:
            raise ValueError("Reward halving interval must be a positive integer.")
        if reward_min_value < 0:
             raise ValueError("Minimum reward value cannot be negative.")

        self.base_difficulty = base_difficulty
        self.difficulty_exp_factor = difficulty_exp_factor
        self.base_reward = base_reward
        self.reward_halving_interval = reward_halving_interval
        self.reward_min_value = reward_min_value

    def calculate_difficulty(self, depth: int, current_network_hashrate_at_depth: Any = None) -> float:
        """
        Calculates the mining difficulty for a given depth.
        Optionally considers network hashrate for adaptive adjustments (placeholder).
        """
        if depth < 0:
            raise ValueError("Depth cannot be negative.")

        # Basic exponential difficulty scaling
        difficulty = self.base_difficulty * (self.difficulty_exp_factor ** depth)

        # Placeholder for adaptive adjustment based on hashrate
        if current_network_hashrate_at_depth is not None:
            # This logic would be complex:
            # - Compare current_network_hashrate_at_depth to a target block time or issuance rate for that depth.
            # - Adjust difficulty up or down.
            # For now, we just acknowledge the parameter.
            pass

        return difficulty

    def calculate_reward(self, depth: int) -> float:
        """
        Calculates the mining reward for a given depth.
        Implements reward halving at specified depth intervals.
        """
        if depth < 0:
            raise ValueError("Depth cannot be negative.")

        # Calculate how many halving periods have passed
        num_halvings = depth // self.reward_halving_interval

        reward = self.base_reward / (2 ** num_halvings)

        # Ensure reward does not fall below a minimum threshold
        return max(reward, self.reward_min_value)

    def get_difficulty_and_reward(self, depth: int, current_network_hashrate_at_depth: Any = None) -> tuple[float, float]:
        """
        Convenience function to get both difficulty and reward for a given depth.
        """
        difficulty = self.calculate_difficulty(depth, current_network_hashrate_at_depth)
        reward = self.calculate_reward(depth)
        return difficulty, reward


if __name__ == '__main__':
    calculator = DepthCalculator(
        base_difficulty=10.0,
        difficulty_exp_factor=1.5,
        base_reward=100.0,
        reward_halving_interval=2,
        reward_min_value=0.1
    )

    print("Depth | Difficulty | Reward")
    print("------|------------|--------")
    for d in range(10):
        diff = calculator.calculate_difficulty(d)
        # Example with adaptive hashrate (not implemented, so diff will be same)
        # diff_adaptive = calculator.calculate_difficulty(d, current_network_hashrate_at_depth=1000)
        rew = calculator.calculate_reward(d)
        print(f"{d: <5} | {diff: <10.2f} | {rew: <6.2f}")

    # Test minimum reward
    print("\nTesting minimum reward clamping:")
    deep_depth = 20 # Should trigger multiple halvings
    rew_deep = calculator.calculate_reward(deep_depth)
    # Base 100, interval 2. Depth 20 -> 10 halvings. 100 / 2^10 = 100 / 1024 approx 0.097
    # Since min_reward is 0.1, it should be clamped to 0.1
    print(f"Reward at depth {deep_depth}: {rew_deep} (Expected to be clamped at {calculator.reward_min_value})")
    assert rew_deep == calculator.reward_min_value

    # Test negative depth
    try:
        calculator.calculate_difficulty(-1)
    except ValueError as e:
        print(f"\nCorrectly caught error for negative depth in difficulty: {e}")
    try:
        calculator.calculate_reward(-1)
    except ValueError as e:
        print(f"Correctly caught error for negative depth in reward: {e}")

    # Test constructor validation
    try:
        DepthCalculator(base_difficulty=0)
    except ValueError as e:
        print(f"Correctly caught constructor error: {e}")
    try:
        DepthCalculator(reward_halving_interval=0)
    except ValueError as e:
        print(f"Correctly caught constructor error: {e}")

    print("\nPrompt 4 DepthCalculator initial implementation seems fine.")
