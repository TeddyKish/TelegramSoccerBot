import tfab_consts
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
        :return:
        """
        new_player = \
            {TFABDBHandler.PLAYER_NAME_KEY: player_name, TFABDBHandler.PLAYER_CHARACTERISTICS_KEY: characteristics}
        players_collection = self.__get_collection(TFABDBHandler.PLAYERS_COLLECTION_NAME)

        players_collection.insert_one(new_player)

    def show_all_players(self):
        """
        :return: A string that contains information about all the available players in the DB.
        """
        players_collection = self.__get_collection(TFABDBHandler.PLAYERS_COLLECTION_NAME)
        all_players = players_collection.find()

        i = 1
        roster_message = ""
        for player in all_players:
            roster_message += "{0}.{1} - {2}\n".format(
                                   i,
                                   player[TFABDBHandler.PLAYER_NAME_KEY],
                                   tfab_consts.PlayerPositionToHebrew[player[TFABDBHandler.PLAYER_CHARACTERISTICS_KEY]])
            i = i + 1

        if roster_message == "":
            return roster_message
        return roster_message[:-1] # Removes the last \n in the string

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