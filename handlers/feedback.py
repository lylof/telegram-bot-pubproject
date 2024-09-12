import os
import logging
from aiogram import types
from .helpers import is_private_chat, enforce_membership

async def feedback_command(message: types.Message):
    """
    Gère la commande /feedback.
    Invite l'utilisateur à entrer ses commentaires ou suggestions.
    """
    if not await is_private_chat(message):
        return

    # Vérifie l'adhésion au groupe et à la chaîne
    if not await enforce_membership(message.from_user.id, message.bot):
        return

    await message.answer("✍️ Veuillez entrer vos commentaires ou suggestions :")

async def receive_feedback(message: types.Message):
    """
    Reçoit les commentaires ou suggestions de l'utilisateur et les envoie à l'administrateur.
    """
    if not await is_private_chat(message):
        return

    # Vérifie l'adhésion au groupe et à la chaîne
    if not await enforce_membership(message.from_user.id, message.bot):
        return

    feedback_text = message.text.strip()
    if not feedback_text:
        await message.answer("⚠️ Les commentaires ne peuvent pas être vides. Veuillez entrer vos commentaires ou suggestions.")
        return

    await message.answer("🙏 Merci pour vos retours ! Nous apprécions votre contribution.")

    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
    try:
        await message.bot.send_message(ADMIN_USER_ID, f"📩 Nouveau feedback reçu :\n\n{feedback_text}")
    except Exception as e:
        logging.error(f"Error sending feedback to admin: {e}")
        await message.answer("⚠️ Une erreur s'est produite lors de l'envoi de vos retours. Veuillez réessayer plus tard.")