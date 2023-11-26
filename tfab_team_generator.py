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
            random.shuffle(players)
            for i in range(3):
                index = 0
                for player in players:
                    if player[TFABDBHandler.PLAYERS_CHARACTERISTICS_KEY] == tfab_consts.PlayerCharacteristics["GOALKEEPER"]:
                        teams[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY].append(player)
                        break
                    index += 1
                players.pop(index)

        def get_best_remaining_player(players):
            random.shuffle(players)
            best_rating = 0
            index = 0

            i = 0
            for player in players:
                curr_rating = player[TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY]
                if curr_rating > best_rating:
                    best_rating = curr_rating
                    index = i
                i += 1

            return players.pop(index)

        result_list = []
        for i in range(3):
            result_list.append({TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY: [],
                                TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY: 0})

        distribute_goalkeepers(result_list, player_dicts_list)
        random.shuffle(player_dicts_list)

        i = 0
        while player_dicts_list:
            best_player = get_best_remaining_player(player_dicts_list)
            result_list[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY].append(best_player)
            result_list[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY] += best_player[TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY]
            i = (i + 1) % 3

        return result_list