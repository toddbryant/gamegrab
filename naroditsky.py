"""naroditsky

Usage:
  naroditsky.py [--num_games=NUMGAMES] [--threshold=THRESHOLD] USERNAME
  naroditsky.py (-h | --help)

Options:
  --num_games=NUMGAMES    Only download last n games [default: 25]
  --threshold=THRESHOLD   Point out moves where more than THRESHOLD sec spent [default: 15]
  -h --help               Show this screen.

Arguments:
  USERNAME      username to download games
"""

from docopt import docopt


import chess
import chess.pgn
import gamegrab
import re

def tenths_sec_to_str(time_tenths):
   min = time_tenths // 600
   sec = (time_tenths % 600) / 10

   if min > 0:
       return f'{min}min {sec}sec'
   else: 
       return f'{sec} sec'

def is_user_white(game, username):
    return game.headers["White"] == username

def is_user_to_move(game, node, username):
    return is_user_white(game, username) != node.turn()

def get_user_perf(game, username):
    user_is_white = is_user_white(game, username)
    opp_rating = int(game.headers["BlackElo"] if user_is_white else game.headers["WhiteElo"])

    if game.headers["Result"] == "1/2-1/2":
        perf = opp_rating
    elif game.headers["Result"] == "1-0":
        perf = opp_rating + (400 if user_is_white else -400)
    elif game.headers["Result"] == "0-1":
        perf = opp_rating + (-400 if user_is_white else 400)

    return perf

def find_long_thinks(game, username, threshold):
    clock_regex = re.compile(r'.*%clk 0:([0-9]*):([0-9\\.]*)')

    node = game.root()
    node.comment = f'{game.headers["Link"]}'
    comments = False
    
    prev_time_tenths_sec = int(game.headers['TimeControl'].split('+')[0]) * 10
    while node.next():
        prev_node = node
        node = node.next()

        if is_user_to_move(game, node, username):
            min, sec = map(float, clock_regex.match(node.comment).groups())
            time_tenths_sec = min * 600 + sec * 10

            delta = prev_time_tenths_sec - time_tenths_sec
            if delta >= threshold:
                comments = True
                node.comment += tenths_sec_to_str(delta)

            prev_time_tenths_sec = time_tenths_sec

    return str(game) if comments else ''

def main(arguments):
    print(arguments)
    username = arguments['USERNAME']
    num_games = arguments['--num_games']
    threshold = int(arguments['--threshold'])

    pgnfile = f'{username}.pgn'
    gamegrab.main({'USERNAME': username, '--blitz-only': True, '--num-games': num_games, '--outfile': pgnfile, '--color': None, '--since': None})

    print('Analyzing games...', flush=True)

    no_long_think_perfs = []
    long_think_perfs = []

    pgn = open(pgnfile)
    with open(f'annotated_{username}.pgn', 'w') as outfile:
        ctr = 0
        while game := chess.pgn.read_game(pgn):
            result = find_long_thinks(game, username, threshold*10)
            perf = get_user_perf(game, username)

            if result:
                outfile.write(result)
                outfile.write('\n\n')

                long_think_perfs.append(perf)
            else:
                no_long_think_perfs.append(perf)
            
            if ctr == num_games:
                break
            ctr += 1

    print(f'Games with no long thinks: {len(no_long_think_perfs)}. Avg perf: {int(sum(no_long_think_perfs) / len(no_long_think_perfs))}')
    print(f'Games with long thinks: {len(long_think_perfs)}. Avg perf: {int(sum(long_think_perfs) / len(long_think_perfs))}')

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments)
