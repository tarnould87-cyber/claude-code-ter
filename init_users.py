"""
Script d'initialisation des utilisateurs.
Lancer UNE SEULE FOIS après le premier démarrage, puis supprimer ou sécuriser ce fichier.

Usage : python init_users.py
"""
from app import get_db, init_db
from werkzeug.security import generate_password_hash

USERS = [
    # (identifiant, mot_de_passe)  <- CHANGEZ les mots de passe avant usage
    ('admin',  'Admin123!'),
    ('user1',  'User1pass!'),
    ('user2',  'User2pass!'),
    ('user3',  'User3pass!'),
]


def create_user(username: str, password: str) -> None:
    with get_db() as conn:
        existing = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()
        if existing:
            print(f"[SKIP] '{username}' existe déjà.")
            return
        conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, generate_password_hash(password))
        )
        print(f"[OK]   '{username}' créé.")


if __name__ == '__main__':
    init_db()
    for uname, pwd in USERS:
        create_user(uname, pwd)
    print("\nTerminé. Modifiez les mots de passe depuis l'interface ou relancez ce script.")
