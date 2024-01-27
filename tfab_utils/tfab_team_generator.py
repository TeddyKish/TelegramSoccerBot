import random
from tfab_framework.tfab_consts import Consts as TConsts
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, value, PULP_CBC_CMD

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
        def get_player_tier(player_list, requested_player):
            """
            Assumes <player_list> is sorted from the best player (in terms of rating) to the worst.
            :param player_list: The players list.
            :param requested_player: The player we wish to acquire the tier from.
            :return: The tier of the requested player.
            """
            ind = 0
            for player in player_list:
                if player[TConsts.PLAYERS_NAME_KEY] == requested_player[TConsts.PLAYERS_NAME_KEY]:
                    return ind // 3
                ind += 1

            return -1

        def get_gk_amount(player_list):
            gks = 0
            for player in player_list:
                if player[TConsts.PLAYERS_CHARACTERISTICS_KEY] == TConsts.PlayerCharacteristics["GOALKEEPER"]:
                    gks += 1

            return gks

        result_list = []
        amount_of_teams = 3

        for i in range(amount_of_teams):
            result_list.append({TConsts.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY: [],
                                TConsts.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY: 0})

        # Sort the list by the player ratings
        random.shuffle(player_dicts_list)
        sorted_players = sorted(player_dicts_list, key=lambda player: player[TConsts.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY], reverse=True)
        num_members = len(sorted_players)

        # Create the LP problem
        prob = LpProblem("GroupPartitioning", LpMinimize)

        # Creating a variable for each player-team combination.
        # Our goal is to later create a restriction that enforces that:
        # X_i_j equals 1 if player <I> belongs to group <J>
        x = {(i, j): LpVariable(f"x_{i}_{j}", 0, 1, "Binary") for i in range(num_members) for j in range(amount_of_teams)}

        # Constraints: each member is assigned to exactly one group
        for i in range(num_members):
            prob += lpSum(x[i, j] for j in range(amount_of_teams)) == 1, f"AssignOnce_{i}"

        # Constraints: each group has the same amount of team members, or at most one additional member
        gks = get_gk_amount(sorted_players)
        if gks == 3 or gks == 0:
            for j in range(amount_of_teams):
                prob += lpSum(x[i, j] for i in range(num_members)) == (num_members // amount_of_teams), f"GroupSize_{j}"
        else:
            smallest_team = LpVariable("smallest_team", 0, 100)
            largest_team = LpVariable("largest_team", 0, 100)
            for j in range(amount_of_teams):
                prob += smallest_team <= lpSum(x[i, j] for i in range(num_members))
                prob += largest_team >= lpSum(x[i, j] for i in range(num_members))

            prob += largest_team - smallest_team <= 1


        # Define m as the weakest team, and M as the strongest team
        m = LpVariable("m", 0, 100)
        M = LpVariable("M", 0, 100)

        for j in range(amount_of_teams):
            prob += m <= lpSum(x[i, j] * sorted_players[i][TConsts.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY]
                               for i in range(num_members))
            prob += M >= lpSum(x[i, j] * sorted_players[i][TConsts.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY]
                               for i in range(num_members))

        # Allow for variations by limiting the difference between the highest-ranked team and the lowest-ranked team
        #prob += M - m, "Objective"

        if using_ranks:
            # Distribute goalkeepers
            for j in range(amount_of_teams):
                prob += lpSum(x[i, j] * (sorted_players[i][TConsts.PLAYERS_CHARACTERISTICS_KEY] == TConsts.PlayerCharacteristics["GOALKEEPER"]) for i in range(num_members)) <= 1

            # Make sure each team contains a single player from each tier
            for j in range(amount_of_teams):
                for tier in range(num_members // amount_of_teams):
                    prob += lpSum(x[i, j] * (get_player_tier(sorted_players, sorted_players[i]) == tier) for i in range(num_members)) == 1


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
                    x[i, j] * (sorted_players[i][TConsts.PLAYERS_CHARACTERISTICS_KEY] in
                               [TConsts.PlayerCharacteristics["OFFENSIVE"], TConsts.PlayerCharacteristics["DEFENSIVE"]])
                    for i in range(num_members))
                prob += role_max >= lpSum(
                    x[i, j] * (sorted_players[i][TConsts.PLAYERS_CHARACTERISTICS_KEY] in
                               [TConsts.PlayerCharacteristics["OFFENSIVE"],
                                TConsts.PlayerCharacteristics["DEFENSIVE"]])
                    for i in range(num_members))
                prob += att_min <= lpSum(
                    x[i, j] * (sorted_players[i][TConsts.PLAYERS_CHARACTERISTICS_KEY] ==
                         TConsts.PlayerCharacteristics["OFFENSIVE"])
                    for i in range(num_members))
                prob += att_max >= lpSum(
                    x[i, j] * (sorted_players[i][TConsts.PLAYERS_CHARACTERISTICS_KEY] ==
                    TConsts.PlayerCharacteristics["OFFENSIVE"])
                    for i in range(num_members))
                prob += def_min <= lpSum(
                    x[i, j] * (sorted_players[i][TConsts.PLAYERS_CHARACTERISTICS_KEY] ==
                    TConsts.PlayerCharacteristics["DEFENSIVE"])
                    for i in range(num_members))
                prob += def_max >= lpSum(
                    x[i, j] * (sorted_players[i][TConsts.PLAYERS_CHARACTERISTICS_KEY] ==
                    TConsts.PlayerCharacteristics["DEFENSIVE"])
                    for i in range(num_members))

            prob += att_max - att_min <= 1
            prob += def_max - def_min <= 1
            prob += role_max - role_min <= 1


        # Solve the LP problem
        seed = random.choice([i for i in range(100)])
        cbc_solver = PULP_CBC_CMD(keepFiles=False,
                                       # Set random seed to ensure reproducability, passes as command-line arg to solver
                                       options=[f"RandomS {seed}"])
        prob.solve(cbc_solver)

        for i in range(num_members):
            for j in range(amount_of_teams):
                if value(x[i, j]) == 1:
                    result_list[j][TConsts.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY].append(sorted_players[i])
                    result_list[j][TConsts.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY] += sorted_players[i][TConsts.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY] # TODO: remove the total rating and calculate it elsewhere

        return result_list