from tfab_logger import tfab_logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.ext import ConversationHandler

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
        self.__configuration = tfab_configuration
        self.__db = tfab_db
        self.__initialize_telegram_app()
        self.__initialize_handlers()
        tfab_logger.debug("TFABApplication successfully initialized")

    def __initialize_telegram_app(self):
        """
        Initiailizes PTB and the connection to our bot.
        """
        self.__ptb_app = ApplicationBuilder().token(self.__configuration.TELEGRAM_BOT_TOKEN).build()

    def __initialize_handlers(self):
        """
        Initializes the different handlers for this application.
        """
        conversation_handler = ConversationHandler(
        entry_points=[CommandHandler(["start", "help"], InputHandlers.entrypoint_handler)],
        states={
            InputHandlers.GENERAL_MENU: [
                CallbackQueryHandler(InputHandlers.general_ranking_menu_handler, pattern=str(InputHandlers.RANKER_MENU)),
                CallbackQueryHandler(InputHandlers.admin_menu_handler, pattern=str(InputHandlers.ADMIN_MENU)),
            ],
            InputHandlers.RANKER_MENU: [
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.RANKER_MENU_RANK_SPECIFIC_PLAYER)),
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.RANKER_MENU_RANK_EVERYONE)),
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.RANKER_MENU_SHOW_MY_RANKINGS)),
            ],
            InputHandlers.ADMIN_MENU: [
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.ADMIN_MENU_GAMES)),
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.ADMIN_MENU_PLAYERS)),
            ],
            InputHandlers.ADMIN_MENU_GAMES: [
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.GAMES_MENU_LIST)),
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.GAMES_MENU_GROUPS)),
            ],
            InputHandlers.GAMES_MENU_LIST: [
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.GAMES_MENU_LIST_SET)),
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.GAMES_MENU_LIST_RANK_OUTSIDER)),
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.GAMES_MENU_LIST_SHOW_TODAY)),
            ],
            InputHandlers.GAMES_MENU_GROUPS: [
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.GAMES_MENU_GROUPS_GENERATE)),
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.GAMES_MENU_GROUPS_SHOW)),
            ],
            InputHandlers.ADMIN_MENU_PLAYERS: [
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.PLAYERS_MENU_EDIT)),
                CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(InputHandlers.PLAYERS_MENU_SHOW)),
            ]
        },
        fallbacks=[CommandHandler(["start", "help"], InputHandlers.entrypoint_handler)]
        )

        # Add ConversationHandler to application that will be used for handling updates
        self.__ptb_app.add_handler(conversation_handler)

        self.__ptb_app.add_handler(MessageHandler(filters.COMMAND, InputHandlers.unknown_command_handler))
        self.__ptb_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), InputHandlers.unknown_text_handler))

    def run(self):
        """
        Performs the actual logic of the TFABApplication.
        """
        self.__ptb_app.run_polling()

class InputHandlers(object):
    """
    Contains the different input handlers for this bot.
    """

    GENERAL_MENU, \
        RANKER_MENU, \
            RANKER_MENU_RANK_EVERYONE, \
            RANKER_MENU_RANK_SPECIFIC_PLAYER, \
            RANKER_MENU_SHOW_MY_RANKINGS, \
        ADMIN_MENU, \
            ADMIN_MENU_GAMES, \
                GAMES_MENU_LIST, \
                    GAMES_MENU_LIST_SET, \
                    GAMES_MENU_LIST_RANK_OUTSIDER, \
                    GAMES_MENU_LIST_SHOW_TODAY, \
                GAMES_MENU_GROUPS, \
                    GAMES_MENU_GROUPS_GENERATE, \
                    GAMES_MENU_GROUPS_SHOW, \
            ADMIN_MENU_PLAYERS,  \
                PLAYERS_MENU_EDIT, \
                PLAYERS_MENU_SHOW = range(17)
    
    @staticmethod
    async def entrypoint_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send message on `/start`."""
        # Get user that sent /start and log his name
        user = update.message.from_user
        tfab_logger.info("\nTFAB: User %s started the conversation.\n", user.first_name)

        start_text = """ברוך הבא לבוטיטו!
הבוטיטו הוא בוט שנועד ליצור כוחות באופן אוטומטי.
לפניך התפריטים הבאים:"""
        
        keyboard = [
            [
                InlineKeyboardButton("דירוגים", callback_data=str(InputHandlers.RANKER_MENU)),
                InlineKeyboardButton("מנהלים", callback_data=str(InputHandlers.ADMIN_MENU)),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(start_text, reply_markup=reply_markup)

        return InputHandlers.GENERAL_MENU
    
    @staticmethod
    async def general_ranking_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the rankers menu.
        """
        query = update.callback_query
        await query.answer()

        text = """להלן פעולות הדירוגים האפשריות:"""

        keyboard = [
                [InlineKeyboardButton("דרג שחקן ספציפי", callback_data=str(InputHandlers.RANKER_MENU_RANK_SPECIFIC_PLAYER))],
                [InlineKeyboardButton("דרג את כולם", callback_data=str(InputHandlers.RANKER_MENU_RANK_EVERYONE))],
                [InlineKeyboardButton("הצג דירוגים שלי", callback_data=str(InputHandlers.RANKER_MENU_SHOW_MY_RANKINGS))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return InputHandlers.RANKER_MENU

    @staticmethod
    async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the admin menu.
        """
        query = update.callback_query
        await query.answer()

        text = """להלן פעולות המנהלים האפשריות:"""

        keyboard = [
                [InlineKeyboardButton("נהל משחקים", callback_data=str(InputHandlers.ADMIN_MENU_GAMES))],
                [InlineKeyboardButton("נהל שחקנים", callback_data=str(InputHandlers.ADMIN_MENU_PLAYERS))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return InputHandlers.ADMIN_MENU

    @staticmethod
    async def pass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        temporary- handles currently unimplemented options.
        """
        query = update.callback_query
        await query.answer()

        text = """אופציה זו עדיין לא מומשה, ניתן לחזור להתחלה עם  /help"""

        await query.edit_message_text(text)
        return ConversationHandler.END

    @staticmethod
    async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="האופציה הזו לא קיימת, ניתן לחזור להתחלה עם /help")
    
    @staticmethod
    async def unknown_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="האופציה הזו לא קיימת, ניתן לחזור להתחלה עם /help")