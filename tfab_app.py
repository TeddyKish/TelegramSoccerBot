import logging
import tfab_exception
import tfab_consts
from enum import IntEnum
from tfab_logger import tfab_logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.ext import ConversationHandler


class TFABApplication(object):
    """
    Handles the entirety of the command handling and logic.
    """
    _instance = None

    # The hierarchy of menus within this application
    GOT_INPUT,  \
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
            ADMIN_MENU_PLAYERS, \
                PLAYERS_MENU_ADD, \
                PLAYERS_MENU_SHOW, \
                PLAYERS_MENU_EDIT, \
                PLAYERS_MENU_DELETE = range(20)

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
                TFABApplication.GENERAL_MENU: [
                    CallbackQueryHandler(RankersMenuHandlers.rankers_menu_handler, pattern=str(TFABApplication.RANKER_MENU)),
                    CallbackQueryHandler(AdminMenuHandlers.admin_menu_handler, pattern=str(TFABApplication.ADMIN_MENU)),
                ],
                TFABApplication.RANKER_MENU: [
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.RANKER_MENU_RANK_SPECIFIC_PLAYER)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.RANKER_MENU_RANK_EVERYONE)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.RANKER_MENU_SHOW_MY_RANKINGS)),
                ],
                TFABApplication.ADMIN_MENU: [
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.ADMIN_MENU_GAMES)),
                    CallbackQueryHandler(AdminMenuHandlers.PlayersMenuHandlers.players_menu_handler, pattern=str(TFABApplication.ADMIN_MENU_PLAYERS)),
                ],
                TFABApplication.ADMIN_MENU_GAMES: [
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.GAMES_MENU_LIST)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.GAMES_MENU_GROUPS)),
                ],
                TFABApplication.GAMES_MENU_LIST: [
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.GAMES_MENU_LIST_SET)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.GAMES_MENU_LIST_RANK_OUTSIDER)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.GAMES_MENU_LIST_SHOW_TODAY)),
                ],
                TFABApplication.GAMES_MENU_GROUPS: [
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.GAMES_MENU_GROUPS_GENERATE)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.GAMES_MENU_GROUPS_SHOW)),
                ],
                TFABApplication.ADMIN_MENU_PLAYERS: [
                    CallbackQueryHandler(AdminMenuHandlers.PlayersMenuHandlers.add_player_handler, pattern=str(TFABApplication.PLAYERS_MENU_ADD) + "|" + "|".join(list(tfab_consts.PlayerCharacteristics.values()))),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.PLAYERS_MENU_SHOW)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.PLAYERS_MENU_EDIT)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.PLAYERS_MENU_DELETE)),
                ],
                TFABApplication.GOT_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, InputHandlers.text_input_handler)
                ]
            },
            fallbacks=[CommandHandler(["start", "help"], InputHandlers.entrypoint_handler)]
        )

        # Add ConversationHandler to application that will be used for handling updates
        self.__ptb_app.add_handler(conversation_handler)

        self.__ptb_app.add_handler(MessageHandler(filters.COMMAND, InputHandlers.unknown_command_handler))
        self.__ptb_app.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), InputHandlers.unknown_text_handler))

    def run(self):
        """
        Performs the actual logic of the TFABApplication.
        """
        self.__ptb_app.run_polling()


class InputHandlers(object):
    """
    Contains the different input handlers for this bot.
    """


    @staticmethod
    async def entrypoint_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send message on `/start` or `/help`."""

        keyboard = [
            [
                InlineKeyboardButton("דירוגים", callback_data=str(TFABApplication.RANKER_MENU)),
                InlineKeyboardButton("מנהלים", callback_data=str(TFABApplication.ADMIN_MENU)),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message is not None:
            # Get user that sent /start and log his name
            user = update.message.from_user
            tfab_logger.info("\nTFAB: User %s started the conversation.\n", user.first_name)

            start_text = """ברוך הבא לבוטיטו!
