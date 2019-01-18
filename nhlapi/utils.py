from csv import DictReader
import os


def get_num_games(season):
    file_header = ["num", "season", "num_teams",
                   "reg_season_games", "total_games"]

    f = open(os.path.join(os.getcwd(), "seasons_info.csv"), mode='r')
    readr = DictReader(f, fieldnames=file_header)
    n_games = 0
    max_n_games = 0
    if season == "2004-2005":
        return []
    else:
        for row in readr:
            if row['season'] == season:
                n_games += row['total_games']
            else:
                pass
            if row['total_games'] > max_n_games:
                max_n_games = row['total_games']
            else:
                pass

        if n_games == 0:
            n_games = max_n_games + 100

        return [str(i).zfill(4-len(str(i))) for i in range(1, n_games)]
