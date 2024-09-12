import logging
import os
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from models import get_user_preference, toggle_user_preference, decrease_remaining_shares
from .helpers import check_channel_membership, row_to_dict, CHANNEL_ID, GROUP_ID, check_group_membership
from handlers.start import start_command

async def parametres_command(callback_query: types.CallbackQuery):
    """
    Gère la commande des paramètres de récurrence.
    Affiche les options de récurrence et parrainage à l'utilisateur.
    """
    user_id = callback_query.from_user.id
    preference = row_to_dict(get_user_preference(user_id))  # Convertir sqlite3.Row en dict
    recurrence_active = preference['recurrence_active']
    recurrence_level = preference.get('recurrence_level', 0)
    referral_count = preference.get('referral_count', 0)

    # Définir le texte et les boutons
    if recurrence_active:
        level_1_text = "Niveau 1 : Désactiver la récurrence"
        level_1_button = InlineKeyboardButton(text="⚠️ Désactiver", callback_data="toggle_recurrence")
    else:
        level_1_text = "Niveau 1 : Activer la récurrence"
        level_1_button = InlineKeyboardButton(text="🔄 Activer", callback_data="toggle_recurrence")

    if recurrence_level < 2:
        level_2_text = f"Niveau 2 : Parrainer 10 personnes ({referral_count}/10)"
        level_2_button = InlineKeyboardButton(text=level_2_text, callback_data="niveaux")
    else:
        level_2_text = "⭐ Niveau 2 activé ✅"
        level_2_button = InlineKeyboardButton(text=level_2_text, callback_data="niveaux_activé")

    # Construire le clavier
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [level_1_button],
            [level_2_button],
            [InlineKeyboardButton(text="⬅️ Retour", callback_data="retour")]
        ]
    )

    # Message de récurrence
    recurrence_message = (
        "📊 <b>Paramètres de Récurrence</b>\n\n"
        f"🔹 <b>Niveau 1 :</b> Partage des annonces automatiquement toutes les 6 heures pour une journée après validation.\n"
        f"  - <i>Avantages :</i> Partage régulier des annonces.\n"
        f"  - <i>Conditions :</i> Rejoindre notre chaîne Telegram : {CHANNEL_ID} et notre groupe : {GROUP_ID}\n\n"
        f"🔸 <b>Niveau 2 :</b> Partage des annonces toutes les 6 heures pendant une semaine.\n"
        f"  - <i>Avantages :</i> Visibilité accrue grâce à un partage prolongé.\n"
        f"  - <i>Conditions :</i> Parrainer 10 personnes qui doivent rejoindre le groupe et le canal des annonces.\n\n"
        "Pour atteindre le <b>Niveau 2</b>, parrainez 10 personnes. Voici votre lien de parrainage :\n"
        f"🔗 t.me/{(await callback_query.bot.get_me()).username}?start={callback_query.from_user.id}"
    )

    await callback_query.message.answer(recurrence_message, reply_markup=keyboard, parse_mode="HTML")

async def toggle_recurrence(callback_query: types.CallbackQuery):
    """
    Active ou désactive la récurrence pour un utilisateur après vérification de l'adhésion à la chaîne et au groupe.
    """
    user_id = callback_query.from_user.id

    # Vérifier l'adhésion à la chaîne et au groupe avant d'activer la récurrence
    if not await check_channel_membership(user_id, callback_query.bot) or not await check_group_membership(user_id, callback_query.bot):
        await callback_query.message.answer(
            f"⚠️ Vous devez rejoindre notre chaîne Telegram et notre groupe pour activer la récurrence :\n"
            f"➡️ Chaîne : {CHANNEL_ID}\n"
            f"➡️ Groupe : {GROUP_ID}"
        )
        return

    toggle_user_preference(user_id)
    new_preference = row_to_dict(get_user_preference(user_id))  # Convertir sqlite3.Row en dict
    state = "activée" if new_preference['recurrence_active'] else "désactivée"

    if state == "activée" and new_preference['recurrence_level'] == 1:
        decrease_remaining_shares(user_id, 4)  # Réinitialiser le nombre de partages restants pour Niveau 1

    await callback_query.message.answer(f"Récurrence {state} ✅")
    await parametres_command(callback_query)

    # Notifiez l'administrateur de l'activation de la récurrence
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
    if not ADMIN_USER_ID:
        logging.error("ADMIN_USER_ID is not set in the environment variables.")
        return

    try:
        ADMIN_USER_ID = int(ADMIN_USER_ID)
        if state == "activée":
            await callback_query.bot.send_message(ADMIN_USER_ID, f"L'utilisateur {user_id} a activé la récurrence.")
    except Exception as e:
        logging.error(f"Error notifying admin: {e}")

async def handle_retour(callback_query: types.CallbackQuery):
    """
    Gère le retour au menu principal.
    """
    await start_command(callback_query.message)

async def handle_niveaux(callback_query: types.CallbackQuery):
    """
    Affiche les informations sur les niveaux de récurrence et gère le parrainage.
    """
    user_id = callback_query.from_user.id
    preference = row_to_dict(get_user_preference(user_id))  # Convertir sqlite3.Row en dict
    referral_count = preference.get('referral_count', 0)
    recurrence_level = preference.get('recurrence_level', 0)

    if recurrence_level < 2:
        level_info = (
            "📊 <b>Niveaux de Récurrence</b>\n\n"
            "🔹 <b>Niveau 1 :</b> Partage des annonces automatiquement toutes les 6 heures pour une journée après validation.\n"
            "  - <i>Avantages :</i> Partage régulier des annonces.\n"
            f"  - <i>Conditions :</i> Rejoindre notre chaîne Telegram : {CHANNEL_ID} et notre groupe : {GROUP_ID}\n\n"
            "🔸 <b>Niveau 2 :</b> Partage des annonces toutes les 6 heures pendant une semaine.\n"
            "  - <i>Avantages :</i> Visibilité accrue grâce à un partage prolongé.\n"
            "  - <i>Conditions :</i> Parrainer 10 personnes qui doivent rejoindre le groupe et le canal des annonces.\n\n"
            f"⚠️ Progression actuelle : {referral_count}/10\n\n"
            "Pour atteindre le <b>Niveau 2</b>, parrainez 10 personnes. Voici votre lien de parrainage :\n"
            f"🔗 t.me/{(await callback_query.bot.get_me()).username}?start={callback_query.from_user.id}"
        )
        await callback_query.message.answer(level_info, parse_mode="HTML")

    # Notifiez l'utilisateur de l'activation automatique du Niveau 2
    if referral_count >= 10 and recurrence_level < 2:
        # Mettre à jour le niveau de récurrence
        toggle_user_preference(user_id)  # Active le Niveau 2
        await callback_query.message.answer("🎉 Félicitations ! Vous avez atteint le Niveau 2 de récurrence.")

    # Option pour l'utilisateur de revenir aux paramètres
    await parametres_command(callback_query)