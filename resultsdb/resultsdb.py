# resultsdb/resultsdb/resultsdb.py
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Eric Truett
# Licensed under the MIT License

"""
Gets results data from resultsdb

Examples:

>>>command()
result
"""

import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from dateutil.parser import parse
import requests
from tzlocal import get_localzone


logging.getLogger(__name__).addHandler(logging.NullHandler())

DATA_DIR = Path(__file__).parent / "data"
HEADERS = {
    'authority': 'resultsdb-api.rotogrinders.com',
    'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
    'dnt': '1',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'accept': '*/*',
    'origin': 'https://rotogrinders.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://rotogrinders.com/',
    'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
    'if-none-match': 'W/"9d65a-vpo7ZUDOOqvtLplU9G6a5uJlRc0"',
}


def _dump(d: dict) -> None:
    """Dumps key / value for scalar and type for list/dict
    
    Args:
        d (dict): the dict to dump

    Returns:
        None

    """
    for k, v in d.items():
        if isinstance(v, (str, float, int)):
            print(k, v)
        else:
            print(k, type(v))


def days_hours_minutes(td):
    """Converts time delta into tuple of days, hours, minutes

    Args:
        td (datetime.timedelta): the timedelta object

    Returns:
        Tuple[int, int, int]

    """
    return td.days, td.seconds // 3600, (td.seconds // 60) % 60


def find_contests(contests: List[dict], filters: dict) -> dict:
    """Finds contests according to filters
    
    Args:
        contests (List[dict]): the contests
        filters (dict): the filters for the find

    Returns:
        dict

    """
    for k, v in filters.items():
        comp, val = v
        if comp == 'eq':
            contests = [c for c in contests if c[k] == val]
        if comp == 'like':
            contests = [c for c in contests if val in c[k]]
        if comp == 'lte':
            contests = [c for c in contests if c[k] <= val]
        if comp == 'gte':
            contests = [c for c in contests if c[k] >= val]
        
    return contests


def find_milly(contests: List[dict]) -> dict():
    """Finds the Millionaire Maker contest
    
        Args:
        contests (List[dict]): the contests
    
    Returns:
        dict
        
    """
    # if there are multiple milly makers, then gets the one with lower entry fee
    filters = {'name': ('like', 'Million')}
    mm = find_contests(contests, filters)
    if len(mm) == 1:
        return mm[0]
    entry_fees = [c['entryFee'] for c in contests]
    return mm[entry_fees.index(min(entry_fees))]


def find_main_slate(slates: List[dict], sport: int = 1, game_count: int = 7, slate_type: str = 'Classic') -> str:
    """Finds main slate from list of slates
    
    Args:
        slates (List[dict]): the slates document
        sport (int): default 1 (NFL)
        game_count (int): the threshold games in the main slate, default 7
        slate_type (str): default 'Classic'

    Returns:
        str

    """
    fbslates = [s for s in slates if
                s['gameCount'] > game_count and 
                s['sport'] == sport and 
                s['slateTypeName'] == slate_type]

    # if the time test fails, then fall back to the 2nd largest slate
    game_counts = sorted([s['gameCount'] for s in fbslates], reverse=True)

    for s in fbslates:
        # easiest test is to check delta between start and end
        start = parse(s['start']).astimezone(get_localzone())
        end = parse(s['end']).astimezone(get_localzone())
        timediff = days_hours_minutes(end - start)
        if timediff in [(0, 3, 25), (0, 3, 10), (0, 3, 20)]:
            return s['_id']
        if s['gameCount'] == game_counts[1]:
            return s['_id']

    logging.warning('Could not find main slate')   
    return None


def get_contests(slate: str, ownership: bool = True) -> List[dict]:
    """Gets contests for a given slate
    
    Args:
        slate (str): the slate id
        ownership (bool): include ownership data, default True

    Returns:
        List[dict]

    """
    url = 'https://resultsdb-api.rotogrinders.com/api/contests'
    params = {'slates': slate, 'ownership': 'true' if ownership else 'false'}
    r = requests.get(url, headers=HEADERS, params=params)
    return r.json()


