from abc import ABCMeta, abstractmethod
import pprint


class AbstractInputOutput(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_settings(self):
        """ Specifies the settings for running the application.

            Returns
            ----------
            arg1 : boolean
                Whether you also want match results
            arg2 : boolean
                Whether we should output in debug modus
        """
        return True, True

    @abstractmethod
    def get_players(self):
        """ Specifies which players we should scrape.

            Returns
            ----------
            arg1 : list<integers>
                All the KNLTB numbers of people you want to scrape
        """
        return [20889364, 13343424, 19621159, 20889320]

    @abstractmethod
    def get_competition(self):
        """ Specifies which competition you want to scrape for which associations

            Returns
            ----------
            arg1 : list<list<competition, association abbreviation>
                Competition is which specific competition you are playing in
                Association abbreviation is the abbreviation used by the knltb at publiek.knltb.nl
        """
        competitions = [["Winteroutdoorcompetitie Zuid 2016/2017", "A.T.C."]]
        return competitions

    @abstractmethod
    def set_player_rating(self, knltb_number, act_e_rating, act_d_rating, old_e_rating, old_d_rating,
                          year_e_rating, year_d_rating):
        """ Specifies what you want to do with the information that was scraped about the ratings of a person.

            Params
            ----------
            knltb_number: The number of the person that was scraped
            act_e_rating: Actual single rating
            act_d_rating: Actual double rating
            old_e_rating: Last years ending single rating
            old_d_rating: Last years ending double rating
            year_e_rating: The rounded actual single rating
            year_d_rating: The rounded actual double rating
            set_or_print: Set whether you want to upload them or print them

            Default
            ----------
            Prints the information in a readable manner.
        """
        print("Player {} , Stats {} - {} / {} - {} / {} - {}".format(knltb_number, act_e_rating, act_d_rating,
                                                                     old_e_rating, old_d_rating, year_e_rating,
                                                                     year_d_rating))

    def set_player_match_results(self, knltb_number, matches):
        """ Specifies what you want to do with the information that was scraped about the matches this person played.

            Params
            ----------
            knltb_number: The number of the person that was scraped
            MatchInfo = collections.namedtuple('Match',
                'date event_name tournament_or_competition match_type category '
                'club_home club_out added_rating rating_at_start_match partner '
                'opponent1 opponent2 home_player who_won match_result'): named_tuple
                Containing all information.

            Default
            ----------
            Prints the match information in a readable manner.
        """
        pprint.pprint(matches)

    @abstractmethod
    def invalid_player(self, knltb_number):
        """ Specifies what to do when we can not find a specific player. This could happen when the board of the
                association decided to cancel a registration but forgot to update this in the system.

            Params
            ----------
            knltb_number: The number of the person that we tried to scrape but did not exist or did not have any
                results yet

            Default
            ----------
            Prints the information in a readable manner.
        """
        print 'Invalid player: {}'.format(knltb_number)

    @abstractmethod
    def set_competition(self, season, own_teams, comp_url, comp_info, comp_results, comp_play_times):
        """ Specifies what to do with the information of competition results.

            Params
            ----------


            Default
            ----------
            Prints the information in a readable manner.
        """
        pprint.pprint(season)
        pprint.pprint(own_teams)
        pprint.pprint(comp_url)
        pprint.pprint(comp_info)
        pprint.pprint(comp_results)
        pprint.pprint(comp_play_times)
