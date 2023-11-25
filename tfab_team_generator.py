import random
import tfab_consts
from tfab_database_handler import TFABDBHandler

class TeamGenerator(object):
    """
    Responsible for generating the most balanced teams out of a player list containing characteristics and ratings.
    """


    @staticmethod
    def generate_teams(player_dicts_list):
        """
        :param player_dicts_list: A list of dictionaries, each describing a player's Name, Characteristic, Rating.
        :return: A list of dictionaries, each describing a team's players and the sum of their ratings.
        """
        def distribute_goalkeepers(teams, players):
            """
            Distributes goalies between the different teams.
            :param teams:
            :param players:
            :return:
            """
            for i in range(3):
                index = 0
                for player in players:
                    if player[TFABDBHandler.PLAYERS_CHARACTERISTICS_KEY] == tfab_consts.PlayerCharacteristics["GOALKEEPER"]:
                        teams[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY].append(player)
                        break
                    index += 1
                players.pop(index)

        result_list = []
        for i in range(3):
            result_list.append({TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY: [],
                                TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY: 0})

        distribute_goalkeepers(result_list, player_dicts_list)
        random.shuffle(player_dicts_list)

        i = 0
        for player in player_dicts_list:
            result_list[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY].append(player)
            result_list[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY] = \
                result_list[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY] \
                + player[TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY]
            i = (i + 1) % 3

        return result_list