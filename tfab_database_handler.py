import tfab_consts
import tfab_exception
from tfab_exception import TFABException
from tfab_logger import tfab_logger
from pymongo import MongoClient

class TFABDBHandler(object):
    """
    Should be an interface for other DB handlers if one wishes to replace, currently works with MongoDB
    """
    PLAYER_NAME_KEY = "PlayerName"
    PLAYER_CHARACTERISTICS_KEY = "PlayerPosition"
    PLAYERS_COLLECTION_NAME = "Players"

    def __init__(self, db_name, db_port):
        self.db_name = db_name
        self.mongo_client = MongoClient("mongodb://localhost:{0}/".format(db_port))
        self.db = self.mongo_client[db_name]
        if self.mongo_client is None or self.db is None:
            raise TFABException("Error initializing MongoDB")

    def insert_player(self, player_name, characteristics):
        """
        Inserts a single player and their characteristics
        """
        new_player = \
            {TFABDBHandler.PLAYER_NAME_KEY: player_name, TFABDBHandler.PLAYER_CHARACTERISTICS_KEY: characteristics}
        players_collection = self.__get_collection(TFABDBHandler.PLAYERS_COLLECTION_NAME)

        try:
            players_collection.insert_one(new_player)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

    def show_all_players(self):
        """
        :return: A string that contains information about all the available players in the DB.
        """
        players_collection = self.__get_collection(TFABDBHandler.PLAYERS_COLLECTION_NAME)

        try:
            all_players = players_collection.find()
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        i = 1
        roster_message = ""
        for player in all_players:
            roster_message += "{0}.{1} ({2})\n".format(
                                   i,
                                   player[TFABDBHandler.PLAYER_NAME_KEY],
                                   tfab_consts.PlayerPositionToHebrew[player[TFABDBHandler.PLAYER_CHARACTERISTICS_KEY]])
            i = i + 1

        if roster_message == "":
            return roster_message
        return roster_message[:-1] # Removes the last \n in the string

    def edit_player(self, player_name, new_characteristic):
        """
        Edits the player's characteristic.
        :param player_name: The player that we wish to edit.
        :param new_characteristic: The new characteristic of the player.
        :return: True if the player was found and the characteristic has been set, False otherwise.
        """
        players_collection = self.__get_collection(TFABDBHandler.PLAYERS_COLLECTION_NAME)
        filter_object = {self.PLAYER_NAME_KEY: player_name}
        update_operation = {'$set': {self.PLAYER_CHARACTERISTICS_KEY: new_characteristic}}

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
        players_collection = self.__get_collection(TFABDBHandler.PLAYERS_COLLECTION_NAME)
        filter_object = {self.PLAYER_NAME_KEY: player_name}
        try:
            result = players_collection.find_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        return result is not None

    def delete_player(self, player_name):
        """
        Deletes a single player.
        :param player_name: The player name that we wish to delete.
        :return: True if a player was deleted, false otherwise
        """
        players_collection = self.__get_collection(TFABDBHandler.PLAYERS_COLLECTION_NAME)
        filter_object = {self.PLAYER_NAME_KEY: player_name}

        # TODO: Make sure the player is deleted from all rankings as well
        # - Maybe by manual deletion
        # - Maybe by enforcing coupling between the rankers collections and the Players collection
        try:
            result = players_collection.delete_one(filter_object)
        except Exception as e:
            raise tfab_exception.DatabaseError("TFAB Database Error occured: " + str(e))

        # Makes sure we actually deleted a player
        return result.deleted_count == 1

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