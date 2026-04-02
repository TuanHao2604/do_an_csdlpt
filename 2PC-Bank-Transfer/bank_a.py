import pyodbc
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import uuid
import hashlib
import requests
from functools import wraps
from logger import get_logger, log_event

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app, supports_credentials=True)

# Cấu hình SQL Server
SERVER = 'localhost,1433'
DATABASE = 'bank_a'
USERNAME = 'sa'
PASSWORD = 'Hao@DBMS2026'
DRIVER = '{ODBC Driver 18 for SQL Server}'
CONNECTION_STRING = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes'

logger = get_logger('bank_a')

# --- Hàm helper ---
def get_db_connection():
    """Return a connection to the bank_a database, creating it if missing."""
    try:
        return pyodbc.connect(CONNECTION_STRING)
    except pyodbc.ProgrammingError as e:
        if 'Cannot open database' in str(e):
            master_cnxn = pyodbc.connect(
                f'DRIVER={DRIVER};SERVER={SERVER};DATABASE=master;UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes'
            )
            master_cnxn.autocommit = True
            master_cursor = master_cnxn.cursor()
            master_cursor.execute("IF DB_ID('bank_a') IS NULL CREATE DATABASE bank_a")
            master_cnxn.close()
            return pyodbc.connect(CONNECTION_STRING)
        raise

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# --- Khởi tạo database ---
def init_db():
    """Tạo schema và dữ liệu mẫu cho Bank A."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.customers','U') IS NULL
            CREATE TABLE dbo.customers (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(100) UNIQUE NOT NULL,
                password NVARCHAR(256) NOT NULL,
                full_name NVARCHAR(200),
                email NVARCHAR(200),
                phone NVARCHAR(50)
            )
        """)
        cursor.execute("""
            IF OBJECT_ID('dbo.accounts','U') IS NULL
            CREATE TABLE dbo.accounts (
                account_number NVARCHAR(50) PRIMARY KEY,
                customer_id INT NOT NULL REFERENCES dbo.customers(id),
                balance DECIMAL(18,2) NOT NULL DEFAULT 0,
                currency NVARCHAR(10) NOT NULL DEFAULT 'USD'
            )
        """)
        cursor.execute("""
            IF OBJECT_ID('dbo.transactions','U') IS NULL
            CREATE TABLE dbo.transactions (
                id INT IDENTITY(1,1) PRIMARY KEY,
                account_number NVARCHAR(50) NOT NULL,
                type NVARCHAR(50) NOT NULL,
                amount DECIMAL(18,2) NOT NULL,
                counterpart NVARCHAR(50),
                status NVARCHAR(50),
                created_at DATETIME NOT NULL DEFAULT GETDATE()
            )
        """)
        cursor.execute("""
            IF OBJECT_ID('dbo.pending_txns','U') IS NULL
            CREATE TABLE dbo.pending_txns (
                txn_id NVARCHAR(100) PRIMARY KEY,
                source_account NVARCHAR(50),
                dest_account NVARCHAR(50),
                amount DECIMAL(18,2) NOT NULL,
                type NVARCHAR(20) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT GETDATE()
            )
        """)

        # Seed dữ liệu mẫu
        cursor.execute("SELECT COUNT(*) FROM dbo.customers")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO dbo.customers (username, password, full_name, email, phone) VALUES (?, ?, ?, ?, ?)",
                           ('alice', hash_password('alice123'), 'Alice Nguyen', 'alice@example.com', '0123456789'))
            cursor.execute("INSERT INTO dbo.customers (username, password, full_name, email, phone) VALUES (?, ?, ?, ?, ?)",
                           ('bob', hash_password('bob123'), 'Bob Tran', 'bob@example.com', '0987654321'))

            cursor.execute("SELECT id FROM dbo.customers WHERE username = ?", ('alice',))
            alice_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM dbo.customers WHERE username = ?", ('bob',))
            bob_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO dbo.accounts (account_number, customer_id, balance, currency) VALUES (?, ?, ?, ?)",
                           ('A1001', alice_id, 1000, 'USD'))
            cursor.execute("INSERT INTO dbo.accounts (account_number, customer_id, balance, currency) VALUES (?, ?, ?, ?)",
                           ('A1002', bob_id, 1000, 'USD'))

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to init DB: {e}")
        raise
    finally:
        conn.close()

