# coordinator.py
from flask import Flask, request, jsonify
import uuid
import requests
from logger import get_logger, log_event
import time 

app = Flask(__name__)
logger = get_logger('coordinator')

# Các URL của các dịch vụ bank
BANK_A_URL = 'http://localhost:5001'
BANK_B_URL = 'http://localhost:5002'

# Trạng thái giao dịch (in-memory) - có thể mở rộng lưu ra DB hoặc file
txn_status = {}


def _get_bank_url(account_number: str) -> str | None:
    if account_number.startswith('A'):
        return BANK_A_URL
    if account_number.startswith('B'):
        return BANK_B_URL
    return None


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Coordinator',
        'banks': {
            'bank_a': BANK_A_URL,
            'bank_b': BANK_B_URL
        }
    })


@app.route('/status/<txn_id>', methods=['GET'])
def status(txn_id):
    entry = txn_status.get(txn_id)
    if not entry:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify(entry)


@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json() or {}
    from_acc = data.get('from_account')
    to_acc = data.get('to_account')
    amount = data.get('amount')

    if not from_acc or not to_acc or not amount:
        return jsonify({"error": "Missing fields"}), 400

    source_bank = _get_bank_url(from_acc)
    dest_bank = _get_bank_url(to_acc)
    if not source_bank or not dest_bank:
        return jsonify({"error": "Invalid account number format"}), 400

    txn_id = str(uuid.uuid4())
    txn_status[txn_id] = {
        'txn_id': txn_id,
        'from': from_acc,
        'to': to_acc,
        'amount': amount,
        'status': 'started'
    }

    log_event('coordinator', {'txn_id': txn_id, 'action': 'start', 'from': from_acc, 'to': to_acc, 'amount': amount})

    # Nếu cùng ngân hàng -> gọi internal transfer
    if source_bank == dest_bank:
        try:
            resp = requests.post(
                f"{source_bank}/internal/transfer",
                json={"from_account": from_acc, "to_account": to_acc, "amount": amount},
                timeout=10
            )
            result = resp.json()
            status_code = resp.status_code
            if status_code == 200 and result.get('status') == 'success':
                txn_status[txn_id]['status'] = 'committed'
                log_event('coordinator', {'txn_id': txn_id, 'state': 'committed', 'type': 'internal'})
            else:
                txn_status[txn_id]['status'] = 'aborted'
                txn_status[txn_id]['reason'] = result
                log_event('coordinator', {'txn_id': txn_id, 'state': 'aborted', 'reason': result})
            return jsonify({'txn_id': txn_id, **result}), status_code
        except Exception as e:
            txn_status[txn_id]['status'] = 'error'
            txn_status[txn_id]['reason'] = str(e)
            log_event('coordinator', {'txn_id': txn_id, 'state': 'error', 'reason': str(e)})
            return jsonify({"status": "error", "reason": str(e)}), 500

    # Cross-bank -> Two-phase commit
    txn_status[txn_id]['status'] = 'preparing'

    try:
        prep_source = requests.post(
            f"{source_bank}/prepare",
            json={
                "txn_id": txn_id,
                "source_account": from_acc,
                "dest_account": to_acc,
                "amount": amount,
                "type": "debit"
            },
            timeout=10
        )
        prep_dest = requests.post(
            f"{dest_bank}/prepare",
            json={
                "txn_id": txn_id,
                "source_account": from_acc,
                "dest_account": to_acc,
                "amount": amount,
                "type": "credit"
            },
            timeout=10
        )

        ready_source = prep_source.status_code == 200 and prep_source.json().get('status') == 'ready'
        ready_dest = prep_dest.status_code == 200 and prep_dest.json().get('status') == 'ready'

        if ready_source and ready_dest:
            txn_status[txn_id]['status'] = 'committing'
            log_event('coordinator', {'txn_id': txn_id, 'state': 'GLOBAL_COMMIT'})

            time.sleep(15)

            commit_source = requests.post(f"{source_bank}/commit", json={"txn_id": txn_id}, timeout=10)
            commit_dest = requests.post(f"{dest_bank}/commit", json={"txn_id": txn_id}, timeout=10)

            if commit_source.status_code == 200 and commit_dest.status_code == 200:
                txn_status[txn_id]['status'] = 'committed'
                return jsonify({"status": "committed", "txn_id": txn_id}), 200

        # Nếu ở đây thì abort
        txn_status[txn_id]['status'] = 'aborted'
        log_event('coordinator', {'txn_id': txn_id, 'state': 'GLOBAL_ABORT', 'reason': 'prepare failed or commit failed'})
        requests.post(f"{source_bank}/rollback", json={"txn_id": txn_id}, timeout=10)
        requests.post(f"{dest_bank}/rollback", json={"txn_id": txn_id}, timeout=10)
        return jsonify({"status": "aborted", "txn_id": txn_id}), 400

    except Exception as e:
        txn_status[txn_id]['status'] = 'error'
        txn_status[txn_id]['reason'] = str(e)
        log_event('coordinator', {'txn_id': txn_id, 'state': 'error', 'reason': str(e)})
        # Best-effort rollback
        try:
            requests.post(f"{source_bank}/rollback", json={"txn_id": txn_id}, timeout=5)
            requests.post(f"{dest_bank}/rollback", json={"txn_id": txn_id}, timeout=5)
        except Exception:
            pass
        return jsonify({"status": "error", "reason": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
