import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from models import increase_referral_count
from .helpers import is_private_chat, enforce_membership

async def start_command(message: types.Message):
    """
    Gère la commande /start. 
    Vérifie si l'utilisateur a été parrainé et envoie un message de bienvenue.
    """
    if not await is_private_chat(message):
        return

    # Vérifie l'adhésion au groupe et à la chaîne
    if not await enforce_membership(message.from_user.id, message.bot):
        return

    # Vérifiez si l'utilisateur a été parrainé
    args = message.text.split()[1:]
    if args:
        try:
            ref_user_id = int(args[0])
            if ref_user_id != message.from_user.id:
                referral_count = increase_referral_count(ref_user_id)
                await message.bot.send_message(ref_user_id, f"🎉 Vous avez parrainé un nouvel utilisateur ! Total parrainages : {referral_count}")
        except ValueError:
            logging.error(f"Invalid referral ID: {args[0]}")
        except Exception as e:
            logging.error(f"Error handling referral: {e}")

    welcome_message = (
        "👋 Bienvenue sur le bot d'annonces !\n\n"
        "Ce bot est conçu pour gérer les annonces de vos groupes, chaînes ou bots Telegram.\n\n"
        "Utilisez les commandes suivantes pour interagir avec le bot :\n"
        "1️⃣ /soumettre - Proposer une annonce\n"
        "2️⃣ /lister_annonces - Voir les annonces en attente d'approbation\n"
        "3️⃣ /aide - Obtenir de l'aide sur l'utilisation du bot\n\n"
        "📢 N'hésitez pas à proposer vos annonces ou à consulter celles des autres !"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Soumettre une annonce", callback_data="soumettre")],
            [InlineKeyboardButton(text="📋 Lister les annonces", callback_data="lister_annonces")],
            [InlineKeyboardButton(text="⚙️ Paramètres", callback_data="parametres")],
            [InlineKeyboardButton(text="🆘 Aide", callback_data="aide")],
        ]
    )
    await message.answer(welcome_message, reply_markup=keyboard)

async def aide_command(message: types.Message):
    """
    Gère la commande /aide. 
    Envoie un message d'aide aux utilisateurs.
    """
    if not await is_private_chat(message):
        return

    # Vérifie l'adhésion au groupe et à la chaîne
    if not await enforce_membership(message.from_user.id, message.bot):
        return

    aide_message = (
        "🆘 Aide - Comment utiliser le bot :\n\n"
        "1️⃣ /soumettre - Proposez une nouvelle annonce.\n"
        "2️⃣ /lister_annonces - Liste des annonces en attente d'approbation.\n"
        "❓ Si vous avez des questions, contactez-nous.\n\n"
        "👉 Utilisez les commandes ci-dessus pour commencer."
    )
    await message.answer(aide_message)

async def handle_aide(callback_query: types.CallbackQuery):
    """
    Gère le callback pour l'aide.
    Appelle la fonction aide_command pour envoyer un message d'aide.
    """
    await aide_command(callback_query.message)