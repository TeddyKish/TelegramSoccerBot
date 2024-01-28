from tfab_framework import tfab_system


def start_operation():
    """
    Currently encompasses all the logic of this bot.
    """
    try:
        tfab_sys = tfab_system.TFABSystem()
        tfab_sys.run_system()
    except Exception as e:
        print(str(e))
        exit(1)


if __name__ == '__main__':
    start_operation()
    exit(0)
