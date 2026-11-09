import tempfile
import unittest
from pathlib import Path
from pipeline import queue


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'queue.json'
        self.lock = self.root / 'queue.lock'

    def tx(self, f, now=100):
        return queue.transact(f, self.path, self.lock, now)

    def add(self):
        return self.tx(lambda s, n: queue.enqueue(s, n, 'case', {'case': 'example'}))

    def take(self, now=100):
        return self.tx(lambda s, n: queue.claim(s, n, 'worker', 10, self.root / 'storage', 100), now)

    def test_dedupe_and_conflict(self):
        first = self.add()
        self.assertEqual(first, self.add())
        with self.assertRaises(ValueError):
            self.tx(lambda s, n: queue.enqueue(s, n, 'case', {'case': 'different'}))
        self.assertEqual(len(self.tx(lambda s, n: s)['jobs']), 1)

    def test_paused_stopped_and_single_lease(self):
        self.add()
        self.assertIsNone(self.take())
        self.tx(lambda s, n: s.update(paused=False, stopped=True))
        self.assertIsNone(self.take())
        self.tx(lambda s, n: s.update(stopped=False))
        self.assertIsNotNone(self.take())
        self.assertIsNone(self.take())

    def test_expired_lease_recovery_rejects_stale_receipt(self):
        job_id = self.add()
        self.tx(lambda s, n: s.update(paused=False))
        old = self.take()
        self.assertEqual(self.tx(queue.recover, 110), 1)
        new = self.take(111)
        with self.assertRaises(ValueError):
            self.tx(lambda s, n: queue.finish(s, n, job_id, old['token'], True, {'ok': True}), 112)
        self.assertEqual(self.tx(lambda s, n: queue.finish(s, n, job_id, new['token'], True, {'ok': True}), 112), 'completed')
        receipts = self.tx(lambda s, n: s)['jobs'][0]['receipts']
        self.assertEqual(len(receipts), 2)
        self.assertEqual(receipts[0]['details']['event'], 'lease_expired')

    def test_invalid_disk_limits_are_rejected_even_when_paused(self):
        for budget, reserve in ((0, 0), (-1, 0), (100, -1)):
            with self.assertRaises(ValueError):
                self.tx(lambda s, n: queue.claim(s, n, 'worker', 10, self.root / 'storage', budget, reserve))

    def test_disk_budget_blocks_claim(self):
        self.add()
        self.tx(lambda s, n: s.update(paused=False))
        storage = self.root / 'storage'; storage.mkdir()
        (storage / 'file').write_bytes(b'x' * 100)
        self.assertIsNone(self.take())
        self.assertEqual(self.tx(lambda s, n: s)['jobs'][0]['status'], 'queued')


if __name__ == '__main__': unittest.main()
