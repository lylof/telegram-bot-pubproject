import sqlite3
import os
import logging

def create_connection():
    """
    Crée et retourne une connexion à la base de données.
    La base de données SQLite est située dans le même répertoire que ce script.

    Returns:
        sqlite3.Connection: Connexion à la base de données.
    """
    try:
        path = os.path.join(os.path.dirname(__file__), 'annonces.db')
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        return connection
    except sqlite3.Error as e:
        logging.error(f"Error creating database connection: {e}")
        raise

def init_db():
    """
    Initialise la base de données en créant les tables si elles n'existent pas déjà.
    Ajoute les colonnes manquantes si nécessaire.
    """
    connection = create_connection()
    cursor = connection.cursor()
    
    try:
        # Créer la table des annonces si elle n'existe pas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annonces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                hashtags TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                lien TEXT NOT NULL,
                scheduled_time1 TIMESTAMP,
                scheduled_time2 TIMESTAMP,
                scheduled_time3 TIMESTAMP,
                scheduled_time4 TIMESTAMP
            )
        ''')

        # Créer la table des préférences utilisateurs si elle n'existe pas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                user_id INTEGER PRIMARY KEY,
                recurrence_active BOOLEAN DEFAULT 1,
                referral_count INTEGER DEFAULT 0,
                recurrence_level INTEGER DEFAULT 0,
                remaining_shares INTEGER DEFAULT 4
            )
        ''')

        # Ajouter la colonne 'remaining_shares' si elle n'existe pas
        cursor.execute('PRAGMA table_info(preferences)')
        columns = [column[1] for column in cursor.fetchall()]
        if 'remaining_shares' not in columns:
            cursor.execute('ALTER TABLE preferences ADD COLUMN remaining_shares INTEGER DEFAULT 4')

        connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
        raise
    finally:
        connection.close()

def get_db_connection():
    """
    Retourne une connexion à la base de données.

    Returns:
        sqlite3.Connection: Connexion à la base de données.
    """
    return create_connection()

if __name__ == "__main__":
    init_db()