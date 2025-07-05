import unittest
import time

from fractal_blockchain.mempool.pool import TransactionPool
from fractal_blockchain.blockchain.transactions import Transaction # Using the new Transaction class
from fractal_blockchain.core.addressing import AddressedFractalCoordinate

class TestTransactionPool(unittest.TestCase):

    def setUp(self):
        self.pool = TransactionPool(max_pool_size=10) # Default size for most tests
        self.sender = AddressedFractalCoordinate(1,(0,))
        self.receiver = AddressedFractalCoordinate(1,(1,))

        self.tx1 = Transaction(sender_coord=self.sender, receiver_coord=self.receiver, amount=10, fee=1, nonce=0)
        self.tx2 = Transaction(sender_coord=self.sender, receiver_coord=self.receiver, amount=20, fee=0.5, nonce=1)
        # Corrected path for sender_coord of tx3 to match its depth of 2
        self.tx3 = Transaction(sender_coord=AddressedFractalCoordinate(2,(0,0)), receiver_coord=self.receiver, amount=5, fee=0.2, nonce=0)


    def test_add_transaction_valid(self):
        self.assertTrue(self.pool.add_transaction(self.tx1))
        self.assertEqual(self.pool.get_transaction_count(), 1)
        self.assertEqual(self.pool.get_transaction(self.tx1.id), self.tx1)

    def test_add_transaction_duplicate(self):
        self.pool.add_transaction(self.tx1)
        self.assertFalse(self.pool.add_transaction(self.tx1), "Should not add duplicate transaction")
        self.assertEqual(self.pool.get_transaction_count(), 1)

    def test_add_transaction_invalid_type(self):
        self.assertFalse(self.pool.add_transaction("not_a_transaction")) # type: ignore
        self.assertEqual(self.pool.get_transaction_count(), 0)

    def test_add_transaction_invalid_content(self):
        tx_neg_amount = Transaction(self.sender, self.receiver, -10, 1, 0)
        self.assertFalse(self.pool.add_transaction(tx_neg_amount), "Should not add tx with negative amount")

        tx_neg_fee = Transaction(self.sender, self.receiver, 10, -1, 0)
        self.assertFalse(self.pool.add_transaction(tx_neg_fee), "Should not add tx with negative fee")

        tx_neg_nonce = Transaction(self.sender, self.receiver, 10, 1, -1)
        self.assertFalse(self.pool.add_transaction(tx_neg_nonce), "Should not add tx with negative nonce")
        self.assertEqual(self.pool.get_transaction_count(), 0)


    def test_remove_transaction(self):
        self.pool.add_transaction(self.tx1)
        self.pool.add_transaction(self.tx2)

        removed_tx = self.pool.remove_transaction(self.tx1.id)
        self.assertEqual(removed_tx, self.tx1)
        self.assertEqual(self.pool.get_transaction_count(), 1)
        self.assertIsNone(self.pool.get_transaction(self.tx1.id))
        self.assertIsNotNone(self.pool.get_transaction(self.tx2.id))

        # Remove non-existent
        removed_non_existent = self.pool.remove_transaction("non_existent_id")
        self.assertIsNone(removed_non_existent)
        self.assertEqual(self.pool.get_transaction_count(), 1)

    def test_get_pending_transactions(self):
        self.pool.add_transaction(self.tx1)
        self.pool.add_transaction(self.tx2)
        self.pool.add_transaction(self.tx3)

        # Get all
        all_pending = self.pool.get_pending_transactions()
        self.assertEqual(len(all_pending), 3)
        self.assertIn(self.tx1, all_pending)
        self.assertIn(self.tx2, all_pending)
        self.assertIn(self.tx3, all_pending)

        # Get limited count
        limited_pending = self.pool.get_pending_transactions(count=2)
        self.assertEqual(len(limited_pending), 2)
        # Order depends on dict insertion (Python 3.7+), check contents generally
        self.assertTrue(self.tx1 in limited_pending or self.tx2 in limited_pending or self.tx3 in limited_pending)

        # Get more than available
        more_than_avail = self.pool.get_pending_transactions(count=10)
        self.assertEqual(len(more_than_avail), 3)

        # Empty pool
        self.pool.clear_pool()
        self.assertEqual(len(self.pool.get_pending_transactions()), 0)


    def test_max_pool_size(self):
        small_pool = TransactionPool(max_pool_size=2)
        self.assertTrue(small_pool.add_transaction(self.tx1))
        self.assertTrue(small_pool.add_transaction(self.tx2))
        self.assertEqual(small_pool.get_transaction_count(), 2)

        # Pool is full
        self.assertFalse(small_pool.add_transaction(self.tx3), "Should not add to full pool")
        self.assertEqual(small_pool.get_transaction_count(), 2)
        self.assertIsNone(small_pool.get_transaction(self.tx3.id))

        # Remove one, then add another
        small_pool.remove_transaction(self.tx1.id)
        self.assertEqual(small_pool.get_transaction_count(), 1)
        self.assertTrue(small_pool.add_transaction(self.tx3))
        self.assertEqual(small_pool.get_transaction_count(), 2)
        self.assertIsNotNone(small_pool.get_transaction(self.tx3.id))

    def test_clear_pool(self):
        self.pool.add_transaction(self.tx1)
        self.pool.add_transaction(self.tx2)
        self.assertGreater(self.pool.get_transaction_count(), 0)

        self.pool.clear_pool()
        self.assertEqual(self.pool.get_transaction_count(), 0)
        self.assertIsNone(self.pool.get_transaction(self.tx1.id))
        # Also check if destination map is cleared (indirectly)
        self.assertEqual(len(self.pool.get_transactions_by_destination(self.receiver)), 0)


    def test_get_transactions_by_destination(self):
        dest1 = AddressedFractalCoordinate(2, (0,0))
        dest2 = AddressedFractalCoordinate(2, (0,1))

        tx_to_dest1_a = Transaction(self.sender, dest1, 1, 0.1, 10)
        tx_to_dest1_b = Transaction(self.sender, dest1, 2, 0.1, 11)
        tx_to_dest2 = Transaction(self.sender, dest2, 3, 0.1, 12)
        tx_to_none = Transaction(self.sender, None, 4, 0.1, 13) # No specific destination

        self.pool.add_transaction(tx_to_dest1_a)
        self.pool.add_transaction(tx_to_dest1_b)
        self.pool.add_transaction(tx_to_dest2)
        self.pool.add_transaction(tx_to_none)

        # Check dest1
        txs_dest1 = self.pool.get_transactions_by_destination(dest1)
        self.assertEqual(len(txs_dest1), 2)
        self.assertIn(tx_to_dest1_a, txs_dest1)
        self.assertIn(tx_to_dest1_b, txs_dest1)

        # Check dest2
        txs_dest2 = self.pool.get_transactions_by_destination(dest2)
        self.assertEqual(len(txs_dest2), 1)
        self.assertIn(tx_to_dest2, txs_dest2)

        # Check None destination
        txs_none_dest = self.pool.get_transactions_by_destination(None)
        self.assertEqual(len(txs_none_dest), 1)
        self.assertIn(tx_to_none, txs_none_dest)

        # Check unknown destination
        unknown_dest = AddressedFractalCoordinate(3,(0,0,0))
        txs_unknown = self.pool.get_transactions_by_destination(unknown_dest)
        self.assertEqual(len(txs_unknown), 0)

        # Test after removal
        self.pool.remove_transaction(tx_to_dest1_a.id)
        txs_dest1_after_remove = self.pool.get_transactions_by_destination(dest1)
        self.assertEqual(len(txs_dest1_after_remove), 1)
        self.assertNotIn(tx_to_dest1_a, txs_dest1_after_remove)
        self.assertIn(tx_to_dest1_b, txs_dest1_after_remove)

        # Test after clear
        self.pool.clear_pool()
        self.assertEqual(len(self.pool.get_transactions_by_destination(dest1)), 0)
        self.assertEqual(len(self.pool.get_transactions_by_destination(None)), 0)


if __name__ == '__main__':
    unittest.main()
