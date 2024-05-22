"""timestats

Usage:
  timestats.py [--num_games=NUMGAMES] [--threshold=THRESHOLD] USERNAME
  timestats.py (-h | --help)

Options:
  --num_games=NUMGAMES    Only download last n games [default: 10000]
  --threshold=THRESHOLD   Point out moves where more than THRESHOLD sec spent [default: 15]
  -h --help               Show this screen.

Arguments:
  USERNAME      username to download games
"""

from docopt import docopt


import chess
import chess.pgn
import datetime
import gamegrab
import os
import re

def tenths_sec_to_str(time_tenths):
   min = time_tenths // 600
   sec = (time_tenths % 600) / 10

   if min > 0:
       return f'{min}min {sec}sec'
   else: 
       return f'{sec} sec'

def is_normal_chess(game):
    return (not 'FEN' in game.headers) or (game.headers['FEN'].startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'))

def is_big_rating_gap(game):
    return abs(int(game.headers['WhiteElo']) - int(game.headers['BlackElo'])) > 400

def is_user_white(game, username):
    return game.headers["White"].lower() == username.lower()

def is_user_to_move(game, node, username):
    return is_user_white(game, username) != node.turn()

def is_60sec(game):
    return game.headers["TimeControl"] == "60"

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

def get_think_times(game, username):
    clock_regex = re.compile(r'.*%clk 0:([0-9]*):([0-9\\.]*)')

    node = game.root()
    node.comment = f'{game.headers["Link"]}'
    comments = False
    
    prev_time_tenths_sec = int(game.headers['TimeControl'].split('+')[0]) * 10
    think_times = []
    scramble_times = []
    while node.next():
        prev_node, node = node, node.next()

        minutes, sec = map(float, clock_regex.match(node.comment).groups())
        time_tenths_sec = minutes * 600 + sec * 10

        if is_user_to_move(game, node, username):
            delta, prev_time_tenths_sec = prev_time_tenths_sec - time_tenths_sec, time_tenths_sec
            think_times.append(delta)
            if time_tenths_sec < 100 and opp_time_tenths_sec < 100:
                scramble_times.append(delta)
        else:
            opp_time_tenths_sec = time_tenths_sec

    return think_times, scramble_times

# Returns true if the game ever reached a time scramble, defined as:
# * Both sides under 10 seconds
# * At least 5 moves played by both sides
def was_time_scramble(game):
    scramble_regex = r'%clk 0:00:0[0-9](?:\.[0-9])?[^%]*%clk 0:00:0[0-9](?:\.[0-9])?'
    return len(re.findall(scramble_regex, str(game))) >= 5

def main(arguments):
    username = arguments['USERNAME']
    num_games = int(arguments['--num_games'])
    threshold = int(arguments['--threshold'])

    pgnfile = f'{username}.pgn'
    if os.path.exists(pgnfile):
        os.remove(pgnfile)
    print(f'Downloading {pgnfile}...')
    gamegrab.main({'USERNAME': username, '--time-class': 'bullet', '--outfile': pgnfile, '--color': None, '--since': '202001'})

    print('Analyzing games...', flush=True)

    no_long_think_perfs = []
    long_think_perfs = []

    scramble_perfs = []
    total_perfs = []

    think_moves, total_moves = 0, 0

    pgn = open(pgnfile)
    think_times_n, total_think, total_premoves = 0, 0, 0
    scramble_thinks_n, scramble_total_think, scramble_premoves = 0, 0, 0

    game_count = 0
    while game := chess.pgn.read_game(pgn):
        if not is_normal_chess(game) or game.headers["TimeControl"] not in ("60", "30") or not is_60sec(game):
            continue
        think_times, scramble_times = get_think_times(game, username)
        perf = get_user_perf(game, username)
        total_perfs.append(perf)

        think_times_n += len(think_times)
        total_think += sum(think_times)
        total_premoves += sum(x for x in think_times if x==1)

        # delete scramble if not enough moves?
        if len(scramble_times) >=4:
            scramble_thinks_n += len(scramble_times)
            scramble_total_think += sum(scramble_times)
            scramble_premoves += sum(x for x in scramble_times if x==1)
            scramble_perfs.append(perf)

        game_count += 1

        if game_count % 100 == 0:
            print(f'[{datetime.datetime.now()}] {game_count} games complete.')

    print(f'{username}')
    print('='*len(username))
    print(f'n: {game_count}')
    print(f'Total thinks: avg={0.1*total_think/think_times_n:.2f} sec, premove rate={100*total_premoves/think_times_n:.2f}%')
    print(f'Scramble thinks: avg={0.1*scramble_total_think/scramble_thinks_n:.2f} sec premove rate={100*scramble_premoves/scramble_thinks_n:.2f}%')

    print(f'Perf in time scrambles: {int(sum(scramble_perfs)/len(scramble_perfs))}')
    print(f'Overall perf: {int(sum(total_perfs) / len(total_perfs))}')

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments)
