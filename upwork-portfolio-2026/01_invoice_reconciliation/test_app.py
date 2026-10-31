import unittest
from datetime import date
from decimal import Decimal
from app import reconcile, money

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.invoices = [{'invoice_id':'I-1', 'customer':'C', 'amount':'100.00', 'due_date':'2026-10-01'}]
    def test_exact_match(self):
        r=reconcile(self.invoices,[{'invoice_id':'I-1','amount':'100.00'}],date(2026,10,31))
        self.assertEqual(r['invoices'][0]['status'],'paid')
    def test_unpaid_overdue(self):
        self.assertEqual(reconcile(self.invoices,[],date(2026,10,31))['invoices'][0]['status'],'overdue')
    def test_partial_and_unmatched(self):
        r=reconcile(self.invoices,[{'invoice_id':'I-1','amount':'25.00'}, {'invoice_id':'X','amount':'2'}],date(2026,10,31))
        self.assertEqual(r['invoices'][0]['status'],'partial_overdue')
        self.assertEqual(len(r['unmatched_payments']),1)
    def test_duplicates_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate invoice'):
            reconcile(self.invoices*2,[],date(2026,10,31))
    def test_precise_decimal(self):
        self.assertEqual(money('0.1') + money('0.2'),Decimal('0.30'))
if __name__ == '__main__': unittest.main()
