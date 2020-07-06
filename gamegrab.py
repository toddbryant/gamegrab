"""gamegrab

Usage:
  gamegrab.py [--blitz-only] [--outfile=OUTFILE] [--show-eco-stats] USERNAME
  gamegrab.py (-h | --help)

Options:
  --blitz-only          Only download blitz games.
  --show-eco-stats      Show performance rating by ECO.
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
    show_eco_stats = arguments['--show-eco-stats']

    white_by_eco = dict()
    black_by_eco = dict()

    with open(outfile, 'w') as f:
        urls = requests.get('https://api.chess.com/pub/player/{0}/games/archives'.format(user))
        for url in urls.json()['archives']:
            print('Downloading {url}...'.format(url=url))
            games = requests.get(url)
            for game in games.json()['games']:
                if game['rules'] == 'chess' and (not blitz_only or game['time_class'] == 'blitz'):
                    pgn = game['pgn'].replace('\\n', '\n')
                    f.write(game['pgn'])

                    if show_eco_stats:
                        try: 
                            eco = re.search('\\n\[ECO "(...)', game['pgn']).group(1)
                        except AttributeError: # occasionally no ECO classification`
                            continue
                        if game['white']['username']==user:
                            if eco not in white_by_eco:
                                white_by_eco[eco] = dict()
                                white_by_eco[eco]['n'] = 0
                                white_by_eco[eco]['score'] = 0    
                                white_by_eco[eco]['avg_opp'] = 0    
                            white_by_eco[eco]['n'] += 1
                            if game['white']['result'] == 'win':
                                white_by_eco[eco]['score'] += 1
                            elif game['white']['result'] == 'draw':
                                white_by_eco[eco]['score'] += 0.5
                            white_by_eco[eco]['avg_opp'] += game['black']['rating']
                        else: # user was black
                            if game['black']['username']==user:
                                if eco not in black_by_eco:
                                    black_by_eco[eco] = dict()
                                    black_by_eco[eco]['n'] = 0
                                    black_by_eco[eco]['score'] = 0    
                                    black_by_eco[eco]['avg_opp'] = 0    
                                black_by_eco[eco]['n'] += 1
                                if game['black']['result'] == 'win':
                                    black_by_eco[eco]['score'] += 1
                                elif game['black']['result'] == 'draw':
                                    black_by_eco[eco]['score'] += 0.5
                                black_by_eco[eco]['avg_opp'] += game['white']['rating']


    if show_eco_stats:
        print('------WHITE ECO STATS------')
        print('eco\tn\tavg_opp\tperf')
        print('-------------------------------')
        for eco in white_by_eco:
            stats = white_by_eco[eco]
            n = stats['n']
            avg_opp = 1.0 * stats['avg_opp']/n
            perf = avg_opp + 800 * stats['score'] / n - 400
            print('{eco}\t{n}\t{avg_opp:.0f}\t{perf:.0f}'.format(eco=eco,n=n,avg_opp=avg_opp,perf=perf))
        
        print('\n\n------BLACK ECO STATS------')
        print('eco\tn\tavg_opp\tperf')
        print('-------------------------------')
        for eco in black_by_eco:
            stats = black_by_eco[eco]
            n = stats['n']
            avg_opp = 1.0 * stats['avg_opp'] / n
            perf = avg_opp + 800 * stats['score'] / n - 400
            print('{eco}\t{n}\t{avg_opp:.0f}\t{perf:.0f}'.format(eco=eco,n=n,avg_opp=avg_opp,perf=perf))


if __name__ == '__main__':
    arguments = docopt(__doc__)
    #print(arguments)
    main(arguments)
