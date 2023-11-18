import re

class RankingsMessageParser:
    """
    Intended to parse user messages, to extract the interesting fields out of them.
    """

    @staticmethod
    def generate_rankings_template(all_player_names, user_rankings):
        """
        Generates a template for the message, intended to be parsed.
        :param all_player_names: Names of all the available players.
        :param user_rankings: This specific user's rankings.
        :return: A template message displaying the different rankings.
        """
        unranked_players = list(set(all_player_names) - set(user_rankings.keys()))

        i = 0
        ranking_message = "אלו השחקנים שדירגת:\n"
        for player, ranking in user_rankings.items():
            i = i + 1
            ranking_message += "{0}.{1} = {2}\n".format(i, player, ranking)

        ranking_message += "\nלהלן השחקנים שלא דירגת:\n"
        for player in unranked_players:
            ranking_message += "{0} = \n".format(player)

        if ranking_message != "":
            ranking_message = ranking_message[:-1]

        return ranking_message

    @staticmethod
    def parse_rankings_message(message):
        """
        Parses the rankings message into a Rankings Dictionary.
        :param message: The rankings template, after being filled with the user's preferences.
        :return: A dictionary with rankings for each player.
        """
        pattern = re.compile(r"(^(\w+\s)+)=\s?(([1-9])|10|(\d\.\d))$")
        result_dict = {}

        for line in message.split("\n"):
            match = pattern.search(line.strip())

            if match:
                result_dict[match.group(1).strip()] = match.group(3)

        return result_dict

