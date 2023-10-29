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
        collection = self.db[TFABDBHandler.PLAYERS_COLLECTION_NAME]
        if collection is None:
            raise TFABException("Unable to access the collection when attempting to insert a player")

        collection.insert_one(new_player)

    def __del__(self):
        self.mongo_client.close()