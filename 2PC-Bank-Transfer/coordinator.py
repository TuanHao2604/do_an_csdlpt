# coordinator.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import requests
import time
import threading
import json
from logger import get_logger, log_event

app = Flask(__name__)
CORS(app, supports_credentials=True)
logger = get_logger('coordinator')

# Các URL của các dịch vụ bank
BANK_A_URL = 'http://localhost:5001'
BANK_B_URL = 'http://localhost:5002'

# Trạng thái giao dịch (in-memory)
txn_status = {}

# Cấu hình giả lập sự cố
crash_config = {
    'enabled': False,
    'crash_point': 'after_prepare',  # 'after_prepare' | 'after_source_commit' | 'before_commit'
    'delay_seconds': 15
}


def _get_bank_url(account_number: str) -> str | None:
    if account_number.startswith('A'):
        return BANK_A_URL
    if account_number.startswith('B'):
        return BANK_B_URL
    return None


# ===================== CRASH SIMULATION =====================
@app.route('/simulate-crash', methods=['POST'])
def simulate_crash():
    """Bật/tắt giả lập sự cố."""
    data = request.get_json() or {}
    crash_config['enabled'] = data.get('enabled', True)
    crash_config['crash_point'] = data.get('crash_point', 'after_prepare')
    crash_config['delay_seconds'] = data.get('delay_seconds', 15)
    log_event('coordinator', {
        'action': 'simulate_crash_config',
        'config': crash_config.copy()
    })
    return jsonify({
        "status": "ok",
        "crash_simulation": crash_config.copy()
    })


@app.route('/simulate-crash', methods=['GET'])
def get_crash_config():
    """Xem cấu hình giả lập sự cố."""
    return jsonify({"crash_simulation": crash_config.copy()})


# ===================== RECOVERY THREAD =====================
def recovery_worker():
    """
    Thread phục hồi: quét pending_txns ở cả 2 bank định kỳ.
    Nếu giao dịch treo > 30 giây → tự động rollback.
    """
    while True:
        time.sleep(10)  # Kiểm tra mỗi 10 giây
        try:
            for bank_name, bank_url in [('Bank A', BANK_A_URL), ('Bank B', BANK_B_URL)]:
                try:
                    resp = requests.get(f"{bank_url}/pending", timeout=5)
                    if resp.status_code != 200:
                        continue
                    pending = resp.json().get('pending', [])
                    for txn in pending:
                        txn_id = txn['txn_id']
                        created_at = txn['created_at']

                        # Kiểm tra nếu giao dịch nằm trong txn_status
                        entry = txn_status.get(txn_id)
                        if entry and entry.get('status') in ('committed', 'aborted'):
                            # Đã có quyết định cuối cùng → thực hiện lại
                            if entry['status'] == 'committed':
                                requests.post(f"{bank_url}/commit", json={"txn_id": txn_id}, timeout=5)
                            else:
                                requests.post(f"{bank_url}/rollback", json={"txn_id": txn_id}, timeout=5)
                            log_event('coordinator', {
                                'action': 'recovery',
                                'txn_id': txn_id,
                                'bank': bank_name,
                                'decision': entry['status']
                            })
                            continue

                        # Nếu giao dịch treo (không có trong txn_status hoặc ở trạng thái trung gian)
                        # → rollback an toàn
                        if entry is None or entry.get('status') in ('started', 'preparing', 'committing', 'error'):
                            # Rollback tất cả banks
                            source_bank = _get_bank_url(txn.get('source_account', 'A'))
                            dest_bank = _get_bank_url(txn.get('dest_account', 'B'))
                            try:
                                if source_bank:
                                    requests.post(f"{source_bank}/rollback", json={"txn_id": txn_id}, timeout=5)
                                if dest_bank:
                                    requests.post(f"{dest_bank}/rollback", json={"txn_id": txn_id}, timeout=5)
                            except:
                                pass

                            txn_status[txn_id] = {
                                'txn_id': txn_id,
                                'status': 'aborted',
                                'reason': 'Auto-recovered: transaction hung detected'
                            }
                            log_event('coordinator', {
                                'action': 'auto_recovery',
                                'txn_id': txn_id,
                                'bank': bank_name,
                                'decision': 'rollback'
                            })

                except Exception as e:
                    logger.debug(f"Recovery check failed for {bank_name}: {e}")
        except Exception as e:
            logger.error(f"Recovery worker error: {e}")


# ===================== ENDPOINTS =====================
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Coordinator',
        'crash_simulation': crash_config.copy(),
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


