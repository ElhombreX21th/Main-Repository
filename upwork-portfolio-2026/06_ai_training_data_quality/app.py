"""AI training data QA portfolio demo. Synthetic data, standard Python only."""
import argparse
import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path

ALLOWED_LABELS = {'positive', 'negative', 'neutral'}

def audit(rows):
    records = list(rows)
    problems = []
    seen_ids = defaultdict(list)
    seen_texts = defaultdict(list)
    label_counts = Counter()
    for index, rec in enumerate(records, 1):
        ident = str(rec.get('id', '')).strip()
        raw_text = str(rec.get('text', '')).strip()
        label = str(rec.get('label', '')).strip()
        canonical = label.casefold()
        if not ident:
            problems.append({'row': index, 'issue': 'missing_id', 'detail': 'ID is blank'})
        else:
            seen_ids[ident].append((index, canonical))
        if not raw_text:
            problems.append({'row': index, 'issue': 'missing_text', 'detail': 'Text is blank'})
        else:
            seen_texts[' '.join(raw_text.casefold().split())].append(index)
        if not label:
            problems.append({'row': index, 'issue': 'missing_label', 'detail': 'Label is blank'})
        elif canonical not in ALLOWED_LABELS:
            problems.append({'row': index, 'issue': 'invalid_label', 'detail': f'Unrecognized label: {label[:60]}'})
        else:
            label_counts[canonical] += 1
            if label != canonical:
                problems.append({'row': index, 'issue': 'label_normalization', 'detail': f'{label} -> {canonical}'})
    for ident, entries in sorted(seen_ids.items()):
        if len(entries) > 1:
            problems.append({'row': entries[1][0], 'issue': 'duplicate_id', 'detail': f'{ident}: rows {", ".join(str(x[0]) for x in entries)}'})
            labels = {x[1] for x in entries if x[1] in ALLOWED_LABELS}
            if len(labels) > 1:
                problems.append({'row': entries[1][0], 'issue': 'conflicting_labels', 'detail': f'{ident}: {", ".join(sorted(labels))}'})
    for text, rows_with_text in seen_texts.items():
        if len(rows_with_text) > 1:
            problems.append({'row': rows_with_text[1], 'issue': 'duplicate_text', 'detail': 'Repeated text at rows ' + ', '.join(map(str, rows_with_text))})
    problems.sort(key=lambda p: (p['row'], p['issue']))
    issue_counts = dict(sorted(Counter(p['issue'] for p in problems).items()))
    return {'source_record_count': len(records), 'issues_found': len(problems),
            'rows_flagged': len({p['row'] for p in problems}),
            'label_distribution': dict(sorted(label_counts.items())),
            'issue_distribution': issue_counts, 'findings': problems,
            'notes': 'Prototype quality audit; human validation required for semantic correctness.'}

def render_html(report):
    metrics = [('Input records', report['source_record_count']), ('Issues found', report['issues_found']),
               ('Rows flagged', report['rows_flagged']), ('Distinct issue types', len(report['issue_distribution']))]
    cards = ''.join(f'<article><span>{html.escape(str(name))}</span><strong>{value}</strong></article>' for name, value in metrics)
    findings = ''.join('<tr><td>' + str(p['row']) + '</td><td>' + html.escape(p['issue'].replace('_', ' ').title()) + '</td><td>' + html.escape(p['detail']) + '</td></tr>' for p in report['findings'])
    counts = ''.join('<tr><td>' + html.escape(k.replace('_', ' ').title()) + '</td><td>' + str(v) + '</td></tr>' for k, v in report['issue_distribution'].items())
    labels = ''.join('<tr><td>' + html.escape(k.title()) + '</td><td>' + str(v) + '</td></tr>' for k, v in report['label_distribution'].items())
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AI Dataset Quality Audit</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0c1120;color:#eff5ff;font:16px system-ui,Arial;padding:36px}}main{{max-width:1200px;margin:auto}}h1{{font-size:35px;margin:14px 0 4px}}p{{color:#9fb1cf}}.tag{{display:inline-block;border:1px solid #334763;padding:7px 12px;border-radius:30px;font-size:12px}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}}article,.box{{border:1px solid #30425e;background:#151f36;border-radius:14px;padding:18px}}article span{{display:block;color:#9fb1cf;font-size:13px}}article strong{{font-size:34px;display:block;margin-top:12px}}section{{display:grid;grid-template-columns:2fr 1fr;gap:14px}}h2{{font-size:17px;margin:0 0 15px}}table{{width:100%;border-collapse:collapse}}td,th{{text-align:left;padding:10px 7px;border-bottom:1px solid #2a3955;font-size:13px}}th{{color:#b8cbeb}}.subbox{{margin-bottom:14px}}footer{{margin-top:18px;font-size:12px;color:#9fb1cf}}@media(max-width:800px){{.cards{{grid-template-columns:1fr 1fr}}section{{grid-template-columns:1fr}}}}
</style></head><body><main><div class="tag">INDEPENDENT PORTFOLIO DEMO — SYNTHETIC TRAINING DATA</div><h1>AI Dataset Quality Audit</h1><p>Data validation, deduplication, label consistency and structured QA reporting</p><div class="cards">{cards}</div><section><div class="box"><h2>Quality Findings</h2><table><thead><tr><th>Row</th><th>Issue</th><th>Explanation</th></tr></thead><tbody>{findings}</tbody></table></div><div><div class="box subbox"><h2>Issue Categories</h2><table><tbody>{counts}</tbody></table></div><div class="box"><h2>Label Distribution</h2><table><tbody>{labels}</tbody></table></div></div></section><footer>Data are fictional. Automated checks are deterministic; no ML-model evaluation, semantic correctness guarantee, or paid-client deployment is claimed.</footer></main></body></html>'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default=str(Path(__file__).with_name('sample_training_data.csv')))
    parser.add_argument('--json', default=str(Path(__file__).with_name('quality_report.json')))
    parser.add_argument('--html', default=str(Path(__file__).with_name('quality_report.html')))
    args = parser.parse_args()
    with open(args.input, newline='', encoding='utf-8-sig') as fh:
        source = list(csv.DictReader(fh))
    report = audit(source)
    Path(args.json).write_text(json.dumps(report, indent=2), encoding='utf-8')
    Path(args.html).write_text(render_html(report), encoding='utf-8')
    print(f"Audited {report['source_record_count']} records; {report['issues_found']} issues; {report['rows_flagged']} rows flagged")

if __name__ == '__main__':
    main()
