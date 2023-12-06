import random
import tfab_consts
from tfab_database_handler import TFABDBHandler
import tfab_app
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, value

class TeamGenerator(object):
    """
    Responsible for generating the most balanced teams out of a player list containing characteristics and ratings.
    """
    @staticmethod
    def generate_teams(player_dicts_list, using_ranks=False):
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
            for i in range(len(teams)):
                index = 0
                for player in players:
                    if player[TFABDBHandler.PLAYERS_CHARACTERISTICS_KEY] == tfab_consts.PlayerCharacteristics["GOALKEEPER"]:
                        teams[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY].append(player)
                        break
                    index += 1
                players.pop(index)

        result_list = []
        amount_of_teams = 3

        for i in range(amount_of_teams):
            result_list.append({TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY: [],
                                TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY: 0})

        #TODO: This currently only works when there are enough goalkeepers!
        #distribute_goalkeepers(result_list, player_dicts_list)
        random.shuffle(player_dicts_list)
        db = tfab_app.TFABApplication.get_instance().db
        num_members = len(player_dicts_list)

        # Create the LP problem
        prob = LpProblem("GroupPartitioning", LpMinimize)

        # Creating a variable for each player-team combination.
        # Our goal is to later create a restriction that enforces that:
        # X_i_j equals 1 if player <I> belongs to group <J>
        x = {(i, j): LpVariable(f"x_{i}_{j}", 0, 1, "Binary") for i in range(num_members) for j in range(amount_of_teams)}

        # Constraints: each member is assigned to exactly one group
        for i in range(num_members):
            prob += lpSum(x[i, j] for j in range(amount_of_teams)) == 1, f"AssignOnce_{i}"

        # Constraints: each group has the same amount of team members
        for j in range(amount_of_teams):
            prob += lpSum(x[i, j] for i in range(num_members)) == (num_members // amount_of_teams), f"GroupSize_{j}"

        # Define m as the weakest team, and M as the strongest team
        m = LpVariable("m", 0, 100)
        M = LpVariable("M", 0, 100)

        for j in range(amount_of_teams):
            prob += m <= lpSum(x[i, j] * player_dicts_list[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY]
                               for i in range(num_members))
            prob += M >= lpSum(x[i, j] * player_dicts_list[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY]
                               for i in range(num_members))

        # Objective: minimize the difference between the highest-ranked team and the lowest-ranked team
        prob += M - m, "Objective"

        if using_ranks:
            for j in range(amount_of_teams):
                prob += lpSum(x[i, j] * (db.get_player_characteristic(player_dicts_list[i][db.PLAYERS_NAME_KEY]) == tfab_consts.PlayerCharacteristics["GOALKEEPER"]) for i in range(num_members)) == 1

            # Define att_max as the largest amount of attackers in one team, and att_min as the smallest amount
            att_min = LpVariable("att_min", 0, 10)
            att_max = LpVariable("att_max", 0, 10)

            # The same for defenders
            def_min = LpVariable("def_min", 0, 10)
            def_max = LpVariable("def_max", 0, 10)

            # Then make sure it is correct globally - for all role-based players
            role_min = LpVariable("role_min", 0, 10)
            role_max = LpVariable("role_max", 0, 10)

            for j in range(amount_of_teams):
                prob += role_min <= lpSum(
                    x[i, j] * (db.get_player_characteristic(player_dicts_list[i][db.PLAYERS_NAME_KEY]) in
                               [tfab_consts.PlayerCharacteristics["OFFENSIVE"], tfab_consts.PlayerCharacteristics["DEFENSIVE"]])
                    for i in range(num_members))
                prob += role_max >= lpSum(
                    x[i, j] * (db.get_player_characteristic(player_dicts_list[i][db.PLAYERS_NAME_KEY]) in
                               [tfab_consts.PlayerCharacteristics["OFFENSIVE"],
                                tfab_consts.PlayerCharacteristics["DEFENSIVE"]])
                    for i in range(num_members))
                prob += att_min <= lpSum(
                    x[i, j] * (db.get_player_characteristic(player_dicts_list[i][db.PLAYERS_NAME_KEY]) ==
                         tfab_consts.PlayerCharacteristics["OFFENSIVE"])
                    for i in range(num_members))
                prob += att_max >= lpSum(
                    x[i, j] * (db.get_player_characteristic(player_dicts_list[i][db.PLAYERS_NAME_KEY]) ==
                    tfab_consts.PlayerCharacteristics["OFFENSIVE"])
                    for i in range(num_members))
                prob += def_min <= lpSum(
                    x[i, j] * (db.get_player_characteristic(player_dicts_list[i][db.PLAYERS_NAME_KEY]) ==
                    tfab_consts.PlayerCharacteristics["DEFENSIVE"])
                    for i in range(num_members))
                prob += def_max >= lpSum(
                    x[i, j] * (db.get_player_characteristic(player_dicts_list[i][db.PLAYERS_NAME_KEY]) ==
                    tfab_consts.PlayerCharacteristics["DEFENSIVE"])
                    for i in range(num_members))

            prob += att_max - att_min <= 1
            prob += def_max - def_min <= 1
            prob += role_max - role_min <= 1


        # Solve the LP problem
        prob.solve()

        for i in range(num_members):
            for j in range(amount_of_teams):
                if value(x[i, j]) == 1:
                    result_list[j][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY].append(player_dicts_list[i])
                    result_list[j][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY] += player_dicts_list[i][TFABDBHandler.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY]

        return result_list