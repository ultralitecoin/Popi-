# Transaction Pool (Mempool) for the Fractal Blockchain

from typing import Dict, List, Optional, Set

from fractal_blockchain.blockchain.transactions import Transaction
from fractal_blockchain.core.addressing import AddressedFractalCoordinate # Added import

class TransactionPool:
    """
    Manages a pool of unconfirmed transactions.
    """
    def __init__(self, max_pool_size: Optional[int] = None):
        # Store transactions by their ID for quick lookup and to prevent duplicates.
        self._transactions: Dict[str, Transaction] = {}
        # Optional: Store transaction IDs by sender and nonce for replay protection
        # and sender-specific transaction ordering/replacement logic.
        # self._sender_nonce_map: Dict[str, Dict[int, str]] = {} # sender_id -> nonce -> tx_id
        self._destination_coord_map: Dict[Optional[AddressedFractalCoordinate], Set[str]] = {} # For Prompt 12

        self.max_pool_size = max_pool_size # Optional limit on pool size

    def add_transaction(self, tx: Transaction) -> bool:
        """
        Adds a transaction to the pool after basic validation.
        Returns True if added, False otherwise (e.g., duplicate, invalid, pool full).
        """
        if not isinstance(tx, Transaction):
            # print(f"Error: Item to add is not a Transaction object: {type(tx)}")
            return False

        if tx.id in self._transactions:
            # print(f"Transaction {tx.id} already in pool.")
            return False # Duplicate

        # Basic validation (more can be added here or before calling add_transaction)
        if tx.amount < 0:
            # print(f"Transaction {tx.id} has negative amount.")
            return False
        if tx.fee < 0:
            # print(f"Transaction {tx.id} has negative fee.")
            return False
        # Nonce should be non-negative (typically starts at 0 or 1)
        if tx.nonce < 0:
            # print(f"Transaction {tx.id} has negative nonce.")
            return False

        # Check max pool size
        if self.max_pool_size is not None and len(self._transactions) >= self.max_pool_size:
            # Pool is full. Eviction strategy would be needed (e.g., evict lowest fee).
            # For now, just reject.
            # print(f"Transaction pool is full. Cannot add transaction {tx.id}.")
            return False

        self._transactions[tx.id] = tx

        # Optional: Update sender_nonce_map
        # if tx.sender_coord: # Assuming sender_coord can be stringified to a unique sender_id
        #    sender_id = str(tx.sender_coord) # Simplistic sender ID
        #    if sender_id not in self._sender_nonce_map:
        #        self._sender_nonce_map[sender_id] = {}
        #    self._sender_nonce_map[sender_id][tx.nonce] = tx.id

        self._add_to_destination_map(tx) # Add to destination map

        return True

    def remove_transaction(self, tx_id: str) -> Optional[Transaction]:
        """Removes a transaction from the pool by its ID. Returns the removed tx or None."""
        tx = self._transactions.pop(tx_id, None)

        # Optional: Remove from sender_nonce_map if implemented
        # if tx and tx.sender_coord:
        #    sender_id = str(tx.sender_coord)
        #    if sender_id in self._sender_nonce_map and tx.nonce in self._sender_nonce_map[sender_id]:
        #        if self._sender_nonce_map[sender_id][tx.nonce] == tx_id: # Ensure it's the same tx
        #            del self._sender_nonce_map[sender_id][tx.nonce]
        #        if not self._sender_nonce_map[sender_id]: # Clean up empty dict for sender
        #            del self._sender_nonce_map[sender_id]
        if tx:
            self._remove_from_destination_map(tx) # Remove from destination map
        return tx

    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        """Retrieves a transaction by its ID."""
        return self._transactions.get(tx_id)

    def get_pending_transactions(self, count: Optional[int] = None) -> List[Transaction]:
        """
        Returns a list of pending transactions.
        If count is specified, returns at most that many transactions.
        Order might be based on fees, arrival time, etc. (Currently insertion order).
        """
        if count is None:
            return list(self._transactions.values())
        else:
            # This returns 'count' items but order is dict insertion order (Python 3.7+)
            # For proper selection (e.g. highest fee), sorting would be needed.
            return list(self._transactions.values())[:count]

    def get_transaction_count(self) -> int:
        """Returns the number of transactions currently in the pool."""
        return len(self._transactions)

    def clear_pool(self):
        """Removes all transactions from the pool."""
        self._transactions.clear()
        self._destination_coord_map.clear() # Clear the destination map as well
        # if hasattr(self, '_sender_nonce_map'):
        #     self._sender_nonce_map.clear()

    # --- Methods for Prompt 12 (Fractal-Aware Mempool) ---
    # e.g., get_transactions_for_coord(destination_coord: AddressedFractalCoordinate)

    def _add_to_destination_map(self, tx: Transaction):
        """Helper to add transaction to the destination coordinate map."""
        # receiver_coord can be None (e.g. contract creation, special txs)
        dest_coord = tx.receiver_coord
        if dest_coord not in self._destination_coord_map:
            self._destination_coord_map[dest_coord] = set()
        self._destination_coord_map[dest_coord].add(tx.id)

    def _remove_from_destination_map(self, tx: Transaction):
        """Helper to remove transaction from the destination coordinate map."""
        dest_coord = tx.receiver_coord
        if dest_coord in self._destination_coord_map:
            if tx.id in self._destination_coord_map[dest_coord]:
                self._destination_coord_map[dest_coord].remove(tx.id)
                if not self._destination_coord_map[dest_coord]: # Clean up empty set
                    del self._destination_coord_map[dest_coord]

    def get_transactions_by_destination(self, destination_coord: Optional[AddressedFractalCoordinate]) -> List[Transaction]:
        """
        Retrieves all transactions destined for a specific fractal coordinate.
        If destination_coord is None, it retrieves transactions with no specific receiver_coord.
        """
        tx_ids = self._destination_coord_map.get(destination_coord, set())
        return [self._transactions[tx_id] for tx_id in tx_ids if tx_id in self._transactions]