def get_entries(contest_id: str, n_entries: int = 10) -> dict:
    """Gets entries for a specific contest
    
    Args:
        contest_id (str): the contest id
        n_entries (int): the number of entries, default 10

    """
    params = (
            ('_contestId', contest_id),
            ('sortBy', 'points'),
            ('order', 'desc'),
            ('index', '0'),
            ('maxFinish', f'{n_entries}'),
            ('players', ''),
            ('users', 'false'),
            ('username', ''),
            ('isLive', 'false'),
            ('minPoints', ''),
            ('maxSalaryUsed', ''),
            ('incomplete', 'false'),
            ('positionsRemaining', ''),
            ('requiredStartingPositions', ''),
        )
    url = 'https://resultsdb-api.rotogrinders.com/api/entries'
    r = requests.get(url, headers=HEADERS, params=params)
    return r.json()


def get_slates(start: str, site: int = 20) -> List[dict]:
    """Gets slate for particular day and site
    
    Args:
        start (str): in m/d/yyyy format
        site (int): default 20, which is dk

    Returns:
        List[dict]

    """
    url = 'https://resultsdb-api.rotogrinders.com/api/slates'
    params = {'start': start, 'site': f'{site}'}
    r = requests.get(url, headers=HEADERS, params=params)
    return r.json()


def parse_results(results: List[dict]) -> List[dict]:
    """Parses contest entry
    
    Args:
        results (List[dict]): the contst results

    Returns:
        List[dict]

    """
    wanted = ['userEntryCount', 'siteScreenName', 'rank', 'points', 'salaryUsed', '_contestId']
    data = []
    for e in results['entries']:
        d = {k: e[k] for k in wanted}
        lu = {}
        for pos, players in e['lineup'].items():
            for p in players:
                if isinstance(p, dict):
                     lu[p['name']] = (pos, p['_slatePlayerId'])
        d['lineup'] = lu
        data.append(d)
    return data


def parse_slate(slate):
    """Parses slate document
    
    Args:
        slate (dict): slate document

    Returns:
        dict

    """
    wanted = ['_id', 'slateTypeName', 'siteSlateId', 'gameCount', 'start', 'end', 'sport']
    return {k: slate[k] for k in wanted} 


def parse_slate_games(slate: dict) -> List[dict]:
    """Parses slate games
    
    Args:
        slate (dict): slate document

    Returns:
        List[dict]

    """
    games = []
    for game in slate['slateGames']:
        wanted = ['date', 'id']
        vegas = ['line', 'o/u', 'total', 'opp_total']
        g = {k: game[k] for k in wanted}
        g['teamHome'] = game['teamHome']['hashtag']
        g['teamAway'] = game['teamAway']['hashtag']
        for item in vegas:
            g[item] = game['vegas'].get(item)
        games.append(g)
    return games


def parse_slate_projected_optimal(slate: dict) -> List[dict]:
    """Parses slate projected optimal lineup
       This is not the actual optimal lineup, is just their projected lineup with highest raw projection

    Args:
        slate (dict): slate document

    Returns:
        List[dict]
    
    """
    players = []
    opt = slate.get('optimalLineup')
    if not opt:
        return None
    wanted = ['name', 'position', 'salary', 'fpts', 'ownership']
    for item in opt:
        player = {k: item[k] for k in wanted}
        try:
            player['ownership'] = float(player['ownership'].str.replace('%', ''))
        except:
            player['ownership'] = None
        players.append(player)
    return players


def parse_slate_players(slate: dict) -> List[dict]:
    """Parses slate players
    
    Args:
        slate (dict): slate document

    Returns:
        List[dict]

    """
    wanted = ['dkName', 'slatePosition', 'siteSlatePlayerId', 'rgPlayerId', 'team', 'salary']
    return [{k: p.get(k) for k in wanted} for p in slate.get('slatePlayers')]


