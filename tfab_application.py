# from tfab_logger import tfab_logger
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
# from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
# from telegram.ext import ConversationHandler

# class TFABCommand(object):
#     """
#     Represents an interactive command within TFAB.
#     """

#     def __init__(self, command_string, command_description, command_callback):
#         """
#         :param command_string: The string the user should enter to invoke the command
#         :param command_description: The description of this command, to be printed on demand
#         :param command_callback: The function to call when this command has been invoked
#         """

#         self.str = command_string
#         self.desc = command_description
#         self.callback = command_callback

# class TFABApplication(object):
#     """
#     Handles the entirety of the command handling and logic.
#     """
#     _instance = None
#     JOIN_PENDING_RANK = 0

#     @staticmethod
#     def get_instance(tfab_config=None, tfab_db=None):
#         if TFABApplication._instance is None:
#             TFABApplication._instance = TFABApplication(tfab_config, tfab_db)
#         return TFABApplication._instance

#     def __init__(self, tfab_configuration, tfab_db):
#         """
#         Constructs a TFABApplication.
#         """
#         self.tfab_configuration = tfab_configuration
#         self.tfab_db = tfab_db
#         self.__initialize_telegram_app()
#         self.__initialize_handlers()
#         tfab_logger.debug("TFABApplication successfully initialized")

#     def __initialize_telegram_app(self):
#         """
#         Initiailizes PTB and the connection to our bot.
#         """
#         self.ptb_app = ApplicationBuilder().token(self.tfab_configuration.TELEGRAM_BOT_TOKEN).build()

#     def __initialize_handlers(self):
#         """
#         Initializes the different handlers for this application.
#         """
#         conv_handler_commands = ["join"]

#         # Commands Handlers
#         for cmd in tfab_user_commands:
#             if cmd.str not in conv_handler_commands:
#                 self.ptb_app.add_handler(CommandHandler(cmd.str, cmd.callback))


#         # The regex pattern specified should catch every legal rating - every integer from 0-10, and real between 1-10.
#         conv_handler = ConversationHandler(
#             entry_points=[CommandHandler("join", join_handler)],
#             states={
#                 TFABApplication.JOIN_PENDING_RANK:
#                     [CallbackQueryHandler(join_pending_rank_handler, pattern="^Okay$"),
#                      MessageHandler(filters.Regex("^(?:\d|10|[1-9]\.[0-9]{1,2})$"), join_pending_rank_handler)]
#             },
#             fallbacks=[CommandHandler("cancel", cancel_handler)],
#         )

#         self.ptb_app.add_handler(conv_handler)
#         self.ptb_app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))
#         self.ptb_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), unknown_text_handler))

#     def run(self):
#         """
#         Performs the actual logic of the TFABApplication.
#         """
#         self.ptb_app.run_polling()


# # Helper functions
# def generate_ranker_table_name(chat_id):
#     """
#     :param chat_id: The relevant chat ID.
#     :return: A string that represents the appropriate ranking table name that matches the chat ID.
#     """
#     return TFABApplication.get_instance().tfab_configuration.USER_RANKINGS_TABLE_NAME_PREFIX + str(chat_id)


# def check_if_user_already_exists(chat_id):
#     """
#     :return: True if the user already joined the DB, False otherwise
#     """
#     tfab_app = TFABApplication.get_instance()
#     return tfab_app.tfab_db.check_table_existence(generate_ranker_table_name(chat_id))


# def add_new_ranking_table(chat_id):
#     """
#     Adds a new ranking table for user <chat_id>.
#     :param chat_id:  The chat id that the belongs to.
#     """
#     tfab_app = TFABApplication.get_instance()

#     table_creation_query = """CREATE TABLE "{0}"( 
#     "{1}" TEXT NOT NULL UNIQUE,
#     "{2}" REAL DEFAULT 0,
#     FOREIGN KEY("Name") REFERENCES "{3}"("{4}"));""".format(
#         generate_ranker_table_name(chat_id),
#         tfab_app.tfab_configuration.RANKING_TABLE_NAME_COLUMN, tfab_app.tfab_configuration.RANKING_TABLE_RANK_COLUMN,
#         tfab_app.tfab_configuration.ALL_PLAYERS_TABLE, tfab_app.tfab_configuration.ALL_PLAYERS_NAME_COLUMN)

#     tfab_app.tfab_db.execute_query(table_creation_query)


