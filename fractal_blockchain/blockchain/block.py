# Defines the structure of Blocks in the Fractal Blockchain

from dataclasses import dataclass, field, asdict
import time
import hashlib
import json # For simple serialization to hash
from typing import List, Optional, Dict, Any

from fractal_blockchain.core.addressing import AddressedFractalCoordinate
# Assuming a simple Transaction structure will be defined elsewhere or is basic for now
# from fractal_blockchain.mempool.pool import Transaction # Or similar path

# For now, let's define a placeholder Transaction if not yet available
# from fractal_blockchain.mempool.pool import Transaction # Or similar path
from fractal_blockchain.blockchain.transactions import Transaction # Import new Transaction class


@dataclass
class FractalBlockHeader:
    parent_hash: str
    timestamp: float
    depth: int
    coordinate: AddressedFractalCoordinate # Using the existing AddressedFractalCoordinate
    merkle_root_transactions: Optional[str] = None # Root hash of transactions in the block

    # Links to children: Could be hashes of child blocks, or their coordinates if known pre-linkage
    # Using a dictionary: child_index (0,1,2,3) -> child_block_hash or child_coord_string
    child_block_references: Dict[int, str] = field(default_factory=dict)

    geometric_proof: Optional[bytes] = None # Placeholder for now
    nonce: int = 0 # For PoW or other consensus mechanisms
    # block_hash will be calculated dynamically, not stored directly to avoid inconsistencies
    # Or, it can be stored if it's the hash of all other fields *before* block_hash itself.

    def calculate_hash(self) -> str:
        """Calculates the hash of the block header."""
        # Ensure consistent order and format for hashing
        # Using json.dumps with sort_keys=True for dictionary fields
        # Need a robust way to serialize AddressedFractalCoordinate

        header_data = {
            "parent_hash": self.parent_hash,
            "timestamp": self.timestamp,
            "depth": self.depth,
            # Serialize AddressedFractalCoordinate to a string or consistent dict
            "coordinate_depth": self.coordinate.depth,
            "coordinate_path": list(self.coordinate.path), # Convert tuple to list for JSON
            "merkle_root_transactions": self.merkle_root_transactions,
            "child_block_references": {str(k): v for k,v in sorted(self.child_block_references.items())}, # Ensure sorted dict for hashing
            "geometric_proof": self.geometric_proof.hex() if self.geometric_proof else None,
            "nonce": self.nonce
        }

        # Using json.dumps for serialization. For production, a more compact and canonical
        # binary serialization might be preferred (e.g., protobuf, or custom byte packing).
        header_string = json.dumps(header_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(header_string.encode('utf-8')).hexdigest()

    def to_dict(self):
        # Custom dict conversion to handle AddressedFractalCoordinate if needed for external use
        d = asdict(self)
        d['coordinate'] = {"depth": self.coordinate.depth, "path": list(self.coordinate.path)}
        if self.geometric_proof:
            d['geometric_proof'] = self.geometric_proof.hex()
        return d


@dataclass
class FractalBlock:
    header: FractalBlockHeader
    transactions: List[Transaction] # Use new Transaction class

    @property
    def block_hash(self) -> str:
        """Returns the hash of the block header."""
        return self.header.calculate_hash()

    def to_dict(self):
        return {
            "header": self.header.to_dict(),
            "transactions": [t.to_dict() for t in self.transactions] # Use Transaction's to_dict()
        }


# --- Genesis Block Creation ---
def create_genesis_block(genesis_coord: AddressedFractalCoordinate = AddressedFractalCoordinate(0, tuple())) -> FractalBlock:
    """
    Creates the Genesis Block for the fractal blockchain.
    The Genesis Block is unique as it has no parent.
    Its fractal coordinate is typically the root of the fractal structure.
    """
    if genesis_coord.depth != 0 or genesis_coord.path != tuple():
        # While technically any coord could be a genesis for a sub-chain,
        # the main chain's genesis is usually (0, ()).
        print(f"Warning: Creating a Genesis block at non-standard coordinate {genesis_coord}")

    genesis_header = FractalBlockHeader(
        parent_hash="0" * 64, # No parent
        timestamp=time.time(), # Or a fixed timestamp for the network launch
        depth=genesis_coord.depth,
        coordinate=genesis_coord,
        merkle_root_transactions=None, # No transactions in this simple Genesis
        child_block_references={}, # No children known at genesis creation
        geometric_proof=b"genesis_proof_placeholder",
        nonce=0 # Or a specific genesis nonce
    )

    genesis_block = FractalBlock(
        header=genesis_header,
        transactions=[] # No transactions in this simple Genesis
    )

    # The block_hash is calculated from the header content.
    # print(f"Genesis Block created with hash: {genesis_block.block_hash}")
    return genesis_block


if __name__ == '__main__':
    print("Fractal Block Structure Demo")

    # Create a Genesis Block
    genesis = create_genesis_block()
    print("\nGenesis Block:")
    # print(json.dumps(genesis.to_dict(), indent=2))
    print(f"  Hash: {genesis.block_hash}")
    print(f"  Coordinate: {genesis.header.coordinate}")
    print(f"  Timestamp: {genesis.header.timestamp}")

    # Create a subsequent block (example)
    # Assume some transactions using the new Transaction class
    sender_c = AddressedFractalCoordinate(0, tuple()) # Example sender coord
    receiver_c = AddressedFractalCoordinate(1, (2,)) # Example receiver coord
    tx1 = Transaction(sender_coord=sender_c, receiver_coord=receiver_c, amount=10.0, fee=0.1, nonce=1, signature="sig_tx1")
    tx2 = Transaction(sender_coord=sender_c, receiver_coord=receiver_c, amount=5.0, fee=0.05, nonce=2, signature="sig_tx2")

    # Merkle root of these transaction IDs
    from fractal_blockchain.structures.merkle import build_merkle_tree_from_hashes
    # Note: hash_data is already imported in structures.merkle, but not directly needed here if using tx.id
    tx_ids = [tx.id for tx in [tx1, tx2]] # Use the pre-calculated transaction IDs
    tx_merkle_root_node = build_merkle_tree_from_hashes(tx_ids)
    tx_merkle_root_hash = tx_merkle_root_node.value if tx_merkle_root_node else None

    block1_coord = AddressedFractalCoordinate(depth=1, path=(0,))
    header1 = FractalBlockHeader(
        parent_hash=genesis.block_hash,
        timestamp=time.time() + 10,
        depth=block1_coord.depth,
        coordinate=block1_coord,
        merkle_root_transactions=tx_merkle_root_hash,
        child_block_references={}, # No children known yet
        geometric_proof=b"proof_for_block1",
        nonce=12345
    )
    block1 = FractalBlock(header=header1, transactions=[tx1, tx2])

    print("\nBlock 1:")
    # print(json.dumps(block1.to_dict(), indent=2))
    print(f"  Hash: {block1.block_hash}")
    print(f"  Parent Hash: {block1.header.parent_hash}")
    print(f"  Coordinate: {block1.header.coordinate}")
    print(f"  Num Transactions: {len(block1.transactions)}")
    print(f"  TX Merkle Root: {block1.header.merkle_root_transactions}")

    # Example of child_block_references
    block1.header.child_block_references = {
        0: "hash_of_child0_of_block1", # Child at path (0,0)
        1: "hash_of_child1_of_block1"  # Child at path (0,1)
    }
    # Recalculate hash if mutable fields like child_block_references change how hash is computed
    # The current calculate_hash includes it, so if it changes, hash changes.
    print(f"  Block 1 Hash (after adding child refs): {block1.header.calculate_hash()}")


    print("\nPrompt 9 Block structure definition complete.")
