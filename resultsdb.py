# resultsdb.py
# scraping rotogrinders resultsdb

from dateutil.parser import parse
from tzlocal import get_localzone
from time import sleep

import requests

headers = {
    'authority': 'resultsdb-api.rotogrinders.com',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
    'dnt': '1',
    'accept': '*/*',
    'origin': 'https://rotogrinders.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://rotogrinders.com/',
    'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
    'if-none-match': 'W/"13d84f-y7jnw9VsZ+LVRAEPYPGh8nxG9/I"',
}

url = 'https://resultsdb-api.rotogrinders.com/api/slates'

dr = (
 '09/13/2020',
 '09/20/2020',
 '09/27/2020',
 '10/04/2020',
 '10/11/2020',
 '10/18/2020',
 '10/25/2020',
 '11/01/2020',
 '11/08/2020',
 '11/15/2020',
 '11/22/2020',
 '11/29/2020',
 '12/06/2020',
 '12/13/2020',
 '12/20/2020',
 '12/27/2020',
 '01/03/2021'
)

for d in dr:
    print(f'Starting {d}')
    params = {'start': d, 'site': '20'}
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    with open(f"{d.replace(r'/', '_')}.json", 'w') as f:
        json.dump(data, f)
        sleep(1)



# data is a list of dicts
# here are the top-level keys and types
"""
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
""";

# can find main slate by looking for start and end
# also slateTypeName = classic
# sport = 1
# slateType = 1
# most reliable method will be to parse start/end
>>> parse(data[12]['start']).astimezone(get_localzone())
datetime.datetime(2020, 9, 13, 12, 0, tzinfo=<DstTzInfo 'America/Chicago' CDT-1 day, 19:00:00 DST>)

>>> parse(data[12]['end']).astimezone(get_localzone())
datetime.datetime(2020, 9, 13, 15, 25, tzinfo=<DstTzInfo 'America/Chicago' CDT-1 day, 19:00:00 DST>)

# so _id can then be used to get summary
# this has a cash average, gpp average, and winnerMap
# can also get projected ownership, actual fpts, projected fpts, and ecr per player per contest
# also have acccess to top 50 entries to contest

# contests resource - to get specific contest
params = (
    ('_id', '5f5e57f818ea8c5997be95ef'),
    ('ownership', 'true'),
)

response = requests.get('https://resultsdb-api.rotogrinders.com/api/contests', headers=headers, params=params)

# get top lineups from a contest
params = (
    ('_contestId', '5f5e57f818ea8c5997be95ef'),
    ('sortBy', 'points'),
    ('order', 'desc'),
    ('index', '0'),
    ('maxFinish', '304500'),
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

response = requests.get('https://resultsdb-api.rotogrinders.com/api/entries', headers=headers, params=params)
