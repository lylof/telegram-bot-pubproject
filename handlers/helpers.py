import os
import html
import logging
from aiogram import types
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
CHANNEL_ID = os.getenv("CHANNEL_ID")
GROUP_ID = os.getenv("GROUP_ID")

if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID is not set in the environment variables")
if not GROUP_ID:
    raise ValueError("GROUP_ID is not set in the environment variables")

async def is_private_chat(message: types.Message) -> bool:
    """
    Vérifie si le message provient d'un chat privé.

    Args:
        message (types.Message): Le message reçu.

    Returns:
        bool: True si le message provient d'un chat privé, False sinon.
    """
    return message.chat.type == "private"

def escape_html(text: str) -> str:
    """
    Échappe les caractères HTML spéciaux dans le texte donné.

    Args:
        text (str): Le texte à échapper.

    Returns:
        str: Le texte avec les caractères HTML échappés.
    """
    return html.escape(text)

def row_to_dict(row) -> dict:
    """
    Convertit un objet sqlite3.Row en dictionnaire.

    Args:
        row (sqlite3.Row): L'objet Row à convertir.

    Returns:
        dict: Le dictionnaire correspondant.
    """
    return {key: row[key] for key in row.keys()}

async def check_channel_membership(user_id: int, bot) -> bool:
    """
    Vérifie si l'utilisateur a rejoint la chaîne Telegram requise.

    Args:
        user_id (int): L'ID de l'utilisateur.
        bot: L'objet bot pour effectuer la vérification.

    Returns:
        bool: True si l'utilisateur est membre de la chaîne, False sinon.
    """
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Error checking channel membership for user {user_id}: {e}")
        return False

async def check_group_membership(user_id: int, bot) -> bool:
    """
    Vérifie si l'utilisateur a rejoint le groupe Telegram requis.

    Args:
        user_id (int): L'ID de l'utilisateur.
        bot: L'objet bot pour effectuer la vérification.

    Returns:
        bool: True si l'utilisateur est membre du groupe, False sinon.
    """
    try:
        member = await bot.get_chat_member(GROUP_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Error checking group membership for user {user_id}: {e}")
        return False

async def check_membership(user_id: int, bot) -> bool:
    """
    Vérifie si l'utilisateur a rejoint à la fois le groupe et la chaîne Telegram requis.

    Args:
        user_id (int): L'ID de l'utilisateur.
        bot: L'objet bot pour effectuer la vérification.

    Returns:
        bool: True si l'utilisateur est membre du groupe et de la chaîne, False sinon.
    """
    is_in_channel = await check_channel_membership(user_id, bot)
    is_in_group = await check_group_membership(user_id, bot)
    return is_in_channel and is_in_group

async def enforce_membership(user_id: int, bot) -> bool:
    """
    Enforce l'utilisateur à rejoindre le groupe et la chaîne avant de permettre des actions.

    Args:
        user_id (int): L'ID de l'utilisateur.
        bot: L'objet bot pour effectuer la vérification.

    Returns:
        bool: True si l'utilisateur est membre du groupe et de la chaîne, False sinon.
    """
    is_member = await check_membership(user_id, bot)
    if not is_member:
        await bot.send_message(
            user_id,
            f"Pour utiliser ce bot, vous devez rejoindre notre groupe et vous abonner à notre chaîne Telegram :\n"
            f"➡️ Groupe : {GROUP_ID}\n"
            f"➡️ Chaîne : {CHANNEL_ID}"
        )
    return is_member