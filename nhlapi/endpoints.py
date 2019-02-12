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

    def _process(self, detail, season, game_type, game_number):
        yr0 = Game._check_date_format(season, type_="season")
        gt = Game._check_game_type(game_type)
        yr1 = str(int(yr0) + 1)
        self.season_string = "".join([str(yr0), yr1])
        self.data.update({"games": []})

        if game_number == 0:
            with ThreadPoolExecutor(max_workers=5) as exc:
                for i in get_num_games(season=self.season_string):
                    gid = "".join([str(yr0), gt, i])
                    url = "/".join([self.url_template, gid, detail])
                    fut = exc.submit(requests.get, url, self.request_params, self.request_headers)
                    js = fut.result().json()
                    js.pop('copyright')
                    self.data['games'].append(js)
        else:
            gnum = Game._check_game_number(game_number, self.season_string)
            gid = "".join([str(yr0), gt, gnum])
            url = urljoin(self.url_template, gid, detail)
            req = requests.get(url, params=self.request_params, headers=self.request_headers)
            js = req.json()
            js.pop("copyright")
            self.data['games'].append(js)
        return self.data

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
        return self._process(detail=detail, season=season, game_type=game_type, game_number=game_number)

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
        return self._process(detail=detail, season=season, game_type=game_type, game_number=game_number)


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
        return self._process(detail=detail, season=season, game_type=game_type, game_number=game_number)

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
                self.request_params.update({"startTimecode": "_".join([dat, tt])})
                if game_number == 0:
                    with ThreadPoolExecutor(max_workers=5) as exc:
                        for i in get_num_games(season=self.season_string):
                            gid = "".join([str(yr0), gt, i])
                            url = urljoin(self.url_template, gid, detail)
                            fut = exc.submit(requests.get, url, self.request_params, self.request_headers)
                            self.data.append(fut.result().json())
                else:
                    gnum = Game._check_game_number(game_number, self.season_string)
                    gid = "".join([str(yr0), gt, gnum])
                    url = urljoin(self.url_template, gid, detail)
                    req = requests.get(url, params=self.request_params, headers=self.request_headers)
                    self.data.append(req.json())
                sleep((n_minutes//2) * 60)

        elif from_time is not None and n_minutes is None:
            tt = Game._check_time_format(from_time)
            self.request_params.update({"startTimecode": "_".join([dat, tt])})
            if game_number == 0:
                with ThreadPoolExecutor(max_workers=5) as exc:
                    for i in get_num_games(season=self.season_string):
                        gid = "".join([str(yr0), gt, i])
                        url = "/".join([self.url_template, gid, detail])
                        fut = exc.submit(requests.get, url, self.request_params, self.request_headers)
                        self.data.append(fut.result().json())
            else:
                gnum = Game._check_game_number(game_number, self.season_string)
                gid = "".join([str(yr0), gt, gnum])
                url = "/".join([self.url_template, gid, detail])
                req = requests.get(url, params=self.request_params, headers=self.request_headers)
                self.data.append(req.json())
        elif from_time is None and n_minutes is None:
            raise ValueError("either from_time OR n_minutes must be specified")
        elif from_time is not None and n_minutes is not None:
            raise ValueError("either from_time OR n_minutes must be specified")

    def __dict__(self):
        return self.data


class Teams(BaseEndpoint):

    def __init__(self):
        super().__init__()
        self.base_url = urljoin(self.url_template, "teams")
        self.data.update({"teams": []})
        self.ID = None
        self.expand = []
        self.season = None

        if self.ID is None:
            pass
        elif type(self.ID) is list:
            team_ext = ",".join([str(i) for i in self.ID])
            self.request_params.update({"teamId": team_ext})
        elif type(self.ID) is int:
            self.request_params.update({"teamId": str(self.ID)})

        if type(self.expand) is list:
            ext = ",".join([i for i in self.expand if Teams._check_expand_arg(i) is True])
            self.request_params.update({"expand": ext})
        else:
            pass

        if self.season is None:
            pass
        else:
            seas = Teams._format_season(season=self.season)
            self.request_params.update({"season": seas})

    @staticmethod
    def _check_expand_arg(x):
        valid = ["team.roster", "person.names", "team.schedule.next", "team.schedule.previous", 'team.stats']
        if x in valid:
            return True

    @staticmethod
    def _format_season(season):
        if type(season) is int:
            if len(season) == 4:
                return "".join([str(season), str(season + 1)])

            else:
                raise ValueError("Unable to interpret season argument. "
                                 "please retry request with first year "
                                 "of season only. (e.g. input 2017 for 2017-2018 season.)")
        elif type(season) is str:
            if len(season) == 4:
                return "".join([season, str(int(season) + 1)])

            else:
                raise ValueError("Unable to interpret season argument. "
                                 "please retry request with first year "
                                 "of season only. (e.g. input 2017 for 2017-2018 season.)")
        else:
            raise ValueError("Invalid season value. must be string or int of length 4,"
                             "representing the first year of the target season."
                             "(e.g. input 2017 for 2017-2018 season.)")

    def get(self, *args, **kwargs):
        req = requests.get(self.base_url, params=self.request_params,
                           headers=self.request_headers)
        js = req.json()['teams']
        self.data['teams'].extend(js)
        return self.data


    def roster(self):
        self.base_url = urljoin(self.base_url, 'roster')
        req = requests.get(self.base_url, params=self.request_params,
                           headers=self.request_headers)
        js = req.json()['teams']
        self.data['teams'].extend(js)
        return self.data

    def stats(self):
        self.base_url = urljoin(self.base_url, "stats")
        req = requests.get(self.base_url, params=self.request_params,
                           headers=self.request_headers)
        js = req.json()['teams']
        self.data['teams'].extend(js)
        return self.data


class Conferences(BaseEndpoint):

    def __init__(self):
        super().__init__()
        self.min_curr_id = 0
        self.baseurl = "https://statsapi.web.nhl.com/api/v1/conferences"

    def get(self, name, is_current=True):
        found = []
        if is_current:
            found = [c for c in self.current if c['name'].lower().find(name.lower()) > -1]
        return found

    def lookup_by_division(self, division=None):
        found = None
        if type(division) is int or division.isdigit() is True:
            dd = int(division)
            divs = Divisions().all_
            found = [d['conference'] for d in divs['divisions'] if d["id"] == dd]

        elif type(division) is str and division.isdigit() is False:
            dd = division.lower()
            divs = Divisions().all_
            found = [d['conference'] for d in divs['divisions'] if d["name"].lower().find(dd) > -1]

        return found

    def lookup_by_team(self, team=None):
        pass


    @property
    def current(self):
        req = requests.get(self.baseurl)
        self.min_curr_id += min([i["id"] for i in req.json()["conferences"]])

        js = req.json()
        for c in js['conferences']:
            c.update({"active": True})
        return js


    @property
    def inactive(self):
        wrld_cup = {"id" : 7,
                    "name" : "World Cup of Hockey",
                    "link" : "/api/v1/conferences/7",
                    "abbreviation" : "WCH",
                    "shortName" : "WCup",
                    "active" : False
                    }
        if self.min_curr_id == 0:
            self.min_curr_id += min([i["id"] for i in self.all_current])

        confs = {"copyright": None, "conferences": []}
        for i in range(1, self.min_curr_id):
            req = requests.get("/".join([self.baseurl, str(i)]))
            js = req.json()
            if confs['copyright'] is not None:
                confs.update({"copyright": js['copyright']})
            cnf = js['conferences'][0]
            cnf.update({"active": False})

            confs['conferences'].append(cnf)
        confs['conferences'].append(wrld_cup)
        return confs

    @property
    def all_(self):
        curr = self.current
        old = self.inactive
        old['conferences'].extend(curr['conferences'])
        return old


class Divisions(BaseEndpoint):

    def __init__(self):
        super().__init__()

        self.divs_list = []
        self.base_url = "https://statsapi.web.nhl.com/api/v1/divisions"

    def get(self, x, is_current=True):
        div = {"msg": "", "division": {}}
        divs = []
        if is_current:
            divs.extend(self.current['divisions'])
        else:
            divs.extend(self.inactive['divisions'])
        if type(x) is str and x.isdigit() is False:
            xx = x.lower()
            for i in divs:
                if xx == i['nameShort'].lower():
                    div['division'].update(i)
                elif xx == i['name'].lower():
                    div['division'].update(i)
                else:
                    pass

        elif type(x) is int or x.isdigit() is True:
            xx = int(x)
            for i in divs:
                if xx == i['id']:
                    div['division'].update(i)
        if len(div) == 0:
            div.update({"msg": "No matching divisions found"})

        return div

    def by_conference(self, conference):
        pass

    @property
    def current(self):
        req = requests.get(self.base_url)
        return req.json()

    @property
    def inactive(self):
        curr = self.current['divisions']
        curr_ids = [c['id'] for c in curr]
        divs = []
        for i in range(1, min(curr_ids)):
            req = requests.get("/".join([self.base_url, str(i)]))
            js = req.json()
            divs.extend(js['divisions'])
        kv = {}
        kv.update({"copyright": curr['copyright'], "divisions": divs})
        return kv

    @property
    def all_(self):
        curr = self.current
        old = self.inactive
        old['divisions'].extend(curr['divisions'])
        return old




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

    def __init__(self, ID, expand=None, start_date=None, end_date=None):
        self.ID = ID

    def _check_id(self, x):
        if type(x) is str and x.isdigit():
            return int(x)
        elif type(x) is int:
            return x
        else:
            raise TypeError("Invalid ID value must be string or int")

    def _check_expand(self, x):
        valid = []
        if x in valid:
            return True
        else:
            return False

    def _check_date_string(self, x):
        if len(x) == 10:
            if x.find("-") > -1:
                pts = x.split("-")
                if len(pts[0]) == 4:
                    return x
                else:
                    raise ValueError("Date format is ambiguous please use YYYY-MM-DD format for all dates")
            else:
                raise ValueError("Invalid Date format please use YYYY-MM-DD for all dates")
        else:
            raise ValueError("Invalid Date format please use YYYY-MM-DD for all dates")


class Standings(object):
    pass


class StatTypes(object):
    pass
