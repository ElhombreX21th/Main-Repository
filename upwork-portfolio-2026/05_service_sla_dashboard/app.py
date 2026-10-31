"""Generate static SLA and repeat-incident HTML dashboard from a work-order CSV."""
import argparse
import csv
import html
import json
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path


def hours_between(start,end):
    return (datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds()/3600


def summarize(rows, sla_hours=None):
    sla_hours=sla_hours or {'critical':4,'high':8,'medium':24,'low':72}
    seen=set();details=[];durations=[]; asset_counts=Counter()
    for r in rows:
        id_=r['ticket_id']
        if id_ in seen: raise ValueError(f'Duplicate ticket {id_}')
        seen.add(id_)
        priority=r['priority'].lower()
        if priority not in sla_hours: raise ValueError(f'Unsupported priority {priority}')
        length=hours_between(r['opened_at'],r['resolved_at'])
        if length<0: raise ValueError('Resolution before opening')
        durations.append(length)
        asset_counts[r['asset_id']]+=1
        details.append({'ticket_id':id_,'asset_id':r['asset_id'],'priority':priority,
                        'resolution_hours':round(length,2),'sla_met':length <= sla_hours[priority]})
    total=len(details);met=sum(d['sla_met'] for d in details)
    return {'tickets':total,'sla_met':met,'sla_breached':total-met,
            'sla_compliance_percent':round(met/total*100,1) if total else None,
            'mean_resolution_hours':round(sum(durations)/total,2) if total else None,
            'repeat_assets':{asset:n for asset,n in sorted(asset_counts.items()) if n>1},
            'details':details}


def render_html(report):
    details=''.join('<tr>'+''.join('<td>'+html.escape(str(row[k]))+'</td>' for k in ('ticket_id','asset_id','priority','resolution_hours','sla_met'))+'</tr>' for row in report['details'])
    pct=report['sla_compliance_percent']
    width=pct if pct is not None else 0
    repeat=', '.join(f'{html.escape(k)} ({n})' for k,n in report['repeat_assets'].items()) or 'None'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Service Operations | SLA Dashboard</title><style>body{{font:16px system-ui;background:#0b1220;color:#f0f5ff;max-width:1000px;margin:40px auto;padding:18px}}h1{{font-size:32px}}.meta{{color:#94a3b8}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px}}.card{{background:#152238;border:1px solid #2c4261;border-radius:12px;padding:22px}}.value{{font-size:32px;font-weight:700}}.meter{{background:#334155;border-radius:12px;overflow:hidden;height:16px}}.meter span{{display:block;width:{width}%;background:#38bdf8;height:100%}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;padding:12px;border-bottom:1px solid #334155}}@media(max-width:550px){{table{{font-size:12px}}}} </style></head><body><p class="meta">PORTFOLIO DEMO / SYNTHETIC DATA</p><h1>Service Operations Overview</h1><div class="grid"><div class="card">Tickets<div class="value">{report['tickets']}</div></div><div class="card">SLA compliance<div class="value">{pct if pct is not None else 'N/A'}%</div><div class="meter"><span></span></div></div><div class="card">Mean resolution<div class="value">{report['mean_resolution_hours'] if report['mean_resolution_hours'] is not None else 'N/A'} h</div></div><div class="card">Breaches<div class="value">{report['sla_breached']}</div></div></div><h2>Repeat assets</h2><p>{repeat}</p><h2>Work orders</h2><table><thead><tr><th>Ticket</th><th>Asset</th><th>Priority</th><th>Resolution h</th><th>SLA met</th></tr></thead><tbody>{details}</tbody></table><p class="meta">Synthetic, non-clinical operational data. No patient/device data.</p></body></html>'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',default=str(Path(__file__).with_name('work_orders.csv')))
    p.add_argument('--output',default=str(Path(__file__).with_name('dashboard.html')))
    args=p.parse_args()
    with open(args.input,newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    report=summarize(rows)
    Path(args.output).write_text(render_html(report),encoding='utf-8')
    Path(args.output).with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"Dashboard generated at {args.output}: {report['tickets']} work orders, {report['sla_breached']} breaches")


if __name__=='__main__':main()
