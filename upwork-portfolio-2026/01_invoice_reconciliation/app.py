"""Invoice-to-payment reconciliation demo (synthetic data). Standard library only."""
import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))

def money(value):
    try:
        return Decimal(str(value).strip()).quantize(Decimal('0.01'))
    except InvalidOperation as exc:
        raise ValueError(f'Invalid monetary value: {value}') from exc

def reconcile(invoices, payments, as_of, tolerance=Decimal('0.01')):
    """Match payments by invoice ID, surface duplicates/unmatched payments."""
    seen = set()
    by_invoice = defaultdict(list)
    for p in payments:
        by_invoice[p['invoice_id']].append(p)
    details = []
    totals = defaultdict(int)
    for inv in invoices:
        ref = inv['invoice_id']
        if ref in seen:
            raise ValueError(f'Duplicate invoice ID: {ref}')
        seen.add(ref)
        amount = money(inv['amount'])
        paid = sum((money(p['amount']) for p in by_invoice[ref]), Decimal('0'))
        remaining = amount - paid
        overdue = date.fromisoformat(inv['due_date']) < as_of
        if remaining < -tolerance:
            status = 'overpaid'
        elif abs(remaining) <= tolerance:
            status = 'paid'
        elif paid > 0:
            status = 'partial_overdue' if overdue else 'partial'
        else:
            status = 'overdue' if overdue else 'unpaid'
        totals[status] += 1
        details.append({'invoice_id': ref, 'customer': inv['customer'],
                        'due_date': inv['due_date'], 'amount': str(amount),
                        'paid': str(paid.quantize(Decimal('0.01'))),
                        'outstanding': str(remaining.quantize(Decimal('0.01'))),
                        'status': status})
    unmatched = [dict(p) for p in payments if p['invoice_id'] not in seen]
    return {'as_of': as_of.isoformat(), 'summary': dict(sorted(totals.items())),
            'invoices': details, 'unmatched_payments': unmatched}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--invoices', default=str(Path(__file__).with_name('invoices.csv')))
    parser.add_argument('--payments', default=str(Path(__file__).with_name('payments.csv')))
    parser.add_argument('--as-of', default='2026-10-31')
    parser.add_argument('--output', default=str(Path(__file__).with_name('report.json')))
    args = parser.parse_args()
    result = reconcile(read_csv(args.invoices), read_csv(args.payments), date.fromisoformat(args.as_of))
    Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"Reconciled {len(result['invoices'])} invoices; "+
          f"unmatched payments: {len(result['unmatched_payments'])}; output: {args.output}")

if __name__ == '__main__':
    main()
