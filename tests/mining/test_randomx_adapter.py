import unittest
import sys
import os

# Adjust path to import from the root directory of the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fractal_blockchain.mining.randomx_adapter import simulate_randomx_hash # FractalCoordinate removed from here
from fractal_blockchain.core.addressing import AddressedFractalCoordinate # Use this instead

class TestRandomXAdapter(unittest.TestCase):

    def test_hash_consistency(self):
        """Test that the hash is consistent for the same inputs."""
        coord = AddressedFractalCoordinate(depth=3, path=(0, 1, 2)) # Path is tuple
        data = b"test_data"
        # Using minimal memory/iterations for speed in unit tests
        hash1 = simulate_randomx_hash(data, coord, memory_size_mb=1, iterations=10)
        hash2 = simulate_randomx_hash(data, coord, memory_size_mb=1, iterations=10)
        self.assertEqual(hash1, hash2)

    def test_hash_changes_with_data(self):
        """Test that the hash changes if the input data changes."""
        coord = AddressedFractalCoordinate(depth=3, path=(0, 1, 2))
        data1 = b"test_data_1"
        data2 = b"test_data_2"
        hash1 = simulate_randomx_hash(data1, coord, memory_size_mb=1, iterations=10)
        hash2 = simulate_randomx_hash(data2, coord, memory_size_mb=1, iterations=10)
        self.assertNotEqual(hash1, hash2)

    def test_hash_changes_with_fractal_coordinate_path(self):
        """Test that the hash changes if the fractal coordinate path changes."""
        coord1 = AddressedFractalCoordinate(depth=3, path=(0, 1, 2))
        coord2 = AddressedFractalCoordinate(depth=3, path=(0, 1, 1)) # Different path
        data = b"test_data"
        hash1 = simulate_randomx_hash(data, coord1, memory_size_mb=1, iterations=10)
        hash2 = simulate_randomx_hash(data, coord2, memory_size_mb=1, iterations=10)
        self.assertNotEqual(hash1, hash2)

    def test_hash_changes_with_fractal_coordinate_depth(self):
        """Test that the hash changes if the fractal coordinate depth changes."""
        coord1 = AddressedFractalCoordinate(depth=3, path=(0, 1, 2))
        # Path length must match depth for AddressedFractalCoordinate
        coord2 = AddressedFractalCoordinate(depth=4, path=(0, 1, 2, 0)) # Different depth, adjusted path
        data = b"test_data"
        hash1 = simulate_randomx_hash(data, coord1, memory_size_mb=1, iterations=10)
        hash2 = simulate_randomx_hash(data, coord2, memory_size_mb=1, iterations=10)
        self.assertNotEqual(hash1, hash2)

    def test_invalid_parameters(self):
        """Test behavior with invalid parameters."""
        coord = AddressedFractalCoordinate(depth=3, path=(0, 1, 2))
        data = b"test_data"
        with self.assertRaises(ValueError):
            simulate_randomx_hash(data, coord, memory_size_mb=0, iterations=10)
        with self.assertRaises(ValueError):
            simulate_randomx_hash(data, coord, memory_size_mb=1, iterations=0)
        with self.assertRaises(ValueError):
            simulate_randomx_hash(data, coord, memory_size_mb=-1, iterations=10)
        with self.assertRaises(ValueError):
            simulate_randomx_hash(data, coord, memory_size_mb=1, iterations=-10)

    def test_addressed_fractal_coordinate_usage_in_hash(self):
        """Test that AddressedFractalCoordinate is used and affects the hash."""
        # This test implicitly confirms that coord_to_string is used internally by simulate_randomx_hash
        # by checking if different coordinates produce different hashes, which is already covered.
        # The main purpose here is to ensure it runs with AddressedFractalCoordinate type.
        coord = AddressedFractalCoordinate(depth=2, path=(1,0))
        data = b"test_data_for_AFC"
        try:
            simulate_randomx_hash(data, coord, memory_size_mb=1, iterations=5)
        except Exception as e:
            self.fail(f"simulate_randomx_hash failed with AddressedFractalCoordinate: {e}")

    # A very basic test for memory usage.
    # This is hard to test accurately without deeper inspection tools or specific library features.
    # We're checking if it runs without error for a slightly larger, yet still small, memory footprint.
    def test_memory_usage_simulation_runs(self):
        """Test that the simulation runs with a slightly larger memory configuration."""
        coord = AddressedFractalCoordinate(depth=3, path=(0, 1, 2))
        data = b"test_data_memory"
        try:
            # Using 2MB and 20 iterations - still small but more than minimal.
            # If this causes MemoryError on a constrained test runner, it might need adjustment.
            simulate_randomx_hash(data, coord, memory_size_mb=2, iterations=20)
        except MemoryError:
            self.fail("simulate_randomx_hash raised MemoryError with 2MB/20 iterations, "
                      "which might indicate an issue or very constrained test environment.")
        except Exception as e:
            self.fail(f"simulate_randomx_hash raised an unexpected exception: {e}")

if __name__ == '__main__':
    # Create dummy __init__.py in mining and tests if they don't exist for discovery
    # This is a common workaround for Python's module discovery in some structures.

    # Ensure fractal_blockchain/mining/__init__.py exists
    mining_init_path = os.path.join(os.path.dirname(__file__), '..', '..', 'fractal_blockchain', 'mining', '__init__.py')
    if not os.path.exists(mining_init_path):
        with open(mining_init_path, 'w') as f:
            pass # Create empty file

    # Ensure tests/mining/__init__.py exists
    test_mining_init_path = os.path.join(os.path.dirname(__file__), '__init__.py')
    if not os.path.exists(test_mining_init_path):
        with open(test_mining_init_path, 'w') as f:
            pass # Create empty file

    # Ensure tests/__init__.py exists
    test_init_path = os.path.join(os.path.dirname(__file__), '..', '__init__.py')
    if not os.path.exists(test_init_path):
        with open(test_init_path, 'w') as f:
            pass # Create empty file

    # Ensure fractal_blockchain/__init__.py exists
    fb_init_path = os.path.join(os.path.dirname(__file__), '..', '..', 'fractal_blockchain', '__init__.py')
    if not os.path.exists(fb_init_path):
        with open(fb_init_path, 'w') as f:
            pass

    unittest.main()
