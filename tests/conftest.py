import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))


@pytest.fixture
def sample():
    with open(os.path.join(ROOT, 'examples', 'races.sample.json'), encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def race(sample):
    """A copy of the first sample race (Berlin Marathon) to modify in a test."""
    return json.loads(json.dumps(sample['races'][0]))
