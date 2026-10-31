import unittest
from app import audit, render_html

def rec(ident='A', text='hello', label='positive'):
    return {'id':ident,'text':text,'label':label}

class DataQualityTests(unittest.TestCase):
    def test_empty_dataset(self):
        self.assertEqual(audit([])['issues_found'], 0)
    def test_valid_record(self):
        self.assertEqual(audit([rec()])['rows_flagged'], 0)
    def test_missing_label(self):
        self.assertEqual(audit([rec(label='')])['issue_distribution']['missing_label'],1)
    def test_invalid_label(self):
        self.assertEqual(audit([rec(label='unknown')])['issue_distribution']['invalid_label'],1)
    def test_case_normalization(self):
        self.assertEqual(audit([rec(label='POSITIVE')])['issue_distribution']['label_normalization'],1)
    def test_duplicate_id(self):
        a=audit([rec('A','one'),rec('A','two')])
        self.assertEqual(a['issue_distribution']['duplicate_id'],1)
    def test_conflicting_labels(self):
        a=audit([rec('A','one','positive'),rec('A','two','negative')])
        self.assertEqual(a['issue_distribution']['conflicting_labels'],1)
    def test_duplicate_text_casefold(self):
        a=audit([rec('A','Hello World'),rec('B','  HELLO  world  ')])
        self.assertEqual(a['issue_distribution']['duplicate_text'],1)
    def test_missing_id_and_text(self):
        a=audit([rec('', '', 'neutral')])
        self.assertIn('missing_id',a['issue_distribution'])
        self.assertIn('missing_text',a['issue_distribution'])
    def test_html_escapes_input(self):
        a=audit([rec('A','x','<img onerror=alert(1)>')])
        page=render_html(a)
        self.assertNotIn('<img onerror=alert(1)>',page)
        self.assertIn('&lt;img',page)
    def test_counts_unique_flagged_rows(self):
        a=audit([rec('A','same','negative'),rec('A','same','positive')])
        self.assertEqual(a['rows_flagged'],1)

if __name__=='__main__': unittest.main()
