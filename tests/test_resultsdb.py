# resultsdb/tests/test_resultsdb.py
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Eric Truett
# Licensed under the MIT License

import datetime
import json
import random

import pytest

from resultsdb import *


def _dump(d, tprint):
    """Dumps first level of dict"""
    for k, v in d.items():
        if isinstance(v, (str, float, int)):
            tprint((k, v))
        else:
            tprint((k, type(v)))


@pytest.fixture
def contests(root_directory):
    pth = root_directory / 'resultsdb' / 'data' / 'contests.json'
    return json.loads(pth.read_text())


@pytest.fixture
def results(root_directory):
    pth = root_directory / 'resultsdb' / 'data' / 'results.json'
    return json.loads(pth.read_text())


@pytest.fixture
def slates(root_directory):
    pth = root_directory / 'resultsdb' / 'data' / 'slates.json'
    return json.loads(pth.read_text())


def test_days_hours_minutes():
    """Tests days_hours_minutes"""
    td = datetime.date(2021, 9, 1) - datetime.date(2021, 8, 31)
    assert days_hours_minutes(td) == (1, 0, 0)
    td = datetime.datetime(2021, 9, 1, 15, 0, 0) - datetime.datetime(2021, 9, 1, 11, 30, 0)
    assert days_hours_minutes(td) == (0, 3, 30)


def test_find_contests(contests):
    """tests find_contests"""
    filters = {'name': ('like', 'Million')}
    c = find_contests(contests, filters)
    assert 'Millionaire' in c[0]['name']


def test_find_milly(contests):
    """tests find_milly"""
    c = find_milly(contests)
    assert 'Millionaire' in c['name']


def test_find_main_slate(slates):
    """Finds main slate from list of slates"""
    s = find_main_slate(slates)
    assert isinstance(s, str)


@pytest.mark.skip
def test_get_contests():
    """Tests get_contests"""
    pass

@pytest.mark.skip
def test_get_entries():
    """Tests get entries"""
    pass


@pytest.mark.skip
def test_get_slates():
    """Tests get slates"""
    pass


def test_parse_results(results):
    """Tests parse_results"""
    r = parse_results(results)
    assert isinstance(r, list)
    for k in ['userEntryCount', 'siteScreenName', 'rank', 'points', 'salaryUsed', '_contestId', 'lineup']:
        assert k in random.choice(r)


def test_parse_slate(slates):
    """tests parse_slate"""
    s = parse_slate(slates[0])
    assert isinstance(s, dict)
    wanted = {'_id', 'slateTypeName', 'siteSlateId', 'gameCount', 'start', 'end', 'sport'}
    assert set(s.keys()) == wanted


def test_parse_slate_games(slates, tprint):
    """tests parse_slate_games"""
    s = random.choice(slates)
    sg = parse_slate_games(s)
    assert isinstance(sg, list)
    sgg = random.choice(sg)
    tprint(sgg)
    assert set(sgg.keys()) == {'date', 'id', 'line', 'o/u', 'total', 'opp_total', 'teamHome', 'teamAway'}


def test_parse_slate_projected_optimal(slates, tprint):
    """Parses slate projected optimal lineup"""
    s = random.choice([item for item in slates if item.get('optimalLineup')])
    #_dump(s.get('optimalLineup')[0], tprint)
    opt = parse_slate_projected_optimal(s)
    assert isinstance(opt, list)
    assert isinstance(random.choice(opt), dict)
    o = s.pop('optimalLineup')
    assert parse_slate_projected_optimal(s) is None
  

def test_parse_slate_players(slates):
    """Tests parse_slate_players"""
    s = random.choice(slates)
    p = parse_slate_players(s)    
    assert isinstance(p, list)
    assert isinstance(random.choice(p), dict)
    assert set(random.choice(p).keys()) == {'dkName', 'slatePosition', 'siteSlatePlayerId', 'rgPlayerId', 'team', 'salary'}


def test_slate_teams(slates):
    """Tests slate_teams"""
    s = random.choice(slates)
    st = slate_teams(s)
    assert isinstance(st, set)
    assert isinstance(random.choice(list(st)), str)
    assert len(st) // 2 == s['gameCount']