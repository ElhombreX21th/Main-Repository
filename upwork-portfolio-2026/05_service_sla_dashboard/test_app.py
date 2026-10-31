import unittest
from app import summarize,render_html

def row(ticket='1',asset='A',priority='high',start='2026-01-01T10:00:00',end='2026-01-01T14:00:00'):
    return {'ticket_id':ticket,'asset_id':asset,'priority':priority,'opened_at':start,'resolved_at':end}

class SlaTests(unittest.TestCase):
    def test_within_sla(self):
        x=summarize([row()])
        self.assertEqual(x['sla_compliance_percent'],100)
    def test_breach(self):
        x=summarize([row(end='2026-01-02T14:00:00')])
        self.assertEqual(x['sla_breached'],1)
    def test_repeated_assets(self):
        x=summarize([row('1'),row('2')])
        self.assertEqual(x['repeat_assets']['A'],2)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):summarize([row(),row()])
    def test_html_safe(self):
        x=summarize([row(ticket='<script>alert(1)</script>')])
        page=render_html(x)
        self.assertNotIn('<script>alert(1)</script>',page)
        self.assertIn('&lt;script&gt;',page)
if __name__=='__main__':unittest.main()
