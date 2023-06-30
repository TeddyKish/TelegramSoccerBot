import tfab_exception
import yaml
from schema import Schema, And
import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler

# CURRENT-MODULE-CONSTANTS
TFAB_CONFIGURATION_PATH = "tfab_configuration.yaml"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="האופציה הזו לא קיימת, אנא נסה שוב")

class TFABConfiguration(object):
    """
    TFAB's configuration object, to be used within PTB.
    """
    def __init__(self, tfab_yaml_configuration_path):
        """
        Creates a member in this class for every key in <tfab_yaml_configuration_path>.
        :param tfab_yaml_configuration_path: The path to the configuration file.
        """

        # Schema for the yaml configuration
        self.__schema__ = Schema(
            {
                'TELEGRAM_BOT_TOKEN': And(str)
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

def start_operation():
    """
    Currently encompasses all the logic of this bot.
    :return:
    """
    try:
        tfab_configuration = TFABConfiguration(TFAB_CONFIGURATION_PATH)
        application = ApplicationBuilder().token(tfab_configuration.TELEGRAM_BOT_TOKEN).build()

        echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
        start_handler = CommandHandler('start', start)
        caps_handler = CommandHandler('caps', caps)
        unknown_handler = MessageHandler(filters.COMMAND, unknown)

        application.add_handler(start_handler)
        application.add_handler(echo_handler)
        application.add_handler(caps_handler)
        application.add_handler(unknown_handler)

        application.run_polling()
    except tfab_exception.TFABException as e:
        logger.error("TFAB Exception occured: ", str(e))
    except Exception as e:
        logger.error("General Exception occured: ", str(e))

if __name__ == '__main__':
    start_operation()
