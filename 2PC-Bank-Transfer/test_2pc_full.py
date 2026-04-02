"""
Test Suite đầy đủ cho hệ thống 2PC Bank Transfer
Bao gồm 7 test case theo yêu cầu đề bài
"""
import requests
import json
import time
import sys

BASE_COORDINATOR = "http://localhost:5000"
BASE_BANK_A = "http://localhost:5001"
BASE_BANK_B = "http://localhost:5002"

PASS = 0
FAIL = 0

def log(msg, status="INFO"):
    icons = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️ ", "WARN": "⚠️ ", "TEST": "🧪"}
    print(f"  {icons.get(status, '  ')} {msg}")


def assert_true(condition, msg):
    global PASS, FAIL
    if condition:
        log(msg, "PASS")
        PASS += 1
    else:
        log(msg, "FAIL")
        FAIL += 1


def get_balance(bank_url, account):
    resp = requests.get(f"{bank_url}/accounts/{account}/balance", timeout=5)
    return resp.json().get("balance")


def check_health():
    """Kiểm tra tất cả services đang chạy."""
    print("\n" + "=" * 60)
    print("🏥 HEALTH CHECK")
    print("=" * 60)
    all_ok = True
    for name, url in [("Coordinator", BASE_COORDINATOR), ("Bank A", BASE_BANK_A), ("Bank B", BASE_BANK_B)]:
        try:
            resp = requests.get(f"{url}/health", timeout=5)
            if resp.status_code == 200:
                log(f"{name}: {resp.json().get('status')}", "PASS")
            else:
                log(f"{name}: HTTP {resp.status_code}", "FAIL")
                all_ok = False
        except Exception as e:
            log(f"{name}: {str(e)[:50]}", "FAIL")
            all_ok = False
    return all_ok


# ==================== TEST CASES ====================

def test_1_happy_path():
    """Test Case 1: Chuyển tiền xuyên ngân hàng thành công (Happy Path)."""
    print("\n" + "=" * 60)
    print("🧪 TEST 1: Happy Path - Chuyển 100 USD từ A1001 → B1001")
    print("=" * 60)

    bal_a_before = get_balance(BASE_BANK_A, "A1001")
    bal_b_before = get_balance(BASE_BANK_B, "B1001")
    log(f"Số dư trước: A1001={bal_a_before}, B1001={bal_b_before}")

    # Tắt crash simulation
    requests.post(f"{BASE_COORDINATOR}/simulate-crash", json={"enabled": False}, timeout=5)

    resp = requests.post(f"{BASE_COORDINATOR}/transfer", json={
        "from_account": "A1001",
        "to_account": "B1001",
        "amount": 100
    }, timeout=30)
    result = resp.json()
    log(f"Response: {json.dumps(result, indent=2)}")

    assert_true(resp.status_code == 200, f"HTTP status = 200 (got {resp.status_code})")
    assert_true(result.get("status") == "committed", f"Status = committed (got {result.get('status')})")

    bal_a_after = get_balance(BASE_BANK_A, "A1001")
    bal_b_after = get_balance(BASE_BANK_B, "B1001")
    log(f"Số dư sau: A1001={bal_a_after}, B1001={bal_b_after}")

    assert_true(bal_a_after == bal_a_before - 100, f"A1001 giảm 100 USD ({bal_a_before} → {bal_a_after})")
    assert_true(bal_b_after == bal_b_before + 100, f"B1001 tăng 100 USD ({bal_b_before} → {bal_b_after})")


def test_2_insufficient_balance():
    """Test Case 2: Không đủ số dư → Abort."""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Insufficient Balance - Chuyển 999999 USD từ A1001 → B1001")
    print("=" * 60)

    bal_a_before = get_balance(BASE_BANK_A, "A1001")
    bal_b_before = get_balance(BASE_BANK_B, "B1001")
    log(f"Số dư trước: A1001={bal_a_before}, B1001={bal_b_before}")

    resp = requests.post(f"{BASE_COORDINATOR}/transfer", json={
        "from_account": "A1001",
        "to_account": "B1001",
        "amount": 999999
    }, timeout=30)
    result = resp.json()
    log(f"Response: status={result.get('status')}, reason={result.get('reason', 'N/A')}")

    assert_true(result.get("status") == "aborted", f"Status = aborted (got {result.get('status')})")

    bal_a_after = get_balance(BASE_BANK_A, "A1001")
    bal_b_after = get_balance(BASE_BANK_B, "B1001")

    assert_true(bal_a_after == bal_a_before, f"A1001 không thay đổi ({bal_a_before} → {bal_a_after})")
    assert_true(bal_b_after == bal_b_before, f"B1001 không thay đổi ({bal_b_before} → {bal_b_after})")


