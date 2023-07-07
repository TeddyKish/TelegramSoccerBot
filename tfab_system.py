from tfab_logger import tfab_logger
from tfab_application import TFABApplication
from tfab_database_handler import TFABSQLiteHandler
from tfab_configuration import TFABConfiguration
from tfab_exception import TFABException

class TFABSystem(object):
    """
    Contains the TFAB Application in its entirety.
    """

    # Constants
    DEFAULT_TFAB_CONFIGURATION_PATH = "tfab_data//tfab_configuration.yaml"

    def __init__(self, tfab_conf_path):
        """
        Initializes a TFABApplication instance.
        """
        try:
            self.__initialize_configuration(tfab_conf_path)
            self.__initialize_database()
            self.__initialize_tfab_app()
        except Exception as e:
            tfab_logger.error("TFAB Exception occured: ", str(e))
            raise TFABException("TFAB Exception occured: ", str(e))

        tfab_logger.debug("TFABSystem successfully initialized")

    def __initialize_configuration(self, tfab_conf_path):
        """
        Initializes the TFABConfiguration.
        """
        self.__tfab_configuration = TFABConfiguration(tfab_conf_path)

    def __initialize_database(self):
        """
        Initializes the database we're working with.
        """
        self.__tfab_db = TFABSQLiteHandler(self.__tfab_configuration.DATABASE_PATH)
        self.__tfab_db.connect()

    def __initialize_tfab_app(self):
        """
        Initializes the TFAB Appication.
        """
        self.tfab_app = TFABApplication.get_instance(self.__tfab_configuration, self.__tfab_db)

    def run_system(self):
        """
        Runs the TFAB System indefinitely.
        """
        self.tfab_app.run()