from collections import namedtuple

import requests
import time
import mmap
import pprint
import os

"""
    Please specify here which InputOutput you will be using.
    Create your own..
    Also specify whether you are debugging
     and what your html_page_directory should be.
"""
# import YourIO as InputOutput
# io = InputOutput.YourIO()
import GeneralIO as InputOutput
io = InputOutput.GeneralIO()

debug = False  # Whether you want verbose information.
html_page_directory = "pages/"  # Which dictionary the html files should end up in.
delay_time = 0.75  # Time between page loads. The lower, the more risky.. Keep it at at least 0.5!
"""
    Specifying the named tuples which will contain all the data.
    This is also how the data will be fed onto the IO(input output class).
"""
TeamInfo = namedtuple('TeamInfo', ['FullDay', 'Day', 'Type', 'Class', 'Name'])
TeamResult = namedtuple('TeamResult', ['Name', 'Position', 'TimesPlayed', 'Won',
                                       'Draw', 'Lost', 'PointsWon', 'PointsLost', 'OwnTeam'])
TeamPlanning = namedtuple("TeamPlanning", ["OwnTeamName", "Opponent", "PlayAtHome", "DayCount", "Date",
                                           "Result", "Status", "CatchUp", "Commencement", "Present",
                                           "CourtType", "Comments"])

"""
    Global variable for keeping track of all the teams of the specific club.
"""
all_friendly_teams_in_this_competition = []

"""
    This python file returns the requested scraped info for all competition teams of your club

    Params
    ----------
    The params are specified in the GeneralIO and explained in AbstractInputOutput.

    Returns (IO - A function is called in the IO class for returning this)
    ----------
    Debug information if requested
    IO - Competition team information of when they will play and what their current result is.
"""


def load_request_into_file(request, filename):
    """
        Loading a specific html page request into a file.

        Parameters
        ----------
        request: request
            The request of the specific page.
        filename: string
            The name the file should be

        Returns
        -------
        mmap.mmap: mmap.mmap file
            The open file.
    """
    with open(filename, 'wb') as fd:
        for chunk in request.iter_content(chunk_size=128):
            fd.write(chunk)
    openfile = open(filename, 'r')
    return mmap.mmap(openfile.fileno(), 0, access=mmap.ACCESS_READ)


def find_competition_uid(competition_name):
    """
        Given a specific competition_name, find the unique identifier such that we can find all the information of the
        team afterwards.

        Parameters
        ----------
        competition_name: string
            Containing the string of the competition. Example = "Winteroutdoorcompetitie Zuid 2016/2017"

        Returns
        -------
        uid: string
            The unique identifier of the competition.

        Raises errors
        -------
        NameError, when the specified competition could not be found.
    """
    url = "http://publiek.mijnknltb.nl/StandenEnUitslagenZoeken.aspx"
    r = requests.get(url, stream=True)

    s = load_request_into_file(r, html_page_directory+'/knltb_competition_page.html')

    current_length = s.find(competition_name)
    current_length = s.rfind('value="', 0, current_length)
    current_length += len('value="')
    begin_length = current_length
    stop_length = s.find('">', begin_length, begin_length + 200)
    uid = s[begin_length:stop_length]
    if len(uid) < 5:
        raise NameError('Specified competition, '+competition_name+', does not exist!')
    return s[begin_length:stop_length]


def get_all_teams_in_competition(competition_uid, association):
    """
        Given a specific competition_uid and association, we find all playing teams for that competition and
        association.

        Parameters
        ----------
        competition_uid: string
            Containing the unique identifier of a specific competition.
        association: string
            Containing the name of your association

        Returns
        -------
        competition_links: list<string>
            The unique identifiers for the specific teams competitions

        Raises errors
        -------
        NameError, when there was not a single team to be found
    """
    url = "http://publiek.mijnknltb.nl/StandenEnUitslagenZoeken.aspx"
    payload = {'id': competition_uid, 'vereniging': association}
    r = requests.get(url, stream=True, params=payload)

    s = load_request_into_file(r, html_page_directory+'/knltb_competition_page.html')

    competition_links = []
    search_string = "<a href=\"StandenEnUitslagen.aspx?id="
    current_find_result = s.find(search_string)
    while current_find_result > 0:
        current_find_result += len(search_string)
        current_end = s.find('">', current_find_result, current_find_result + 100)
        competition_links.append(s[current_find_result:current_end])
        current_find_result = s.find(search_string, current_end)
    if len(competition_links) < 1:
        raise NameError('Specified competition with association, '+association+', does not exist!')
    return competition_links

def get_current_season(competition_name):
    if "Zomer" in competition_name or "Voorjaar" in competition_name:
        return "Zomer"
    elif "Winter" in competition_name:
        return "Winter"
    elif "Najaars" in competition_name:
        return "Najaars"
    else:
        return "Zomer"


