"""gamegrab

Usage:
  gamegrab.py [--blitz-only] [--outfile=OUTFILE] [--color=COLOR] [--since=YYYYMM] [--show-eco-stats] USERNAME
  gamegrab.py (-h | --help)

Options:
  --blitz-only          Only download blitz games.
  --outfile=OUTFILE     Name of outputfile (defaults to USERNAME.pgn).
  --color=COLOR         Download games of specific color.   
  --since=YYYYMM        Only download games on or after given year and month.
  -h --help             Show this screen.

Arguments:
  USERNAME      username to download games
"""
from docopt import docopt

import requests
import json
import re

def main(arguments):
    user = arguments['USERNAME']
    outfile = arguments['--outfile'] or '{0}.pgn'.format(user)
    blitz_only = arguments['--blitz-only']
    color = arguments['--color'].lower() if arguments['--color'] else None
    since = arguments['--since'] if arguments['--since'] else None
    if since:
        from_year = int(since[:4])
        from_month = int(since[5:6])

    with open(outfile, 'w') as f:
        urls = requests.get('https://api.chess.com/pub/player/{0}/games/archives'.format(user))
        for url in urls.json()['archives']:
            if since:
                url_year, url_month = map(int, url.split('/')[-2:])
                if url_year < from_year or (url_year == from_year and url_month < from_month):
                    continue
            print('Downloading {url}...'.format(url=url))
            games = requests.get(url)
            for game in games.json()['games']:
                if game['rules'] == 'chess' and (not blitz_only or game['time_class'] == 'blitz') and (not color or game[color]['username'].lower()==user.lower()):
                    pgn = game['pgn'].replace('\\n', '\n')
                    try:
                        f.write(game['pgn'])
                    except UnicodeEncodeError: # hack
                        print('UnicodeEncodeError, skipping month.')
                        continue

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments)
