from tfab_logger import tfab_logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.ext import ConversationHandler

class TFABCommand(object):
    """
    Represents an interactive command within TFAB.
    """

    def __init__(self, command_string, command_description, command_callback):
        """
        :param command_string: The string the user should enter to invoke the command
        :param command_description: The description of this command, to be printed on demand
        :param command_callback: The function to call when this command has been invoked
        """

        self.str = command_string
        self.desc = command_description
        self.callback = command_callback

class TFABApplication(object):
    """
    Handles the entirety of the command handling and logic.
    """
    _instance = None

    @staticmethod
    def get_instance(tfab_config=None, tfab_db=None):
        if TFABApplication._instance is None:
            TFABApplication._instance = TFABApplication(tfab_config, tfab_db)
        return TFABApplication._instance

    def __init__(self, tfab_configuration, tfab_db):
        """
        Constructs a TFABApplication.
        """
        self.configuration = tfab_configuration
        self.db = tfab_db
        self.__initialize_telegram_app()
        self.__initialize_handlers()
        tfab_logger.debug("TFABApplication successfully initialized")

    def __initialize_telegram_app(self):
        """
        Initiailizes PTB and the connection to our bot.
        """
        self.ptb_app = ApplicationBuilder().token(self.configuration.TELEGRAM_BOT_TOKEN).build()

    def __initialize_handlers(self):
        """
        Initializes the different handlers for this application.
        """
        conv_handler_commands = []

        # Commands Handlers
        for cmd in tfab_user_commands:
            if cmd.str not in conv_handler_commands:
                self.ptb_app.add_handler(CommandHandler(cmd.str, cmd.callback))
                
        self.ptb_app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))
        self.ptb_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), unknown_text_handler))

    def run(self):
        """
        Performs the actual logic of the TFABApplication.
        """
        self.ptb_app.run_polling()

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Botito! Use /help to proceed")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = """שלום רב! אני שמח מאוד שהצטרפת
מטרת הבוטיטו היא להפוך את תהליך יצירת הכוחות בכדורגל לאוטומטי לחלוטין!
פעולות אפשריות:
"""
    global tfab_user_commands
    keyboard = []
    for cmd in tfab_user_commands:
        keyboard.append([InlineKeyboardButton(cmd.str, callback_data=cmd.str)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(update.effective_chat.id, text=help_message, reply_markup=reply_markup)

async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, this command doesn't exist.")

async def unknown_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, this option doesn't exist.")

tfab_user_commands = []
tfab_user_commands.append(TFABCommand("start", "Starts the first time interaction with Botito", start_handler))
tfab_user_commands.append(TFABCommand("help", "Shows the features supported by Botito", help_handler))


def start_operation():
    """
    Currently encompasses all the logic of this bot.
    :return:
    """
    # tfab_app.__app.add_handler(CallbackQueryHandler(button_callback))