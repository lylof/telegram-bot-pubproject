from aiogram import Bot
import logging
import os  # Import os to load environment variables
from aiogram import types
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from models import (
    create_annonce,
    get_pending_annonces,
    update_annonce_status,
    get_annonce_by_id,
    get_user_preference,
    decrease_remaining_shares,
    toggle_user_preference
)
from .helpers import escape_html, is_private_chat, row_to_dict, enforce_membership
from database import get_db_connection  # Import necessary function
import datetime
import asyncio  # Ensure asyncio is imported

# Charger les variables d'environnement
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

class AnnonceForm(StatesGroup):
    title = State()
    description = State()
    lien = State()
    hashtags = State()
    confirmation = State()

async def soumettre_annonce_command(message: types.Message, state: FSMContext):
    """
    Gère la commande /soumettre.
    Demande à l'utilisateur de commencer par fournir le titre de l'annonce.
    """
    if not await is_private_chat(message):
        return

    # Vérifie l'adhésion au groupe et à la chaîne
    if not await enforce_membership(message.from_user.id, message.bot):
        return

    await state.set_state(AnnonceForm.title)
    await message.answer("Quel est le nom de votre groupe, chaîne ou bot ? (ex: Vêtements de Qualité)")

async def set_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AnnonceForm.description)
    await message.answer("Veuillez fournir une description détaillée de votre annonce. (ex: Nous vendons des vêtements de qualité à des prix abordables.)")

async def set_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AnnonceForm.lien)
    await message.answer("Veuillez fournir le lien Telegram vers votre groupe, canal ou bot. (ex: https://t.me/vetements_qualite)")

async def set_lien(message: types.Message, state: FSMContext):
    link = message.text
    if not link.startswith("https://t.me/"):
        await message.answer("Veuillez fournir un lien Telegram valide. Essayez encore.")
        return
    await state.update_data(lien=link)
    await state.set_state(AnnonceForm.hashtags)
    await message.answer(
        "Ajoutez des hashtags pertinents (jusqu'à trois, séparés par des espaces). "
        "Ne mettez pas de '#' au début des hashtags, le bot s'en charge automatiquement.\n"
        "ex: vetements mode accessoires")

async def set_hashtags(message: types.Message, state: FSMContext):
    hashtags = message.text.split()
    if len(hashtags) > 3:
        await message.answer("Vous pouvez ajouter jusqu'à trois hashtags. Essayez encore.")
        return
    await state.update_data(hashtags=" ".join(hashtags))
    data = await state.get_data()

    title = escape_html(data['title'])
    description = escape_html(data['description'])
    lien = escape_html(data['lien'])
    formatted_hashtags = " ".join([f"#{escape_html(ht)}" for ht in hashtags])

    preview_message = (
        f"📝 <b>Annonce :</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"{description}\n\n"
        f"{lien}\n\n"
        f"{formatted_hashtags}"
    )

    try:
        await message.answer(
            preview_message,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Valider", callback_data="valider"),
                    InlineKeyboardButton(text="❌ Rejeter", callback_data="rejeter")
                ]
            ]),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer("⚠️ Une erreur s'est produite lors de la prévisualisation de l'annonce. Veuillez vérifier vos entrées.")
        logging.error(f"Error while sending preview message: {e}")
        return

    await state.set_state(AnnonceForm.confirmation)

