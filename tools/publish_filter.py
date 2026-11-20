"""Pre-publish filter: full private table -> races that the site may show.

    python3 -I tools/publish_filter.py races_full.json publish_rules.json data/races_public.json

Rules (see publish_rules.example.json; keep your real rules file private):
  use_public_column   if true, rows with public == "N" are dropped
  hide_ids            hide by id, optional note
  hide_date_ranges    hide by date range (inclusive)
  hide_sports / hide_tags / hide_countries

Also writes publish_report.md next to the output, listing every hidden race and why.
The `public` column is removed from the output."""
import json, sys, os

src, rules_path, out = sys.argv[1:4]
data = json.load(open(src, encoding='utf-8'))
R = json.load(open(rules_path, encoding='utf-8'))
ids = {h['id']: h.get('note') or '' for h in R.get('hide_ids', [])}
ranges = R.get('hide_date_ranges', [])
sports, tags, ccs = set(R.get('hide_sports', [])), set(R.get('hide_tags', [])), set(R.get('hide_countries', []))


def why(r):
    if R.get('use_public_column', True) and r.get('public') == 'N':
        return 'public = N'
    if r['id'] in ids:
        return 'hide_ids' + (': ' + ids[r['id']] if ids[r['id']] else '')
    for g in ranges:
        if g['from'] <= r['date'] <= g['to']:
            return 'date %s to %s' % (g['from'], g['to']) + (': ' + g['note'] if g.get('note') else '')
    if r.get('sport') in sports:
        return 'hide_sports: ' + r['sport']
    if r.get('country') in ccs:
        return 'hide_countries: ' + r['country']
    t = tags.intersection(r.get('tags') or [])
    if t:
        return 'hide_tags: ' + ', '.join(sorted(t))
    return None


keep, hidden = [], []
for r in data['races']:
    w = why(r)
    if w:
        hidden.append((r, w))
    else:
        r = dict(r)
        r.pop('public', None)
        keep.append(r)

json.dump({'generated': data.get('generated'), 'races': keep}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
rep = os.path.join(os.path.dirname(os.path.abspath(out)), 'publish_report.md')
with open(rep, 'w', encoding='utf-8') as f:
    f.write('# Publish report\n\n%d races, %d published, %d hidden.\n\n| Date | Race | Reason |\n|---|---|---|\n' % (len(data['races']), len(keep), len(hidden)))
    for r, w in hidden:
        f.write('| %s | %s | %s |\n' % (r['date'], r['name'].get('en') or r['name'].get('zh') or r['id'], w))
print('total', len(data['races']), 'publish', len(keep), 'hidden', len(hidden), '->', out, rep)