def test_3_invalid_account():
    """Test Case 3: Tài khoản đích không tồn tại → Abort."""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Invalid Account - Chuyển từ A1001 → B9999 (không tồn tại)")
    print("=" * 60)

    bal_a_before = get_balance(BASE_BANK_A, "A1001")
    log(f"Số dư trước: A1001={bal_a_before}")

    resp = requests.post(f"{BASE_COORDINATOR}/transfer", json={
        "from_account": "A1001",
        "to_account": "B9999",
        "amount": 50
    }, timeout=30)
    result = resp.json()
    log(f"Response: status={result.get('status')}, reason={result.get('reason', 'N/A')}")

    assert_true(result.get("status") == "aborted", f"Status = aborted (got {result.get('status')})")

    bal_a_after = get_balance(BASE_BANK_A, "A1001")
    assert_true(bal_a_after == bal_a_before, f"A1001 không thay đổi ({bal_a_before} → {bal_a_after})")


def test_4_internal_transfer():
    """Test Case 4: Chuyển tiền nội bộ (cùng bank, không qua 2PC)."""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Internal Transfer - Chuyển 50 USD A1001 → A1002 (nội bộ)")
    print("=" * 60)

    bal_a1_before = get_balance(BASE_BANK_A, "A1001")
    bal_a2_before = get_balance(BASE_BANK_A, "A1002")
    log(f"Số dư trước: A1001={bal_a1_before}, A1002={bal_a2_before}")

    resp = requests.post(f"{BASE_COORDINATOR}/transfer", json={
        "from_account": "A1001",
        "to_account": "A1002",
        "amount": 50
    }, timeout=10)
    result = resp.json()
    log(f"Response: {json.dumps(result)}")

    assert_true(resp.status_code == 200, f"HTTP status = 200 (got {resp.status_code})")
    assert_true(result.get("status") == "success", f"Status = success (got {result.get('status')})")

    bal_a1_after = get_balance(BASE_BANK_A, "A1001")
    bal_a2_after = get_balance(BASE_BANK_A, "A1002")

    assert_true(bal_a1_after == bal_a1_before - 50, f"A1001 giảm 50 ({bal_a1_before} → {bal_a1_after})")
    assert_true(bal_a2_after == bal_a2_before + 50, f"A1002 tăng 50 ({bal_a2_before} → {bal_a2_after})")


def test_5_crash_simulation():
    """Test Case 5: Giả lập sự cố - Coordinator delay sau Phase 1 (Prepare)."""
    print("\n" + "=" * 60)
    print("🧪 TEST 5: Crash Simulation - Giả lập delay 5s sau Prepare")
    print("=" * 60)

    bal_a_before = get_balance(BASE_BANK_A, "A1001")
    bal_b_before = get_balance(BASE_BANK_B, "B1001")
    log(f"Số dư trước: A1001={bal_a_before}, B1001={bal_b_before}")

    # Bật crash simulation: delay 5 giây sau prepare
    resp = requests.post(f"{BASE_COORDINATOR}/simulate-crash", json={
        "enabled": True,
        "crash_point": "after_prepare",
        "delay_seconds": 5
    }, timeout=5)
    log(f"Crash simulation enabled: {resp.json()}")

    # Gửi chuyển tiền (sẽ bị delay)
    log("Đang chuyển tiền (sẽ bị delay 5s do crash simulation)...")
    start_time = time.time()
    resp = requests.post(f"{BASE_COORDINATOR}/transfer", json={
        "from_account": "A1001",
        "to_account": "B1001",
        "amount": 25
    }, timeout=30)
    elapsed = time.time() - start_time
    result = resp.json()
    log(f"Response after {elapsed:.1f}s: status={result.get('status')}")

    assert_true(result.get("status") == "aborted", f"Giao dịch aborted và hoàn lại tiền (got {result.get('status')})")
    assert_true("hoàn lại số dư" in result.get("reason", ""), "Có thông báo hoàn tiền")

    # Tắt crash simulation
    requests.post(f"{BASE_COORDINATOR}/simulate-crash", json={"enabled": False}, timeout=5)

    # Đợi 1 chút để rollback thực sự commit vào DB
    time.sleep(1)

    bal_a_after = get_balance(BASE_BANK_A, "A1001")
    bal_b_after = get_balance(BASE_BANK_B, "B1001")
    log(f"Số dư sau: A1001={bal_a_after}, B1001={bal_b_after}")
    
    assert_true(bal_a_before == bal_a_after, f"Số dư A1001 không đổi sau khi rollback ({bal_a_before} == {bal_a_after})")
    assert_true(bal_b_before == bal_b_after, f"Số dư B1001 không đổi ({bal_b_before} == {bal_b_after})")


