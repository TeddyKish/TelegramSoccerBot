from enum import Enum
from tfab_system import TFABSystem


class ProcessExitCodes(Enum):
    STATUS_SUCCESS = 0
    STATUS_FAILURE = 1

def start_operation():
    """
    Currently encompasses all the logic of this bot.
    :return:
    """
    tfab_app = TFABSystem()
    tfab_app.run_system()

if __name__ == '__main__':
    start_operation()
    exit(ProcessExitCodes.STATUS_SUCCESS)