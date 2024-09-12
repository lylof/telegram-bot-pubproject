import logging
from aiogram import types

async def handle_errors(update: types.Update, exception: Exception) -> bool:
    """
    Gère les erreurs survenant lors de l'exécution des handlers.

    Args:
        update (types.Update): L'update reçu.
        exception (Exception): L'exception levée.

    Returns:
        bool: True si l'erreur a été traitée, False sinon.
    """
    logging.error(f"Update {update} caused error {exception}")

    # Gestion des erreurs pour les messages
    if isinstance(update, types.Message):
        await update.answer("⚠️ Une erreur est survenue. Veuillez réessayer plus tard.")
        
    # Gestion des erreurs pour les requêtes de callback
    elif isinstance(update, types.CallbackQuery):
        await update.message.answer("⚠️ Une erreur s'est produite lors de la gestion de votre demande. Veuillez réessayer plus tard.")
        await update.answer()  # Fermer la boîte de dialogue de chargement
        
    # Gestion des erreurs pour les requêtes inline
    elif isinstance(update, types.InlineQuery):
        await update.answer(
            results=[],
            switch_pm_text="⚠️ Une erreur est survenue. Veuillez réessayer plus tard.",
            switch_pm_parameter="start",
            cache_time=0
        )
    
    # Ajouter plus de conditions pour d'autres types d'événements si nécessaire

    return True