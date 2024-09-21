import logging
import os
import asyncio
import datetime
import html
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from dotenv import load_dotenv
from error_handlers import handle_errors
from database import init_db, get_db_connection
from handlers.start import start_command, aide_command, handle_aide
from handlers.feedback import feedback_command, receive_feedback
from handlers.annonces import (
soumettre_annonce_command,
set_title,
set_description,
set_lien,
set_hashtags,
confirm_annonce,
lister_annonces_command,
gestion_annonce,
handle_soumettre,
handle_lister_annonces,
AnnonceForm,
share_approved_annonces
)
from handlers.parametres import (
parametres_command,
toggle_recurrence,
handle_retour,
handle_niveaux
)
# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
GROUP_ID = os.getenv("GROUP_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
# Vérification des variables d'environnement
if not TOKEN or not ADMIN_USER_ID or not GROUP_ID or not CHANNEL_ID:
raise ValueError("TOKEN, ADMIN_USER_ID, GROUP_ID, et CHANNEL_ID doivent
être définis dans le fichier .env")
# Conversion de ADMIN_USER_ID en entier
try:
ADMIN_USER_ID = int(ADMIN_USER_ID)
except ValueError:
raise ValueError("ADMIN_USER_ID doit être un entier valide")
# Configuration du logging
logging.basicConfig(level=logging.INFO)
# Initialiser le bot
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
# Initialiser la base de données
init_db()
def escape_html(text):
"""
Échappe les caractères HTML spéciaux dans le texte donné.
"""
return html.escape(text)
# Enregistrement des gestionnaires de commandes avec le filtre Command
dp.message.register(start_command, Command(commands=["start"]))
dp.message.register(soumettre_annonce_command,
Command(commands=["soumettre"]))
dp.message.register(set_title, AnnonceForm.title)
dp.message.register(set_description, AnnonceForm.description)
dp.message.register(set_lien, AnnonceForm.lien)
dp.message.register(set_hashtags, AnnonceForm.hashtags)
dp.callback_query.register(confirm_annonce, AnnonceForm.confirmation)
dp.message.register(lister_annonces_command,
Command(commands=["lister_annonces"]))
dp.callback_query.register(gestion_annonce, lambda callback_query:
callback_query.data.startswith(("approuver_", "rejeter_")))
dp.message.register(aide_command, Command(commands=["aide"]))
dp.message.register(feedback_command, Command(commands=["feedback"]))
dp.message.register(receive_feedback) # Enregistrement direct
# Enregistrement des gestionnaires pour les boutons interactifs
dp.callback_query.register(handle_soumettre, lambda callback_query:
callback_query.data == "soumettre")
dp.callback_query.register(handle_lister_annonces, lambda callback_query:
callback_query.data == "lister_annonces")
dp.callback_query.register(handle_aide, lambda callback_query:
callback_query.data == "aide")
dp.callback_query.register(parametres_command, lambda callback_query:
callback_query.data == "parametres")
dp.callback_query.register(toggle_recurrence, lambda callback_query:
callback_query.data == "toggle_recurrence")
dp.callback_query.register(handle_retour, lambda callback_query:
callback_query.data == "retour")
dp.callback_query.register(handle_niveaux, lambda callback_query:
callback_query.data == "niveaux")
# Gestionnaire d'erreurs
dp.errors.register(handle_errors)
# Fonction principale pour démarrer le bot
async def main():
logging.info("Starting bot...")
# Lancer la tâche périodique avec bot et GROUP_ID
asyncio.create_task(share_approved_annonces(bot, GROUP_ID))
await dp.start_polling(bot)
if __name__ == "__main__":
asyncio.run(main())
