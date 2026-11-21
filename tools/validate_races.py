"""Check a races JSON file before it is published.

    python3 -I tools/validate_races.py examples/races.sample.json [more files...]

Exits with status 1 if any race has an error, so CI can block a bad dataset.
Checks:
  - top level is {"races": [...]} and every id is unique
  - required fields: id, date, name, lat, lng, geo.path (see README)
  - date is a real YYYY-MM-DD date; lat/lng are in range
  - sport, category and tags have text in assets/i18n.json, so the page never shows a raw key
  - geo.path matches the boundary files in assets/geo/ (when a file for that top-level area exists);
    geo.path[0] is the map's top-level area and may differ from `country`
  - links are http(s) URLs; numbers such as distance_km are not negative
Warnings (do not fail the run) are printed for things that are allowed but worth a look.
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_DIR = os.path.join(ROOT, 'assets', 'geo')
I18N = os.path.join(ROOT, 'assets', 'i18n.json')

ID_RE = re.compile(r'^\d{8}-\d{3}$')
LOC_PRECISION = {'strava_start', 'strava_leg', 'manual_start', 'venue', 'city'}
LEGS = {'swim', 'bike', 'run', None}


def load_i18n_keys(path=I18N):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return set(data.get('en', {}))


_geo_cache = {}


def load_units(name):
    """Return (prov ids, unit ids) for assets/geo/<name>.json, or None if there is no such file."""
    if name not in _geo_cache:
        path = os.path.join(GEO_DIR, name + '.json')
        if not os.path.exists(path):
            _geo_cache[name] = None
        else:
            with open(path, encoding='utf-8') as f:
                topo = json.load(f)
            provs, ids = set(), set()
            for obj in topo.get('objects', {}).values():
                for g in obj.get('geometries', []):
                    p = g.get('properties') or {}
                    if p.get('prov'):
                        provs.add(p['prov'])
                    if p.get('id'):
                        ids.add(p['id'])
            _geo_cache[name] = (provs, ids)
    return _geo_cache[name]


def is_url(v):
    return isinstance(v, str) and re.match(r'^https?://\S+$', v) is not None


def check_race(r, i18n_keys, key_names=None):
    """Return (errors, warnings) for one race dict."""
    errors, warnings = [], []
    if not isinstance(r, dict):
        return ['race is not an object'], []

    for k in ('id', 'date', 'name', 'lat', 'lng', 'geo'):
        if r.get(k) in (None, '', {}):
            errors.append('missing ' + k)

    rid = r.get('id')
    if isinstance(rid, str) and not ID_RE.match(rid):
        warnings.append('id %r is not in the usual YYYYMMDD-NNN form' % rid)

    date = r.get('date')
    if isinstance(date, str):
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            errors.append('date %r is not a real YYYY-MM-DD date' % date)
    elif date is not None:
        errors.append('date must be a string')

    name = r.get('name')
    if name is not None and not (isinstance(name, dict) and (name.get('en') or name.get('zh'))):
        errors.append('name needs an "en" or "zh" value')

    for k, lo, hi in (('lat', -90, 90), ('lng', -180, 180)):
        v = r.get(k)
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            errors.append('%s must be a number' % k)
        elif not lo <= v <= hi:
            errors.append('%s %s is out of range' % (k, v))

    for k in ('distance_km', 'elev_m'):
        v = r.get(k)
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0):
            errors.append('%s must be a non-negative number or null' % k)

    for k in ('sport', 'category'):
        v = r.get(k)
        if v is not None and '%s.%s' % (k, v) not in i18n_keys:
            errors.append('%s %r has no text in assets/i18n.json' % (k, v))
    for t in r.get('tags') or []:
        if 'tag.' + t not in i18n_keys:
            warnings.append('tag %r has no text in assets/i18n.json' % t)

    lp = r.get('loc_precision')
    if lp is not None and lp not in LOC_PRECISION:
        errors.append('loc_precision %r is not one of %s' % (lp, sorted(LOC_PRECISION)))

    geo_errors, geo_warnings = check_geo(r, key_names or {})
    errors += geo_errors
    warnings += geo_warnings
    errors += check_links(r.get('links'))
    return errors, warnings


def check_geo(r, key_names):
    """Return (errors, warnings). key_names is the dataset's optional "names" map for district keys."""
    geo = r.get('geo')
    if not geo:
        return [], []
    path = geo.get('path') if isinstance(geo, dict) else None
    if not isinstance(path, list) or not 1 <= len(path) <= 4 or not all(isinstance(p, str) and p for p in path):
        return ['geo.path must be a list of 1 to 4 area keys'], []
    errors, warnings = [], []
    units = load_units('units-' + path[0])
    if units:
        provs, ids = units
        if len(path) > 1 and path[1] not in provs:
            errors.append('first-level area %r is not in assets/geo/units-%s.json' % (path[1], path[0]))
        if len(path) > 2 and path[2] not in ids:
            errors.append('second-level area %r is not in assets/geo/units-%s.json' % (path[2], path[0]))
    if len(path) > 3:
        districts = load_units('districts-' + path[0])
        # A district key is fine if it has an outline or a name in the dataset's "names" map.
        if path[3] not in key_names and not (districts and path[3] in districts[1]):
            warnings.append('district %r has no outline in assets/geo/ and no entry in "names"' % path[3])
    return errors, warnings


def check_links(links):
    if links is None:
        return []
    if not isinstance(links, dict):
        return ['links must be an object']
    errors = []
    for k in ('website', 'strava'):
        v = links.get(k)
        if v is not None and not is_url(v):
            errors.append('links.%s is not an http(s) URL' % k)
    legs = links.get('strava_legs')
    if legs is not None:
        if not isinstance(legs, list):
            errors.append('links.strava_legs must be a list or null')
        else:
            for n, leg in enumerate(legs):
                if not isinstance(leg, dict) or not is_url(leg.get('url')) or leg.get('leg') not in LEGS:
                    errors.append('links.strava_legs[%d] needs a URL and leg swim/bike/run/null' % n)
    return errors


def validate(data, i18n_keys):
    """Return a list of (race id or index, level, message)."""
    if not isinstance(data, dict) or not isinstance(data.get('races'), list):
        return [('file', 'error', 'top level must be an object with a "races" list')]
    problems, seen = [], set()
    key_names = data.get('names') if isinstance(data.get('names'), dict) else {}
    for n, r in enumerate(data['races']):
        label = r.get('id') if isinstance(r, dict) and r.get('id') else '#%d' % n
        if isinstance(r, dict) and r.get('id'):
            if r['id'] in seen:
                problems.append((label, 'error', 'duplicate id'))
            seen.add(r['id'])
        errs, warns = check_race(r, i18n_keys, key_names)
        problems += [(label, 'error', m) for m in errs]
        problems += [(label, 'warning', m) for m in warns]
    return problems


def main(argv):
    if not argv:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    keys = load_i18n_keys()
    failed = False
    for path in argv:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        problems = validate(data, keys)
        n_err = sum(1 for p in problems if p[1] == 'error')
        n_races = len(data.get('races', [])) if isinstance(data, dict) else 0
        for label, level, msg in problems:
            # ##vso / ::error style lines are picked up by Azure Pipelines and GitHub Actions logs.
            tag = '##vso[task.logissue type=%s]' % level if os.environ.get('TF_BUILD') else level.upper() + ': '
            print('%s%s: %s: %s' % (tag, path, label, msg))
        print('%s: %d races, %d errors, %d warnings' % (path, n_races, n_err, len(problems) - n_err))
        failed = failed or n_err > 0
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