# def generate_rankings_message(players_and_rankings, with_skipped=False):
#     """
#     Prints A nice message with the players and their rankings.
#     :param players_and_rankings: A list that contains  player-rank tuples
#     :param with_skipped: Whether to print players that were skipped, too
#     """
#     printed_message = "This is your ranking list:"
#     player_index = 1
#     for player_rank in players_and_rankings:
#         if str(player_rank[1]) != "0.0":
#             printed_message += "\n" + "{0}.{1} = {2}".format(player_index, player_rank[0], player_rank[1])
#             player_index = player_index + 1

#     return printed_message

# async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Botito! Use /help to proceed")


# async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     help_message = """Welcome to.. Botito!
# The Botito is a bot used to rank players in football matches.
# To start, you need to /join the Rankers Group.
# Then, run /rank to rank players!
    
# The Botito supports the following commands:
# """
#     global tfab_user_commands
#     for cmd in tfab_user_commands:
#         help_message += f"/{cmd.str} - {cmd.desc}\n"

#     await context.bot.send_message(chat_id=update.effective_chat.id, text=help_message)


# async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if check_if_user_already_exists(update.effective_chat.id):
#         await context.bot.send_message(chat_id=update.effective_chat.id,
#                                        text="You've already joined the Rankers Group!")
#         return

#     add_new_ranking_table(update.effective_chat.id)


#     buttons = [[InlineKeyboardButton("Let's start!", callback_data="Okay")]]

#     # Create an InlineKeyboardMarkup from the list of buttons
#     keyboard = InlineKeyboardMarkup(buttons)

#     await context.bot.send_message(chat_id=update.effective_chat.id,
#                                    text="Congratulations! You joined the Rankers Group!\nLet's start ranking..")
#     await context.bot.send_message(chat_id=update.effective_chat.id,
#                                    text="I will now ask you to rank a new player each time.\n"
#                                         "Please write a number between 1-10.\n"
#                                         "Numbers like 3.5 or 7.8 are okay too.\n"
#                                         "Write 0 if you want to skip the player.\n"
#                                         "If you want to stop, write /cancel.\n"
#                                         "Do you agree?", reply_markup=keyboard)
#     context.user_data["last_player"] = None
#     return TFABApplication.JOIN_PENDING_RANK


# async def join_pending_rank_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     tfab_app = TFABApplication.get_instance()
#     cb_query = update.callback_query

#     if cb_query:
#         await cb_query.answer()
#     else:
#         if context.user_data["last_player"] is not None:
#             insertion_query = """INSERT INTO {0} ({1}, {2}) VALUES ('{3}', {4});""".format(
#                 generate_ranker_table_name(update.effective_chat.id),
#                 tfab_app.tfab_configuration.RANKING_TABLE_NAME_COLUMN,
#                 tfab_app.tfab_configuration.RANKING_TABLE_RANK_COLUMN,
#                 context.user_data["last_player"], update.message.text)

#             tfab_app.tfab_db.execute_query(insertion_query)
#             tfab_app.tfab_db.commit_changes()
#             await context.bot.send_message(chat_id=update.effective_chat.id,
#                                            text="Saved ranking for {0}".format(context.user_data["last_player"]))

#     available_players = tfab_app.tfab_db.get_column_from_table(
#         tfab_app.tfab_configuration.ALL_PLAYERS_NAME_COLUMN, tfab_app.tfab_configuration.ALL_PLAYERS_TABLE)

#     currently_ranked_players = tfab_app.tfab_db.get_column_from_table(
#         tfab_app.tfab_configuration.ALL_PLAYERS_NAME_COLUMN, generate_ranker_table_name(update.effective_chat.id))
#     not_yet_ranked_players = list(set(available_players) - set(currently_ranked_players))

#     if not not_yet_ranked_players:
#         await context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for ranking everyone!")
#         return ConversationHandler.END

#     context.user_data["last_player"] = not_yet_ranked_players[0]
#     await context.bot.send_message(chat_id=update.effective_chat.id,
#                                    text="Please rank {0}\n".format(
#                                        context.user_data["last_player"]))
#     return TFABApplication.JOIN_PENDING_RANK


# async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id,
#                                    text="Alright, we'll continue another time!")


# async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         TFABApplication.get_instance().tfab_db.execute_query("DROP TABLE {0}".format(
#             generate_ranker_table_name(update.effective_chat.id)))
#         TFABApplication.get_instance().tfab_db.commit_changes()
#     except Exception as e:
#         tfab_logger.debug(str(e))
#         await context.bot.send_message(chat_id=update.effective_chat.id,
#                                        text="Nothing to delete, your ranking table does not exist.")
#         return