def get_team_info(competition_team_uid, association):
    """
        Given a specific competition_team_uid and association, we find all information of this specific teams
        competition.

        Parameters
        ----------
        competition_team_uid: string
            Containing the unique identifier of a specific competition for a given team.
        association: string
            Containing the name of your association

        Returns
        -------
        team_link: string / url
            Contains the link to the public KNLTB site for this teams competition
        team_information: string
            Contains information of which league and more.
        team_results_info:
            Information of what the current distribution is between how much they are located in the competition ATM.
        s: mmap.mmap file
            The open file.
    """
    url = "http://publiek.mijnknltb.nl/StandenEnUitslagen.aspx"
    payload = {'id': competition_team_uid}
    r = requests.get(url, stream=True, params=payload)
    print("Fetching for the next team at this link :" + r.url)
    team_link = r.url

    s = load_request_into_file(r, html_page_directory+'/knltb_competition_page.html')

    current_find_result = s.find("<div class=\"knltb-public-label\">") + len("<div class=\"knltb-public-label\">")
    current_find_result = s.find("<div class=\"knltb-public-label\">", current_find_result) + \
        len("<div class=\"knltb-public-label\">")
    current_end_result = s.find("</div>", current_find_result)
    team_information = find_out_what_for_competition_this_is(s[current_find_result:current_end_result])

    if debug:
        pprint.pprint(team_information)

    team_results_info = []
    search_string_for_single_team = "<tr bgcolor="
    current_find_result = s.find(search_string_for_single_team)
    while current_find_result > 0:
        current_find_result = s.find("\">", current_find_result) + len(';">')
        current_find_result = s.find("\">\r\n", current_find_result) + len("\">\r\n")
        end_find_result = s.find("\r\n", current_find_result)
        total_string = s[current_find_result:end_find_result].strip()
        position = total_string[0:1]
        team_name = total_string[2:]
        if association in team_name:
            all_friendly_teams_in_this_competition.append(team_name)
        times_played, current_find_result = get_next_column_value(s, current_find_result)
        times_won, current_find_result = get_next_column_value(s, current_find_result)
        times_draw, current_find_result = get_next_column_value(s, current_find_result)
        times_lost, current_find_result = get_next_column_value(s, current_find_result)
        points_won, current_find_result = get_next_column_value(s, current_find_result)
        points_lost, current_find_result = get_next_column_value(s, current_find_result)

        if team_name.find(association) >= 0:
            own_team = True
        else:
            own_team = False

        result_team = TeamResult(team_name, position, times_played, times_won, times_draw, times_lost,
                                 points_won, points_lost, own_team)
        if debug:
            pprint.pprint(result_team)

        team_results_info.append(result_team)
        current_find_result = s.find(search_string_for_single_team, current_find_result)

    return team_link, team_information, team_results_info, s


def get_next_column_value(s, begin_length, identifier='<td class="crm-wp-cell" width="30">',
                          deidentifier="</td>"):
    """
        Function for getting something in between an identifier and deidentifier.

        Parameters
        ----------
        s: mmap.mmap file
            The open file.
        begin_length: int
            Current position in the document
        identifier: string
            The identifier, where the value should be between the identifier and deidentifier.
        deidentifier: string
            The deidentifier, where the value should be between the identifier and deidentifier.

        Returns
        -------
        s[a:b]: string
            String containing the requested value, if found.
        end_length: int
            New current position in the document
    """
    begin_length = s.find(identifier, begin_length) + len(identifier)
    end_length = s.find(deidentifier, begin_length)
    return s[begin_length:end_length], end_length


def find_out_what_for_competition_this_is(s):
    """
        Function to figure out what for competition this is. Just as the name says ^^

        Parameters
        ----------
        s: mmap.mmap file
            The open file but scoped to most info of the team.
        out_of_scope_s: mmap.mmap file
            The open file but scoped to the hole file.

        Returns
        -------
        team_information: NamedTuple TeamInfo
            Containing all information about this competition.
    """
    original_s = s
    end_of_string = 9999
    type_comp = "unknown.. little error"
    comp_class = "unknown.. little error"
    if s.find("Gemengd") >= 0:
        end_of_string = s.find("Gemengd")
        type_comp = s[end_of_string:]
    elif s.find("Heren") >= 0:
        end_of_string = s.find("Heren")
        type_comp = s[end_of_string:]
    elif s.find("Dames") >= 0:
        end_of_string = s.find("Dames")
        type_comp = s[end_of_string:]
    elif s.find("Jongens") >= 0:
        end_of_string = s.find("Jongens")
        type_comp = s[end_of_string:]
    elif s.find("Meisjes") >= 0:
        end_of_string = s.find("Meisjes")
        type_comp = s[end_of_string:]

    type_comp = type_comp[0:len(type_comp) - 1]

    s = s[5:end_of_string]
    day = s[:s.find(" ")]

    begin_of_string = 50
    if s.find("Eredivisie") >= 0:
        begin_of_string = s.find("Eredivisie")
        comp_class = "Eredivisie"
    elif s.find("Eerste divisie") >= 0:
        begin_of_string = s.find("Eerste divisie")
        comp_class = "Eerste divisie"
    elif s.find("Hoofdklasse") >= 0:
        begin_of_string = s.find("Hoofdklasse")
        comp_class = "Hoofdklasse"
    elif s.find("Overgangsklasse") >= 0:
        begin_of_string = s.find("Overgangsklasse")
        comp_class = "Overgangsklasse"
    elif s.find("Open klasse") >= 0:
        begin_of_string = s.find("Open klasse")
        comp_class = "Open klasse"
    elif s.find("klasse") >= 0:
        begin_of_string = s.find("klasse")
        comp_class = s[begin_of_string - 3:begin_of_string + len("klasse")]
        begin_of_string -= 3

    full_day = s[:begin_of_string - 1]

    team_information = TeamInfo(full_day, day, type_comp, comp_class, original_s)
    return team_information


