from tfab_logger import tfab_logger
from pymongo import MongoClient

class TFABDBHandler(object):
    """
    Should be an interface for other DB handlers if one wishes to replace, currently works with MongoDB
    """
    def __init__(self, db_name, db_port):
        self.db_name = db_name
        self.mongo_client = MongoClient("mongodb://localhost:{0}/{1}".format(db_port, db_name))

    def __del__(self):
        self.mongo_client.close()