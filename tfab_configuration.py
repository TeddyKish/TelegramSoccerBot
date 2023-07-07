import tfab_exception
import yaml
from schema import Schema, And

class TFABConfiguration(object):
    """
    TFAB's configuration object, to be used within PTB.
    """
    def __init__(self, tfab_yaml_configuration_path, custom_schema=None):
        """
        Creates a member in this class for every key in <tfab_yaml_configuration_path>.
        :param tfab_yaml_configuration_path: The path to the configuration file.
        """

        # Schema for the yaml configuration
        if custom_schema is not None:
            self.__schema = custom_schema
        else:
            self.__schema__ = Schema(
                {
                    'TELEGRAM_BOT_TOKEN': And(str),
                    'DATABASE_PATH': And(str),
                    'ALL_PLAYERS_TABLE': And(str),
                    'ALL_PLAYERS_NAME_COLUMN': And(str),
                    'USER_RANKINGS_TABLE_NAME_PREFIX': And(str),
                    'RANKING_TABLE_NAME_COLUMN': And(str),
                    'RANKING_TABLE_RANK_COLUMN': And(str)
                }
            )

        try:
            with open(tfab_yaml_configuration_path, "r") as conf_file:
                self.__configuration_dictionary__ = yaml.safe_load(conf_file)
                self.__schema__.validate(self.__configuration_dictionary__)
            for key, value in self.__configuration_dictionary__.items():
                setattr(self, key, value)
        except Exception as e:
            raise tfab_exception.ConfigurationError("TFAB Configuration Error occured: " + str(e))