# --- Auth ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, full_name FROM customers WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row.password == hash_password(password):
        session['user_id'] = row.id
        # Lấy danh sách tài khoản
        conn2 = get_db_connection()
        c2 = conn2.cursor()
        c2.execute("SELECT account_number, balance, currency FROM accounts WHERE customer_id = ?", (row.id,))
        accounts = []
        for r in c2.fetchall():
            accounts.append({
                "account_number": r.account_number,
                "balance": float(r.balance),
                "currency": r.currency
            })
        conn2.close()
        return jsonify({
            "status": "success",
            "message": "Logged in",
            "user_id": row.id,
            "full_name": row.full_name,
            "accounts": accounts
        })
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"})

# --- Đăng ký ---
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
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM customers WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({"error": "Username already exists"}), 400

        cursor.execute("SELECT 1 FROM accounts WHERE account_number = ?", (account_number,))
        if cursor.fetchone():
            return jsonify({"error": "Account number already exists"}), 400

        cursor.execute("""
            INSERT INTO customers (username, password, full_name, email, phone) 
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?)
        """, (username, hash_password(password), full_name, email, phone))
        customer_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO accounts (account_number, customer_id, balance, currency) VALUES (?, ?, ?, ?)",
            (account_number, customer_id, initial_balance, 'USD'),
        )
        conn.commit()
        return jsonify({"status": "success", "account_number": account_number})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# --- Public Endpoints (dùng cho frontend) ---
@app.route('/accounts', methods=['GET'])
def list_accounts():
    """Liệt kê tất cả tài khoản (public cho demo)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.account_number, a.balance, a.currency, c.full_name
        FROM accounts a JOIN customers c ON a.customer_id = c.id
    """)
    accounts = []
    for row in cursor.fetchall():
        accounts.append({
            "account_number": row.account_number,
            "balance": float(row.balance),
            "currency": row.currency,
            "full_name": row.full_name
        })
    conn.close()
    return jsonify({"accounts": accounts, "bank": "Bank A"})


