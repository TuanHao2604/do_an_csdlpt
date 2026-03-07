# 2PC Bank Transfer System
Hệ thống chuyển tiền ngân hàng với giao thức Two-Phase Commit

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Coordinator   │◄──────────────►│     Bank A      │
│    (Port 5000)  │                │  SQL Server     │
│                 │                │   (Port 5001)   │
└─────────────────┘                └─────────────────┘
         │
         │
         ▼
┌─────────────────┐
│     Bank B      │
│  PostgreSQL     │
│   (Port 5002)   │
└─────────────────┘
```

## 📋 Tính năng

- **Two-Phase Commit Protocol**: Đảm bảo tính nhất quán phân tán
- **Microservices Architecture**: Mỗi bank là một service độc lập
- **Multi-Database**: Bank A dùng SQL Server, Bank B dùng PostgreSQL
- **REST API**: Giao tiếp qua HTTP endpoints
- **Fault Tolerance**: Xử lý lỗi và rollback tự động

## 🚀 Cài đặt và chạy

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Chuẩn bị databases
```bash
# PostgreSQL cho Bank B
sudo systemctl start postgresql
sudo -u postgres createdb bank_b

# SQL Server cho Bank A (Docker)
docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=Hao@DBMS' \
  -p 1433:1433 --name sqlserver \
  -d mcr.microsoft.com/mssql/server:2022-latest

# Tạo database bank_a trong SQL Server
sqlcmd -S localhost -U sa -P 'Hao@DBMS' -Q "CREATE DATABASE bank_a"
```

### 3. Chạy hệ thống
```bash
# Chạy tất cả services cùng lúc
./run_system.sh

# Hoặc chạy từng service riêng biệt:
# Terminal 1: python3 coordinator.py
# Terminal 2: python3 bank_a.py
# Terminal 3: python3 bank_b.py
```

### 4. Test hệ thống
```bash
python3 test_flask_system.py
```

## 📡 API Endpoints

### Coordinator (Port 5000)
- `POST /transfer` - Thực hiện giao dịch chuyển tiền
- `GET /status/<txn_id>` - Kiểm tra trạng thái giao dịch
- `GET /health` - Health check

### Bank A - SQL Server (Port 5001)
- `POST /prepare` - Phase 1: Prepare
- `POST /commit` - Phase 2: Commit
- `POST /rollback` - Rollback transaction
- `GET /balance` - Xem số dư
- `GET /health` - Health check

### Bank B - PostgreSQL (Port 5002)
- `POST /prepare` - Phase 1: Prepare
- `POST /commit` - Phase 2: Commit
- `POST /rollback` - Rollback transaction
- `GET /balance` - Xem số dư
- `GET /health` - Health check

## 🧪 Test giao dịch

```bash
# Chuyển 100 từ Bank A sang Bank B
curl -X POST http://localhost:5000/transfer \
  -H "Content-Type: application/json" \
  -d '{"from_account": "A1001", "to_account": "B1001", "amount": 100}'

# Kiểm tra kết quả
curl http://localhost:5000/status/txn_001
curl http://localhost:5001/balance
curl http://localhost:5002/balance
```

## 📁 Cấu trúc file

```
2PC-Bank-Transfer/
├── coordinator.py      # Coordinator service
├── bank_a.py          # Bank A (SQL Server)
├── bank_b.py          # Bank B (PostgreSQL)
├── logger.py          # Logging utility
├── requirements.txt   # Python dependencies
├── SETUP.md          # Chi tiết setup
├── QUICKSTART.md     # Hướng dẫn nhanh
├── run_system.sh     # Script chạy hệ thống
└── test_flask_system.py # Test script
```

## 🔧 Cấu hình

- **Coordinator**: Port 5000
- **Bank A**: Port 5001, SQL Server
- **Bank B**: Port 5002, PostgreSQL
- **Database**: Tự động tạo bảng khi khởi động

## 🐛 Troubleshooting

Xem file `SETUP.md` để biết chi tiết troubleshooting và cách xử lý lỗi thường gặp.