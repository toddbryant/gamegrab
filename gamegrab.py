"""gamegrab

Usage:
  gamegrab.py [--time-class=TC] [--outfile=OUTFILE] [--color=COLOR] [--since=YYYYMM] [--show-eco-stats] USERNAME
  gamegrab.py (-h | --help)

Options:
  --time-class=TC       Only download games of specified time control.
  --outfile=OUTFILE     Name of outputfile (defaults to USERNAME.pgn).
  --color=COLOR         Download games of specific color.   
  --num-games=NUMGAMES  Download only this many recent games.
  --since=YYYYMM        Only download games on or after given year and month.
  -h --help             Show this screen.

Arguments:
  USERNAME      username to download games
"""
from docopt import docopt

import requests
import json
import re

CHESSCOM_HEADERS = { \
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36' \
}


def main(arguments):
    user = arguments['USERNAME']
    outfile = arguments['--outfile'] if '--outfile' in arguments else f'{user}.pgn'
    time_class = arguments['--time-class'] if '--time-class' in arguments else None
    color = arguments['--color'].lower() if arguments.get('--color') else None
    since = arguments['--since'] if '--since' in arguments else None
    num_games = int(arguments['--num-games']) if '--num-games' in arguments else None

    if since:
        from_year = int(since[:4])
        from_month = int(since[4:6])

    with open(outfile, 'w') as f:
        urls = requests.get('https://api.chess.com/pub/player/{0}/games/archives'.format(user), headers=CHESSCOM_HEADERS)
        game_ctr = 0
        for url in urls.json()['archives'][::-1]:
            if since:
                url_year, url_month = map(int, url.split('/')[-2:])
                if url_year < from_year or (url_year == from_year and url_month < from_month):
                    continue
            #print('Downloading {url}...'.format(url=url), flush=True)
            games = requests.get(url, headers=CHESSCOM_HEADERS)
            for game in games.json()['games'][::-1]:
                if game['rules'] == 'chess' and game['rated'] and (not time_class or game['time_class'] == time_class) and (not color or game[color]['username'].lower()==user.lower()):
                    pgn = game['pgn'].replace('\\n', '\n')
                    try:
                        f.write(game['pgn'])
                        f.write('\n')
                        game_ctr += 1
                        if num_games and game_ctr >= num_games:
                            return 
                    except UnicodeEncodeError: # hack
                        print('UnicodeEncodeError, skipping month.')
                        continue

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments)
