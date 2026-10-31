import unittest
from app import analyze

def event(ts,asset='A',kind='FAULT',code='F'):
    return {'timestamp':ts,'asset_id':asset,'event':kind,'code':code}

class MonitorTests(unittest.TestCase):
    def test_downtime(self):
        e=[event('2026-01-01T00:00:00Z'),event('2026-01-01T00:25:00Z',kind='RESTORED')]
        self.assertEqual(analyze(e)['faults'][0]['mean_repair_minutes'],25)
    def test_open_fault(self):
        self.assertEqual(len(analyze([event('2026-01-01T00:00:00Z')])['open_faults']),1)
    def test_orphan_recovery(self):
        self.assertEqual(analyze([event('2026-01-01T00:00:00Z',kind='RESTORED')])['timeline'][0]['event'],'ORPHAN_RESTORE')
    def test_sorted_input(self):
        e=[event('2026-01-01T00:05:00Z',kind='RESTORED'),event('2026-01-01T00:00:00Z')]
        self.assertEqual(analyze(e)['faults'][0]['mean_repair_minutes'],5)
    def test_invalid_event_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unknown event'):
            analyze([event('2026-01-01T00:00:00Z',kind='BOGUS')])
if __name__=='__main__':unittest.main()
