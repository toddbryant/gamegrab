from chess.engine import Cp, Mate, MateGiven, Limit, SimpleEngine
import chess.pgn
import re

def add_result(times, perf, results):
    if times not in results:
        results[times] = {'n': 0, 'perf': 0}
    n, old_perf = results[times]['n'], results[times]['perf']

    results[times]['perf'] = (old_perf * n + perf) / (n + 1)
    results[times]['n'] += 1

DIFFS = (-1200, -600, -300, -150, 150, 300, 600, 1200)
EVALS = [-MateGiven, -Mate(99), Cp(-500), Cp(-300), Cp(-100), Cp(0), Cp(100), Cp(300), Cp(500), Mate(99), MateGiven]

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

def is_user_white(game, username):
    return game.headers["White"] == username

def print_results(results):
    for d in DIFFS:
        print(d, results.get(d, 'No games'))

def print_eval_results(results):
    for i, eval in enumerate(EVALS[:-1]):
        result_str = f'[{EVALS[i]}, {EVALS[i+1]}]'
        print(result_str, results.get(result_str, 'No games'))


def check_eval(username='ToddBryant'):
    stockfish = SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
    results = {}
    game_count = 0 

    with open(f'{username}.pgn') as f:
        while game := chess.pgn.read_game(f):
            user_is_white = is_user_white(game, username)
            perf = get_user_perf(game, username)

            node = game.root()

            move_ctr = 0
            while node.next() and move_ctr <= 40:
                node = node.next()
                move_ctr += 1
            if move_ctr < 40:
                continue

            # Evaluate the position on move 20
            eval = stockfish.analyse(node.board(), Limit(depth=16))['score']
            eval = eval.white() if user_is_white else eval.black()
            print(eval)

            for i, level in enumerate(EVALS[:-1]):
                if EVALS[i] <= eval < EVALS[i+1]:
                    add_result(f'[{EVALS[i]}, {EVALS[i+1]}]', perf, results)
            game_count += 1
            print(f'Processed {game_count} games.', flush=True)

    return results

def main(username='ToddBryant'):
    diffs = {d: set() for d in DIFFS}
    results = {}

    with open(f'{username}.pgn') as f:
        while game := chess.pgn.read_game(f):
            # Only consider 3 0 games
            if game.headers["TimeControl"] != "180":
                continue

            user_is_white = is_user_white(game, username)
            perf = get_user_perf(game, username)

            node = game.root()
            user_time, opp_time = 1800, 1800
            add_result((user_time, opp_time), perf, results)
            clock_regex = re.compile(r'.*%clk 0:([0-9]*):([0-9\\.]*)')

            diffs_found = {d: False for d in DIFFS}
            while node.next():
                node = node.next()
                try:
                    min, sec = map(float, clock_regex.match(node.comment).groups())
                except AttributeError:
                    continue

                time_ds = min * 600 + int(sec * 10)

                white_to_move = not node.turn()
                if user_is_white and white_to_move:
                    user_time = time_ds
                elif not user_is_white and not white_to_move:
                    user_time = time_ds
                else:
                    opp_time = time_ds

                add_result((user_time, opp_time), perf, results)
                for diff in DIFFS:
                    if diff < 0 and user_time <= opp_time + diff or diff > 0 and user_time >= opp_time + diff:
                        if not diffs_found[diff]:
                            add_result(diff, perf, results)
                            diffs_found[diff] = True


    return results

if __name__ == '__main__':
    main()
