import json

import pytest

import validate_races as v

KEYS = v.load_i18n_keys()


def errors(race):
    return v.check_race(race, KEYS)[0]


def test_sample_dataset_is_valid(sample):
    problems = v.validate(sample, KEYS)
    assert [p for p in problems if p[1] == 'error'] == []


def test_good_race_has_no_errors(race):
    assert errors(race) == []


@pytest.mark.parametrize('field', ['id', 'date', 'name', 'lat', 'lng', 'geo'])
def test_required_fields(race, field):
    del race[field]
    assert 'missing ' + field in errors(race)


@pytest.mark.parametrize('date', ['2025-02-30', '21/09/2025', '2025-9-21'])
def test_bad_dates(race, date):
    race['date'] = date
    assert any('date' in e for e in errors(race))


@pytest.mark.parametrize('field,value', [('lat', 91), ('lat', -90.5), ('lng', 181), ('lat', '52.5'), ('lng', True)])
def test_coordinates(race, field, value):
    race[field] = value
    assert any(e.startswith(field) for e in errors(race))


def test_unknown_sport_and_category(race):
    race['sport'] = 'quidditch'
    race['category'] = 'marathon_plus'
    errs = errors(race)
    assert any("sport 'quidditch'" in e for e in errs)
    assert any("category 'marathon_plus'" in e for e in errs)


def test_unknown_tag_is_only_a_warning(race):
    race['tags'] = ['not_a_real_tag']
    errs, warns = v.check_race(race, KEYS)
    assert errs == []
    assert any('not_a_real_tag' in w for w in warns)


def test_geo_top_level_may_differ_from_country(race):
    race['country'] = 'XX'
    assert errors(race) == []


def test_district_key_needs_outline_or_name(race):
    race['geo']['path'] = ['CN', 'CN-SH', '310101', 'D-1']
    race['country'] = 'CN'
    errs, warns = v.check_race(race, KEYS)
    assert errs == [] and any("'D-1'" in w for w in warns)
    errs, warns = v.check_race(race, KEYS, {'D-1': {'en': 'Somewhere'}})
    assert errs == [] and warns == []


def test_geo_path_must_exist_in_boundary_files(race):
    race['geo']['path'] = ['DE', 'DE-XX', 'DE-XX']
    errs = errors(race)
    assert any('first-level' in e for e in errs)
    assert any('second-level' in e for e in errs)


def test_country_without_boundary_file_is_not_checked(race):
    race['country'] = 'FR'
    race['geo']['path'] = ['FR', 'FR-IDF', 'FR-75']
    assert errors(race) == []


def test_bad_links(race):
    race['links']['website'] = 'javascript:alert(1)'
    race['links']['strava_legs'] = [{'url': 'https://www.strava.com/activities/1', 'leg': 'kayak'}]
    errs = errors(race)
    assert any('links.website' in e for e in errs)
    assert any('strava_legs[0]' in e for e in errs)


def test_negative_distance(race):
    race['distance_km'] = -5
    assert any('distance_km' in e for e in errors(race))


def test_duplicate_ids(sample):
    sample['races'].append(dict(sample['races'][0]))
    problems = v.validate(sample, KEYS)
    assert (sample['races'][0]['id'], 'error', 'duplicate id') in problems


def test_bad_top_level():
    assert v.validate([], KEYS)[0][1] == 'error'


def test_cli_exit_codes(tmp_path, sample):
    good = tmp_path / 'good.json'
    good.write_text(json.dumps(sample), encoding='utf-8')
    assert v.main([str(good)]) == 0
    sample['races'][0]['lat'] = 200
    bad = tmp_path / 'bad.json'
    bad.write_text(json.dumps(sample), encoding='utf-8')
    assert v.main([str(bad)]) == 1
