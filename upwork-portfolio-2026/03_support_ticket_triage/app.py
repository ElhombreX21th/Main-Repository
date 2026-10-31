"""Explainable support triage baseline: classification, risk, and PII redaction."""
import argparse
import csv
import json
import re
from pathlib import Path

RULES={
  'access': ('login','password','access denied','unauthorized','permission'),
  'billing': ('invoice','charge','refund','payment','subscription'),
  'integration': ('api','webhook','endpoint','integration','sync'),
  'reliability': ('crash','outage','downtime','unavailable','error 500'),
}
CRITICAL=('patient safety','production down','data loss','entire site offline')
HIGH=('urgent','blocked','outage','cannot work','severe')
EMAIL=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE=re.compile(r'(?<!\d)(?:\+?\d[\d()\s.-]{8,}\d)(?!\d)')

def redact(text):
    return PHONE.sub('[PHONE]', EMAIL.sub('[EMAIL]', text))

def classify(subject, body):
    text=(subject+' '+body).lower()
    counts={name:sum(1 for keyword in terms if keyword in text) for name,terms in RULES.items()}
    ranked=sorted(counts.items(),key=lambda x:(-x[1],x[0]))
    best,score=ranked[0]
    category=best if score else 'general'
    priority='critical' if any(w in text for w in CRITICAL) else 'high' if any(w in text for w in HIGH) else 'normal'
    tie=len([1 for _,v in counts.items() if v==score])>1
    review=score<2 or tie or priority=='critical'
    return {'category':category, 'priority':priority,'evidence_keywords':score,
            'needs_human_review':review,'summary':redact(subject.strip())[:120]}

def triage(rows):
    result=[]
    seen=set()
    for row in rows:
        ticket_id=row['id'].strip()
        if not ticket_id or ticket_id in seen:
            raise ValueError('Empty/duplicate ticket ID')
        seen.add(ticket_id)
        result.append({'id':ticket_id,**classify(row['subject'],row['body'])})
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',default=str(Path(__file__).with_name('tickets.csv')))
    p.add_argument('--output',default=str(Path(__file__).with_name('triage.json')))
    args=p.parse_args()
    with open(args.input,newline='',encoding='utf-8') as fh:
        rows=list(csv.DictReader(fh))
    data=triage(rows)
    Path(args.output).write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('Triaged',len(data),'tickets; human review:',sum(x['needs_human_review'] for x in data))

if __name__=='__main__':main()
