import logging
from database import get_db_connection

def create_annonce(user_id, username, title, description, hashtags, lien, scheduled_time1, scheduled_time2, scheduled_time3, scheduled_time4):
    """
    Crée une nouvelle annonce dans la base de données.

    Args:
        user_id (int): ID de l'utilisateur.
        username (str): Nom d'utilisateur de Telegram.
        title (str): Titre de l'annonce.
        description (str): Description de l'annonce.
        hashtags (str): Hashtags de l'annonce.
        lien (str): Lien de l'annonce.
        scheduled_time1 (datetime): Heure de la première publication.
        scheduled_time2 (datetime): Heure de la deuxième publication.
        scheduled_time3 (datetime): Heure de la troisième publication.
        scheduled_time4 (datetime): Heure de la quatrième publication.

    Returns:
        int: ID de l'annonce créée.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO annonces (user_id, username, title, description, hashtags, lien, scheduled_time1, scheduled_time2, scheduled_time3, scheduled_time4)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, title, description, hashtags, lien, scheduled_time1, scheduled_time2, scheduled_time3, scheduled_time4))
        annonce_id = c.lastrowid
        conn.commit()
        return annonce_id
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to create annonce: {e}")
        raise e
    finally:
        conn.close()

def get_pending_annonces():
    """
    Récupère toutes les annonces en attente d'approbation.

    Returns:
        list: Liste des annonces en attente.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM annonces WHERE status = "pending"')
        annonces = c.fetchall()
        return annonces
    except Exception as e:
        logging.error(f"Failed to get pending annonces: {e}")
        raise e
    finally:
        conn.close()

def update_annonce_status(annonce_id, status):
    """
    Met à jour le statut d'une annonce dans la base de données.

    Args:
        annonce_id (int): ID de l'annonce.
        status (str): Nouveau statut de l'annonce.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('UPDATE annonces SET status = ? WHERE id = ?', (status, annonce_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to update annonce status: {e}")
        raise e
    finally:
        conn.close()

def get_annonce_by_id(annonce_id):
    """
    Récupère une annonce par son ID.

    Args:
        annonce_id (int): ID de l'annonce.

    Returns:
        sqlite3.Row: Annonce correspondante.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM annonces WHERE id = ?', (annonce_id,))
        annonce = c.fetchone()
        return annonce
    except Exception as e:
        logging.error(f"Failed to get annonce by ID: {e}")
        raise e
    finally:
        conn.close()

def get_user_preference(user_id):
    """
    Récupère la préférence de récurrence de l'utilisateur.

    Args:
        user_id (int): ID de l'utilisateur.

    Returns:
        dict: Préférence de l'utilisateur.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT recurrence_active, recurrence_level, referral_count, remaining_shares FROM preferences WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        return result if result else {'recurrence_active': True, 'recurrence_level': 0, 'referral_count': 0, 'remaining_shares': 4}
    except Exception as e:
        logging.error(f"Failed to get user preference: {e}")
        raise e
    finally:
        conn.close()

def toggle_user_preference(user_id):
    """
    Active ou désactive la récurrence pour un utilisateur.

    Args:
        user_id (int): ID de l'utilisateur.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT recurrence_active FROM preferences WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        if result:
            new_value = not result['recurrence_active']
            c.execute('UPDATE preferences SET recurrence_active = ?, remaining_shares = 4 WHERE user_id = ?', (new_value, user_id))
        else:
            c.execute('INSERT INTO preferences (user_id, recurrence_active, remaining_shares) VALUES (?, ?, ?)', (user_id, True, 4))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to toggle user preference: {e}")
        raise e
    finally:
        conn.close()

def update_referral_count(user_id, count):
    """
    Met à jour le nombre de parrainages de l'utilisateur.

    Args:
        user_id (int): ID de l'utilisateur.
        count (int): Nombre de parrainages à ajouter.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('UPDATE preferences SET referral_count = referral_count + ? WHERE user_id = ?', (count, user_id))
        c.execute('SELECT referral_count FROM preferences WHERE user_id = ?', (user_id,))
        referral_count = c.fetchone()['referral_count']
        if referral_count >= 10:
            c.execute('UPDATE preferences SET recurrence_level = 2 WHERE user_id = ?', (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to update referral count: {e}")
        raise e
    finally:
        conn.close()

def increase_referral_count(user_id):
    """
    Augmente le nombre de parrainages de l'utilisateur et active le Niveau 2 si le seuil est atteint.

    Args:
        user_id (int): ID de l'utilisateur.

    Returns:
        int: Nombre total de parrainages après l'incrémentation.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('UPDATE preferences SET referral_count = referral_count + 1 WHERE user_id = ?', (user_id,))
        c.execute('SELECT referral_count FROM preferences WHERE user_id = ?', (user_id,))
        referral_count = c.fetchone()['referral_count']
        if referral_count >= 10:
            c.execute('UPDATE preferences SET recurrence_level = 2 WHERE user_id = ?', (user_id,))
        conn.commit()
        return referral_count
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to increase referral count: {e}")
        raise e
    finally:
        conn.close()

def decrease_remaining_shares(user_id, remaining_shares):
    """
    Décrémente le nombre de partages restants pour un utilisateur.

    Args:
        user_id (int): ID de l'utilisateur.
        remaining_shares (int): Nombre de partages restants.
    """
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('UPDATE preferences SET remaining_shares = ? WHERE user_id = ?', (remaining_shares, user_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to update remaining shares: {e}")
        raise e
    finally:
        conn.close()