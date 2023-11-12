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
    ADMIN_LOGIN, \
    RANKERS_LOGIN, \
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
                PLAYERS_MENU_DELETE = range(22)

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
        self.__ptb_app = ApplicationBuilder().token(self.configuration.TELEGRAM_BOT_TOKEN).build()

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
                # TODO: add here -> state for "go back", that holds all of the different functions
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
                    CallbackQueryHandler(AdminMenuHandlers.PlayersMenuHandlers.add_player_handler, pattern=str(TFABApplication.PLAYERS_MENU_ADD)),
                    CallbackQueryHandler(AdminMenuHandlers.PlayersMenuHandlers.show_players_handler, pattern=str(TFABApplication.PLAYERS_MENU_SHOW)),
                    CallbackQueryHandler(AdminMenuHandlers.PlayersMenuHandlers.edit_player_handler, pattern=str(TFABApplication.PLAYERS_MENU_EDIT)),
                    CallbackQueryHandler(AdminMenuHandlers.PlayersMenuHandlers.delete_player_handler, pattern=str(TFABApplication.PLAYERS_MENU_DELETE)),
                    CallbackQueryHandler(AdminMenuHandlers.PlayersMenuHandlers.characteristics_handler, pattern=str("|".join(list(tfab_consts.PlayerCharacteristics.values()))))
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

        class EntryPointStates:
            START = 0,
            END_OF_OPERATION = 1,
            ILLEGAL = 2

        def get_entry_method(update, context):
            """
            :param update: The update received.
            :return: The method by which this function was called.
            """
            if update.message is not None and (update.message.text == "/start" or update.message.text == "/help"):
                # User started the interaction
                return EntryPointStates.START
            if (update.message is None and update.callback_query is not None) or \
               (update.message is not None and update.callback_query is None):
                # Got here through an operation whose last interaction was either :
                # 1. A callback query
                # 2. A message
                return EntryPointStates.END_OF_OPERATION

            # Bugs
            return EntryPointStates.ILLEGAL

        keyboard = [
            [
                InlineKeyboardButton("דירוגים", callback_data=str(TFABApplication.RANKER_MENU)),
                InlineKeyboardButton("מנהלים", callback_data=str(TFABApplication.ADMIN_MENU)),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        entry_method = get_entry_method(update, context)
        if entry_method == EntryPointStates.START:
            # Get user that sent /start and log his name
            user = update.message.from_user
            tfab_logger.info("\nTFAB: User %s started the conversation.\n", user.first_name)

            start_text = """ברוך הבא לבוטיטו!
הבוטיטו נוצר כדי לעזור בארגון משחקי הכדורגל.
לפניך התפריטים הבאים:"""

            await update.message.reply_text(start_text, reply_markup=reply_markup)
        if entry_method == EntryPointStates.END_OF_OPERATION:
            operation_success_message = """הפעולה בוצעה בהצלחה."""
            operation_failure_message = """הפעולה נכשלה."""
            menus_text = """לפניך התפריטים הבאים:"""
            final_text = ""

            if context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS]:
                final_text = operation_success_message + "\n" + menus_text
            else:
                final_text = operation_failure_message + "\n" + menus_text

            await context.bot.send_message(chat_id=update.effective_chat.id, text=final_text, reply_markup=reply_markup)
        if entry_method == EntryPointStates.ILLEGAL:
            await InputHandlers.illegal_situation_handler(update, context)

        context.user_data.clear()
        return TFABApplication.GENERAL_MENU

    @staticmethod
    async def text_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        This one is basically a router between functions that need input.
        """
        if context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.PLAYERS_MENU_ADD:
            return await AdminMenuHandlers.PlayersMenuHandlers.add_player_handler(update, context)
        elif context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.PLAYERS_MENU_DELETE:
            return await AdminMenuHandlers.PlayersMenuHandlers.delete_player_handler(update, context)
        elif context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.PLAYERS_MENU_EDIT:
            return await AdminMenuHandlers.PlayersMenuHandlers.edit_player_handler(update, context)
        elif context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.ADMIN_LOGIN:
            return await InputHandlers.admin_login_handler(update, context)
        elif context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.RANKERS_LOGIN:
            return await InputHandlers.ranker_login_handler(update, context)
        else:
            raise tfab_exception.TFABException("text input handler reached invalid state")

    @staticmethod
    async def admin_login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Responsible for validating admin requests.
        """
        if UserDataIndices.CURRENT_STATE in context.user_data and \
            context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.ADMIN_LOGIN:
                if update.message:
                    if update.message.text:
                        if update.message.text == \
                            TFABApplication.get_instance().configuration.BOTITO_SECRET_ADMINS_PASSWORD:
                            TFABApplication.get_instance().db.insert_admin\
                    (update.effective_user.first_name + " "+ update.effective_user.last_name, update.effective_user.id)
                            context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
                            return await InputHandlers.entrypoint_handler(update, context)
                # If this is not just a regular text message, fail
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text="הסיסמא שגויה.")
                context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                return await InputHandlers.entrypoint_handler(update, context)
        else:
            context.user_data[UserDataIndices.CURRENT_STATE] = TFABApplication.ADMIN_LOGIN
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="אנא הקלד את סיסמת המנהלים")
            return TFABApplication.GOT_INPUT

    @staticmethod
    async def ranker_login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Responsible for validating ranker requests.
        """
        if UserDataIndices.CURRENT_STATE in context.user_data and \
                context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.RANKERS_LOGIN:
            if update.message:
                if update.message.text:
                    if update.message.text == \
                            TFABApplication.get_instance().configuration.BOTITO_SECRET_RANKERS_PASSWORD:
                        TFABApplication.get_instance().db.insert_ranker \
                            (update.effective_user.first_name + " " + update.effective_user.last_name,
                             update.effective_user.id)
                        context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
                        return await InputHandlers.entrypoint_handler(update, context)
            # If this is not just a regular text message, fail
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="הסיסמא שגויה.")
            context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
            return await InputHandlers.entrypoint_handler(update, context)
        else:
            context.user_data[UserDataIndices.CURRENT_STATE] = TFABApplication.RANKERS_LOGIN
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="אנא הקלד את סיסמת המדרגים")
            return TFABApplication.GOT_INPUT

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
                                       text="האופציה לא קיימת. לחזרה לתפריט הראשי /help")

    @staticmethod
    async def unknown_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="האופציה לא קיימת. לחזרה לתפריט הראשי /help")

    @staticmethod
    async def illegal_situation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="הגעת למצב בלתי אפשרי, דווח על זה במהירות למפתחים")

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

        # First check if the user is logged in as a ranker.
        if not TFABApplication.get_instance().db.check_ranker_existence(update.effective_user.id):
            return await InputHandlers.ranker_login_handler(update, context)

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

        # First check if the user is logged in as admin.
        if not TFABApplication.get_instance().db.check_admin_existence(update.effective_user.id):
            return await InputHandlers.admin_login_handler(update, context)


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
                    player_name = user_data[UserDataIndices.CONTEXTUAL_ADDED_PLAYER]
                    characteristic = None
                    if query.data in [tfab_consts.PlayerCharacteristics["GOALKEEPER"],
                                      tfab_consts.PlayerCharacteristics["DEFENSIVE"],
                                      tfab_consts.PlayerCharacteristics["OFFENSIVE"],
                                      tfab_consts.PlayerCharacteristics["ALLAROUND"]]:
                        characteristic = query.data

                    if not player_name or not characteristic:
                        return await InputHandlers.illegal_situation_handler(update, context)
                    TFABApplication.get_instance().db.insert_player(player_name, characteristic)

                    user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
                    return await InputHandlers.entrypoint_handler(update, context)
                else:
                    return await InputHandlers.illegal_situation_handler(update, context)
            elif message is not None:
                # Situation 2
                user_data[UserDataIndices.CONTEXTUAL_ADDED_PLAYER] = message.text

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

        @staticmethod
        async def edit_player_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_data = context.user_data
            query = update.callback_query
            message = update.message

            # Used to differentiate between the following states:
            # 1. The user got to this handler through the Players menu
            # 2. The user entered the name of the player he wishes to edit
            # 3. The user entered the new player characteristic

            # Situation 1
            if query is not None:
                await query.answer()

                if query.data == str(TFABApplication.PLAYERS_MENU_EDIT):
                    # This means we got here through the players menu
                    user_data[UserDataIndices.CURRENT_STATE] = TFABApplication.PLAYERS_MENU_EDIT

                    text = """מה שם השחקן שתרצה לערוך?"""

                    await query.edit_message_text(text)
                    return TFABApplication.GOT_INPUT

                # Situation 3 - Check if it was a characteristic
                elif query.data in list(tfab_consts.PlayerCharacteristics.values()):
                    player_name = user_data[UserDataIndices.CONTEXTUAL_EDITED_PLAYER]
                    characteristic = None
                    if query.data in [tfab_consts.PlayerCharacteristics["GOALKEEPER"],
                                      tfab_consts.PlayerCharacteristics["DEFENSIVE"],
                                      tfab_consts.PlayerCharacteristics["OFFENSIVE"],
                                      tfab_consts.PlayerCharacteristics["ALLAROUND"]]:
                        characteristic = query.data

                    if not player_name or not characteristic:
                        return await InputHandlers.illegal_situation_handler(update, context)

                    if TFABApplication.get_instance().db.edit_player(player_name, characteristic):
                        user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
                        return await InputHandlers.entrypoint_handler(update, context)
                    else:
                        await context.bot.send_message(chat_id=update.effective_chat.id,
                                                       text="""קרתה שגיאה בפעולת עריכת השחקן""")
                        context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                        return await InputHandlers.entrypoint_handler(update, context)
                else:
                    user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                    return await InputHandlers.illegal_situation_handler(update, context)
            elif message is not None:
                # Situation 2
                user_data[UserDataIndices.CONTEXTUAL_EDITED_PLAYER] = message.text

                if not TFABApplication.get_instance().db.check_player_existence(message.text):
                    await context.bot.send_message(chat_id=update.effective_chat.id,
                                                   text="""לא קיים שחקן כזה, וודא שהשם כתוב נכון""")
                    context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                    return await InputHandlers.entrypoint_handler(update, context)

                text = """בחר את הסוג המעודכן עבור השחקן:"""
                keyboard = [
                    [InlineKeyboardButton("מתאים לכל המגרש",
                                          callback_data=str(tfab_consts.PlayerCharacteristics["ALLAROUND"]))],
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

        @staticmethod
        async def delete_player_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_data = context.user_data
            query = update.callback_query
            message = update.message

            # Used to differentiate between the following states:
            # 1. The user got to this handler through the Players menu
            # 2. The user entered the name of the player he wishes to delete

            # Situation 1
            if query is not None:
                await query.answer()

                if query.data == str(TFABApplication.PLAYERS_MENU_DELETE):
                    # This means we got here through the players menu
                    user_data[UserDataIndices.CURRENT_STATE] = TFABApplication.PLAYERS_MENU_DELETE

                    text = """מה שם השחקן שתרצה למחוק?"""

                    await query.edit_message_text(text)
                    return TFABApplication.GOT_INPUT
                else:
                    return await InputHandlers.illegal_situation_handler(update, context)
            # Situation 2
            elif message is not None:
                player_name = message.text
                if not player_name:
                    return await InputHandlers.illegal_situation_handler(update, context)

                if TFABApplication.get_instance().db.delete_player(player_name):
                    context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
                    return await InputHandlers.entrypoint_handler(update, context)
                else:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="""לא קיים שחקן כזה, וודא שהשם כתוב נכון""")
                    context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                    return await InputHandlers.entrypoint_handler(update, context)
            else:
                tfab_logger.log("Illegal state in bot.", logging.CRITICAL)
                raise tfab_exception.TFABException("Add player handler reached invalid state")

        @staticmethod
        async def show_players_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query

            # Situation 1
            if query is None:
                tfab_logger.log("Illegal state in bot.", logging.CRITICAL)
                raise tfab_exception.TFABException("Add player handler reached invalid state")

            await query.answer()

            all_players_message = TFABApplication.get_instance().db.show_all_players()
            context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True

            await context.bot.send_message(chat_id=update.effective_chat.id, text=all_players_message)
            return await InputHandlers.entrypoint_handler(update, context)

        @staticmethod
        async def characteristics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if UserDataIndices.CURRENT_STATE in context.user_data:
                state = context.user_data[UserDataIndices.CURRENT_STATE]
                if state == TFABApplication.PLAYERS_MENU_ADD:
                    return await AdminMenuHandlers.PlayersMenuHandlers.add_player_handler(update, context)
                elif state == TFABApplication.PLAYERS_MENU_EDIT:
                    return await AdminMenuHandlers.PlayersMenuHandlers.edit_player_handler(update, context)

            return await InputHandlers.illegal_situation_handler(update, context)


class UserDataIndices(object):
    CONTEXTUAL_ADDED_PLAYER = "AddedPlayer"
    CONTEXTUAL_DELETED_PLAYER = "DeletedPlayer"
    CONTEXTUAL_EDITED_PLAYER = "EditedPlayer"
    CURRENT_STATE = "CurrentState"
    CONTEXTUAL_LAST_OPERATION_STATUS = "CurrentStatus"