async def confirm_annonce(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    title = escape_html(data['title'])
    description = escape_html(data['description'])
    lien = escape_html(data['lien'])
    formatted_hashtags = data['hashtags'].replace(' ', ' #')
    user_id = callback_query.from_user.id
    preference = row_to_dict(get_user_preference(user_id))
    recurrence_active = preference['recurrence_active']
    recurrence_level = preference.get('recurrence_level', 0)

    if callback_query.data == "valider":
        now = datetime.datetime.now()
        if recurrence_level == 2:
            annonce_id = create_annonce(
                user_id=user_id,
                username=callback_query.from_user.username,
                title=data['title'],
                description=data['description'],
                hashtags=data['hashtags'],
                lien=data['lien'],
                scheduled_time1=now + datetime.timedelta(minutes=15),
                scheduled_time2=now + datetime.timedelta(hours=6),
                scheduled_time3=now + datetime.timedelta(hours=12),
                scheduled_time4=now + datetime.timedelta(hours=18)
            )
            # Planifier les partages pour toute la semaine
            for day in range(1, 7):
                create_annonce(
                    user_id=user_id,
                    username=callback_query.from_user.username,
                    title=data['title'],
                    description=data['description'],
                    hashtags=data['hashtags'],
                    lien=data['lien'],
                    scheduled_time1=now + datetime.timedelta(days=day, minutes=15),
                    scheduled_time2=now + datetime.timedelta(days=day, hours=6),
                    scheduled_time3=now + datetime.timedelta(days=day, hours=12),
                    scheduled_time4=now + datetime.timedelta(days=day, hours=18)
                )
        elif recurrence_active:
            annonce_id = create_annonce(
                user_id=user_id,
                username=callback_query.from_user.username,
                title=data['title'],
                description=data['description'],
                hashtags=data['hashtags'],
                lien=data['lien'],
                scheduled_time1=now + datetime.timedelta(minutes=15),
                scheduled_time2=now + datetime.timedelta(hours=6),
                scheduled_time3=now + datetime.timedelta(hours=12),
                scheduled_time4=now + datetime.timedelta(hours=18)
            )
        else:
            annonce_id = create_annonce(
                user_id=user_id,
                username=callback_query.from_user.username,
                title=data['title'],
                description=data['description'],
                hashtags=data['hashtags'],
                lien=data['lien'],
                scheduled_time1=now + datetime.timedelta(minutes=15),
                scheduled_time2=None,
                scheduled_time3=None,
                scheduled_time4=None
            )
        await callback_query.message.answer("✅ Votre annonce a été soumise pour approbation.")

        # Notify admin
        try:
            await callback_query.bot.send_message(
                ADMIN_USER_ID,
                f"Nouvelle annonce à approuver :\n\n"
                f"<b>{title}</b>\n\n"
                f"{description}\n\n"
                f"{lien}\n\n"
                f"#{formatted_hashtags}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Approuver", callback_data=f"approuver_{annonce_id}"),
                        InlineKeyboardButton(text="❌ Rejeter", callback_data=f"rejeter_{annonce_id}")
                    ]
                ])
            )
        except Exception as e:
            logging.error(f"Error while notifying admin: {e}")
    elif callback_query.data == "rejeter":
        await callback_query.message.answer("❌ La soumission de l'annonce a été annulée.")
    await state.clear()

async def lister_annonces_command(message: types.Message):
    if not await is_private_chat(message):
        return

    # Vérifie l'adhésion au groupe et à la chaîne
    if not await enforce_membership(message.from_user.id, message.bot):
        return

    annonces = get_pending_annonces()
    if annonces:
        for annonce in annonces:
            try:
                await message.answer(
                    f"Titre: <b>{escape_html(annonce['title'])}</b>\n"
                    f"Description: {escape_html(annonce['description'])}\n"
                    f"Lien: {escape_html(annonce['lien'])}\n"
                    f"Hashtags: #{escape_html(annonce['hashtags']).replace(' ', ' #')}",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ Approuver", callback_data=f"approuver_{annonce['id']}"),
                            InlineKeyboardButton(text="❌ Rejeter", callback_data=f"rejeter_{annonce['id']}")
                        ]
                    ]),
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Error while listing annonces: {e}")
    else:
        await message.answer("Aucune annonce en attente.")

