# bank_b.py
import psycopg2
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import hashlib
from functools import wraps
from logger import get_logger, log_event

app = Flask(__name__)
app.secret_key = 'anothersecretkey'
CORS(app, supports_credentials=True)

DB_CONFIG = {
    'dbname': 'bank_b',
    'user': 'postgres',
    'password': 'Hao@DBMS2026',
    'host': 'localhost',
    'port': 15432
}

logger = get_logger('bank_b')

# --- Helpers ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def get_db_connection():
    """Connect to bank_b, creating the database if it doesn't exist."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        if 'does not exist' in str(e):
            default_cfg = DB_CONFIG.copy()
            default_cfg['dbname'] = 'postgres'
            conn = psycopg2.connect(**default_cfg)
            conn.autocommit = True
            c = conn.cursor()
            c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['dbname'],))
            if not c.fetchone():
                c.execute(f"CREATE DATABASE {DB_CONFIG['dbname']}")
            c.close()
            conn.close()
            return psycopg2.connect(**DB_CONFIG)
        raise

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            account_number TEXT PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            balance NUMERIC(18,2) NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'USD'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            account_number TEXT NOT NULL,
            type TEXT NOT NULL,
            amount NUMERIC(18,2) NOT NULL,
            counterpart TEXT,
            status TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_txns (
            txn_id TEXT PRIMARY KEY,
            source_account TEXT,
            dest_account TEXT,
            amount NUMERIC(18,2) NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    ''')

    # Seed
    c.execute("SELECT COUNT(*) FROM customers")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO customers (username, password, full_name, email, phone) VALUES (%s, %s, %s, %s, %s)",
            ('charlie', hash_password('charlie123'), 'Charlie Le', 'charlie@example.com', '0912345678')
        )
        c.execute(
            "INSERT INTO customers (username, password, full_name, email, phone) VALUES (%s, %s, %s, %s, %s)",
            ('dave', hash_password('dave123'), 'Dave Pham', 'dave@example.com', '0987123456')
        )
        c.execute("SELECT id FROM customers WHERE username = %s", ('charlie',))
        charlie_id = c.fetchone()[0]
        c.execute("SELECT id FROM customers WHERE username = %s", ('dave',))
        dave_id = c.fetchone()[0]
        c.execute(
            "INSERT INTO accounts (account_number, customer_id, balance, currency) VALUES (%s, %s, %s, %s)",
            ('B1001', charlie_id, 1000, 'USD')
        )
        c.execute(
            "INSERT INTO accounts (account_number, customer_id, balance, currency) VALUES (%s, %s, %s, %s)",
            ('B1002', dave_id, 1000, 'USD')
        )

    conn.commit()
    conn.close()


# --- Auth ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password, full_name FROM customers WHERE username = %s", (username,))
    row = c.fetchone()
    conn.close()

    if row and row[1] == hash_password(password):
        session['user_id'] = row[0]
        conn2 = get_db_connection()
        c2 = conn2.cursor()
        c2.execute("SELECT account_number, balance, currency FROM accounts WHERE customer_id = %s", (row[0],))
        accounts = []
        for r in c2.fetchall():
            accounts.append({
                "account_number": r[0],
                "balance": float(r[1]),
                "currency": r[2]
            })
        conn2.close()
        return jsonify({
            "status": "success",
            "message": "Logged in",
            "user_id": row[0],
            "full_name": row[2],
            "accounts": accounts
        })

    return jsonify({"error": "Invalid credentials"}), 401


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"})


# --- Registration ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')
    account_number = data.get('account_number')
    initial_balance = data.get('initial_balance', 0)

    if not username or not password or not account_number:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT 1 FROM customers WHERE username = %s", (username,))
        if c.fetchone():
            return jsonify({"error": "Username already exists"}), 400
        c.execute("SELECT 1 FROM accounts WHERE account_number = %s", (account_number,))
        if c.fetchone():
            return jsonify({"error": "Account number already exists"}), 400

        c.execute(
            "INSERT INTO customers (username, password, full_name, email, phone) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (username, hash_password(password), full_name, email, phone)
        )
        customer_id = c.fetchone()[0]
        c.execute(
            "INSERT INTO accounts (account_number, customer_id, balance, currency) VALUES (%s, %s, %s, %s)",
            (account_number, customer_id, initial_balance, 'USD')
        )
        conn.commit()
        return jsonify({"status": "success", "account_number": account_number})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# --- Public Endpoints ---
@app.route('/accounts', methods=['GET'])
def list_accounts():
    """Liệt kê tất cả tài khoản."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT a.account_number, a.balance, a.currency, c.full_name
        FROM accounts a JOIN customers c ON a.customer_id = c.id
    """)
    accounts = []
    for row in c.fetchall():
        accounts.append({
            "account_number": row[0],
            "balance": float(row[1]),
            "currency": row[2],
            "full_name": row[3]
        })
    conn.close()
    return jsonify({"accounts": accounts, "bank": "Bank B"})


@app.route('/accounts/<account_number>/info', methods=['GET'])
def account_info(account_number):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT a.account_number, a.balance, a.currency, c.full_name, c.email, c.phone "
        "FROM accounts a JOIN customers c ON a.customer_id = c.id WHERE a.account_number = %s",
        (account_number,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({
        "account_number": row[0],
        "balance": float(row[1]),
        "currency": row[2],
        "full_name": row[3],
        "email": row[4],
        "phone": row[5]
    })


@app.route('/accounts/<account_number>/balance', methods=['GET'])
def balance(account_number):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT balance FROM accounts WHERE account_number = %s", (account_number,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({"account_number": account_number, "balance": float(row[0])})


@app.route('/transactions/<account_number>', methods=['GET'])
def get_transactions(account_number):
    """Lấy lịch sử giao dịch."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, account_number, type, amount, counterpart, status, created_at
        FROM transactions
        WHERE account_number = %s
        ORDER BY created_at DESC
    """, (account_number,))
    txns = []
    for row in c.fetchall():
        txns.append({
            "id": row[0],
            "account_number": row[1],
            "type": row[2],
            "amount": float(row[3]),
            "counterpart": row[4],
            "status": row[5],
            "created_at": str(row[6])
        })
    conn.close()
    return jsonify({"transactions": txns})


# --- Withdraw ---
@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json() or {}
    account_number = data.get('account_number')
    amount = data.get('amount')
    if not account_number or not amount or amount <= 0:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT balance FROM accounts WHERE account_number = %s", (account_number,))
        row = c.fetchone()
        if not row:
            return jsonify({"error": "Account not found"}), 404
        bal = float(row[0])
        if bal < amount:
            return jsonify({"error": "Insufficient balance"}), 400

        c.execute("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, account_number))
        c.execute(
            "INSERT INTO transactions (account_number, type, amount, counterpart, status) VALUES (%s, 'withdraw', %s, %s, %s)",
            (account_number, amount, None, 'success')
        )
        conn.commit()
        return jsonify({"status": "success", "new_balance": bal - amount})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# --- Internal Transfer ---
@app.route('/internal/transfer', methods=['POST'])
def internal_transfer():
    data = request.get_json() or {}
    from_acc = data.get('from_account')
    to_acc = data.get('to_account')
    amount = data.get('amount')
    if not from_acc or not to_acc or not amount or amount <= 0:
        return jsonify({"error": "Invalid request"}), 400
    if from_acc == to_acc:
        return jsonify({"error": "Cannot transfer to same account"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT balance FROM accounts WHERE account_number = %s", (from_acc,))
        row = c.fetchone()
        if not row:
            return jsonify({"error": "Source account not found"}), 404
        if float(row[0]) < amount:
            return jsonify({"error": "Insufficient balance"}), 400

        c.execute("SELECT account_number FROM accounts WHERE account_number = %s", (to_acc,))
        if not c.fetchone():
            return jsonify({"error": "Destination account not found"}), 404

        c.execute("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, from_acc))
        c.execute("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, to_acc))

        c.execute(
            "INSERT INTO transactions (account_number, type, amount, counterpart, status) VALUES (%s, 'transfer_out', %s, %s, %s)",
            (from_acc, amount, to_acc, 'success')
        )
        c.execute(
            "INSERT INTO transactions (account_number, type, amount, counterpart, status) VALUES (%s, 'transfer_in', %s, %s, %s)",
            (to_acc, amount, from_acc, 'success')
        )

        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# --- 2PC Endpoints ---
@app.route('/prepare', methods=['POST'])
def prepare():
    data = request.get_json() or {}
    txn_id = data.get('txn_id')
    source_account = data.get('source_account')
    dest_account = data.get('dest_account')
    amount = data.get('amount')
    txn_type = data.get('type')

    if not txn_id or not amount or not txn_type:
        return jsonify({"status": "abort", "reason": "Missing required fields"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        if txn_type == 'debit':
            c.execute("SELECT balance FROM accounts WHERE account_number = %s", (source_account,))
            row = c.fetchone()
            if not row:
                return jsonify({"status": "abort", "reason": "Source account not found"})
            if float(row[0]) < amount:
                return jsonify({"status": "abort", "reason": "Insufficient balance"})
                
            # Trừ tiền để "hold" lại (giữ chỗ)
            c.execute("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, source_account))
            # Ghi nhận giao dịch trừ tiền ngay lúc này để lịch sử khớp
            c.execute(
                "INSERT INTO transactions (account_number, type, amount, counterpart, status) VALUES (%s, 'transfer_out', %s, %s, %s)",
                (source_account, amount, dest_account, 'success')
            )

            c.execute(
                "INSERT INTO pending_txns (txn_id, source_account, dest_account, amount, type) VALUES (%s, %s, %s, %s, %s)",
                (txn_id, source_account, dest_account, amount, 'debit')
            )
        elif txn_type == 'credit':
            c.execute("SELECT account_number FROM accounts WHERE account_number = %s", (dest_account,))
            if not c.fetchone():
                return jsonify({"status": "abort", "reason": "Destination account not found"})
            c.execute(
                "INSERT INTO pending_txns (txn_id, source_account, dest_account, amount, type) VALUES (%s, %s, %s, %s, %s)",
                (txn_id, source_account, dest_account, amount, 'credit')
            )
        else:
            return jsonify({"status": "abort", "reason": "Unknown transaction type"}), 400

        conn.commit()
        log_event('bank_b', {'txn_id': txn_id, 'action': 'prepare', 'type': txn_type, 'status': 'ready'})
        return jsonify({"status": "ready"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@app.route('/commit', methods=['POST'])
def commit():
    data = request.get_json() or {}
    txn_id = data.get('txn_id')
    if not txn_id:
        return jsonify({"status": "error", "message": "Missing txn_id"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT source_account, dest_account, amount, type FROM pending_txns WHERE txn_id = %s",
            (txn_id,)
        )
        row = c.fetchone()
        if not row:
            return jsonify({"status": "committed"})

        source_account, dest_account, amount, txn_type = row

        if txn_type == 'debit':
            # Balance và log giao dịch đã trừ lúc prepare, không cần làm gì thêm ở đây
            pass
        else:
            c.execute(
                "UPDATE accounts SET balance = balance + %s WHERE account_number = %s",
                (amount, dest_account)
            )
            c.execute(
                "INSERT INTO transactions (account_number, type, amount, counterpart, status) VALUES (%s, 'transfer_in', %s, %s, %s)",
                (dest_account, amount, source_account, 'success')
            )

        c.execute("DELETE FROM pending_txns WHERE txn_id = %s", (txn_id,))
        conn.commit()
        log_event('bank_b', {'txn_id': txn_id, 'action': 'commit', 'status': 'committed'})
        return jsonify({"status": "committed"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@app.route('/rollback', methods=['POST'])
def rollback():
    data = request.get_json() or {}
    txn_id = data.get('txn_id')
    if not txn_id:
        return jsonify({"status": "error", "message": "Missing txn_id"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT source_account, dest_account, amount, type FROM pending_txns WHERE txn_id = %s", (txn_id,))
        row = c.fetchone()
        if row:
            source_account, dest_account, amount, txn_type = row
            if txn_type == 'debit':
                # Hoàn lại tiền vì giao dịch bị hủy
                c.execute("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, source_account))
                # Ghi log hoàn tiền
                c.execute(
                    "INSERT INTO transactions (account_number, type, amount, counterpart, status) VALUES (%s, 'refund_in', %s, %s, %s)",
                    (source_account, amount, dest_account, 'success')
                )

        c.execute("DELETE FROM pending_txns WHERE txn_id = %s", (txn_id,))
        conn.commit()
        log_event('bank_b', {'txn_id': txn_id, 'action': 'rollback', 'status': 'rolled_back'})
        return jsonify({"status": "rolled_back"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


# --- Pending (for recovery) ---
@app.route('/pending', methods=['GET'])
def list_pending():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT txn_id, source_account, dest_account, amount, type, created_at FROM pending_txns")
    rows = c.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "txn_id": r[0],
            "source_account": r[1],
            "dest_account": r[2],
            "amount": float(r[3]),
            "type": r[4],
            "created_at": str(r[5])
        })
    return jsonify({"pending": result})


@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT 1")
        conn.close()
        return jsonify({"status": "healthy", "service": "BankB", "database": "PostgreSQL"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "service": "BankB", "error": str(e)}), 500


def recover_pending():
    import requests
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT txn_id, source_account, dest_account, amount, type FROM pending_txns")
    rows = c.fetchall()
    for row in rows:
        txn_id, source_account, dest_account, amount, txn_type = row
        try:
            resp = requests.get(f"http://localhost:5000/status/{txn_id}", timeout=5)
            state = 'unknown'
            if resp.status_code == 200:
                state = resp.json().get('status')
            elif resp.status_code == 404:
                # Nếu Coordinator không biết giao dịch này, tức là nó chưa từng hoàn tất Phase 1 hoặc đã bị hủy
                state = 'aborted'
            
            if state == 'committed':
                if txn_type == 'credit':
                    c.execute("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, dest_account))
                    c.execute("INSERT INTO transactions (account_number, type, amount, counterpart, status) VALUES (%s, 'transfer_in', %s, %s, %s)", (dest_account, amount, source_account, 'success'))
                c.execute("DELETE FROM pending_txns WHERE txn_id = %s", (txn_id,))
                conn.commit()
                log_event('bank_b', {'txn_id': txn_id, 'action': 'recover_commit', 'status': 'completed'})
            elif state in ('aborted', 'error'):
                if txn_type == 'debit':
                    c.execute("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, source_account))
                    c.execute("INSERT INTO transactions (account_number, type, amount, counterpart, status) VALUES (%s, 'refund_in', %s, %s, %s)", (source_account, amount, dest_account, 'success'))
                c.execute("DELETE FROM pending_txns WHERE txn_id = %s", (txn_id,))
                conn.commit()
                log_event('bank_b', {'txn_id': txn_id, 'action': 'recover_rollback', 'status': 'completed'})
        except Exception as e:
            logger.error(f"Recovery error for {txn_id}: {e}")
    conn.close()

if __name__ == '__main__':
    init_db()
    recover_pending()
    app.run(port=5002, debug=False)
