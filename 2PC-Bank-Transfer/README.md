# 2PC Bank Transfer System

Hệ thống demo mô phỏng **chuyển tiền giữa hai ngân hàng** sử dụng **Two-Phase Commit (2PC)** để đảm bảo tính nhất quán phân tán.

---

## 🏗️ Kiến trúc hệ thống

- **Coordinator** (port 5000): Orchestrator điều phối 2PC
- **Bank A** (port 5001): SQL Server (db `bank_a`)
- **Bank B** (port 5002): PostgreSQL (db `bank_b`)

```
[Client] → [Coordinator] → [Bank A] / [Bank B]
```

---

## ✅ Tính năng chính

- Chuyển tiền giữa 2 ngân hàng với **Two-Phase Commit**
- Đăng ký / đăng nhập / logout
- Xem số dư, rút tiền, chuyển nội bộ
- Trạng thái giao dịch theo `txn_id`
- Health check cho từng service

---

## 🚀 Quickstart

### 1) Cài dependencies
```bash
pip install -r requirements.txt
```

### 2) Chạy dịch vụ (3 terminal)
```bash
python3 coordinator.py
python3 bank_a.py
python3 bank_b.py
```

> Hoặc chạy nhanh: `./run_system.sh`

---

## 📡 API Endpoints

### Coordinator (port 5000)
- `POST /transfer` – khởi tạo chuyển tiền (2PC)
- `GET /status/<txn_id>` – trạng thái giao dịch
- `GET /health` – health check

### Bank A (port 5001) / Bank B (port 5002)
- `POST /register` – đăng ký tài khoản
- `POST /login` – đăng nhập
- `POST /logout` – đăng xuất
- `GET /accounts/<account_number>/info` – thông tin tài khoản
- `GET /accounts/<account_number>/balance` – số dư
- `POST /withdraw` – rút tiền
- `POST /internal/transfer` – chuyển nội bộ (cùng bank)
- `POST /prepare` – 2PC prepare
- `POST /commit` – 2PC commit
- `POST /rollback` – 2PC rollback
- `GET /health` – health check

---

## 🧪 Ví dụ curl

### Đăng ký + đăng nhập
```bash
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123","account_number":"A1001","initial_balance":1000}'

curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}'
```

### Xem số dư
```bash
curl http://localhost:5001/accounts/A1001/balance
```

### Chuyển nội bộ (Bank A)
```bash
curl -X POST http://localhost:5001/internal/transfer \
  -H "Content-Type: application/json" \
  -d '{"from_account":"A1001","to_account":"A1002","amount":100}'
```

### Chuyển xuyên ngân hàng (2PC)
```bash
curl -X POST http://localhost:5000/transfer \
  -H "Content-Type: application/json" \
  -d '{"from_account":"A1001","to_account":"B1001","amount":100}'
```

### Kiểm tra trạng thái giao dịch
```bash
curl http://localhost:5000/status/<txn_id>
```

---

## 📂 Cấu trúc project

```
2PC-Bank-Transfer/
├── coordinator.py        # Coordinator service
├── bank_a.py            # Bank A (SQL Server)
├── bank_b.py            # Bank B (PostgreSQL)
├── logger.py            # Logging
├── requirements.txt     # Dependencies
├── run_system.sh        # Chạy nhanh 3 services
├── test_flask_system.py # Test end-to-end
├── SETUP.md             # Hướng dẫn cài đặt chi tiết
└── README.md            # Tài liệu này
```

---

## 🛠️ Lưu ý

- Bank A/B tự tạo schema khi khởi động nếu thiếu.
- Nếu coordinator tắt giữa chừng, giao dịch có thể ở trạng thái pending; tra cứu với `/status/<txn_id>`.
