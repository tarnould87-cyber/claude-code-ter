import json
import os
import sqlite3
from functools import wraps
from math import ceil
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ter-dev-key-changez-moi-en-production')

DATABASE = os.path.join(os.path.dirname(__file__), 'ter.db')
MARGE    = 1.35
PER_PAGE = 20


# ===========================================================================
# Database
# ===========================================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS matieres_lib (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                designation TEXT NOT NULL,
                prix_kg     REAL NOT NULL,
                actif       INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS postes_lib (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                code         TEXT UNIQUE NOT NULL,
                designation  TEXT NOT NULL,
                taux_horaire REAL NOT NULL,
                actif        INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS chiffrages (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                ref_piece           TEXT NOT NULL,
                ref_client          TEXT DEFAULT '',
                code_affaire        TEXT DEFAULT '',
                quantite            INTEGER DEFAULT 1,
                notes               TEXT DEFAULT '',
                operateur           TEXT NOT NULL,
                statut              TEXT DEFAULT 'brouillon',
                matiere_id          INTEGER,
                matiere_designation TEXT DEFAULT '',
                matiere_masse_brute REAL DEFAULT 0,
                matiere_prix_kg     REAL DEFAULT 0,
                cout_matiere        REAL DEFAULT 0,
                cout_mo             REAL DEFAULT 0,
                cout_revient        REAL DEFAULT 0,
                prix_vente          REAL DEFAULT 0,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (matiere_id) REFERENCES matieres_lib(id)
            );

            CREATE TABLE IF NOT EXISTS lignes_op (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                chiffrage_id      INTEGER NOT NULL,
                ordre             INTEGER DEFAULT 0,
                poste_code        TEXT NOT NULL,
                poste_designation TEXT NOT NULL,
                temps_h           REAL DEFAULT 0,
                taux_horaire      REAL DEFAULT 0,
                cout_ligne        REAL DEFAULT 0,
                FOREIGN KEY (chiffrage_id) REFERENCES chiffrages(id) ON DELETE CASCADE
            );
        ''')


def seed_libraries(conn):
    """Insert default postes and matieres if tables are empty."""
    if conn.execute('SELECT COUNT(*) FROM postes_lib').fetchone()[0] == 0:
        conn.executemany(
            'INSERT INTO postes_lib (code, designation, taux_horaire) VALUES (?,?,?)',
            [
                ('Z1',  'Etude',           55.0),
                ('Z5',  'Réglages',        65.0),
                ('Z10', 'Tour CN',         65.0),
                ('Z20', 'Fraisage CN',     65.0),
                ('Z30', 'Rectification',   70.0),
                ('Z40', 'Débit scie',      45.0),
                ('Z45', 'Ebavurage',       50.0),
                ('Z50', 'Soudure TIG/MIG', 60.0),
                ('Z60', 'Tôlerie/Pliage',  55.0),
                ('Z70', 'Plasma CN',       55.0),
                ('Z80', 'Contrôle',        50.0),
            ]
        )
    if conn.execute('SELECT COUNT(*) FROM matieres_lib').fetchone()[0] == 0:
        conn.executemany(
            'INSERT INTO matieres_lib (designation, prix_kg) VALUES (?,?)',
            [
                ('Acier S235',    1.20),
                ('Acier traité',  2.50),
                ('Inox 304',      4.50),
                ('Alu 2017',      3.80),
                ('Cuivre/Laiton', 8.00),
            ]
        )


def safe_float(v, default=0.0):
    try:
        return float(str(v).replace(',', '.'))
    except (ValueError, TypeError):
        return default


def safe_int(v, default=1):
    try:
        return max(1, int(v))
    except (ValueError, TypeError):
        return default


# ===========================================================================
# Auth
# ===========================================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            error = 'Veuillez remplir tous les champs.'
        else:
            with get_db() as conn:
                user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            if user and check_password_hash(user['password_hash'], password):
                session.permanent = False
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('dashboard'))
            error = 'Identifiant ou mot de passe incorrect.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ===========================================================================
# Dashboard
# ===========================================================================

@app.route('/')
@login_required
def dashboard():
    with get_db() as conn:
        stats = dict(
            total     = conn.execute("SELECT COUNT(*) FROM chiffrages").fetchone()[0],
            brouillon = conn.execute("SELECT COUNT(*) FROM chiffrages WHERE statut='brouillon'").fetchone()[0],
            valide    = conn.execute("SELECT COUNT(*) FROM chiffrages WHERE statut='valide'").fetchone()[0],
        )
    return render_template('dashboard.html', username=session.get('username'), stats=stats)


# ===========================================================================
# Chiffrages – list
# ===========================================================================

@app.route('/chiffrages')
@login_required
def chiffrages_liste():
    page          = max(1, request.args.get('page', 1, type=int))
    q             = request.args.get('q', '').strip()
    statut_filtre = request.args.get('statut', '')

    clauses, params = [], []
    if q:
        clauses.append("(ref_piece LIKE ? OR ref_client LIKE ? OR code_affaire LIKE ?)")
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    if statut_filtre:
        clauses.append('statut=?')
        params.append(statut_filtre)

    where = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''

    with get_db() as conn:
        total = conn.execute(
            f'SELECT COUNT(*) FROM chiffrages {where}', params
        ).fetchone()[0]
        chiffrages = conn.execute(
            f'SELECT * FROM chiffrages {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?',
            params + [PER_PAGE, (page - 1) * PER_PAGE]
        ).fetchall()

    pages = max(1, ceil(total / PER_PAGE))
    return render_template('chiffrages/liste.html',
        username=session.get('username'),
        chiffrages=chiffrages, page=page, pages=pages,
        total=total, q=q, statut_filtre=statut_filtre,
    )


# ===========================================================================
# Chiffrages – create / edit helpers
# ===========================================================================

def _get_libs(conn):
    postes   = [dict(r) for r in conn.execute('SELECT * FROM postes_lib  WHERE actif=1 ORDER BY code')]
    matieres = [dict(r) for r in conn.execute('SELECT * FROM matieres_lib WHERE actif=1 ORDER BY designation')]
    return postes, matieres


def _save(conn, chiffrage_id=None):
    """Parse form, recalculate costs server-side, persist. Returns (id, error_msg)."""
    ref_piece = request.form.get('ref_piece', '').strip()
    if not ref_piece:
        return None, 'La référence pièce est obligatoire.'

    ref_client   = request.form.get('ref_client', '').strip()
    code_affaire = request.form.get('code_affaire', '').strip()
    quantite     = safe_int(request.form.get('quantite', 1))
    notes        = request.form.get('notes', '').strip()
    statut       = request.form.get('action', 'brouillon')
    if statut not in ('brouillon', 'valide'):
        statut = 'brouillon'

    mat_id    = request.form.get('matiere_id') or None
    if mat_id:
        mat_id = int(mat_id)
    masse     = safe_float(request.form.get('matiere_masse_brute', 0))
    prix_kg   = safe_float(request.form.get('matiere_prix_kg', 0))
    mat_desig = request.form.get('matiere_designation', '').strip()
    c_mat     = round(masse * prix_kg * quantite, 4)

    postes_map = {r['code']: dict(r) for r in conn.execute('SELECT * FROM postes_lib WHERE actif=1')}

    row_ids = [r for r in request.form.get('row_ids', '').split(',') if r.strip()]
    lignes  = []
    for i, rid in enumerate(row_ids):
        code  = request.form.get(f'{rid}_code', '').strip()
        temps = safe_float(request.form.get(f'{rid}_temps', 0))
        taux  = safe_float(request.form.get(f'{rid}_taux', 0))
        if not code or temps <= 0:
            continue
        p = postes_map.get(code, {})
        if not taux:
            taux = p.get('taux_horaire', 0)
        lignes.append(dict(
            ordre=i, poste_code=code,
            poste_designation=p.get('designation', code),
            temps_h=temps, taux_horaire=taux,
            cout_ligne=round(temps * taux, 4),
        ))

    if statut == 'valide' and not lignes:
        return None, 'Ajoutez au moins une opération avant de valider.'

    c_mo      = round(sum(l['cout_ligne'] for l in lignes) * quantite, 4)
    c_revient = round(c_mat + c_mo, 4)
    p_vente   = round(c_revient * MARGE, 4)

    vals = (ref_piece, ref_client, code_affaire, quantite, notes, statut,
            mat_id, mat_desig, masse, prix_kg, c_mat, c_mo, c_revient, p_vente)

    if chiffrage_id is None:
        cur = conn.execute('''
            INSERT INTO chiffrages
              (ref_piece,ref_client,code_affaire,quantite,notes,statut,
               matiere_id,matiere_designation,matiere_masse_brute,matiere_prix_kg,
               cout_matiere,cout_mo,cout_revient,prix_vente,operateur)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', vals + (session['username'],))
        chiffrage_id = cur.lastrowid
    else:
        conn.execute('''
            UPDATE chiffrages SET
              ref_piece=?,ref_client=?,code_affaire=?,quantite=?,notes=?,statut=?,
              matiere_id=?,matiere_designation=?,matiere_masse_brute=?,matiere_prix_kg=?,
              cout_matiere=?,cout_mo=?,cout_revient=?,prix_vente=?,
              updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', vals + (chiffrage_id,))
        conn.execute('DELETE FROM lignes_op WHERE chiffrage_id=?', (chiffrage_id,))

    if lignes:
        conn.executemany('''
            INSERT INTO lignes_op
              (chiffrage_id,ordre,poste_code,poste_designation,temps_h,taux_horaire,cout_ligne)
            VALUES (?,?,?,?,?,?,?)
        ''', [(chiffrage_id, l['ordre'], l['poste_code'], l['poste_designation'],
               l['temps_h'], l['taux_horaire'], l['cout_ligne']) for l in lignes])

    return chiffrage_id, None


# ===========================================================================
# Chiffrages – routes
# ===========================================================================

@app.route('/chiffrages/nouveau', methods=['GET', 'POST'])
@login_required
def chiffrage_nouveau():
    with get_db() as conn:
        postes, matieres = _get_libs(conn)
        if request.method == 'POST':
            chiffrage_id, err = _save(conn)
            if err:
                flash(err, 'error')
            else:
                flash('Chiffrage enregistré.', 'success')
                return redirect(url_for('chiffrage_detail', chiffrage_id=chiffrage_id))

    return render_template('chiffrages/form.html',
        username=session.get('username'),
        chiffrage=None, lignes_json='[]',
        postes=postes, matieres=matieres,
        postes_json=json.dumps(postes, ensure_ascii=False),
        matieres_json=json.dumps(matieres, ensure_ascii=False),
        mode='create',
    )


@app.route('/chiffrages/<int:chiffrage_id>/modifier', methods=['GET', 'POST'])
@login_required
def chiffrage_modifier(chiffrage_id):
    with get_db() as conn:
        c = conn.execute('SELECT * FROM chiffrages WHERE id=?', (chiffrage_id,)).fetchone()
        if not c:
            flash('Chiffrage introuvable.', 'error')
            return redirect(url_for('chiffrages_liste'))

        postes, matieres = _get_libs(conn)

        if request.method == 'POST':
            _, err = _save(conn, chiffrage_id=chiffrage_id)
            if err:
                flash(err, 'error')
            else:
                flash('Chiffrage mis à jour.', 'success')
                return redirect(url_for('chiffrage_detail', chiffrage_id=chiffrage_id))
            c = conn.execute('SELECT * FROM chiffrages WHERE id=?', (chiffrage_id,)).fetchone()

        lignes = [dict(r) for r in conn.execute(
            'SELECT * FROM lignes_op WHERE chiffrage_id=? ORDER BY ordre', (chiffrage_id,)
        )]

    return render_template('chiffrages/form.html',
        username=session.get('username'),
        chiffrage=c, lignes_json=json.dumps(lignes, ensure_ascii=False),
        postes=postes, matieres=matieres,
        postes_json=json.dumps(postes, ensure_ascii=False),
        matieres_json=json.dumps(matieres, ensure_ascii=False),
        mode='edit',
    )


@app.route('/chiffrages/<int:chiffrage_id>')
@login_required
def chiffrage_detail(chiffrage_id):
    with get_db() as conn:
        c = conn.execute('SELECT * FROM chiffrages WHERE id=?', (chiffrage_id,)).fetchone()
        if not c:
            flash('Chiffrage introuvable.', 'error')
            return redirect(url_for('chiffrages_liste'))
        lignes = conn.execute(
            'SELECT * FROM lignes_op WHERE chiffrage_id=? ORDER BY ordre', (chiffrage_id,)
        ).fetchall()
    return render_template('chiffrages/detail.html',
        username=session.get('username'), chiffrage=c, lignes=lignes)


@app.route('/chiffrages/<int:chiffrage_id>/dupliquer', methods=['POST'])
@login_required
def chiffrage_dupliquer(chiffrage_id):
    with get_db() as conn:
        src = conn.execute('SELECT * FROM chiffrages WHERE id=?', (chiffrage_id,)).fetchone()
        if not src:
            flash('Chiffrage introuvable.', 'error')
            return redirect(url_for('chiffrages_liste'))

        cur = conn.execute('''
            INSERT INTO chiffrages
              (ref_piece,ref_client,code_affaire,quantite,notes,operateur,statut,
               matiere_id,matiere_designation,matiere_masse_brute,matiere_prix_kg,
               cout_matiere,cout_mo,cout_revient,prix_vente)
            VALUES (?,?,?,?,?,'brouillon',?,?,?,?,?,?,?,?,?)
        ''', (f"{src['ref_piece']} (copie)", src['ref_client'], src['code_affaire'],
              src['quantite'], src['notes'],
              session['username'],
              src['matiere_id'], src['matiere_designation'],
              src['matiere_masse_brute'], src['matiere_prix_kg'],
              src['cout_matiere'], src['cout_mo'], src['cout_revient'], src['prix_vente']))
        new_id = cur.lastrowid

        for l in conn.execute(
            'SELECT * FROM lignes_op WHERE chiffrage_id=? ORDER BY ordre', (chiffrage_id,)
        ):
            conn.execute('''
                INSERT INTO lignes_op
                  (chiffrage_id,ordre,poste_code,poste_designation,temps_h,taux_horaire,cout_ligne)
                VALUES (?,?,?,?,?,?,?)
            ''', (new_id, l['ordre'], l['poste_code'], l['poste_designation'],
                  l['temps_h'], l['taux_horaire'], l['cout_ligne']))

    flash('Chiffrage dupliqué avec succès.', 'success')
    return redirect(url_for('chiffrage_modifier', chiffrage_id=new_id))


@app.route('/chiffrages/<int:chiffrage_id>/archiver', methods=['POST'])
@login_required
def chiffrage_archiver(chiffrage_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE chiffrages SET statut='archive',updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (chiffrage_id,)
        )
    flash('Chiffrage archivé.', 'success')
    return redirect(url_for('chiffrages_liste'))


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == '__main__':
    init_db()
    with get_db() as conn:
        seed_libraries(conn)
    app.run(host='0.0.0.0', port=5000, debug=False)