@app.route('/accounts/<account_number>/info', methods=['GET'])
def account_info(account_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.account_number, a.balance, a.currency, c.full_name, c.email, c.phone
        FROM accounts a
        JOIN customers c ON a.customer_id = c.id
        WHERE a.account_number = ?
    """, (account_number,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({
            "account_number": row.account_number,
            "balance": float(row.balance),
            "currency": row.currency,
            "full_name": row.full_name,
            "email": row.email,
            "phone": row.phone
        })
    return jsonify({"error": "Account not found"}), 404

@app.route('/accounts/<account_number>/balance', methods=['GET'])
def balance(account_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (account_number,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"account_number": account_number, "balance": float(row.balance)})
    return jsonify({"error": "Account not found"}), 404


@app.route('/transactions/<account_number>', methods=['GET'])
def get_transactions(account_number):
    """Lấy lịch sử giao dịch của tài khoản."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, account_number, type, amount, counterpart, status, created_at
        FROM transactions
        WHERE account_number = ?
        ORDER BY created_at DESC
    """, (account_number,))
    txns = []
    for row in cursor.fetchall():
        txns.append({
            "id": row.id,
            "account_number": row.account_number,
            "type": row.type,
            "amount": float(row.amount),
            "counterpart": row.counterpart,
            "status": row.status,
            "created_at": str(row.created_at)
        })
    conn.close()
    return jsonify({"transactions": txns})


# --- Rút tiền ---
@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    account_number = data.get('account_number')
    amount = data.get('amount')
    if not account_number or not amount or amount <= 0:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (account_number,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Account not found"}), 404
        bal = row.balance
        if bal < amount:
            return jsonify({"error": "Insufficient balance"}), 400

        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_number = ?", (amount, account_number))
        cursor.execute("""
            INSERT INTO transactions (account_number, type, amount, counterpart, status, created_at)
            VALUES (?, 'withdraw', ?, NULL, 'success', GETDATE())
        """, (account_number, amount))
        conn.commit()
        return jsonify({"status": "success", "new_balance": float(bal - amount)})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- Chuyển tiền nội bộ ---
@app.route('/internal/transfer', methods=['POST'])
def internal_transfer():
    data = request.get_json()
    from_acc = data.get('from_account')
    to_acc = data.get('to_account')
    amount = data.get('amount')
    if not from_acc or not to_acc or not amount or amount <= 0:
        return jsonify({"error": "Invalid request"}), 400
    if from_acc == to_acc:
        return jsonify({"error": "Cannot transfer to same account"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (from_acc,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Source account not found"}), 404
        if row.balance < amount:
            return jsonify({"error": "Insufficient balance"}), 400

        cursor.execute("SELECT account_number FROM accounts WHERE account_number = ?", (to_acc,))
        if not cursor.fetchone():
            return jsonify({"error": "Destination account not found"}), 404

        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_number = ?", (amount, from_acc))
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_number = ?", (amount, to_acc))

        cursor.execute("""
            INSERT INTO transactions (account_number, type, amount, counterpart, status, created_at)
            VALUES (?, 'transfer_out', ?, ?, 'success', GETDATE())
        """, (from_acc, amount, to_acc))
        cursor.execute("""
            INSERT INTO transactions (account_number, type, amount, counterpart, status, created_at)
            VALUES (?, 'transfer_in', ?, ?, 'success', GETDATE())
        """, (to_acc, amount, from_acc))

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
    cursor = conn.cursor()
    try:
        if txn_type == 'debit':
            cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (source_account,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"status": "abort", "reason": "Source account not found"})
            if row.balance < amount:
                return jsonify({"status": "abort", "reason": "Insufficient balance"})
            
            # Trừ tiền để "hold" lại (giữ chỗ)
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_number = ?", (amount, source_account))
            # Ghi nhận giao dịch trừ tiền ngay lúc này để lịch sử khớp
            cursor.execute(
                "INSERT INTO transactions (account_number, type, amount, counterpart, status, created_at) VALUES (?, 'transfer_out', ?, ?, 'success', GETDATE())",
                (source_account, amount, dest_account)
            )

            cursor.execute(
                "INSERT INTO pending_txns (txn_id, source_account, dest_account, amount, type) VALUES (?, ?, ?, ?, ?)",
                (txn_id, source_account, dest_account, amount, 'debit')
            )
        elif txn_type == 'credit':
            cursor.execute("SELECT account_number FROM accounts WHERE account_number = ?", (dest_account,))
            if not cursor.fetchone():
                return jsonify({"status": "abort", "reason": "Destination account not found"})
            cursor.execute(
                "INSERT INTO pending_txns (txn_id, source_account, dest_account, amount, type) VALUES (?, ?, ?, ?, ?)",
                (txn_id, source_account, dest_account, amount, 'credit')
            )
        else:
            return jsonify({"status": "abort", "reason": "Unknown transaction type"}), 400

        conn.commit()
        log_event('bank_a', {'txn_id': txn_id, 'action': 'prepare', 'type': txn_type, 'status': 'ready'})
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
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT source_account, dest_account, amount, type FROM pending_txns WHERE txn_id = ?",
            (txn_id,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"status": "committed"})

        source_account, dest_account, amount, txn_type = row

        if txn_type == 'debit':
            # Balance và log giao dịch đã trừ lúc prepare, không cần làm gì thêm ở đây
            pass
        else:
            cursor.execute(
                "UPDATE accounts SET balance = balance + ? WHERE account_number = ?",
                (amount, dest_account)
            )
            cursor.execute(
                "INSERT INTO transactions (account_number, type, amount, counterpart, status, created_at) VALUES (?, 'transfer_in', ?, ?, 'success', GETDATE())",
                (dest_account, amount, source_account)
            )

        cursor.execute("DELETE FROM pending_txns WHERE txn_id = ?", (txn_id,))
        conn.commit()
        log_event('bank_a', {'txn_id': txn_id, 'action': 'commit', 'status': 'committed'})
        return jsonify({"status": "committed"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/rollback', methods=['POST'])
def rollback():
    data = request.get_json()
    txn_id = data['txn_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT source_account, dest_account, amount, type FROM pending_txns WHERE txn_id = ?", (txn_id,))
        row = cursor.fetchone()
        if row:
            source_account, dest_account, amount, txn_type = row
            if txn_type == 'debit':
                # Hoàn lại tiền vì giao dịch bị hủy
                cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_number = ?", (amount, source_account))
                # Ghi log hoàn tiền
                cursor.execute(
                    "INSERT INTO transactions (account_number, type, amount, counterpart, status, created_at) VALUES (?, 'refund_in', ?, ?, 'success', GETDATE())",
                    (source_account, amount, dest_account)
                )

        cursor.execute("DELETE FROM pending_txns WHERE txn_id = ?", (txn_id,))
        conn.commit()
        log_event('bank_a', {'txn_id': txn_id, 'action': 'rollback', 'status': 'rolled_back'})
        return jsonify({"status": "rolled_back"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

# --- Pending transactions (for recovery) ---
@app.route('/pending', methods=['GET'])
def list_pending():
    """Liệt kê các giao dịch đang treo (cho recovery)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT txn_id, source_account, dest_account, amount, type, created_at FROM pending_txns")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "txn_id": r.txn_id,
            "source_account": r.source_account,
            "dest_account": r.dest_account,
            "amount": float(r.amount),
            "type": r.type,
            "created_at": str(r.created_at)
        })
    return jsonify({"pending": result})

