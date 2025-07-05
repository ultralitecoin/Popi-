from dataclasses import dataclass, astuple, fields
import hashlib
import time # Keep for actual timestamping if needed, but not for uncontrolled example default

# Use AddressedFractalCoordinate as it's the more complete one
from fractal_blockchain.core.addressing import AddressedFractalCoordinate, coord_to_string, string_to_coord

@dataclass(frozen=True)
class MinimalBlockHeader:
    previous_block_hash: str
    merkle_root: str
    timestamp: int # Timestamp will be an integer
    fractal_coord_str: str # String representation of AddressedFractalCoordinate
    # Nonce is handled by the miner separately

    def serialize_for_hashing(self) -> bytes:
        """
        Serializes the header fields (excluding nonce) into a byte string for hashing.
        Order matters for consistent hashing.
        """
        # Ensure consistent order of fields for serialization
        data_tuple = (
            self.previous_block_hash,
            self.merkle_root,
            self.timestamp,
            self.fractal_coord_str
        )
        # Simple concatenation for simulation. Real systems use more robust serialization.
        return "|".join(map(str, data_tuple)).encode('utf-8')

    def get_fractal_coordinate(self) -> AddressedFractalCoordinate | None:
        """ Utility to parse the fractal_coord_str back into an object. """
        # Ensure allow_void_paths=True if your system uses voids in AddressedFractalCoordinate paths
        return string_to_coord(self.fractal_coord_str, allow_void_paths=True)


    @classmethod
    def create_example(cls, prev_hash: str, coord: AddressedFractalCoordinate, example_timestamp: int = 1678886400): # Default to a fixed timestamp
        """
        Creates an example MinimalBlockHeader.
        Timestamp is fixed for reproducibility in examples unless specified.
        """
        return cls(
            previous_block_hash=prev_hash,
            merkle_root="dummy_merkle_root_" + hashlib.sha256(coord_to_string(coord).encode()).hexdigest()[:10], # Make it unique per coord
            timestamp=example_timestamp,
            fractal_coord_str=coord_to_string(coord)
        )

if __name__ == '__main__':
    # Example usage:
    coord_obj = AddressedFractalCoordinate(depth=2, path=(1,2)) # Path can include 0,1,2,3

    # Create header with default example timestamp
    header1 = MinimalBlockHeader.create_example(
        prev_hash="0000abcdef",
        coord=coord_obj
    )
    print(f"Header 1 (default ts): {header1}")

    # Create header with a specific timestamp
    header2 = MinimalBlockHeader.create_example(
        prev_hash="0000abcdef",
        coord=coord_obj,
        example_timestamp=1234567890
    )
    print(f"Header 2 (specific ts): {header2}")

    serialized_data_for_miner = header2.serialize_for_hashing()
    print(f"Serialized data for miner (from header2, pre-nonce): {serialized_data_for_miner}")

    retrieved_coord = header2.get_fractal_coordinate()
    print(f"Retrieved coordinate object from header2: {retrieved_coord}, Expected: {coord_obj}")
    assert retrieved_coord == coord_obj

    # Example of how miner would use the serialized data and coordinate object
    nonce = 123
    nonce_bytes = nonce.to_bytes(8, 'big')
    full_input_for_hash_function = serialized_data_for_miner + nonce_bytes # Miner appends nonce
    print(f"Full input for hash function (with nonce {nonce}): {full_input_for_hash_function}")

    # The hashing functions in anti_asic_miner.py (simulate_randomx_hash, etc.) expect:
    # - input_data: bytes (this would be `full_input_for_hash_function` or equivalent)
    # - fractal_coord: FractalCoordinate object (this would be `retrieved_coord`)
    #
    # The AntiASICMiner's `mine_block_attempt` prepares `full_input_data` by combining
    # `block_data_to_hash` (which is `header.serialize_for_hashing()`) and `nonce_bytes`.
    # It then passes this `full_input_data` and the `fractal_coord` object to the algo_func.
    # This seems consistent.
