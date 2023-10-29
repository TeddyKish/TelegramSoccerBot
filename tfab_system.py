from tfab_logger import tfab_logger
from tfab_app import TFABApplication
from tfab_database_handler import TFABDBHandler
from tfab_configuration import TFABConfiguration
from tfab_exception import TFABException
import tfab_consts

class TFABSystem(object):
    """
    Contains the TFAB Application in its entirety.
    """

    def __init__(self, tfab_conf_path=tfab_consts.DEFAULT_CONFIGURATION_PATH):
        """
        Initializes a TFABApplication instance.
        """
        try:
            self.__initialize_configuration(tfab_conf_path)
            self.__initialize_database(tfab_consts.DATABASE_NAME, self.__configuration.MONGODB_PORT)
            self.__initialize_app(self.__configuration, self.__db)
            tfab_logger.debug("TFABSystem successfully initialized")
        except Exception as e:
            tfab_logger.error("TFAB Exception occured: ", str(e))
            raise TFABException("TFAB Exception occured: ", str(e))

    def __initialize_configuration(self, conf_path):
        """
        Initializes the TFABConfiguration.
        """
        self.__configuration = TFABConfiguration(conf_path)

    def __initialize_database(self, db_name, db_port):
        """
        Initializes the database we're working with.
        """
        self.__db = TFABDBHandler(db_name, db_port)

    def __initialize_app(self, config, db):
        """
        Initializes the TFAB Appication.
        """
        self.__app = TFABApplication.get_instance(config, db)

    def run_system(self):
        """
        Runs the TFAB System indefinitely.
        """
        try:
            self.__app.run()
        except Exception as e:
            tfab_logger.error("TFAB Exception occured: ", str(e))
            raise TFABException("TFAB Exception occured: ", str(e))
            exit(1)