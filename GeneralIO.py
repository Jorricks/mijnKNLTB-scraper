from AbstractInputOutput import AbstractInputOutput


class GeneralIO(AbstractInputOutput):
    def get_settings(self):
        return True, True
        # return input('Wil je ook de veranderingen van de rating over tijd? \n'
        #              'Vul dit in op de volgende manier '
        #              'Ja = "True" en Nee = "False", zonder " tekens : \n'), \
        #        input('Hoeveel output wil je terug hebben in de console? \n'
        #              'Normaal = "False" en Maximaal = "True" : \n')

    def get_players(self):
        return [20889364, 22582657]
        # return input('Wat zijn de KNLTB nummers die je wil scrapen? \n'
        #              'Vul dit in op de volgende manier '
        #              '[20889364, 13343424, 19621159, ....., 20889320] : \n')

    def get_competition(self):
        return super(GeneralIO)

    def set_player_rating(self, knltb_number, act_e_rating, act_d_rating, old_e_rating, old_d_rating,
                          year_e_rating, year_d_rating):
        return super(GeneralIO, self).set_player_rating(knltb_number, act_e_rating, act_d_rating, old_e_rating,
                                                        old_d_rating, year_e_rating, year_d_rating)

    def invalid_player(self, knltb_number):
        return super(GeneralIO, self).invalid_player(knltb_number)

    def set_competition(self, season, own_teams, comp_url, comp_info, comp_results, comp_play_times):
        return super(GeneralIO, self).set_competition(season, own_teams, comp_info, comp_results, comp_play_times)