@app.route('/transactions', methods=['GET'])
def list_transactions():
    """Liệt kê tất cả giao dịch đã ghi nhận."""
    return jsonify({"transactions": list(txn_status.values())})


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
        'status': 'started',
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    log_event('coordinator', {'txn_id': txn_id, 'action': 'start', 'from': from_acc, 'to': to_acc, 'amount': amount})

    # Nếu cùng ngân hàng → gọi internal transfer
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

    # ==================== TWO-PHASE COMMIT ====================
    txn_status[txn_id]['status'] = 'preparing'

    try:
        # ====== PHASE 1: PREPARE ======
        log_event('coordinator', {'txn_id': txn_id, 'phase': 'PREPARE', 'action': 'sending_prepare_to_source'})
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

        log_event('coordinator', {'txn_id': txn_id, 'phase': 'PREPARE', 'action': 'sending_prepare_to_dest'})
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

        log_event('coordinator', {
            'txn_id': txn_id,
            'phase': 'PREPARE_RESULT',
            'source_ready': ready_source,
            'dest_ready': ready_dest
        })

        if ready_source and ready_dest:
            # ====== GIẢI LẬP SỰ CỐ: sau Phase 1, trước Phase 2 ======
            if crash_config['enabled'] and crash_config['crash_point'] == 'after_prepare':
                delay = crash_config['delay_seconds']
                log_event('coordinator', {
                    'txn_id': txn_id,
                    'action': 'CRASH_SIMULATION',
                    'crash_point': 'after_prepare',
                    'message': f'Giả lập đứt kết nối. Giao dịch thất bại sau Prepare.'
                })
                txn_status[txn_id]['status'] = 'aborted'
                txn_status[txn_id]['crash_simulated'] = True
                
                reason = "Giả lập treo hệ thống: Mất kết nối. Đã hủy chuyển tiền và hoàn lại số dư cho Bank A."
                txn_status[txn_id]['reason'] = reason
                
                # Sleep một chút tạo cảm giác delay
                time.sleep(2)
                
                # Thực hiện rollback
                log_event('coordinator', {
                    'txn_id': txn_id,
                    'action': 'CRASH_SIMULATION_END',
                    'message': 'Đang tiến hành hoàn tiền (Rollback)...'
                })
                requests.post(f"{source_bank}/rollback", json={"txn_id": txn_id}, timeout=10)
                requests.post(f"{dest_bank}/rollback", json={"txn_id": txn_id}, timeout=10)
                
                return jsonify({"status": "aborted", "txn_id": txn_id, "reason": reason}), 400

            # ====== PHASE 2: COMMIT ======
            txn_status[txn_id]['status'] = 'committing'
            log_event('coordinator', {'txn_id': txn_id, 'phase': 'COMMIT', 'state': 'GLOBAL_COMMIT'})

            commit_source = requests.post(f"{source_bank}/commit", json={"txn_id": txn_id}, timeout=10)

            # Giả lập crash giữa 2 lệnh commit
            if crash_config['enabled'] and crash_config['crash_point'] == 'after_source_commit':
                delay = crash_config['delay_seconds']
                log_event('coordinator', {
                    'txn_id': txn_id,
                    'action': 'CRASH_SIMULATION',
                    'crash_point': 'after_source_commit',
                    'delay_seconds': delay,
                    'message': f'Giả lập crash sau khi Bank nguồn đã commit, trước khi Bank đích commit...'
                })
                time.sleep(delay)

            commit_dest = requests.post(f"{dest_bank}/commit", json={"txn_id": txn_id}, timeout=10)

            if commit_source.status_code == 200 and commit_dest.status_code == 200:
                txn_status[txn_id]['status'] = 'committed'
                log_event('coordinator', {'txn_id': txn_id, 'phase': 'RESULT', 'state': 'COMMITTED'})
                return jsonify({"status": "committed", "txn_id": txn_id}), 200

        # ====== ABORT ======
        txn_status[txn_id]['status'] = 'aborted'
        abort_reason = 'prepare failed'
        if not ready_source:
            abort_reason = f"Source bank abort: {prep_source.json().get('reason', 'unknown')}"
        elif not ready_dest:
            abort_reason = f"Dest bank abort: {prep_dest.json().get('reason', 'unknown')}"

        txn_status[txn_id]['reason'] = abort_reason
        log_event('coordinator', {'txn_id': txn_id, 'phase': 'ABORT', 'state': 'GLOBAL_ABORT', 'reason': abort_reason})

        requests.post(f"{source_bank}/rollback", json={"txn_id": txn_id}, timeout=10)
        requests.post(f"{dest_bank}/rollback", json={"txn_id": txn_id}, timeout=10)
        return jsonify({"status": "aborted", "txn_id": txn_id, "reason": abort_reason}), 400

    except Exception as e:
        txn_status[txn_id]['status'] = 'error'
        txn_status[txn_id]['reason'] = str(e)
        log_event('coordinator', {'txn_id': txn_id, 'phase': 'ERROR', 'reason': str(e)})
        # Best-effort rollback
        try:
            requests.post(f"{source_bank}/rollback", json={"txn_id": txn_id}, timeout=5)
            requests.post(f"{dest_bank}/rollback", json={"txn_id": txn_id}, timeout=5)
        except Exception:
            pass
        return jsonify({"status": "error", "reason": str(e)}), 500


if __name__ == '__main__':
    # Khởi động recovery thread
    recovery_thread = threading.Thread(target=recovery_worker, daemon=True)
    recovery_thread.start()
    logger.info("Recovery worker thread started")

    app.run(port=5000, debug=True, use_reloader=False)