def schema_contest() -> str:
    """Schema for contest document"""
    return """
        _id 5f70c6f3430508338f95ddab
        winner
        slateType 1
        gameCount 13
        siteSlateId 39913
        start 2020-09-27T17:00:00.000Z
        sport 1
        prizePool 4275000
        maxEntriesPerUser 150
        maxEntries 251470
        entryFee 20
        name NFL $4.25M Fantasy Football Millionaire [$1M to 1st + ToC Entry]
        siteContestId 92556624
        _slateId 5f70c6aaed428f3375ac25cb
        entryCount 249799
        rgPrizePool 588146.0700000001
        rgPrizeWinnerCount 11432
        complete True
        prizes
   
    """


def schema_entry() -> str:
    """Schema for entry document"""
    return """
        timestamp <class 'str'>
        page <class 'int'>
        entries <class 'list'>
        count <class 'int'>

        entry:
            _id <class 'str'>
            userEntryCount <class 'int'>
            siteScreenName <class 'str'>
            user <class 'dict'>
            siteEntryId <class 'str'>
            rank <class 'int'>
            timeRemaining <class 'int'>
            points <class 'float'>
            lineup <class 'dict'>
            salaryUsed <class 'int'>
            _contestId <class 'str'>
            slotsRemaining <class 'int'>
            prize <class 'dict'>
            createdAt <class 'str'>

        lineup:
            {'DST': [{'_slatePlayerId': '5f7147dd430508338fc85203', 'name': 'Colts'}],
            'TE': [{'_slatePlayerId': '5f7147dd430508338fc85227',
            'name': 'Austin Hooper'}],
            'WR': [{'_slatePlayerId': '5f7147dd430508338fc852a6', 'name': 'DK Metcalf'},
            {'_slatePlayerId': '5f7147dd430508338fc852a3', 'name': 'Tyler Lockett'},
            {'_slatePlayerId': '5f7147dd430508338fc85275', 'name': 'Michael Gallup'}],
            'RB': [{'_slatePlayerId': '5f7147dd430508338fc851f2', 'name': 'Jeff Wilson'},
            {'_slatePlayerId': '5f7147dd430508338fc85200', 'name': 'Rex Burkhead'}],
            'FLEX': [{'_slatePlayerId': '5f7147dd430508338fc852be',
            'name': 'Derrick Henry'}],
            'QB': [{'_slatePlayerId': '5f7147dd430508338fc852ba',
            'name': 'Russell Wilson'}],
            'summary': ['Russell Wilson',
            'Derrick Henry',
            'Jeff Wilson',
            'Rex Burkhead',
            'DK Metcalf',
            'Tyler Lockett',
            'Michael Gallup',
            'Austin Hooper',
            'Colts']}
    """


def schema_slate() -> str:
    """Shows schema of slate document
    
    Args:
        None

    Returns:
        str

    """
    return """
        _id <class 'str'>
        isSalary <class 'bool'>
        slateTypeName <class 'str'>
        gameCount <class 'int'>
        siteSlateId <class 'str'>
        end <class 'str'>
        start <class 'str'>
        sport <class 'int'>
        siteId <class 'int'>
        slateType <class 'int'>
        gameTypeId <class 'int'>
        updatedAt <class 'str'>
        __v <class 'int'>
        startingPositions <class 'list'>
        complete <class 'bool'>
        optimalLineup <class 'list'>
        slateGames <class 'list'>
        slatePlayers <class 'list'>
        createdAt <class 'str'>
    """

def slate_teams(slate: dict) -> Set[str]:
    """Gets teams on given slate
    
    Args:
        slate (dict): the slate document

    Returns:
        Set[str]

    """
    return set([sp['team'] for sp in slate['slatePlayers']])