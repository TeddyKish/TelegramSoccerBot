from tfab_logger import tfab_logger
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

    def check_table_existence(self, table_name):
        """
        :param table_name: The table name in question.
        :return: True if <table_name> exists as a table within our DB, False otherwise
        """
        TABLE_SEARCH_QUERY = """SELECT name FROM sqlite_master WHERE type='table' AND name='{0}';""".format(table_name)
        return len(self.execute_query(TABLE_SEARCH_QUERY)) != 0

    def get_column_from_table(self, column_name, table_name):
        """
        :param column_name: The column we're interested in
        :param table_name: The table that contains <column_name> as a column
        :return: A list populated by <column_name>'s entries
        """
        result = self.execute_query("SELECT {0} FROM {1}".format(column_name, table_name))
        if not result:
            return []
        return [kv_tuple[0] for kv_tuple in result]

    def execute_query(self, query):
        cursor = self.connection.cursor()

        cursor.execute(query)
        tfab_logger.info("Executed query: {0}".format(query))

        result = cursor.fetchall()
        cursor.close()

        return result

    def execute_script(self, script):
        cursor = self.connection.cursor()
        cursor.executescript(script)
        cursor.close()

    def commit_changes(self):
        self.connection.commit()