"""
Generate a list of game headers, clock difference, and eval at move 20 for a PGN archive
"""

import chess
import chess.pgn
import datetime
import re

pgn = open('ToddBryant.pgn')

STOCKFISH = chess.engine.SimpleEngine.popen_uci("stockfish")
STOCKFISH.configure({"Threads": 4, "Hash": 1000})

game_cnt = 0
clock_regex = re.compile(r'.*%clk 0:([0-9]*):([0-9\\.]*)')
while game := chess.pgn.read_game(pgn):
    node = game.root()
    white_rating = int(game.headers['WhiteElo'])
    black_rating = int(game.headers['BlackElo'])
    if game.headers['Result'] == '1-0':
        result = 1
    elif game.headers['Result'] == '0-1':
        result = 0
    else:
        result = 0.5

    ply_count = 0
    while node.next():
        ply_count += 1
        prev_node = node
        node = node.next()

        if ply_count in (39, 40):
            min, sec = map(float, clock_regex.match(node.comment).groups())
            time_tenths_sec = min * 600 + sec * 10
            if ply_count == 39:
                white_time = time_tenths_sec
            else:
                black_time = time_tenths_sec
                # Only count games where there was a 30+ sec time difference
                #if abs(white_time-black_time) < 300:
                #    break
                eval = STOCKFISH.analyse(chess.Board(node.board().fen()), limit=chess.engine.Limit(depth=20))['score']
                try:
                    eval = eval.relative.cp/100
                except:
                    pass
                print(f'{game.headers["Link"]} {result} {white_rating} {black_rating} {white_time} {black_time} {eval}')
    game_cnt += 1
