"""gamegrab

Usage:
  gamegrab.py [--blitz-only] [--outfile=OUTFILE] [--show-eco-stats] USERNAME
  gamegrab.py (-h | --help)

Options:
  --blitz-only          Only download blitz games.
  --outfile=OUTFILE     Name of outputfile (defaults to USERNAME.pgn).
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

    with open(outfile, 'w') as f:
        urls = requests.get('https://api.chess.com/pub/player/{0}/games/archives'.format(user))
        for url in urls.json()['archives']:
            print('Downloading {url}...'.format(url=url))
            games = requests.get(url)
            for game in games.json()['games']:
                if game['rules'] == 'chess' and (not blitz_only or game['time_class'] == 'blitz'):
                    pgn = game['pgn'].replace('\\n', '\n')
                    try:
                        f.write(game['pgn'])
                    except UnicodeEncodeError: # hack
                        print('UnicodeEncodeError, skipping month.')
                        continue

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments)
