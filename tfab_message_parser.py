import re
from tfab_database_handler import TFABDBHandler

class MessageParser:
    """
    Intended to parse user messages, to extract the interesting fields out of them.
    """


    @staticmethod
    def _get_date_value(message):
        """
        :param message: The message to search in.
        :return: The date value (if it exists), or None otherwise.
        """
        pattern = re.compile(r"((0?[1-9])|1\d|2\d|30|31)[./\\-]((0?[1-9])|1[012])[./\\-]((20)?([2-9]\d))")
        for line in message.split("\n"):
            match = pattern.search(line.strip())

            if match:
                return {TFABDBHandler.MATCHDAYS_DATE_DAY_KEY: match.group(1).strip(),
                        TFABDBHandler.MATCHDAYS_DATE_MONTH_KEY: match.group(3).strip(),
                        TFABDBHandler.MATCHDAYS_DATE_YEAR_KEY: match.group(5).strip()}

        return None

    @staticmethod
    def _get_placement_value(message):
        """
        :param message: The message to search in.
        :return: The placement value (if it exists), or None otherwise
        """
        pattern = re.compile(r"מיקום: ([א-ת\d \"]*)")
        for line in message.split("\n"):
            match = pattern.search(line.strip())

            if match:
                return match.group(1).strip()

        return None

    @staticmethod
    def _get_roster_value(message):
        """
        :param message: The message to search in.
        :return: The roster value (if it exists), or None otherwise.
        """
        pattern = re.compile(r"^\d{1,2}\.(([א-ת \-`'\u05f3\u2019]+)|)")
        name_characters_blacklist = r"[^א-ת \-`'\u05f3\u2019]"
        players = []

        first_part_started = False

        for line in message.split("\n"):
            match = pattern.search(line.strip())

            if match:
                if not first_part_started:
                    first_part_started = True
                players.append(re.sub(name_characters_blacklist, "", match.group(1).strip()))
            elif first_part_started:
                break

        return players

    @staticmethod
    def parse_matchday_message(message):
        """
        Parses a matchday message into a dictionary.
        :param message:
        :return: A dictionary that contains the game date, roster, location and the original message.
        """
        return {TFABDBHandler.MATCHDAYS_DATE_KEY: MessageParser._get_date_value(message),
                TFABDBHandler.MATCHDAYS_LOCATION_KEY: MessageParser._get_placement_value(message),
                TFABDBHandler.MATCHDAYS_ORIGINAL_MESSAGE_KEY: message,
                TFABDBHandler.MATCHDAYS_ROSTER_KEY: MessageParser._get_roster_value(message)}

    @staticmethod
    def generate_rankings_template(all_player_names, user_rankings):
        """
        Generates a template for the message, intended to be parsed.
        :param all_player_names: Names of all the available players.
        :param user_rankings: This specific user's rankings.
        :return: A template message displaying the different rankings.
        """
        unranked_players = list(set(all_player_names) - set(user_rankings.keys()))

        if len(user_rankings.items()) == 0:
            ranking_message = "לא קיימים שחקנים שדירגת.\n"
        else:
            ranking_message = "אלו השחקנים שדירגת:\n"

            i = 0
            for player, ranking in user_rankings.items():
                i = i + 1
                ranking_message += "{0}.{1} = {2}\n".format(i, player, ranking)

        if len(unranked_players) == 0:
            ranking_message += "\nדירגת את כל השחקנים האפשריים."
        else:
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
        Every item in the dictionary is in the form of {<PlayerName>: <NumericalRankingValue>}
        """
        pattern = re.compile(r"(^(\w+\s)+)=\s?(([1-9])|10|(\d\.\d))$")
        result_dict = {}

        for line in message.split("\n"):
            match = pattern.search(line.strip())

            if match:
                result_dict[match.group(1).strip()] = match.group(3)

        return result_dict
