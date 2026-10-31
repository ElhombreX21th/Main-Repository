import unittest
from app import FixtureSource, synchronize, retry_fetch, TransientError

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'id':'1','updated_at':'2026-01-01','v':1}, {'id':'2','updated_at':'2026-01-02','v':1}, {'id':'1','updated_at':'2026-01-03','v':2}]
    def test_pages_and_latest_version(self):
        state,n=synchronize(FixtureSource(self.rows),page_size=2)
        self.assertEqual((n,len(state['records'])),(3,2))
        self.assertEqual(state['records']['1']['v'],2)
    def test_retry_recovers(self):
        source=FixtureSource(self.rows,{'0':2})
        state,n=synchronize(source,page_size=2)
        self.assertEqual(n,3)
    def test_retry_exhausts(self):
        with self.assertRaises(TransientError):
            retry_fetch(FixtureSource(self.rows,{'0':3}),'0',2,attempts=3)
    def test_resume_checkpoint(self):
        checkpoint={'cursor':'2','records':{'1':self.rows[0]}}
        state,n=synchronize(FixtureSource(self.rows),checkpoint,page_size=2)
        self.assertEqual(n,1)
        self.assertEqual(state['records']['1']['v'],2)
    def test_reject_bad_record(self):
        with self.assertRaisesRegex(ValueError,'updated_at'):
            synchronize(FixtureSource([{'id':'a'}]))
if __name__ == '__main__':unittest.main()
