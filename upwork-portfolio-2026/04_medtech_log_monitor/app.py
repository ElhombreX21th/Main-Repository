"""Vendor-neutral medical equipment log analytics on synthetic events."""
import argparse
import csv
import json
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path

def parse_time(value):
    return datetime.fromisoformat(value.replace('Z','+00:00'))

def analyze(events):
    """Track fault trends and close/open fault windows by asset and code."""
    events=sorted(events,key=lambda x:parse_time(x['timestamp']))
    active={}
    counts=Counter()
    durations=defaultdict(list)
    timeline=[]
    for e in events:
        timestamp=parse_time(e['timestamp'])
        asset=e['asset_id'];code=e['code'];kind=e['event'].upper()
        key=(asset,code)
        if kind=='FAULT':
            counts[key]+=1
            if key not in active:
                active[key]=timestamp
            timeline.append({'asset':asset,'code':code,'event':'FAULT','timestamp':timestamp.isoformat()})
        elif kind=='RESTORED':
            if key not in active:
                timeline.append({'asset':asset,'code':code,'event':'ORPHAN_RESTORE','timestamp':timestamp.isoformat()})
                continue
            delta=(timestamp-active.pop(key)).total_seconds()/60
            if delta < 0: raise ValueError('Restored before fault')
            durations[key].append(round(delta,2))
            timeline.append({'asset':asset,'code':code,'event':'RESTORED','downtime_min':round(delta,2)})
        else:
            raise ValueError(f'Unknown event {kind}')
    per_code=[]
    for key,n in sorted(counts.items()):
        mins=durations[key]
        per_code.append({'asset_id':key[0],'fault_code':key[1],'fault_count':n,
                         'resolved_count':len(mins),'mean_repair_minutes':round(sum(mins)/len(mins),2) if mins else None,
                         'open_fault':key in active})
    return {'faults':per_code,'open_faults':[{'asset_id':k[0],'code':k[1]} for k in sorted(active)],'timeline':timeline}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',default=str(Path(__file__).with_name('synthetic_events.csv')))
    p.add_argument('--output',default=str(Path(__file__).with_name('analysis.json')))
    args=p.parse_args()
    with open(args.input,newline='',encoding='utf-8') as fh: rows=list(csv.DictReader(fh))
    result=analyze(rows)
    Path(args.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f"Analyzed {len(rows)} events, {len(result['faults'])} fault families, {len(result['open_faults'])} unresolved")

if __name__=='__main__':main()