#     await context.bot.send_message(chat_id=update.effective_chat.id,
#                                    text="Successfully deleted your rankings.")


# async def rank_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # first check if the dude has a table or not
#     if not check_if_user_already_exists(update.effective_chat.id):
#         await context.bot.send_message(chat_id=update.effective_chat.id,
#                                        text="You haven't joined the Rankers Group yet - try running /join")
#         return

#     # Create a list of InlineKeyboardButtons for each ranking option
#     tfab_app = TFABApplication.get_instance()
#     players_names = tfab_app.tfab_db.get_column_from_table(
#         tfab_app.tfab_configuration.ALL_PLAYERS_NAME_COLUMN, tfab_app.tfab_configuration.ALL_PLAYERS_TABLE)
#     keyboard = []
#     for player in players_names:
#         keyboard.append([InlineKeyboardButton(player, callback_data=player)])

#     # Create an InlineKeyboardMarkup from the list of buttons
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     # Send the ranking message with the inline keyboard
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a player:",
#                                    reply_markup=reply_markup)


# async def show_alltime_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not check_if_user_already_exists(update.effective_chat.id):
#         await context.bot.send_message(chat_id=update.effective_chat.id,
#                                        text="You haven't joined the Rankers Group yet - try running /join")
#         return

#     tfab_app = TFABApplication.get_instance()
#     get_rankings_query = """SELECT {0},{1} FROM {2}""".format(
#         tfab_app.tfab_configuration.RANKING_TABLE_NAME_COLUMN, tfab_app.tfab_configuration.RANKING_TABLE_RANK_COLUMN,
#         generate_ranker_table_name(update.effective_chat.id)
#     )
#     results = tfab_app.tfab_db.execute_query(get_rankings_query)
#     await context.bot.send_message(chat_id=update.effective_chat.id,
#                                    text=generate_rankings_message(results))


# async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, this command doesn't exist.")


# async def unknown_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, this option doesn't exist.")


# async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text_caps = ' '.join(context.args).upper()
#     await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


# async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Process specific ranking

#     # Create a list of InlineKeyboardButtons for each ranking option
#     keyboard = []
#     for option in [i for i in range(1, 100)]:
#         keyboard.append([InlineKeyboardButton(option, callback_data=option)])

#     # Create an InlineKeyboardMarkup from the list of buttons
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     # Send the ranking message with the inline keyboard
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose an option:",
#                                    reply_markup=reply_markup)


# # Define a command handler for /verify command (only accessible by the administrator)
# async def verify(update, context):
#     # Perform verification logic
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="Ranking verified!")


# # Define a callback query handler to handle button clicks
# i = 2
# async def button_callback(update: Update, context):
#     query = update.callback_query
#     global i
#     i = i + 1
#     keyboard = []
#     for option in ["{0}".format(num) for num in range(1, i)]:
#         keyboard.append([InlineKeyboardButton(option, callback_data=option)])

#     # Create an InlineKeyboardMarkup from the list of buttons
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     if i != 4 and i != 6:
#         await context.bot.editMessageReplyMarkup(chat_id=query.message.chat_id,
#                                                  message_id=query.message.message_id,
#                                                  reply_markup=reply_markup)
#     else:
#         await context.bot.edit_message_text(
#             chat_id=query.message.chat_id,
#             message_id=query.message.message_id,
#             text=query.data
#         )
#         await context.bot.editMessageReplyMarkup(chat_id=query.message.chat_id,
#                                                  message_id=query.message.message_id,
#                                                  reply_markup=reply_markup)


# tfab_user_commands = []
# tfab_user_commands.append(TFABCommand("start", "Starts the first time interaction with Botito", start_handler))
# tfab_user_commands.append(TFABCommand("help", "Shows the features supported by Botito", help_handler))
# tfab_user_commands.append(TFABCommand("join", "Join the Rankers for Botito", join_handler))
# tfab_user_commands.append(TFABCommand("rank", "Rank a specific player from the group", rank_handler))
# tfab_user_commands.append(TFABCommand("showall", "Show ranking for all of the players", show_alltime_handler))
# tfab_user_commands.append(TFABCommand("delete", "Deletes your rankings completely - be careful!", delete_handler))


# def start_operation():
#     """
#     Currently encompasses all the logic of this bot.
#     :return:
#     """
#     # tfab_app.__app.add_handler(CallbackQueryHandler(button_callback))