async def gestion_annonce(callback_query: types.CallbackQuery):
    user = callback_query.from_user
    if user.id != ADMIN_USER_ID:
        await callback_query.answer("Vous n'avez pas la permission de faire cela.")
        return

    try:
        action, annonce_id = callback_query.data.split('_')
        annonce = get_annonce_by_id(annonce_id)

        if not annonce:
            await callback_query.answer("Annonce non trouvée.")
            return

        if action == "approuver":
            update_annonce_status(annonce_id, "approved")
            await callback_query.message.answer("Annonce approuvée. ✅")
            try:
                await callback_query.bot.send_message(annonce['user_id'], "Votre annonce a été approuvée et sera partagée automatiquement. 🎉")
            except Exception as e:
                logging.error(f"Failed to notify user: {e}")
        elif action == "rejeter":
            update_annonce_status(annonce_id, "rejected")
            await callback_query.message.answer("Annonce rejetée. ❌")
            try:
                await callback_query.bot.send_message(annonce['user_id'], "Votre annonce a été rejetée. 😞")
            except Exception as e:
                logging.error(f"Failed to notify user: {e}")
    except Exception as e:
        logging.error(f"Error processing announcement: {e}")

async def handle_soumettre(callback_query: types.CallbackQuery, state: FSMContext):
    await soumettre_annonce_command(callback_query.message, state)

async def handle_lister_annonces(callback_query: types.CallbackQuery):
    await lister_annonces_command(callback_query.message)

async def handle_aide(callback_query: types.CallbackQuery):
    await aide_command(callback_query.message)

async def share_approved_annonces(bot: Bot, group_id: str):
    """
    Tâche périodique pour partager les annonces approuvées.
    Réduit le compteur de partages restants pour les utilisateurs de Niveau 1.
    """
    while True:
        now = datetime.datetime.now()
        logging.info(f"Checking for announcements to share at {now}")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM annonces 
            WHERE status = "approved" 
            AND (
                scheduled_time1 <= ? OR
                scheduled_time2 <= ? OR
                scheduled_time3 <= ? OR
                scheduled_time4 <= ?
            )
        ''', (now, now, now, now))
        
        annonces = cursor.fetchall()

        for annonce in annonces:
            for i in range(1, 5):
                scheduled_time = annonce[f'scheduled_time{i}']
                if scheduled_time:
                    scheduled_time = datetime.datetime.fromisoformat(scheduled_time)
                    if scheduled_time <= now:
                        try:
                            logging.info(f"Sharing announcement {annonce['id']} (scheduled time {i})")
                            await bot.send_message(
                                group_id,
                                f"<b>{escape_html(annonce['title'])}</b>\n\n"
                                f"{escape_html(annonce['description'])}\n\n"
                                f"{escape_html(annonce['lien'])}\n\n"
                                f"#{escape_html(annonce['hashtags']).replace(' ', ' #')}",
                                parse_mode="HTML",
                                disable_web_page_preview=False
                            )
                            cursor.execute(f'UPDATE annonces SET scheduled_time{i} = NULL WHERE id = ?', (annonce['id'],))
                            conn.commit()

                            # Décrémenter le nombre de partages restants
                            user_preference = row_to_dict(get_user_preference(annonce['user_id']))
                            if user_preference["recurrence_level"] == 1:
                                remaining_shares = user_preference["remaining_shares"] - 1
                                if remaining_shares <= 0:
                                    toggle_user_preference(annonce['user_id'])  # Désactiver la récurrence
                                    remaining_shares = 4  # Réinitialiser pour la prochaine activation
                                    await bot.send_message(
                                        annonce['user_id'],
                                        "⚠️ Votre récurrence Niveau 1 a été désactivée après 4 partages."
                                    )
                                decrease_remaining_shares(annonce['user_id'], remaining_shares)
                        except Exception as e:
                            logging.error(f"Failed to share annonce {annonce['id']} (scheduled time {i}): {e}")

        conn.close()
        await asyncio.sleep(60)  # Vérification toutes les minutes
