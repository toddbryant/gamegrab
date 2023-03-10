"""graph
Plots user's n-game moving rating average over time on chess.com.

Usage:
  graph.py [--time-class=TC] [--since=YYYYMM] [--moving-avg=N] [--download] USERNAME
  graph.py (-h | --help)

Options:
  --time-class=TC       Time class to consider (default blitz).
  --moving-avg=N        Show n-game moving rating average (default 500).
  --since=YYYYMM        Only download games on or after given year and month.
  --download            Re-download games history.
  -h --help             Show this screen.

Arguments:
  USERNAME      username to download games
"""

from docopt import docopt
import chess.pgn
import gamegrab
import os
import pandas as pd
import plotly.express as px

def main(arguments):
    username = arguments['USERNAME']
    time_class = arguments.get('--time-class') or 'blitz'
    moving_avg = int(arguments.get('--moving-avg') or 500)
    since = arguments['--since'] if '--since' in arguments else None

    pgnfile = f'{username}.pgn'
    if not os.path.exists(pgnfile) or arguments.get('--download'):
        gamegrab.main({'USERNAME': username, '--time-class': 'blitz',  '--outfile': pgnfile, '--color': None, '--since': None})

    history = []
    with open(pgnfile) as f:
        while headers := chess.pgn.read_headers(f):
            rating = int(headers['WhiteElo']) if headers['White'].lower() == username.lower() else int(headers['BlackElo'])
            date = headers['UTCDate']
            time = headers['UTCTime']

            history.append((f'{date} {time}', rating))

    # Games may not ordered correctly
    history = sorted(history, key=lambda x:x[0])
    
    dates, ratings = [], []
    for i, (time, rating) in enumerate(history[moving_avg:], start=moving_avg):
        date = time.split(' ')[0]
        avg = int(sum(x[1] for x in history[i-moving_avg+1:i+1]) / moving_avg) 
        if len(dates) == 0 or dates[-1] != date:
           dates.append(date)
           ratings.append(avg)
        else:
            ratings[-1] = avg
    
    df = pd.DataFrame({'date': dates, 'rating': ratings})
    fig = px.line(df, x="date", y="rating", title=f"{moving_avg}-game {time_class} rating average for {username}")

    fig.show()

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments)
