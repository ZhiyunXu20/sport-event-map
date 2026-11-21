import json
import subprocess
import sys
import os

import publish_filter as pf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def races(*specs):
    out = []
    for n, (date, extra) in enumerate(specs):
        r = {'id': '%s-%03d' % (date.replace('-', ''), n), 'date': date, 'name': {'en': 'Race %d' % n},
             'sport': 'road', 'country': 'GB', 'tags': []}
        r.update(extra)
        out.append(r)
    return {'generated': 'test', 'races': out}


def test_no_rules_publishes_everything():
    data = races(('2025-01-01', {}), ('2025-02-01', {}))
    keep, hidden = pf.apply_rules(data, {})
    assert len(keep) == 2 and hidden == []


def test_public_column_is_used_and_removed():
    data = races(('2025-01-01', {'public': 'N'}), ('2025-02-01', {'public': 'Y'}))
    keep, hidden = pf.apply_rules(data, {'use_public_column': True})
    assert [r['date'] for r in keep] == ['2025-02-01']
    assert 'public' not in keep[0]
    assert hidden[0][1] == 'public = N'


def test_public_column_can_be_ignored():
    data = races(('2025-01-01', {'public': 'N'}))
    keep, _ = pf.apply_rules(data, {'use_public_column': False})
    assert len(keep) == 1 and 'public' not in keep[0]


def test_input_is_not_modified():
    data = races(('2025-01-01', {'public': 'Y'}))
    pf.apply_rules(data, {})
    assert data['races'][0]['public'] == 'Y'


def test_hide_by_id_with_note():
    data = races(('2025-01-01', {}), ('2025-02-01', {}))
    rid = data['races'][0]['id']
    keep, hidden = pf.apply_rules(data, {'hide_ids': [{'id': rid, 'note': 'private'}]})
    assert len(keep) == 1
    assert hidden[0][1] == 'hide_ids: private'


def test_date_range_is_inclusive():
    data = races(('2024-11-30', {}), ('2024-12-01', {}), ('2025-07-31', {}), ('2025-08-01', {}))
    keep, hidden = pf.apply_rules(data, {'hide_date_ranges': [{'from': '2024-12-01', 'to': '2025-07-31'}]})
    assert [r['date'] for r in keep] == ['2024-11-30', '2025-08-01']
    assert len(hidden) == 2


def test_hide_by_sport_country_and_tag():
    data = races(('2025-01-01', {'sport': 'swim'}), ('2025-01-02', {'country': 'CN'}),
                 ('2025-01-03', {'tags': ['club', 'fun']}), ('2025-01-04', {}))
    keep, hidden = pf.apply_rules(data, {'hide_sports': ['swim'], 'hide_countries': ['CN'], 'hide_tags': ['club']})
    assert [r['date'] for r in keep] == ['2025-01-04']
    assert [w for _, w in hidden] == ['hide_sports: swim', 'hide_countries: CN', 'hide_tags: club']


def test_report_lists_hidden_races():
    data = races(('2025-01-01', {'public': 'N'}), ('2025-02-01', {}))
    keep, hidden = pf.apply_rules(data, {})
    md = pf.report_markdown(len(data['races']), keep, hidden)
    assert '2 races, 1 published, 1 hidden.' in md
    assert '| 2025-01-01 | Race 0 | public = N |' in md


def test_cli_end_to_end(tmp_path, sample):
    sample['races'][0]['public'] = 'N'
    src, rules, out = tmp_path / 'full.json', tmp_path / 'rules.json', tmp_path / 'out' / 'races.json'
    out.parent.mkdir()
    src.write_text(json.dumps(sample), encoding='utf-8')
    rules.write_text(json.dumps({'use_public_column': True}), encoding='utf-8')
    subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'tools', 'publish_filter.py'), str(src), str(rules), str(out)],
                   check=True, capture_output=True)
    result = json.loads(out.read_text(encoding='utf-8'))
    assert len(result['races']) == len(sample['races']) - 1
    assert (out.parent / 'publish_report.md').exists()
