import re
from tfab_framework.tfab_consts import Consts as TConsts
from tfab_framework.tfab_database_handler import TFABDBHandler
from datetime import datetime

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
                day = match.group(1).strip()
                month = match.group(3).strip()
                year = match.group(5).strip()

                if len(year) == 2:
                    year = "20" + year

                return datetime(int(year), int(month), int(day)).strftime(TConsts.MATCHDAYS_DATE_FORMAT)

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

        # Used to signify the start of the player list.
        # We assume that the player list is consecutive - that is, all players appear in one after the other.
        # Once we encounter a line that is not of the correct form - we can infer that the player list has ended.
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
    def stringify_player_list(player_list, with_characteristic=True):
        """
        Returns a formatted string that nicely displays the player list.
        """
        i = 1
        all_players_message = ""

        if with_characteristic:
            for player_name, characteristic, rating in player_list:
                all_players_message += "{0}.{1} = {3:.2f} ({2})\n".format(i, player_name, characteristic, rating)
                i += 1
        else:
            for player_name, _, rating in player_list:
                all_players_message += "{0}.{1} = {2}\n".format(i, player_name, rating)
                i += 1

        # Removes the last "\n" in the string if the string isn't trivial
        return all_players_message[:-1] if all_players_message != "" else ""

    @staticmethod
    def parse_matchday_message(message):
        """
        Parses a matchday message into a dictionary.
        :param message:
        :return: A dictionary that contains the game date, roster, location and the original message.
        """
        return {TConsts.MATCHDAYS_DATE_KEY: MessageParser._get_date_value(message),
                TConsts.MATCHDAYS_LOCATION_KEY: MessageParser._get_placement_value(message),
                TConsts.MATCHDAYS_ORIGINAL_MESSAGE_KEY: message,
                TConsts.MATCHDAYS_ROSTER_KEY: MessageParser._get_roster_value(message)}

    @staticmethod
    def generate_matchday_message(matchday_dict):
        """
        :return: A nicely formatted message, describing the information within <matchday_dict>
        """
        message = "הרשימה היומית כפי שנקלטה בבוטיטו:\n"
        date = matchday_dict[TConsts.MATCHDAYS_DATE_KEY]
        location = matchday_dict[TConsts.MATCHDAYS_LOCATION_KEY]
        player_list = matchday_dict[TConsts.MATCHDAYS_ROSTER_KEY]
        teams = matchday_dict[TConsts.MATCHDAYS_TEAMS_KEY]
        db = TFABDBHandler.get_instance()

        if date:
            message += "תאריך: {0}\n".format(date)
        if location:
            message += "מיקום: {0}\n".format(location)
        if player_list and not teams:
            message += "----------------------------------------\n"
            message += MessageParser.stringify_player_list(player_list, with_characteristic=False)
            message += "\n----------------------------------------\n"
        if teams:
            message += "\nלהלן הקבוצות שנוצרו עבור המשחק:\n"
            for team_index, team in enumerate(teams):
                players = team[TConsts.MATCHDAYS_SPECIFIC_TEAM_ROSTER_KEY]
                field_players_ratings = [player[TConsts.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY] for player in players if player[TConsts.PLAYERS_CHARACTERISTICS_KEY] != TConsts.PlayerCharacteristics["GOALKEEPER"]]
                message += "קבוצה {0}: (ציון - {1:.2f}, ממוצע - {2:.2f})\n".format(team_index + 1, team[TConsts.MATCHDAYS_SPECIFIC_TEAM_RATING_KEY], sum(field_players_ratings) / len(field_players_ratings))
                for player_index, player in enumerate(players):
                    message += "{0}.{1} - {2:.2f} ({3})\n".format(player_index + 1, player[TConsts.PLAYERS_NAME_KEY],
                                                      player[TConsts.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY],
                                                    TConsts.PlayerPositionToHebrew[db.get_player_characteristic(player[TConsts.PLAYERS_NAME_KEY])])
                message += "\n\n"

            message += "שיהיה בהצלחה!"

        return message

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

            for player, ranking in user_rankings.items():
                ranking_message += "{0} = {1}\n".format(player, ranking)

        if len(unranked_players) == 0:
            ranking_message += "\nדירגת את כל השחקנים האפשריים."
        else:
            ranking_message += "\nלהלן השחקנים שלא דירגת:\n"
            for player in unranked_players:
                ranking_message += "{0} = \n".format(player)

        # Get rid of the last "\n"
        return ranking_message[:-1] if ranking_message != "" else ""

    @staticmethod
    def parse_rankings_message(message):
        """
        Parses the rankings message into a Rankings Dictionary.
        :param message: The rankings template, after being filled with the user's preferences.
        :return: A dictionary with rankings for each player.
        Every item in the dictionary is in the form of {<PlayerName>: <NumericalRankingValue>}
        """
        pattern = re.compile(r"(^([א-ת \-`'\u05f3\u2019]+\s)+)=\s?(([1-9])|10|(\d\.\d))$")
        result_dict = {}

        for line in message.split("\n"):
            match = pattern.search(line.strip())

            if match:
                result_dict[match.group(1).strip()] = match.group(3)

        return result_dict
