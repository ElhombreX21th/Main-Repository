import unittest
from app import classify,redact,triage

class TriageTests(unittest.TestCase):
    def test_integration_label(self):
        self.assertEqual(classify('API webhook','Endpoint integration fails')['category'],'integration')
    def test_critical_always_reviewed(self):
        d=classify('Patient safety','Production down')
        self.assertEqual(d['priority'],'critical')
        self.assertTrue(d['needs_human_review'])
    def test_low_evidence_reviewed(self):
        d=classify('Question','Hello')
        self.assertEqual(d['category'],'general')
        self.assertTrue(d['needs_human_review'])
    def test_redact_email(self):
        self.assertNotIn('abc@example.com',redact('Write abc@example.com'))
    def test_duplicate_rejected(self):
        r={'id':'T1','subject':'s','body':'b'}
        with self.assertRaises(ValueError): triage([r,r])
if __name__=='__main__':unittest.main()
