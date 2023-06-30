import logging
from tfab_logger import logger
from tfab_configuration import TFABConfiguration
from enum import Enum
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# CURRENT-MODULE-CONSTANTS
TFAB_CONFIGURATION_PATH = "tfab_data//tfab_configuration.yaml"

class ProcessExitCodes(Enum):
    STATUS_SUCCESS = 0
    STATUS_FAILURE = 1



async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #Process specific ranking

    # Create a list of InlineKeyboardButtons for each ranking option
    keyboard = []
    for option in ["option1", "option2", "option3"]:
        keyboard.append([InlineKeyboardButton(option, callback_data=option)])

    # Create an InlineKeyboardMarkup from the list of buttons
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the ranking message with the inline keyboard
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose an option:", reply_markup=reply_markup)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="האופציה הזו לא קיימת, אנא נסה שוב")

# Define a command handler for /verify command (only accessible by the administrator)
async def verify(update, context):
    # Perform verification logic
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ranking verified!")

# Define a callback query handler to handle button clicks
i = 2
async def button_callback(update: Update, context):
    query = update.callback_query
    global i
    i = i + 1
    keyboard = []
    for option in ["{0}".format(num) for num in range(1,i)]:
        keyboard.append([InlineKeyboardButton(option, callback_data=option)])


def start_operation():
    """
    Currently encompasses all the logic of this bot.
    :return:
    """
    try:
        tfab_configuration = TFABConfiguration(TFAB_CONFIGURATION_PATH)
    except Exception as e:
        logger.error("General Exception occured: ", str(e))
        exit(ProcessExitCodes.STATUS_FAILURE)

    application = ApplicationBuilder().token(tfab_configuration.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('caps', caps))
    application.add_handler(CommandHandler('rank', rank))
    application.add_handler(CommandHandler('verify', verify))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling()

if __name__ == '__main__':
    start_operation()
    exit(ProcessExitCodes.STATUS_SUCCESS)