def get_team_planning(s, association):
    """
        Function that gets the team planning.

        Parameters
        ----------
        s: mmap.mmap file
            The open file.
        association: string
            Containing the name of your association

        Returns
        -------
        team_planning: List of NamedTuples TeamPlanning
            Containing the planning of this team.
    """
    team_planning = []
    current_index = s.find(">" + association)
    current_day_index = s.find('>Dag ') + len('>Dag ')
    while current_index > 0:
        current_index = s.rfind("<tr title=", 0, current_index)
        commencement, current_index = get_next_column_value(s, current_index, "Aanvang:&lt;/b> ", "&lt;br/>")
        present, current_index = get_next_column_value(s, current_index, "Aanwezig:&lt;/b> ", "&lt;br/>")
        court_type, current_index = get_next_column_value(s, current_index, "Baansoort:&lt;/b> ", "&lt;br/>")
        comment, current_index = get_next_column_value(s, current_index, "Opmerking:&lt;/b>", "\"")
        team_1, current_index = get_next_column_value(s, current_index, "<td class=\"crm-wp-cell\">", "</td>")
        team_2, current_index = get_next_column_value(s, current_index, "<td class=\"crm-wp-cell\">", "</td>")
        if team_1.find(association) >= 0:
            own_team = team_1
            play_at_home = True
            opponent = team_2
        else:
            own_team = team_2
            play_at_home = False
            opponent = team_1
        result_day, current_index = get_next_column_value(s, current_index, "<td class=\"crm-wp-cell\">", "</td>")
        status, current_index = get_next_column_value(s, current_index, "<td class=\"crm-wp-cell\">", "</td>")
        catch_up, current_index = get_next_column_value(s, current_index, "<td class=\"crm-wp-cell\">", "</td>")

        day_count = s[current_day_index:current_day_index + 1]
        date = s[current_day_index + 3:current_day_index + 13]

        current_index = s.find(">" + association, current_index)
        new_day_index = s.find('>Dag ', current_day_index) + len('>Dag ')
        if new_day_index < current_index:
            current_day_index = new_day_index

        planning = TeamPlanning(own_team, opponent, play_at_home, day_count, date, result_day, status, catch_up,
                                commencement, present, court_type, comment)

        if debug:
            pprint.pprint(planning)

        team_planning.append(planning)
    return team_planning

try:
    """
        The main loop that combines it all

        We start out by checking if the directory exists on the file system, if not we create it.
        Then we follow by getting the main page of competition information.
        Followed by finding the required competition seasons.
        Then for each competition team:
            We fetch the page
            We get all the information
            We send this information to the input output
        Finally we say bye bye

        Of course you should be able to interrupt with your keyboard, hence by Ctrl+C you can exit the program early.
    """
    if not os.path.exists(html_page_directory):
        os.makedirs(html_page_directory)

    competitions = io.get_competition()
    # Competitions has a structure of [0] - name, [1] - club
    for competition_season in competitions:
        competition_season.append(find_competition_uid(competition_season[0]))
        print ('Competition season {} has competition uid {}'.format(competition_season[0], competition_season[2]))
        time.sleep(delay_time)

    # Competitions has a structure of [0] - name, [1] - club, [2] - uid of competition-season
    for competition_season in competitions:
        competition_season.append(get_all_teams_in_competition(competition_season[2], competition_season[1]))
        time.sleep(delay_time)

    # Competitions has a structure of [0] - name, [1] - club, [2] - uid of competition, [3] - list of uid teams
    for competition_season in competitions:
        for team in competition_season[3]:
            del all_friendly_teams_in_this_competition[:]
            current_season_name = get_current_season(competition_season[0])
            team_url, team_info, team_results, file_mmap = get_team_info(team, competition_season[1])
            team_list = [team_url, team_info, team_results, get_team_planning(file_mmap, competition_season[1])]
            io.set_competition(current_season_name, all_friendly_teams_in_this_competition,
                               team_url, team_info, team_results,
                               get_team_planning(file_mmap, competition_season[1]))
            file_mmap.close()
            time.sleep(delay_time)

    print('Finished Bye Bye, exiting..')

except KeyboardInterrupt:
    print('Received CTRL + C, exiting..')
