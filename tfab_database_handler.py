from tfab_logger import logger
import sqlite3

class TFABSQLiteHandler(object):
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None

    def connect(self):
        self.connection = sqlite3.connect(self.db_name)

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()

        if params:
            cursor.execute(query, params)
            logger.info("Executed query: {0} {1}".format(query, params))
        else:
            cursor.execute(query)
            logger.info("Executed query: {0}".format(query))

        result = cursor.fetchall()
        cursor.close()



        return result

    def execute_script(self, script):
        cursor = self.connection.cursor()
        cursor.executescript(script)
        cursor.close()

    def commit_changes(self):
        self.connection.commit()