import logging
import tfab_exception
import tfab_team_generator
import tfab_consts
from datetime import datetime

import tfab_message_parser
from tfab_logger import tfab_logger
from telegram.constants import ParseMode
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
            RANKER_MENU_SHOW_MY_RANKINGS, \
        ADMIN_MENU, \
            ADMIN_MENU_MATCHDAYS, \
                MATCHDAYS_MENU_SET_TODAY_LIST, \
                MATCHDAYS_MENU_GENERATE_TEAMS, \
                MATCHDAYS_MENU_RANK_OUTSIDER, \
                MATCHDAYS_MENU_SHOW_TODAY_INFO, \
            ADMIN_MENU_PLAYERS, \
                PLAYERS_MENU_ADD, \
                PLAYERS_MENU_SHOW, \
                PLAYERS_MENU_EDIT, \
                PLAYERS_MENU_DELETE = range(18)

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
                TFABApplication.RANKER_MENU: [
                    CallbackQueryHandler(RankersMenuHandlers.rank_everyone_handler, pattern=str(TFABApplication.RANKER_MENU_RANK_EVERYONE)),
                    CallbackQueryHandler(RankersMenuHandlers.show_my_rankings_handler, pattern=str(TFABApplication.RANKER_MENU_SHOW_MY_RANKINGS)),
                ],
                TFABApplication.ADMIN_MENU: [
                    CallbackQueryHandler(AdminMenuHandlers.MatchdaysMenuHandlers.matchdays_menu_handler, pattern=str(TFABApplication.ADMIN_MENU_MATCHDAYS)),
                    CallbackQueryHandler(AdminMenuHandlers.PlayersMenuHandlers.players_menu_handler, pattern=str(TFABApplication.ADMIN_MENU_PLAYERS)),
                ],
                TFABApplication.ADMIN_MENU_MATCHDAYS: [
                    CallbackQueryHandler(AdminMenuHandlers.MatchdaysMenuHandlers.set_todays_list_handler, pattern=str(TFABApplication.MATCHDAYS_MENU_SET_TODAY_LIST)),
                    CallbackQueryHandler(InputHandlers.pass_handler, pattern=str(TFABApplication.MATCHDAYS_MENU_RANK_OUTSIDER)),
                    CallbackQueryHandler(AdminMenuHandlers.MatchdaysMenuHandlers.show_todays_info_handler, pattern=str(TFABApplication.MATCHDAYS_MENU_SHOW_TODAY_INFO)),
                    CallbackQueryHandler(AdminMenuHandlers.MatchdaysMenuHandlers.generate_teams_handler, pattern=str(TFABApplication.MATCHDAYS_MENU_GENERATE_TEAMS)),
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

class HandlerUtils(object):
    """
    Contains utilities for the different handlers.
    """
    class UpdateType:
        CALLBACK_QUERY = 0,
        TEXTUAL_MESSAGE = 1,
        OTHER = 2


    @staticmethod
    def get_update_type(update):
        if update.message and update.message.text and update.message.text != "":
            return HandlerUtils.UpdateType.TEXTUAL_MESSAGE
        elif update.message is None and update.callback_query is not None:
            return HandlerUtils.UpdateType.CALLBACK_QUERY

        return HandlerUtils.UpdateType.OTHER


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
            update_type = HandlerUtils.get_update_type(update)
            if update_type == HandlerUtils.UpdateType.TEXTUAL_MESSAGE:
                if update.message.text == "/start" or update.message.text == "/help":
                    return EntryPointStates.START

            if update_type != HandlerUtils.UpdateType.OTHER:
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
        elif context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.RANKER_MENU_RANK_EVERYONE:
            return await RankersMenuHandlers.rank_everyone_handler(update, context)
        elif context.user_data[UserDataIndices.CURRENT_STATE] == TFABApplication.MATCHDAYS_MENU_SET_TODAY_LIST:
            return await AdminMenuHandlers.MatchdaysMenuHandlers.set_todays_list_handler(update, context)
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
                            if update.effective_user.first_name and update.effective_user.last_name:
                                TFABApplication.get_instance().db.insert_admin\
                    (update.effective_user.first_name + " "+ update.effective_user.last_name, update.effective_user.id)
                            elif update.effective_user.first_name:
                                TFABApplication.get_instance().db.insert_admin \
                                    (update.effective_user.first_name,
                                     update.effective_user.id)
                            else:
                                await context.bot.send_message(chat_id=update.effective_chat.id,
                                                               text="השם שלך בטלגרם מוזר, תקן אותו אחי ואז תחזור")
                                context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                                return await InputHandlers.entrypoint_handler(update, context)
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
                        if update.effective_user.first_name and update.effective_user.last_name:
                            TFABApplication.get_instance().db.insert_ranker \
                                (update.effective_user.first_name + " " + update.effective_user.last_name,
                                 update.effective_user.id)
                        elif update.effective_user.first_name:
                            TFABApplication.get_instance().db.insert_ranker \
                                (update.effective_user.first_name,
                                 update.effective_user.id)
                        else:
                            await context.bot.send_message(chat_id=update.effective_chat.id,
                                                           text="השם שלך בטלגרם מוזר, תקן אותו אחי ואז תחזור")
                            context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                            return await InputHandlers.entrypoint_handler(update, context)
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
    def get_rankings_template(update, context):
        player_names = [name for name, _ in TFABApplication.get_instance().db.get_player_list()]
        user_rankings = TFABApplication.get_instance().db.get_user_rankings(update.effective_user.id)
        if user_rankings is None:
            raise tfab_exception.TFABException("Logged-in user doesn't have rankings!")

        return tfab_message_parser.MessageParser.generate_rankings_template(player_names, user_rankings)

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
            [InlineKeyboardButton("דרג שחקנים", callback_data=str(TFABApplication.RANKER_MENU_RANK_EVERYONE))],
            [InlineKeyboardButton("הצג דירוגים שלי", callback_data=str(TFABApplication.RANKER_MENU_SHOW_MY_RANKINGS))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return TFABApplication.RANKER_MENU

    @staticmethod
    async def rank_everyone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the "rank everyone" option.
        """
        update_type = HandlerUtils.get_update_type(update)

        if update_type == HandlerUtils.UpdateType.OTHER:
            await InputHandlers.illegal_situation_handler(update, context)
            return TFABApplication.GENERAL_MENU
        elif update_type == HandlerUtils.UpdateType.CALLBACK_QUERY:
            await update.callback_query.answer()

            rankings_template = RankersMenuHandlers.get_rankings_template(update, context)

            await context.bot.send_message(chat_id=update.effective_chat.id, text=rankings_template)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="""שלחתי לך תבנית לדירוגים, תמלא אותה ושלח לי""")
            context.user_data[UserDataIndices.CURRENT_STATE] = TFABApplication.RANKER_MENU_RANK_EVERYONE
            return TFABApplication.GOT_INPUT
        elif update_type == HandlerUtils.UpdateType.TEXTUAL_MESSAGE:
            # Do stuff after you got the user's ranking message
            rankings_message = update.message.text
            rankings_dict = tfab_message_parser.MessageParser.parse_rankings_message(rankings_message)
            found, modified = TFABApplication.get_instance().db.modify_user_rankings(update.effective_user.id, rankings_dict)

            if modified:
                success_message = "להלן פעולות הדירוג שבוצעו בהצלחה:\n"
                for name, ranking in rankings_dict.items():
                    success_message += "{0} = {1}\n".format(name, ranking)

                await context.bot.send_message(chat_id=update.effective_chat.id, text=success_message)
            elif found:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="לא בוצעו שינויים, הזנת דירוגים שגויים או זהים לקודמים. כמו כן, לא ניתן לדרג שוערים")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="פעולת הדירוג נכשלה, האם ההודעה שלך תקינה?")
            context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = found
            return await InputHandlers.entrypoint_handler(update, context)

        return await InputHandlers.illegal_situation_handler(update, context)

    @staticmethod
    async def show_my_rankings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the "show my rankings" option.
        """
        if HandlerUtils.get_update_type(update) != HandlerUtils.UpdateType.CALLBACK_QUERY:
            await InputHandlers.illegal_situation_handler(update, context)
            return TFABApplication.GENERAL_MENU

        await update.callback_query.answer()

        rankings_template = RankersMenuHandlers.get_rankings_template(update, context)

        await context.bot.send_message(chat_id=update.effective_chat.id, text=rankings_template)
        context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
        return await InputHandlers.entrypoint_handler(update, context)


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
            [InlineKeyboardButton("נהל משחקים", callback_data=str(TFABApplication.ADMIN_MENU_MATCHDAYS))],
            [InlineKeyboardButton("נהל שחקנים", callback_data=str(TFABApplication.ADMIN_MENU_PLAYERS))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return TFABApplication.ADMIN_MENU

    class MatchdaysMenuHandlers(object):
        """
        Handles the matchdays menu hierarchy.
        """

        @staticmethod
        async def matchdays_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """
            Handle the admin->matchdays menu.
            """
            query = update.callback_query
            await query.answer()

            text = """בחר את האפשרות הרצויה:"""

            keyboard = [
                [InlineKeyboardButton("הצג מידע להיום", callback_data=str(TFABApplication.MATCHDAYS_MENU_SHOW_TODAY_INFO))],
                [InlineKeyboardButton("צור כוחות", callback_data=str(TFABApplication.MATCHDAYS_MENU_GENERATE_TEAMS))],
                [InlineKeyboardButton("קבע רשימה להיום", callback_data=str(TFABApplication.MATCHDAYS_MENU_SET_TODAY_LIST)),
                 InlineKeyboardButton("דרג מזמין חיצוני", callback_data=str(TFABApplication.MATCHDAYS_MENU_RANK_OUTSIDER))]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            return TFABApplication.ADMIN_MENU_MATCHDAYS

        @staticmethod
        async def generate_teams_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """
            Handle the admin->matchdays->generate teams menu.
            """
            query = update.callback_query
            await query.answer()
            db = TFABApplication.get_instance().db

            today_date = datetime.now().strftime(db.MATCHDAYS_DATE_FORMAT)
            if not db.check_matchday_existence(today_date):
                context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                await context.bot.send_message(chat_id=update.effective_chat.id, text="עדיין לא נקבעה רשימה להיום")
                return await InputHandlers.entrypoint_handler(update, context)

            todays_matchday = db.get_matchday(today_date)
            todays_player_list = todays_matchday[db.MATCHDAYS_ROSTER_KEY]

            all_players_exist_in_db = True
            for player in todays_player_list:
                if not db.check_player_existence(player):
                    all_players_exist_in_db = False
                    break

            if not all_players_exist_in_db:
                context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                await context.bot.send_message(chat_id=update.effective_chat.id, text="ברשימה קיימים שחקנים לא מוכרים למערכת, תוסיף אותם דרך תפריט השחקנים ואז נסה שוב")
                return await InputHandlers.entrypoint_handler(update, context)

            # Prepare the data for the generation function
            player_dicts_list = []
            for player in todays_player_list:
                player_dicts_list.append({
                    db.PLAYERS_NAME_KEY: player,
                    db.PLAYERS_CHARACTERISTICS_KEY: db.get_player_characteristic(player),
                    db.MATCHDAYS_SPECIFIC_TEAM_PLAYER_RATING_KEY: db.get_player_average_rating(player)})

            await context.bot.send_message(chat_id=update.effective_chat.id, text="מחשב..")
            teams_dict = tfab_team_generator.TeamGenerator.generate_teams(player_dicts_list, True)
            if not db.insert_teams_to_matchday(today_date, teams_dict):
                # Impossible because we already checked that there is a matchday occuring today
                await InputHandlers.illegal_situation_handler(update, context)
                return TFABApplication.GENERAL_MENU

            message = tfab_message_parser.MessageParser.generate_matchday_message(db.get_matchday(today_date))
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
            context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
            return await InputHandlers.entrypoint_handler(update, context)

        @staticmethod
        async def set_todays_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """
            Handle the admin->matchdays->set list menu.
            """
            update_type = HandlerUtils.get_update_type(update)

            if update_type == HandlerUtils.UpdateType.CALLBACK_QUERY:
                await update.callback_query.answer()

                await context.bot.send_message(chat_id=update.effective_chat.id, text="שלח בבקשה את רשימת המשחק להיום")
                context.user_data[UserDataIndices.CURRENT_STATE] = TFABApplication.MATCHDAYS_MENU_SET_TODAY_LIST
                return TFABApplication.GOT_INPUT
            elif update_type == HandlerUtils.UpdateType.TEXTUAL_MESSAGE:
                # Do stuff after you got the user's list
                list_message = update.message.text
                result_dictionary = tfab_message_parser.MessageParser.parse_matchday_message(list_message)
                context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False

                if result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_ROSTER_KEY] is None:
                    await context.bot.send_message(chat_id=update.effective_chat.id,
                                                   text="הרשימה ששלחת לא תקינה, לא הצלחתי לקרוא את רשימת השחקנים כהלכה")
                    return await InputHandlers.entrypoint_handler(update, context)
                elif result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_DATE_KEY] is None:
                    await context.bot.send_message(chat_id=update.effective_chat.id,
                                                   text="הרשימה ששלחת לא תקינה, לא הצלחתי לקרוא את התאריך כהלכה")
                    return await InputHandlers.entrypoint_handler(update, context)
                elif result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_LOCATION_KEY] is None:
                    await context.bot.send_message(chat_id=update.effective_chat.id,
                                                   text="הרשימה ששלחת לא תקינה, לא הצלחתי לקרוא את המיקום כהלכה")
                    return await InputHandlers.entrypoint_handler(update, context)
                elif result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_ORIGINAL_MESSAGE_KEY] is None:
                    return await InputHandlers.illegal_situation_handler(update, context)

                today_date = datetime.now().strftime(TFABApplication.get_instance().db.MATCHDAYS_DATE_FORMAT)
                if today_date != result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_DATE_KEY]:
                    context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = False
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="ניתן לקבוע רשימה רק ביום המשחק")
                    return await InputHandlers.entrypoint_handler(update, context)

                # Insert DB information
                TFABApplication.get_instance().db.insert_matchday(
                    result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_ORIGINAL_MESSAGE_KEY],
                    result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_LOCATION_KEY],
                    result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_ROSTER_KEY],
                    result_dictionary[TFABApplication.get_instance().db.MATCHDAYS_DATE_KEY])

                await context.bot.send_message(chat_id=update.effective_chat.id,
                                                   text="הרשימה תקינה ונקלטה בהצלחה")
                context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
                return await InputHandlers.entrypoint_handler(update, context)

            await InputHandlers.illegal_situation_handler(update, context)
            return TFABApplication.GENERAL_MENU

        @staticmethod
        async def show_todays_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """
            Handle the admin->matchdays->show info menu.
            """
            await update.callback_query.answer()
            today_date = datetime.now().strftime(TFABApplication.get_instance().db.MATCHDAYS_DATE_FORMAT)
            todays_matchday = TFABApplication.get_instance().db.get_matchday(today_date)

            if not todays_matchday:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="עדיין לא נקבעה רשימה להיום")
            else:
                message = tfab_message_parser.MessageParser.generate_matchday_message(todays_matchday)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

            context.user_data[UserDataIndices.CONTEXTUAL_LAST_OPERATION_STATUS] = True
            return await InputHandlers.entrypoint_handler(update, context)

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

            all_players_list = TFABApplication.get_instance().db.get_player_list()
            all_players_message = tfab_message_parser.MessageParser.stringify_player_list(all_players_list)
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