הבוטיטו נוצר כדי לעזור בארגון משחקי הכדורגל.
לפניך התפריטים הבאים:"""

            await update.message.reply_text(start_text, reply_markup=reply_markup)
        elif update.callback_query is not None:
            start_text = """הפעולה בוצעה בהצלחה.
            לפניך התפריטים הבאים:"""
            await update.callback_query.edit_message_text(start_text, reply_markup=reply_markup)

        return TFABApplication.GENERAL_MENU

    @staticmethod
    async def text_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        This one is basically a router between functions that need input.
        """
        if context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.PLAYERS_MENU_ADD:
            res = await AdminMenuHandlers.PlayersMenuHandlers.add_player_handler(update, context)
            return res
        else:
            raise tfab_exception.TFABException("text input handler reached invalid state")

    @staticmethod
    async def pass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles currently unimplemented options.
        """
        query = update.callback_query
        await query.answer()

        text = """אופציה זו עדיין לא מומשה, ניתן לחזור להתחלה עם  /help"""

        await query.edit_message_text(text)
        return ConversationHandler.END

    @staticmethod
    async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="האופציה הזו לא קיימת, ניתן לחזור להתחלה עם /help")

    @staticmethod
    async def unknown_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="האופציה הזו לא קיימת, ניתן לחזור להתחלה עם /help")


class RankersMenuHandlers(object):
    """
    Encompasses the Ranking menu options.
    """

    @staticmethod
    async def rankers_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the rankers menu.
        """
        query = update.callback_query
        await query.answer()

        text = """להלן פעולות הדירוגים האפשריות:"""

        keyboard = [
            [InlineKeyboardButton("דרג שחקן ספציפי", callback_data=str(TFABApplication.RANKER_MENU_RANK_SPECIFIC_PLAYER))],
            [InlineKeyboardButton("דרג את כולם", callback_data=str(TFABApplication.RANKER_MENU_RANK_EVERYONE))],
            [InlineKeyboardButton("הצג דירוגים שלי", callback_data=str(TFABApplication.RANKER_MENU_SHOW_MY_RANKINGS))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return TFABApplication.RANKER_MENU


class AdminMenuHandlers(object):
    """
    Encompasses the Admin menu options.
    """

    @staticmethod
    async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the admin menu.
        """
        query = update.callback_query
        await query.answer()

        text = """להלן פעולות המנהלים האפשריות:"""

        keyboard = [
            [InlineKeyboardButton("נהל משחקים", callback_data=str(TFABApplication.ADMIN_MENU_GAMES))],
            [InlineKeyboardButton("נהל שחקנים", callback_data=str(TFABApplication.ADMIN_MENU_PLAYERS))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return TFABApplication.ADMIN_MENU

    class PlayersMenuHandlers(object):
        """
        Encompasses the complicated operations of the players menu
        """

        @staticmethod
        async def players_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """
            Handle the admin->players menu.
            """
            query = update.callback_query
            await query.answer()

            text = """בחר את האפשרות הרצויה:"""

            keyboard = [
                [InlineKeyboardButton("הצג שחקנים", callback_data=str(TFABApplication.PLAYERS_MENU_SHOW))],
                [InlineKeyboardButton("הוסף שחקן", callback_data=str(TFABApplication.PLAYERS_MENU_ADD))],
                [InlineKeyboardButton("מחק שחקן", callback_data=str(TFABApplication.PLAYERS_MENU_DELETE)),
                 InlineKeyboardButton("ערוך שחקן", callback_data=str(TFABApplication.PLAYERS_MENU_EDIT))]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            return TFABApplication.ADMIN_MENU_PLAYERS

        @staticmethod
        async def add_player_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_data = context.user_data
            query = update.callback_query
            message = update.message

            # Used to differentiate between the following states:
            # 1. The user got to this handler through the Players menu
            # 2. The user entered the name of the player he wishes to add
            # 3. The user entered the player characteristic

            # Situation 1
            if query is not None:
                await query.answer()

                if query.data == str(TFABApplication.PLAYERS_MENU_ADD):
                    # This means we got here through the players menu
                    user_data[UserDataIndices.CURRENT_STATE] = TFABApplication.PLAYERS_MENU_ADD

                    text = """מה שם השחקן שתרצה להוסיף?"""

                    await query.edit_message_text(text)
                    return TFABApplication.GOT_INPUT

                # Situation 3 - Check if it was a characteristic
                elif query.data in list(tfab_consts.PlayerCharacteristics.values()):
                    if query.data == tfab_consts.PlayerCharacteristics["GOALKEEPER"]:
                        pass
                    elif query.data == tfab_consts.PlayerCharacteristics["DEFENSIVE"]:
                        pass
                    elif query.data == tfab_consts.PlayerCharacteristics["OFFENSIVE"]:
                        pass
                    elif query.data == tfab_consts.PlayerCharacteristics["ALLAROUND"]:
                        pass

                    # Global things to do after choosing the characteristic
                    # Insert name and characteristic to the DB

                    user_data = dict()
                    res = await InputHandlers.entrypoint_handler(update, context)
                    return res
                else:
                    pass # Illegal operation
            elif message is not None:
                # Situation 2
                user_data[UserDataIndices.CONTEXTUAL_ADDED_PLAYER] = message

                text = """בחר את סוג השחקן:"""
                keyboard = [
                    [InlineKeyboardButton("מתאים לכל המגרש", callback_data=str(tfab_consts.PlayerCharacteristics["ALLAROUND"]))],
                    [InlineKeyboardButton("שוער", callback_data=str(tfab_consts.PlayerCharacteristics["GOALKEEPER"])),
                     InlineKeyboardButton("התקפה", callback_data=str(tfab_consts.PlayerCharacteristics["OFFENSIVE"])),
                     InlineKeyboardButton("הגנה", callback_data=str(tfab_consts.PlayerCharacteristics["DEFENSIVE"]))]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await message.reply_text(text, reply_markup=reply_markup)
                return TFABApplication.ADMIN_MENU_PLAYERS

            else:
                tfab_logger.log("Illegal state in bot.", logging.CRITICAL)
                raise tfab_exception.TFABException("Add player handler reached invalid state")


class UserDataIndices(object):
    CONTEXTUAL_ADDED_PLAYER = "AddedPlayer"
    CURRENT_STATE = "CurrentState"