# --- Recovery ---
def recover_pending():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT txn_id, source_account, dest_account, amount, type FROM pending_txns")
    rows = cursor.fetchall()
    for row in rows:
        txn_id, source_account, dest_account, amount, txn_type = row
        try:
            resp = requests.get(f"http://localhost:5000/status/{txn_id}", timeout=5)
            state = 'unknown'
            if resp.status_code == 200:
                state = resp.json().get('status')
            elif resp.status_code == 404:
                # Nếu Coordinator không biết giao dịch này, tức là nó đã bị hủy từ trong trứng nước
                state = 'aborted'
            
            if state == 'committed':
                if txn_type == 'credit':
                    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_number = ?", (amount, dest_account))
                    cursor.execute("INSERT INTO transactions (account_number, type, amount, counterpart, status, created_at) VALUES (?, 'transfer_in', ?, ?, 'success', GETDATE())", (dest_account, amount, source_account))
                cursor.execute("DELETE FROM pending_txns WHERE txn_id = ?", (txn_id,))
                conn.commit()
                log_event('bank_a', {'txn_id': txn_id, 'action': 'recover_commit', 'status': 'completed'})
            elif state in ('aborted', 'error'):
                if txn_type == 'debit':
                    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_number = ?", (amount, source_account))
                    cursor.execute("INSERT INTO transactions (account_number, type, amount, counterpart, status, created_at) VALUES (?, 'refund_in', ?, ?, 'success', GETDATE())", (source_account, amount, dest_account))
                cursor.execute("DELETE FROM pending_txns WHERE txn_id = ?", (txn_id,))
                conn.commit()
                log_event('bank_a', {'txn_id': txn_id, 'action': 'recover_rollback', 'status': 'completed'})
        except Exception as e:
            logger.error(f"Recovery error for {txn_id}: {e}")
    conn.close()


@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        return jsonify({"status": "healthy", "service": "BankA", "database": "SQLServer"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "service": "BankA", "error": str(e)}), 500


if __name__ == '__main__':
    init_db()
    recover_pending()
    app.run(port=5001, debug=True)