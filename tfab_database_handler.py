import tfab_consts
import tfab_exception
from tfab_exception import TFABException
from tfab_logger import tfab_logger
from pymongo import MongoClient


class TFABDBHandler(object):
    """
    Should be an interface for other DB handlers if one wishes to replace, currently works with MongoDB
    """
    PLAYERS_COLLECTION_NAME = "Players"
    PLAYERS_NAME_KEY = "PlayerName"
    PLAYERS_CHARACTERISTICS_KEY = "PlayerPosition"

    RANKERS_COLLECTION_NAME = "AuthorizedRankers"
    RANKERS_USER_RANKINGS_KEY = "UserRankings"
    ADMINS_COLLECTION_NAME = "AuthorizedAdmins"
    USER_ID_KEY = "UserId"
    USER_FULLNAME_KEY = "UserFullName"

    MATCHDAYS_COLLECTION_NAME = "Matchdays"
    MATCHDAYS_TEAMS_KEY = "Teams"
    MATCHDAYS_ORIGINAL_MESSAGE_KEY = "OriginalMessage"
    MATCHDAYS_LOCATION_KEY = "Location"
    MATCHDAYS_ROSTER_KEY = "Players"
    MATCHDAYS_DATE_KEY = "Date"
    MATCHDAYS_DATE_DAY_KEY = "Day"
    MATCHDAYS_DATE_MONTH_KEY = "Month"
    MATCHDAYS_DATE_YEAR_KEY = "Year"


    def __init__(self, db_name, db_port):
        self.db_name = db_name
        self.mongo_client = MongoClient("mongodb://localhost:{0}/".format(db_port))
        self.db = self.mongo_client[db_name]

        if self.mongo_client is None or self.db is None:
            raise TFABException("Error initializing MongoDB")

        collection_names = self.db.list_collection_names()
        for cname in [self.PLAYERS_COLLECTION_NAME, self.ADMINS_COLLECTION_NAME, self.RANKERS_COLLECTION_NAME, self.MATCHDAYS_COLLECTION_NAME]:
            if cname not in collection_names:
                self.db.create_collection(cname)

    def insert_player(self, player_name, characteristics):
        """
        Inserts a single player and their characteristics
        """
        new_player = \
            {self.PLAYERS_NAME_KEY: player_name, self.PLAYERS_CHARACTERISTICS_KEY: characteristics}
        players_collection = self.__get_collection(self.PLAYERS_COLLECTION_NAME)

        try:
            players_collection.insert_one(new_player)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

    def insert_admin(self, admin_name, admin_id):
        """
        Inserts <admin_name, admin_id> to the admins' collection.
        """
        new_admin = \
            {self.USER_ID_KEY: admin_id, self.USER_FULLNAME_KEY: admin_name}
        admins_collection = self.__get_collection(self.ADMINS_COLLECTION_NAME)

        try:
            admins_collection.insert_one(new_admin)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

    def insert_ranker(self, ranker_name, ranker_id):
        """
        Inserts <ranker_name, ranker_id> to the rankers collection.
        """
        new_ranker = \
            {self.USER_ID_KEY: ranker_id, self.USER_FULLNAME_KEY: ranker_name, self.RANKERS_USER_RANKINGS_KEY: {}}
        rankers_collection = self.__get_collection(self.RANKERS_COLLECTION_NAME)

        try:
            rankers_collection.insert_one(new_ranker)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

    def insert_matchday(self, original_message, location, player_list, date_day, date_month, date_year):
        """
        Inserts <matchday_dict> to the DB.
        If there is a matchday on the same date, it deletes the previous matchday and sets the current one as new.
        """
        if not isinstance(player_list, list) or not isinstance(original_message, str) or not isinstance(location, str)\
            or not isinstance(date_day, str) or not isinstance(date_month, str) or not isinstance(date_year,str):
            raise tfab_exception.DatabaseError("TFAB Database Error occured: Illegal data when inserting a new matchday")

        if self.check_matchday_existence(date_day, date_month, date_year):
            if not self.delete_matchday(date_day, date_month, date_year):
                raise tfab_exception.DatabaseError("TFAB Database Error occured: Couldn't delete existing matchday")

        matchday_date_dict = {self.MATCHDAYS_DATE_DAY_KEY: date_day, self.MATCHDAYS_DATE_MONTH_KEY: date_month,
                      self.MATCHDAYS_DATE_YEAR_KEY: date_year}
        matchday_dict = {self.MATCHDAYS_ORIGINAL_MESSAGE_KEY: original_message,
                         self.MATCHDAYS_LOCATION_KEY: location,
                         self.MATCHDAYS_ROSTER_KEY: player_list,
                         self.MATCHDAYS_DATE_KEY: matchday_date_dict}

        matchdays_collection = self.__get_collection(self.MATCHDAYS_COLLECTION_NAME)

        try:
            matchdays_collection.insert_one(matchday_dict)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

    def get_player_list(self):
        """
        :return: A cursor that contains information about all the available players in the DB.
        """
        players_collection = self.__get_collection(self.PLAYERS_COLLECTION_NAME)

        try:
            all_players_cursor = players_collection.find()
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        player_list = []
        for player in all_players_cursor:
            player_list.append((player[self.PLAYERS_NAME_KEY],
                                tfab_consts.PlayerPositionToHebrew[player[self.PLAYERS_CHARACTERISTICS_KEY]]))
        return player_list

    def get_user_rankings(self, user_id):
        """
        :param user_id: The ID of the requested user.
        :return: The user's rankings field as saved in the DB.
        """
        rankers_collection = self.__get_collection(self.RANKERS_COLLECTION_NAME)
        filter_object = {self.USER_ID_KEY: user_id}

        try:
            result = rankers_collection.find_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        # If no such user exists
        if result is None:
            return None

        return result[self.RANKERS_USER_RANKINGS_KEY]

    def modify_user_rankings(self, user_id, rankings_dictionary):
        """
        :param user_id: The ID of the user.
        :param rankings_dictionary: A dictionary containing all the desired modifications to perform.
        * note - removes illegal rankings from the rankings dictionary.
        :return: True if succeeded, false otherwise.
        """
        rankers_collection = self.__get_collection(self.RANKERS_COLLECTION_NAME)
        filter_object = {self.USER_ID_KEY: user_id}
        update_object = {}

        for player_name, ranking in rankings_dictionary.copy().items():
            # Make sure player exists and isn't a goalkeeper
            if self.check_player_existence(player_name) and\
                    self.get_player_characteristic(player_name) != tfab_consts.PlayerCharacteristics["GOALKEEPER"]:
                update_object["{0}.{1}".format(self.RANKERS_USER_RANKINGS_KEY, player_name)] = ranking
            else:
                rankings_dictionary.pop(player_name)

        try:
            result = rankers_collection.update_one(filter_object, {"$set": update_object})
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        return result.matched_count == 1, result.modified_count == 1

    def edit_player(self, player_name, new_characteristic):
        """
        Edits the player's characteristic.
        :param player_name: The player that we wish to edit.
        :param new_characteristic: The new characteristic of the player.
        :return: True if the player was found and the characteristic has been set, False otherwise.
        """
        players_collection = self.__get_collection(self.PLAYERS_COLLECTION_NAME)
        filter_object = {self.PLAYERS_NAME_KEY: player_name}
        update_operation = {'$set': {self.PLAYERS_CHARACTERISTICS_KEY: new_characteristic}}

        try:
            results = players_collection.update_one(filter_object, update_operation)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        # Not checking modified_count, to allow an admin to click on the same characteristic without triggering errors
        return results.matched_count == 1

    def check_player_existence(self, player_name):
        """
        Checks whether a player exists in the database.
        :param player_name: The player name to search
        :return: True if the player exists in the Players collection, False otherwise
        """
        players_collection = self.__get_collection(self.PLAYERS_COLLECTION_NAME)
        filter_object = {self.PLAYERS_NAME_KEY: player_name}
        try:
            result = players_collection.find_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        return result is not None

    def get_player_characteristic(self, player_name):
        """
        :param player_name: The player to check.
        :return: The characteristic of <player_name>.
        """
        players_collection = self.__get_collection(self.PLAYERS_COLLECTION_NAME)
        filter_object = {self.PLAYERS_NAME_KEY: player_name}
        try:
            result = players_collection.find_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        return None if result is None else result[self.PLAYERS_CHARACTERISTICS_KEY]

    def check_admin_existence(self, admin_id):
        """
        :return: True if <admin_id> exists in the Admins collection, False otherwise
        """
        admins_collection = self.__get_collection(self.ADMINS_COLLECTION_NAME)
        filter_object = {self.USER_ID_KEY: admin_id}
        try:
            result = admins_collection.find_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        return result is not None

    def check_ranker_existence(self, ranker_id):
        """
        :return: True if <admin_id> exists in the Admins collection, False otherwise
        """
        rankers_collection = self.__get_collection(self.RANKERS_COLLECTION_NAME)
        filter_object = {self.USER_ID_KEY: ranker_id}
        try:
            result = rankers_collection.find_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        return result is not None

    def check_matchday_existence(self, date_day, date_month, date_year):
        """
        :return: True if a matchday that occurs in <DDMMYY> exists, False otherwise.
        """
        matchdays_collection = self.__get_collection(self.MATCHDAYS_COLLECTION_NAME)
        filter_object = {self.MATCHDAYS_DATE_KEY: {self.MATCHDAYS_DATE_DAY_KEY: date_day,
                                                   self.MATCHDAYS_DATE_MONTH_KEY: date_month,
                                                   self.MATCHDAYS_DATE_YEAR_KEY: date_year}}
        try:
            result = matchdays_collection.find_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        return result is not None

    def delete_player(self, player_name):
        """
        Deletes a single player from the entire database.
        :param player_name: The player name that we wish to delete.
        :return: True if the player was deleted successfully, false otherwise
        """
        players_collection = self.__get_collection(self.PLAYERS_COLLECTION_NAME)
        player_name_filter = {self.PLAYERS_NAME_KEY: player_name}

        rankers_collection = self.__get_collection(self.RANKERS_COLLECTION_NAME)
        delete_ranking_operation = {'$unset': {"{0}.{1}".format(self.RANKERS_USER_RANKINGS_KEY, player_name): ""}}

        try:
            player_delete_result = players_collection.delete_one(player_name_filter)
            player_rankings_delete_result = rankers_collection.update_many({}, delete_ranking_operation)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        # Makes sure we actually deleted a player
        return player_delete_result.deleted_count == 1

    def delete_matchday(self, date_day, date_month, date_year):
        """
        Deletes the matchday that occurs at <DDMMYY>.
        :return: True if a single matchday was deleted successfully, False otherwise.
        """
        matchdays_collection = self.__get_collection(self.MATCHDAYS_COLLECTION_NAME)
        filter_object = {self.MATCHDAYS_DATE_KEY: {self.MATCHDAYS_DATE_DAY_KEY: date_day,
                                                   self.MATCHDAYS_DATE_MONTH_KEY: date_month,
                                                   self.MATCHDAYS_DATE_YEAR_KEY: date_year}}

        try:
            matchdays_delete_result = matchdays_collection.delete_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        # Makes sure we actually deleted a player
        return matchdays_delete_result.deleted_count == 1

    def __get_collection(self, collection_name):
        """
        :return: The requested collection, if there were no errors.
        """
        collection = self.db[collection_name]
        if collection is None:
            raise TFABException("Unable to access the collection when attempting to insert a player")

        return collection

    def __del__(self):
        self.mongo_client.close()