def test_6_recovery_check():
    """Test Case 6: Kiểm tra recovery - Pending transactions phải được xử lý."""
    print("\n" + "=" * 60)
    print("🧪 TEST 6: Recovery Check - Kiểm tra không còn pending transactions")
    print("=" * 60)

    # Kiểm tra Bank A
    resp_a = requests.get(f"{BASE_BANK_A}/pending", timeout=5)
    pending_a = resp_a.json().get("pending", [])
    log(f"Bank A pending: {len(pending_a)} giao dịch")
    assert_true(len(pending_a) == 0, f"Bank A không còn pending (count={len(pending_a)})")

    # Kiểm tra Bank B
    resp_b = requests.get(f"{BASE_BANK_B}/pending", timeout=5)
    pending_b = resp_b.json().get("pending", [])
    log(f"Bank B pending: {len(pending_b)} giao dịch")
    assert_true(len(pending_b) == 0, f"Bank B không còn pending (count={len(pending_b)})")


def test_7_concurrent_transfers():
    """Test Case 7: Giao dịch đồng thời."""
    print("\n" + "=" * 60)
    print("🧪 TEST 7: Concurrent Transfers - 3 giao dịch đồng thời")
    print("=" * 60)
    import concurrent.futures

    bal_a1_before = get_balance(BASE_BANK_A, "A1001")
    bal_b1_before = get_balance(BASE_BANK_B, "B1001")
    log(f"Số dư trước: A1001={bal_a1_before}, B1001={bal_b1_before}")

    def do_transfer(amt):
        resp = requests.post(f"{BASE_COORDINATOR}/transfer", json={
            "from_account": "A1001",
            "to_account": "B1001",
            "amount": amt
        }, timeout=30)
        return resp.json()

    # Tắt crash simulation
    requests.post(f"{BASE_COORDINATOR}/simulate-crash", json={"enabled": False}, timeout=5)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(do_transfer, 10) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    committed = sum(1 for r in results if r.get("status") == "committed")
    log(f"Kết quả: {committed}/3 giao dịch committed")

    for i, r in enumerate(results):
        log(f"  Transfer {i+1}: status={r.get('status')}, txn_id={r.get('txn_id', 'N/A')[:8]}...")

    assert_true(committed >= 1, f"Ít nhất 1 giao dịch committed ({committed}/3)")

    bal_a1_after = get_balance(BASE_BANK_A, "A1001")
    bal_b1_after = get_balance(BASE_BANK_B, "B1001")
    log(f"Số dư sau: A1001={bal_a1_after}, B1001={bal_b1_after}")

    expected_deducted = committed * 10
    assert_true(
        bal_a1_after == bal_a1_before - expected_deducted,
        f"A1001 giảm đúng {expected_deducted} USD ({bal_a1_before} → {bal_a1_after})"
    )


# ==================== MAIN ====================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 2PC BANK TRANSFER - FULL TEST SUITE")
    print("=" * 60)
    print("Mô hình: Coordinator(5000) ↔ BankA/SQLServer(5001) ↔ BankB/PostgreSQL(5002)")

    if not check_health():
        print("\n❌ Một số services chưa chạy. Vui lòng khởi động trước.")
        print("   ./run_system.sh")
        sys.exit(1)

    test_1_happy_path()
    test_2_insufficient_balance()
    test_3_invalid_account()
    test_4_internal_transfer()
    test_5_crash_simulation()
    test_6_recovery_check()
    test_7_concurrent_transfers()

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 KẾT QUẢ: {PASS} PASS / {FAIL} FAIL / {PASS + FAIL} TOTAL")
    print("=" * 60)
    if FAIL == 0:
        print("🎉 TẤT CẢ TEST CASE ĐỀU PASS!")
    else:
        print(f"⚠️  Có {FAIL} test case FAIL. Kiểm tra lại.")
    sys.exit(0 if FAIL == 0 else 1)
