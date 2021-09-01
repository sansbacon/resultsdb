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

from nflschedule import *


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


def get_contests(slate: str, ownership: bool = True) -> dict:
    """Gets contests for a given slate
    
    Args:
        slate (str): the slate id
        ownership (bool): include ownership data, default True

    Returns:
        dict

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


def get_slates(start: str, site: int = 20) -> dict:
    """Gets slate for particular day and site
    
    Args:
        start (str): in m/d/yyyy format
        site (int): default 20, which is dk

    Returns:
        dict

    """
    url = 'https://resultsdb-api.rotogrinders.com/api/slates'
    params = {'start': start, 'site': f'{site}'}
    r = requests.get(url, headers=HEADERS, params=params)
    return r.json()



def find_main_slate(slate):
    """Finds main slate from list of slates"""
    fbslates = [s for s in slate if
                s['gameCount'] > 5 and 
                s['sport'] == 1 and 
                s['slateTypeName'] == "Classic"]

    # if the time test fails, then fall back to the 2nd largest slate
    game_counts = sorted([s['gameCount'] for s in fbslates], reverse=True)

    for s in fbslates:
        # easiest test is to check delta between start and end
        start = parse(s['start']).astimezone(get_localzone())
        end = parse(s['end']).astimezone(get_localzone())
        if days_hours_minutes(end - start) == (0, 3, 25):
            return s['_id']
        if s['gameCount'] == game_counts[1]:
            return s['_id']

    logging.warning('Could not find main slate')   
    return fbslates


def slate_schema() -> str:
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