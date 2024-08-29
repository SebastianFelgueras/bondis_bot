from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from threading import Lock 
import logging
import pickle
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Predefined categories
with open("lineas_de_bondi.txt") as f:
    lineas_de_bondi = [int(x) for x in f.read().split()]

# Dictionary to keep track of subscribers by category
class suscriptos:
    def __init__(self) -> None:
        try:
            pickle.load("DB.pkl")
        except:
            self.suscriptos = {linea:set() for linea in lineas_de_bondi}
    def __call__(self,user,linea):
        self.suscriptos[linea].add(user)
    def guardar(self):
        with open("DB.pkl","wb") as f:
            pickle.dump(self,f)
subscriptions = suscriptos()

# Command handler to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f'Hola! Te podés suscribir para que te avise cada vez que un bondi de las líneas que te interesen entre a ciudad.\n'
    )

# Command handler to show subscription categories as buttons
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(str(category), callback_data=f"subscribe {category}")] for category in lineas_de_bondi
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Elegí una línea para suscribirte:',
        reply_markup=reply_markup
    )

# Callback de suscripción
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    data = query.data
    action, linea = data.split()
    linea = int(linea)
    chat_id = query.message.chat_id

    if action == "subscribe":
        subscriptions(chat_id,linea)
        await query.edit_message_text(f'Te suscribiste a la línea {linea}')
    elif action == "unsubscribe":
        if chat_id in subscriptions.suscriptos[linea]:
            subscriptions.suscriptos[linea].remove(chat_id)
            await query.edit_message_text(f'Te desuscribiste de la línea {linea}')
        else:
            await query.edit_message_text(f'No estabas suscripto a la línea {linea}')
    subscriptions.guardar()


# Command handler to unsubscribe a user from a category
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    subscribed_categories = [category for category in lineas_de_bondi if chat_id in subscriptions.suscriptos[category]]

    if not subscribed_categories:
        await update.message.reply_text('No estás suscripto a nada')
        return

    keyboard = [
        [InlineKeyboardButton(str(category), callback_data=f"unsubscribe {category}")]
        for category in subscribed_categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Elegí una categoría de la cual desuscribirte:',
        reply_markup=reply_markup
    )


async def notify_subscribers(context: ContextTypes.DEFAULT_TYPE, linea: int):
    for chat_id in subscriptions.suscriptos[linea]:
        await context.bot.send_message(chat_id=chat_id, text=f"Acaba de llegar un bondi de la línea {linea}!")

def main() -> None:
    with open("token.txt","r") as t:
        application = ApplicationBuilder().token(t.read()).build()

    application.job_queue.run_repeating(thread, interval=5, first=10)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("suscribirse", subscribe))
    application.add_handler(CommandHandler("desuscribirse", unsubscribe))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

async def thread(context):
    for linea in lineas_de_bondi:
        await notify_subscribers(context,linea)

if __name__ == '__main__':
    main()