if __name__ == '__main__':
    from fractal_blockchain.core.addressing import AddressedFractalCoordinate
    pool = TransactionPool(max_pool_size=100)

    sender1 = AddressedFractalCoordinate(1, (0,))
    receiver1 = AddressedFractalCoordinate(1, (1,))

    tx1 = Transaction(sender_coord=sender1, receiver_coord=receiver1, amount=10, fee=1, nonce=0)
    tx2 = Transaction(sender_coord=sender1, receiver_coord=receiver1, amount=20, fee=0.5, nonce=1)
    tx3_invalid_amount = Transaction(sender_coord=sender1, receiver_coord=receiver1, amount=-5, fee=1, nonce=2)

    print(f"Adding tx1: {pool.add_transaction(tx1)}")
    print(f"Adding tx2: {pool.add_transaction(tx2)}")
    print(f"Adding tx1 again (duplicate): {pool.add_transaction(tx1)}")
    print(f"Adding tx3 (invalid amount): {pool.add_transaction(tx3_invalid_amount)}")

    print(f"\nPool count: {pool.get_transaction_count()}") # Expected 2
    assert pool.get_transaction_count() == 2

    retrieved_tx1 = pool.get_transaction(tx1.id)
    print(f"Retrieved tx1: {retrieved_tx1.id if retrieved_tx1 else 'Not found'}")
    assert retrieved_tx1 == tx1

    print("\nPending transactions (all):")
    for tx in pool.get_pending_transactions():
        print(f"  ID: {tx.id}, Amount: {tx.amount}, Fee: {tx.fee}")

    print("\nPending transactions (limit 1):")
    for tx in pool.get_pending_transactions(count=1):
        print(f"  ID: {tx.id}, Amount: {tx.amount}, Fee: {tx.fee}")
    assert len(pool.get_pending_transactions(count=1)) <= 1


    removed_tx = pool.remove_transaction(tx2.id)
    print(f"\nRemoved tx2: {removed_tx.id if removed_tx else 'Not found or already removed'}")
    assert removed_tx == tx2
    print(f"Pool count after removal: {pool.get_transaction_count()}") # Expected 1
    assert pool.get_transaction_count() == 1

    # Test max pool size
    pool_small = TransactionPool(max_pool_size=1)
    print(f"\nSmall pool (size 1), adding tx1: {pool_small.add_transaction(tx1)}")
    assert pool_small.get_transaction_count() == 1
    # Try to add another transaction
    tx_another = Transaction(sender_coord=sender1, receiver_coord=receiver1, amount=5, fee=0.2, nonce=3)
    print(f"Small pool, adding another tx: {pool_small.add_transaction(tx_another)}") # Should fail
    assert pool_small.get_transaction_count() == 1 # Still 1
    assert pool_small.get_transaction(tx_another.id) is None


    pool.clear_pool()
    print(f"\nPool count after clear: {pool.get_transaction_count()}")
    assert pool.get_transaction_count() == 0

    print("\nTransactionPool basic implementation complete.")
