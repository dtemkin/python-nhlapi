from datetime import datetime as dt
from datetime import timedelta as td
from time import sleep
import requests
from nhlapi.utils import get_num_games
from nhlapi.base import BaseEndpoint
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin


class Game(BaseEndpoint):

    def __init__(self):
        super().__init__()
        self.season_string = None
        self.data = []

    @staticmethod
    def _format_game_number(x):
        sn = str(x)
        z = 4 - len(sn)
        return sn.zfill(z)

    @staticmethod
    def _check_date_format(s, type_):
        if type_ == "season":
            if type(s) is str:
                try:
                    int(s)
                except TypeError:
                    raise TypeError("Season must be in YYYY Format.")
                else:
                    if len(s) != 4:
                        raise ValueError("Invalid Season. Incorrect number of values Detected. Must be in format YYYYMMDD.")
                    else:
                        return s
            elif type(s) == type(dt.today()):
                date = s.strftime("%Y")
                return date
            elif type(s) == int:
                if s > 1940:
                    return str(s)
                else:
                    raise ValueError("Specified season out of range.")
            else:
                raise TypeError("Date must be valid string or datetime object")
        elif type_ == "date":
            if type(s) is str:
                try:
                    int(s)
                except TypeError:
                    raise TypeError("Date must be in YYYYMMDD format")
                else:
                    if len(s) != 8:
                        raise ValueError("Invalid date. Invalid number of digits. Must be in YYYYMMDD format")
                    else:
                        return s
            elif type(s) == type(dt.today()):
                date = s.strftime("%Y%m%d")
                return date
            elif type(s) is int:
                if s >= 19400101:
                    return str(s)
                else:
                    raise ValueError("Specified date out of range.")
            else:
                raise TypeError("Date must be valid string or datetime object")

    @staticmethod
    def _check_time_format(t):
        try:
            int(t)
        except TypeError:
            raise TypeError("Time must be in HHMMSS Format.")
        else:
            if len(t) != 6:
                raise ValueError("Invalid Date. Too Many Values Detected. Must be in format YYYYMMDD.")
            else:
                return t

    @staticmethod
    def _check_game_type(g):
        if type(g) is int:
            if g in range(1, 5):
                return "0"+str(g)
            else:
                raise ValueError("game_type must be value 1-4")
        elif type(g) is str:
            if len(g) < 2:
                if int(g) in range(1, 5):
                    return "0"+str(g)
                else:
                    raise ValueError("game_type must be value 1-4")
            elif len(g) == 2:
                if g.find("0") > -1:
                    return g
                else:
                    raise ValueError('game_type must be value in '
                                     '["01", "02", "03", "04"]')
            elif g in ['preseason', 'regular', 'playoffs', 'all-star']:
                _map = {"preseason": "01", "regular": "02",
                        "playoffs": "03", "all-star": "04"}
                return _map[g]
            else:
                raise ValueError('game_type must be '
                                 '["01", "02", "03", "04"],'
                                 'or ["preseason", "regular", '
                                 '"playoffs", "all-star"]')
        else:
            raise TypeError("Invalid game_type must be int or str")

    @staticmethod
    def _check_game_number(n, season_str):
        nx = get_num_games(season=season_str)
        ns = Game._format_game_number(n)
        if ns in nx:
            return ns
        else:
            raise IndexError("game_number exceeds number of games in selected season")

    def feed(self, season, game_type, game_number=0):
        """
        ######

        Returns all data about a specified game id including
        play data with on-ice coordinates and post-game
        details like first, second and third stars and any
        details about shootouts. The data returned is simply
        too large at often over 30k lines and is best
        explored with a JSON viewer

        ######
        :param game_number:
            For regular season and preseason games, this ranges from 0001 to the number of games played. (1271 for seasons with 31 teams (2017 and onwards) and 1230 for seasons with 30 teams).
            For playoff games, the 2nd digit of the specific number gives the round of the playoffs, the 3rd digit specifies the matchup, and the 4th digit specifies the game (out of 7).
        :param season:
            The season in which the game is occurring, e.g. '2017' for the 2017-2018 season
        :param game_type:
            2 digits give the type of game, where 01 = preseason,
            02 = regular season, 03 = playoffs, 04 = all-star
        :return:
        """
        detail = "feed/live"
        yr0 = Game._check_date_format(season, type_="season")
        gt = Game._check_game_type(game_type)
        yr1 = str(int(yr0) + 1)
        self.season_string = "".join([str(yr0), yr1])

        if game_number == 0:
            with ThreadPoolExecutor(max_workers=5) as exc:
                for i in get_num_games(season=self.season_string):
                    gid = "".join([str(yr0), gt, i])
                    url = "/".join([self.url_template, gid, detail])
                    fut = exc.submit(requests.get, url, self.params, self.headers)
                    self.data.append(fut.result().json())
        else:
            gnum = Game._check_game_number(game_number, self.season_string)
            gid = "".join([str(yr0), gt, gnum])
            url = urljoin(self.url_template, gid, detail)
            req = requests.get(url, params=self.params, headers=self.headers)
            self.data.append(req.json())

    def boxscore(self, season, game_type, game_number=0):
        """
        ######

        Returns far less detail than feed/live and is
        much more suitable for post-game details including
        goals, shots, PIMs, blocked, takeaways, giveaways and hits.

        ######
        :param game_number:
            For regular season and preseason games, this ranges from 0001 to the number of games played. (1271 for seasons with 31 teams (2017 and onwards) and 1230 for seasons with 30 teams).
            For playoff games, the 2nd digit of the specific number gives the round of the playoffs, the 3rd digit specifies the matchup, and the 4th digit specifies the game (out of 7).
        :param season:
            The season in which the game is occurring, e.g. '2017' for the 2017-2018 season
        :param game_type:
            2 digits give the type of game, where 01 = preseason,
            02 = regular season, 03 = playoffs, 04 = all-star
        :return:
        """
        detail = "boxscore"
        yr0 = Game._check_date_format(season, type_="season")
        gt = Game._check_game_type(game_type)
        yr1 = int(yr0) + 1
        self.season_string = "-".join([yr0, yr1])
        if game_number == 0:
            with ThreadPoolExecutor(max_workers=5) as exc:
                for i in get_num_games(season=self.season_string):
                    gid = "".join([str(yr0), gt, i])
                    url = urljoin(self.url_template, gid, detail)
                    fut = exc.submit(requests.get, url, self.params, self.headers)
                    self.data.append(fut.result().json())
        else:
            gnum = Game._check_game_number(game_number, self.season_string)
            gid = "".join([str(yr0), gt, gnum])
            url = urljoin(self.url_template, gid, detail)
            req = requests.get(url, params=self.params, headers=self.headers)
            self.data.append(req.json())

    def content(self, season, game_type, game_number=0):
        """
        ######

        Complex endpoint returning multiple types of media
        relating to the game including videos of shots, goals and saves.

        ######
        :param game_number:
            For regular season and preseason games, this ranges from 0001 to the number of games played. (1271 for seasons with 31 teams (2017 and onwards) and 1230 for seasons with 30 teams).
            For playoff games, the 2nd digit of the specific number gives the round of the playoffs, the 3rd digit specifies the matchup, and the 4th digit specifies the game (out of 7).
        :param season:
            The season in which the game is occurring, e.g. '2017' for the 2017-2018 season
        :param game_type:
            2 digits give the type of game, where 01 = preseason,
            02 = regular season, 03 = playoffs, 04 = all-star
        :return:
        """

        detail = "content"
        yr0 = Game._check_date_format(season, type_="season")
        gt = Game._check_game_type(game_type)

        yr1 = int(yr0) + 1
        self.season_string = "-".join([yr0, yr1])
        if game_number == 0:
            with ThreadPoolExecutor(max_workers=5) as exc:
                for i in get_num_games(season=self.season_string):
                    gid = "".join([str(yr0), gt, i])
                    url = urljoin(self.url_template, gid, detail)
                    fut = exc.submit(requests.get, url, self.params, self.headers)
                    self.data.append(fut.result().json())
        else:
            gnum = Game._check_game_number(game_number, self.season_string)
            gid = "".join([str(yr0), gt, gnum])
            url = urljoin(self.url_template, gid, detail)
            req = requests.get(url, params=self.params, headers=self.headers)
            self.data.append(req.json())

    def updates(self, season, game_type,
                game_date, game_number=0,
                from_time=None, n_minutes=None):
        """
        ######

        Returns updates (like new play events, updated stats for
        boxscore, etc.) for the specified game ID since the given
        startTimecode. If the startTimecode param is missing,
        returns an empty array.

        ######
        :param game_number:
            For regular season and preseason games, this ranges from 0001 to the number of games played. (1271 for seasons with 31 teams (2017 and onwards) and 1230 for seasons with 30 teams).
            For playoff games, the 2nd digit of the specific number gives the round of the playoffs, the 3rd digit specifies the matchup, and the 4th digit specifies the game (out of 7).
        :param season:
            The season in which the game is occurring, e.g. '2017' for the 2017-2018 season
        :param game_type:
            2 digits give the type of game, where 01 = preseason,
            02 = regular season, 03 = playoffs, 04 = all-star
        :param game_date:
            the date of the game, can be string in YYYYMMDD format or
            valid DateTime Object
        :param from_time:
            the starting timestamp from which to gather all subsequent game updates
        :param n_minutes:
            can be used in lieu of the from_time parameter to establish a timestamp,
            new data will be collected continuously until the game is terminated
            every n_minutes
        :return:
        """

        detail = "feed/live/diffPatch"
        yr0 = Game._check_date_format(season, type_="season")
        dat = Game._check_date_format(game_date, type_="date")
        gt = Game._check_game_type(game_type)
        yr1 = int(yr0) + 1
        self.season_string = "-".join([yr0, yr1])

        if from_time is None and n_minutes is not None:
            vals = None
            while vals != "stop":
                ts = dt.now() - td(minutes=n_minutes)
                tt = ts.strftime("%H%M%S")
                self.params.update({"startTimecode": "_".join([dat, tt])})
                if game_number == 0:
                    with ThreadPoolExecutor(max_workers=5) as exc:
                        for i in get_num_games(season=self.season_string):
                            gid = "".join([str(yr0), gt, i])
                            url = urljoin(self.url_template, gid, detail)
                            fut = exc.submit(requests.get, url, self.params, self.headers)
                            self.data.append(fut.result().json())
                else:
                    gnum = Game._check_game_number(game_number, self.season_string)
                    gid = "".join([str(yr0), gt, gnum])
                    url = urljoin(self.url_template, gid, detail)
                    req = requests.get(url, params=self.params, headers=self.headers)
                    self.data.append(req.json())
                sleep((n_minutes//2) * 60)

        elif from_time is not None and n_minutes is None:
            tt = Game._check_time_format(from_time)
            self.params.update({"startTimecode": "_".join([dat, tt])})
            if game_number == 0:
                with ThreadPoolExecutor(max_workers=5) as exc:
                    for i in get_num_games(season=self.season_string):
                        gid = "".join([str(yr0), gt, i])
                        url = "/".join([self.url_template, gid, detail])
                        fut = exc.submit(requests.get, url, self.params, self.headers)
                        self.data.append(fut.result().json())
            else:
                gnum = Game._check_game_number(game_number, self.season_string)
                gid = "".join([str(yr0), gt, gnum])
                url = "/".join([self.url_template, gid, detail])
                req = requests.get(url, params=self.params, headers=self.headers)
                self.data.append(req.json())
        elif from_time is None and n_minutes is None:
            raise ValueError("either from_time OR n_minutes must be specified")
        elif from_time is not None and n_minutes is not None:
            raise ValueError("either from_time OR n_minutes must be specified")

    def __iter__(self):
        return self.data


class Conference(object):

    def __init__(self, ID=None):
        pass


class Division(object):

    def __init__(self, ID=None):
        pass


class Draft(object):

    def __init__(self, year=None):
        pass

    def prospects(self, ID=None):
        pass


class People(object):

    def __init__(self, ID):
        pass

    def stats(self):
        pass


class Schedule(object):

    def __init__(self):
        pass


class Standings(object):
    pass


class StatTypes(object):

    def __init__(self):
        pass


class Teams(BaseEndpoint):

    def __init__(self, ID=None, season=None, expand=None):
        super().__init__()
        self.base_url = urljoin(self.url_template, "teams")
        
        if ID is None:
            pass
        elif type(ID) is list:
            team_ext = ",".join([str(i) for i in ID])
            self.params.update({"teamId": team_ext})
        elif type(ID) is int:
            self.params.update({"teamId": str(ID)})

        if type(expand) is list:
            ext = ",".join([i for i in expand if Teams._check_expand_arg(i) is True])
            self.params.update({"expand": ext})
        elif type(expand) is str:
            self.params.update({"expand": expand})
        else:
            pass

        if season is None:
            pass
        else:
            seas = Teams._format_season(season=season)
            self.params.update({"season": seas})


    @staticmethod
    def _check_expand_arg(x):
        valid = ["team.roster", "person.names", "team.schedule.next", "team.schedule.previous", 'team.stats']
        if x in valid:
            return True

    @staticmethod
    def _format_season(season):
        if type(season) is int:
            if len(season) == 4:
                return "".join([str(season), str(season+1)])

            else:
                raise ValueError("Unable to interpret season argument. "
                                 "please retry request with first year "
                                 "of season only. (e.g. input 2017 for 2017-2018 season.)")
        elif type(season) is str:
            if len(season) == 4:
                return "".join([season, str(int(season)+1)])

            else:
                raise ValueError("Unable to interpret season argument. "
                                 "please retry request with first year "
                                 "of season only. (e.g. input 2017 for 2017-2018 season.)")
        else:
            raise ValueError("Invalid season value. must be string or int of length 4,"
                             "representing the first year of the target season."
                             "(e.g. input 2017 for 2017-2018 season.)")

    def basic(self):
        req = requests.get(self.base_url, params=self.params, headers=self.headers)
        self.data = req.json()

    def roster(self):
        self.base_url = urljoin(self.base_url, 'roster')
        req = requests.get(self.base_url, params=self.params, headers=self.headers)
        self.data = req.json()

    def stats(self):
        self.base_url = urljoin(self.base_url, "stats")
        req = requests.get(self.base_url, params=self.params, headers=self.headers)
        self.data = req.json()

    def __iter__(self):
        return self.data
