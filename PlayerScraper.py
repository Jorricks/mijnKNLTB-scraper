import collections

import requests
import mmap
import time
import TerminalColors as BgColors
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
    This python file returns the requested scraped info for the given knltb numbers

    Params
    ----------
    The params are specified in the GeneralIO and explained in AbstractInputOutput.

    Returns (IO - A function is called in the IO class for returning this)
    ----------
    Debug information if requested
    IO - KNLTB ratings and the actual ratings of the people
    IO - Competition/Tournament results
"""


def load_player_page(number):
    """
        Loading a players KNLTB page into your filesystem.

        Parameters
        ----------
        number: int
            The KNLTB number of the person we want to scrape.

        Returns
        -------
        open(file)
            The variable of the open file
    """
    url = "http://publiek.mijnknltb.nl/Spelersprofiel.aspx?bondsnummer=" + str(number)
    r = requests.get(url, stream=True)
    filename = html_page_directory+'/last_knltb_player.html'
    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
    return open(filename, 'r+')


def get_player_data(openfile, knltb_number):
    """
        Scraping the information of the KNLTB players webpage which is already downloaded as a file.

        Parameters
        ----------
        openfile: open(file)
            The downloaded HTML file from the public KNLTB site for this KNLTB player.
        knltb_number: int
            KNLTB number of the person that is the owner of the page and we want to scrape

        Returns
        -------
        set_player_rating
            Sets the players rating in the IO.
        boolean: whether it is a valid player
    """
    s = mmap.mmap(openfile.fileno(), 0, access=mmap.ACCESS_READ)

    all_strings = ['<td class="knltb-public-label">Speelsterkte Enkel 2017</td>',
                   '<td class="knltb-public-label">Speelsterkte Dubbel 2017</td>',
                   '<td class="knltb-public-label">Rating Enkel</td>',
                   '<td class="knltb-public-label">Rating Dubbel</td>',
                   '<td class="knltb-public-label">Eindejaarsrating Enkel</td>',
                   '<td class="knltb-public-label">Eindejaarsrating Dubbel</td>']
    ratings = []
    debug_for_rating = ['Players single rating of this year is ', 'Players double rating of this year is ',
                        'Players current single rating ', 'Players current double rating ',
                        'Players single rating end of last year ', 'Players double rating end of last year ']

    current_length = 0
    for idx, string in enumerate(all_strings):
        current_length = s.find(string, current_length)+len(string)
        temp_value, current_length = get_td_val(s, "<td>", current_length)
        if temp_value is not False:
            ratings.append(temp_value)
            if debug:
                print(debug_for_rating[idx] + temp_value)

    s.close()

    if len(ratings) == 6:
        io.set_player_rating(knltb_number, ratings[2], ratings[3], ratings[4], ratings[5], ratings[0], ratings[1])
        return True
    else:
        io.invalid_player(knltb_number)
        return False


def get_player_changes_over_time(openfile, knltb_number):
    """
        Getting match information of a player.

        Parameters
        ----------
        openfile: open(file)
            The downloaded HTML file from the public KNLTB site for this KNLTB player.
        knltb_number: int
            KNLTB number of the person that is the owner of the page and we want to scrape

        Returns
        -------
        Nothing. It calls set_player_match_results in the IO.
    """
    s = mmap.mmap(openfile.fileno(), 0, access=mmap.ACCESS_READ)

    current_length = s.find('Spelersprofiel\r\n        :&nbsp;')
    current_length += len('Spelersprofiel\r\n        :&nbsp;')
    end_length = s.find('&nbsp;[', current_length)
    player_name = s[current_length:end_length]
    if len(player_name) > 40 or len(player_name) < 1:
        return False

    list_of_matches = []

    current_length = s.find('Partijresultaten competitie')
    tournament_length = s.find('Partijresultaten toernooien')
    current_length = s.find('<table class="knltb-geselecteerde-toernooien" ', current_length)
    for match_result in get_matches_information(s, current_length, player_name, False, tournament_length):
        list_of_matches.append(match_result)

    current_length = tournament_length
    current_length = s.find('<table class="knltb-geselecteerde-toernooien" ', current_length)
    for match_result in get_matches_information(s, current_length, player_name, True):
        list_of_matches.append(match_result)

    io.set_player_match_results(knltb_number, list_of_matches)


def get_matches_information(s, current_length, player_name, tournament_or_competition, stop_length=False):
    """
        Getting all matches with combining information for either tournaments or competition

        Parameters
        ----------
        s: mmap.mmap
            The downloaded HTML file opened through the mmap.mmap interface.
        current_length: int
            The current search location, character, we are in the file.
        player_name: string
            A string containing the players name
        tournament_or_competition: boolean
            Whether we are searching for a tournament match or a competition match.
            Tournament is true, Competition is false
        stop_length: specifies at which char we need to stop with searching

        Returns
        -------
        matches_info: mixed
            Containing a list of all competition matches played or all tournament matches played.
            Containment's can be found in get_match_info
    """
    cl = s.find("Datum", current_length)
    cl = s.find("<tr", cl)
    matches_info = []

    last_current_length = 0
    while cl > 0:
        if last_current_length > cl:
            print "Error: Infinite loop in trying to find info about ", player_name
            break
        else:
            last_current_length = cl

        if stop_length is not False and cl > stop_length:
            break
        match_info, cl = get_match_info(s, cl, player_name, tournament_or_competition)
        matches_info.append(match_info)
        cl = s.find("<tr", cl)
    return matches_info


""" Defining this to be the return type of get_match_info together with cl. """
MatchInfo = collections.namedtuple('Match', 'date event_name tournament_or_competition match_type category '
                                            'club_home club_out added_rating rating_at_start_match partner '
                                            'opponent1 opponent2 home_player who_won match_result')


def get_match_info(s, cl, player_name, tournament_or_competition):
    """
        Getting the information for a specific match.

        Parameters
        ----------
        s: mmap.mmap
            The downloaded HTML file opened through the mmap.mmap interface.
        cl: int
            The current search location, character, we are in the file.
            Renamed to make the lines fit nicer on a line.
        player_name: string
            A string containing the players name
        tournament_or_competition: boolean
            Whether we are searching for a tournament match or a competition match.
            Tournament is true, Competition is false

        Returns
        -------
        match_info: mixed
            date: string
            event_name: string
                Contains either the tournaments name or the competition name.
            tournament_or_competition: boolean
                Whether the match was a tournament or competition based match
                Tournament is true, Competition is false
            match_type: enum("Enkel","Dubbel")
            category(optional): string. False if not relevant
                Category of the tournament
            club_home(optional): string. False if not relevant
                What was the homeplaying club
                What was the out play club
            added_rating(optional): string. False if not relevant
                Containing the rating that was added due to the match
            rating_at_start_match: string
                Containing the rating you started the match with.
            partner(optional): string. False if not relevant
                Double partner
            opponent1: string
                Containing the opponent
            opponent2(optional): string. False if not relevant
                Containing the opponent
            home_player: boolean
                Whether it was a home match or outside
            who_won: string
                Resulting text who won
            match_result: string
                The score of the match
    """

    date, cl = get_td_val(s, '<td class="crm-wp-cell crm-wp-cell-padding-top">', cl)

    event_name, cl = get_td_val(s, '<td class="crm-wp-cell crm-wp-cell-padding-top" colspan="4">', cl)
    match_type, cl = get_td_val(s, '<td class="crm-wp-cell crm-wp-cell-padding-top crm-wp-cell-padding-bottom">', cl)
    if tournament_or_competition is True:
        category, cl = get_td_val(s, 'crm-wp-cell-padding-bottom" colspan="2">', cl)
        club_home = False
        club_out = False
    else:
        category = False
        club_home, cl = get_td_val(s, '<td class="crm-wp-cell crm-wp-cell-padding-top crm-wp-cell-padding-bottom">', cl)
        club_out, cl = get_td_val(s, '<td class="crm-wp-cell crm-wp-cell-padding-top crm-wp-cell-padding-bottom">', cl)

    added_rating, cl = get_td_val(s, 'crm-wp-cell-padding-top crm-wp-cell-padding-bottom" colspan="2">', cl)

    cl = s.find("<tr", cl)

    if match_type == "Dubbel":
        amount_of_players = 4
    else:
        amount_of_players = 2
    players = []
    player_name_lower = player_name.rsplit(' ', 1)
    player_name_lower = player_name_lower[0] + ' ' + player_name_lower[1].lower()
    rating_at_start_match = False
    for x in range(0, amount_of_players):
        random_player_name, cl = get_td_val(s, '" target="_blank">', cl, " (")
        if random_player_name == player_name or random_player_name == player_name_lower:
            rating_at_start_match, cl = get_td_val(s, 'nbsp;', cl, ")</a>")
        players.append(random_player_name)

    try:
        index_of_player = players.index(player_name)
    except ValueError:
        player_name_lower = player_name.rsplit(' ', 1)
        player_name_lower = player_name_lower[0]+' '+player_name_lower[1].lower()
        index_of_player = players.index(player_name_lower)

    if match_type == "Dubbel":
        if index_of_player == 0 or index_of_player == 1:
            home_player = True
            if index_of_player == 0:
                partner = players[1]
            else:
                partner = players[0]
            opponent1 = players[2]
            opponent2 = players[3]
        else:
            home_player = False
            if index_of_player == 2:
                partner = players[3]
            else:
                partner = players[2]
            opponent1 = players[0]
            opponent2 = players[1]
    else:
        partner = False
        if index_of_player == 0:
            home_player = True
            opponent1 = players[1]
        else:
            home_player = False
            opponent1 = players[0]
        opponent2 = False

    who_won, cl = get_td_val(s, 'style="vertical-align:middle;white-space:nowrap">', cl)
    match_result, cl = get_td_val(s, 'style="vertical-align:middle">', cl)

    match = MatchInfo(date, event_name, tournament_or_competition, match_type, category, club_home, club_out,
                      added_rating, rating_at_start_match, partner, opponent1, opponent2, home_player, who_won,
                      match_result)

    return match, cl


def get_td_val(s, identifier, current_length, deidentifier="</td>"):
    """
        Getting the td value of

        Parameters
        ----------
        s: mmap.mmap
            The downloaded HTML file opened through the mmap.mmap interface.
        identifier: string
            A unique string that we can search for that is followed by the <td>*</td> that we are looking for.
        current_length: int
            The current search location, character, we are in the file.
        deidentifier: string
            The string that makes sure we are at the end of the thing we were searching for.

        Returns
        -------
        temp_value: string
            Containing the value we were searching for
        end_length+len(deidentifier): int
            The character we visited as last+1 in our file
    """
    current_length = s.find(identifier, current_length) + len(identifier)
    end_length = s.find(deidentifier, current_length)
    temp_value = s[current_length: end_length]
    if len(temp_value) < 100:
        return temp_value, end_length + len(deidentifier)
    else:
        return False, False


try:
    """
        The main loop that combines it all

        We start out by checking if the directory exists on the file system, if not we create it.
        Then we follow by getting the KNLTB players and the settings.
        Then as long as we have a remaining player:
            We fetch his page
            We get his ratings
            If set in settings we also get the changes over time
        Finally we say bye bye

        Of course you should be able to interrupt with your keyboard, hence by Ctrl+C you can exit the program early.
    """

    if not os.path.exists(html_page_directory):
        os.makedirs(html_page_directory)

    counter = 0
    knltb_numbers = io.get_players
    want_rating_changes, debug = io.get_settings()
    print BgColors.TerminalColors.ok_blue + "Let's start!" + BgColors.TerminalColors.end_color
    while counter < len(knltb_numbers):
        nr = knltb_numbers[counter]
        html_page = load_player_page(nr)
        if debug:
            print('Got player: {}'.format(nr))
        get_player_data(html_page, nr)

        if want_rating_changes is True:
            get_player_changes_over_time(html_page, nr)
        counter += 1
        time.sleep(delay_time)

    if counter == len(knltb_numbers):
        print('Finished Bye Bye, exiting..')

except KeyboardInterrupt:
    print('Received CTRL + C, exiting..')
