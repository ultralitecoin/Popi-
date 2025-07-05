# Defines Transaction structures for the Fractal Blockchain

from dataclasses import dataclass, field, asdict
import time
import hashlib
import json
from typing import Optional, Dict, Any

from fractal_blockchain.core.addressing import AddressedFractalCoordinate

@dataclass
class Transaction:
    sender_coord: Optional[AddressedFractalCoordinate] # None for coinbase or certain contract interactions
    receiver_coord: Optional[AddressedFractalCoordinate] # None for contract creation
    amount: float # Using float for now; for financial systems, use Decimal or integer units
    fee: float
    nonce: int # Sender-specific sequence number to prevent replays
    timestamp: float = field(default_factory=time.time)
    transaction_type: str = "standard" # New field for transaction type
    signature: Optional[str] = None # Placeholder for cryptographic signature
    data: Optional[Dict[str, Any]] = None # For smart contract calls, messages, etc.

    # id will be the hash of the transaction content (excluding the id itself)
    id: str = field(init=False, repr=True) # Calculate after initialization

    def __post_init__(self):
        # Calculate and set the transaction ID (hash) after all other fields are set.
        # The 'id' field itself is excluded from the hash calculation.
        self.id = self._calculate_hash()

    def _to_hashable_dict(self) -> Dict[str, Any]:
        """Converts transaction to a dictionary suitable for consistent hashing, excluding 'id'."""
        d = {
            "sender_coord": self.sender_coord.path if self.sender_coord else None, # Path for hashing
            "sender_coord_depth": self.sender_coord.depth if self.sender_coord else None,
            "receiver_coord": self.receiver_coord.path if self.receiver_coord else None, # Path for hashing
            "receiver_coord_depth": self.receiver_coord.depth if self.receiver_coord else None,
            "amount": self.amount,
            "fee": self.fee,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "transaction_type": self.transaction_type, # Added to hashable dict
            # Signature is part of the signed content, so it's part of hash
            "signature": self.signature,
            "data": self.data
        }
        # Filter out None values to ensure consistent hashing if fields are truly optional
        # However, for hashing, even None should be represented consistently.
        # Let's keep None values as they are serialized by json.dumps.
        return d

    def _calculate_hash(self) -> str:
        """Calculates the SHA256 hash of the transaction content."""
        # Exclude 'id' itself from hashing.
        hashable_dict = self._to_hashable_dict()
        # Sort keys for consistent serialization
        tx_string = json.dumps(hashable_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(tx_string.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Converts transaction to a dictionary for general use, including 'id'."""
        d = asdict(self)
        # Convert AddressedFractalCoordinate to a more serializable dict format if present
        if self.sender_coord:
            d['sender_coord'] = {"depth": self.sender_coord.depth, "path": list(self.sender_coord.path)}
        if self.receiver_coord:
            d['receiver_coord'] = {"depth": self.receiver_coord.depth, "path": list(self.receiver_coord.path)}
        return d

    def to_json_serializable(self) -> Dict[str, Any]:
        """For use in Merkle tree, etc. Excludes 'id' as it's derived, includes others."""
        # This is what gets hashed for Merkle root in blocks.
        # It should match what _calculate_hash uses, but without the 'id'.
        # The block's Merkle tree should be over transaction IDs (hashes), or over full transaction contents.
        # If over IDs, then this method is not directly used for that.
        # If over full contents, then this serialization matters.
        # Let's assume block Merkle tree is over transaction *IDs*.
        # So, this method is more for general serialization if needed.
        # The _calculate_hash method defines what makes a TX unique.

        # For Merkle root in block, we typically hash transaction IDs.
        # If we were to hash full transactions, this method would be important.
        # For now, let's align it with to_dict() for block content representation if needed.
        # However, the current block implementation uses PlaceholderTransaction.to_json_serializable()
        # which just returns __dict__. We'll need to update that.
        return self.to_dict() # For now, includes id.

if __name__ == '__main__':
    sender = AddressedFractalCoordinate(1, (0,))
    receiver = AddressedFractalCoordinate(2, (1,2))

    tx1 = Transaction(
        sender_coord=sender,
        receiver_coord=receiver,
        amount=10.0,
        fee=0.1,
        nonce=1,
        signature="sig123",
        data={"message": "hello"}
    )
    print(f"Transaction 1 ID: {tx1.id}")
    print(f"Transaction 1 dict: {json.dumps(tx1.to_dict(), indent=2)}")

    tx2 = Transaction(
        sender_coord=sender, # Same sender
        receiver_coord=receiver,
        amount=10.0,
        fee=0.1,
        nonce=2, # Different nonce
        signature="sig456",
        data={"message": "hello again"}
    )
    print(f"\nTransaction 2 ID: {tx2.id}")
    print(f"Transaction 2 dict: {json.dumps(tx2.to_dict(), indent=2)}")
    assert tx1.id != tx2.id

    tx3_same_as_1_content_diff_ts = Transaction(
        sender_coord=sender,
        receiver_coord=receiver,
        amount=10.0,
        fee=0.1,
        nonce=1, # Same nonce as tx1
        signature="sig123", # Same sig
        data={"message": "hello"}, # Same data
        timestamp=tx1.timestamp + 10 # Different timestamp
    )
    print(f"\nTransaction 3 (diff timestamp from tx1) ID: {tx3_same_as_1_content_diff_ts.id}")
    assert tx1.id != tx3_same_as_1_content_diff_ts.id # Timestamp is part of hash

    # Test transaction without optional coords (e.g. coinbase or special)
    tx4_no_sender = Transaction(
        sender_coord=None,
        receiver_coord=receiver,
        amount=50.0, # Coinbase-like
        fee=0.0,
        nonce=0, # Nonce might be 0 or block height for coinbase
        signature=None # Coinbase not signed by sender
    )
    print(f"\nTransaction 4 (no sender) ID: {tx4_no_sender.id}")
    print(f"Transaction 4 dict: {json.dumps(tx4_no_sender.to_dict(), indent=2)}")

    print("\nTransaction class defined.")
