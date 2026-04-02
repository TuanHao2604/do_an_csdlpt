# BÁO CÁO ĐỒ ÁN MÔN CƠ SỞ DỮ LIỆU PHÂN TÁN

## Đề tài: Hệ thống chuyển tiền liên ngân hàng sử dụng giao thức Two-Phase Commit (2PC)

**Tên ứng dụng:** NovaBank – Hệ thống ngân hàng phân tán

---

## MỤC LỤC

1. [Phân tán vật lý](#1-phân-tán-vật-lý)
2. [Kiểu phân tán](#2-kiểu-phân-tán)
3. [Phân tích Database](#3-phân-tích-database)
4. [Trình bày cách cài đặt](#4-trình-bày-cách-cài-đặt)
5. [Mô tả luồng phân tán](#5-mô-tả-luồng-phân-tán)

---

## 1. PHÂN TÁN VẬT LÝ

### 1.1. Tổng quan kiến trúc vật lý

Hệ thống NovaBank được triển khai theo mô hình **phân tán vật lý (Physical Distribution)** với các node chạy trên các tiến trình (process) và cổng mạng (port) riêng biệt, mô phỏng việc các dịch vụ nằm trên các máy chủ khác nhau.

### 1.2. Sơ đồ phân bố vật lý

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MÁY CHỦ / MÔI TRƯỜNG TRIỂN KHAI                │
│                                                                         │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐      │
│  │   Coordinator    │   │     Bank A       │   │     Bank B       │      │
│  │   (Flask)        │   │     (Flask)      │   │     (Flask)      │      │
│  │   Port: 5000     │   │   Port: 5001     │   │   Port: 5002     │      │
│  │                  │   │                  │   │                  │      │
│  │  - Điều phối 2PC │   │  - Nghiệp vụ    │   │  - Nghiệp vụ    │      │
│  │  - Recovery      │   │    ngân hàng     │   │    ngân hàng     │      │
│  │  - Crash sim     │   │  - Auth/Login    │   │  - Auth/Login    │      │
│  └────────┬─────────┘   └───────┬──────────┘   └───────┬──────────┘      │
│           │                     │                      │                 │
│           │              ┌──────┴──────┐        ┌──────┴──────┐         │
│           │              │  SQL Server  │        │ PostgreSQL  │         │
│           │              │  (Docker)    │        │ (Native)    │         │
│           │              │  Port: 1433  │        │ Port: 15432 │         │
│           │              │  DB: bank_a  │        │ DB: bank_b  │         │
│           │              └─────────────┘        └─────────────┘         │
│           │                                                              │
│  ┌────────┴──────────────────────────────────────────────────────┐      │
│  │                    Frontend Layer (React + Vite)               │      │
│  │                                                                │      │
│  │  ┌──────────────────┐          ┌──────────────────┐           │      │
│  │  │  NovaBank A       │          │  NovaBank B       │           │      │
│  │  │  Port: 3000       │          │  Port: 3001       │           │      │
│  │  │  Proxy → :5001    │          │  Proxy → :5002    │           │      │
│  │  │  Proxy → :5000    │          │  Proxy → :5000    │           │      │
│  │  └──────────────────┘          └──────────────────┘           │      │
│  └────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3. Chi tiết các node vật lý

| Thành phần | Vai trò | Công nghệ | Port | Database |
|---|---|---|---|---|
| **Coordinator** | Điều phối giao dịch 2PC | Flask (Python) | 5000 | In-memory (dict) |
| **Bank A** | Dịch vụ ngân hàng A | Flask (Python) + pyodbc | 5001 | SQL Server (`bank_a`) |
| **Bank B** | Dịch vụ ngân hàng B | Flask (Python) + psycopg2 | 5002 | PostgreSQL (`bank_b`) |
| **NovaBank A** | Giao diện Web Bank A | React + Vite + TailwindCSS | 3000 | — |
| **NovaBank B** | Giao diện Web Bank B | React + Vite + TailwindCSS | 3001 | — |
| **SQL Server** | CSDL cho Bank A | Microsoft SQL Server 2022 (Docker) | 1433 | `bank_a` |
| **PostgreSQL** | CSDL cho Bank B | PostgreSQL | 15432 | `bank_b` |

### 1.4. Đặc điểm phân tán vật lý

- **Đa hệ quản trị CSDL (Heterogeneous DBMS):** Hệ thống sử dụng đồng thời SQL Server và PostgreSQL — hai DBMS khác nhau hoàn toàn, thể hiện tính phân tán không đồng nhất (heterogeneous distributed database).
- **Giao tiếp qua mạng HTTP/REST:** Tất cả các node giao tiếp thông qua giao thức HTTP (RESTful API), cho phép triển khai trên các máy chủ vật lý khác nhau chỉ cần thay đổi URL.
- **Phân tách tiến trình:** Mỗi thành phần chạy trên một tiến trình (process) riêng biệt, đảm bảo tính độc lập và khả năng chịu lỗi (fault tolerance).
- **Có thể mở rộng:** Kiến trúc cho phép thêm Bank C, Bank D,... bằng cách triển khai thêm các instance Flask kết nối tới DBMS tương ứng.

---

## 2. KIỂU PHÂN TÁN

### 2.1. Phân loại kiểu phân tán được sử dụng

Hệ thống NovaBank áp dụng kiểu **phân tán ngang (Horizontal Fragmentation / Horizontal Partitioning)**.

### 2.2. Giải thích chi tiết

#### 2.2.1. Phân tán ngang (Horizontal Fragmentation)

Dữ liệu cùng cấu trúc (schema) được **chia theo hàng (record)** và lưu trữ tại các site khác nhau dựa trên **tiền tố số tài khoản**:

```
Bảng logic: ACCOUNTS (toàn hệ thống)
┌──────────────────┬──────────┬─────────┐
│ account_number   │ balance  │ currency│
├──────────────────┼──────────┼─────────┤
│ A1001 (Alice)    │ 1000.00  │ USD     │  ← Lưu tại Bank A (SQL Server)
│ A1002 (Bob)      │ 1000.00  │ USD     │  ← Lưu tại Bank A (SQL Server)
│ B1001 (Charlie)  │ 1000.00  │ USD     │  ← Lưu tại Bank B (PostgreSQL)
│ B1002 (Dave)     │ 1000.00  │ USD     │  ← Lưu tại Bank B (PostgreSQL)
└──────────────────┴──────────┴─────────┘
```

**Điều kiện phân tán:**
- Tài khoản có prefix **`A`** → thuộc **Bank A** (SQL Server, site 1)
- Tài khoản có prefix **`B`** → thuộc **Bank B** (PostgreSQL, site 2)

Code xác định site trong `coordinator.py`:

```python
def _get_bank_url(account_number: str) -> str | None:
    if account_number.startswith('A'):
        return BANK_A_URL   # http://localhost:5001
    if account_number.startswith('B'):
        return BANK_B_URL   # http://localhost:5002
    return None
```

#### 2.2.2. Các bảng được phân tán ngang

Cả 4 bảng dữ liệu đều được phân tán ngang theo cùng tiêu chí:

| Bảng | Bank A (SQL Server) | Bank B (PostgreSQL) | Tiêu chí phân tán |
|---|---|---|---|
| `customers` | alice, bob | charlie, dave | Theo ngân hàng đăng ký |
| `accounts` | A1001, A1002 | B1001, B1002 | Prefix `A` / `B` |
| `transactions` | Giao dịch của A10xx | Giao dịch của B10xx | Theo account_number |
| `pending_txns` | Txn liên quan Bank A | Txn liên quan Bank B | Theo role trong 2PC |

#### 2.2.3. Tại sao không phải phân tán dọc?

- **Phân tán dọc** (Vertical Fragmentation) chia bảng theo **cột** (column), mỗi site lưu một tập cột khác nhau
- Trong hệ thống này, **tất cả các cột đều được lưu đầy đủ** tại mỗi site — chỉ khác nhau về **tập bản ghi** (rows)
- → Đây chính xác là **phân tán ngang**

#### 2.2.4. Tính chất phân tán

| Tính chất | Đánh giá | Giải thích |
|---|---|---|
| **Completeness** (Đầy đủ) | ✅ | Mọi bản ghi đều thuộc ít nhất 1 fragment |
| **Reconstruction** (Tái tạo) | ✅ | `UNION` hai fragment cho ra toàn bộ dữ liệu gốc |
| **Disjointness** (Không giao) | ✅ | Tài khoản `A*` chỉ nằm ở Bank A, `B*` chỉ nằm ở Bank B |

---

## 3. PHÂN TÍCH DATABASE

### 3.1. Schema Database — Bank A (SQL Server)

```sql
-- Bảng khách hàng
CREATE TABLE dbo.customers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(100) UNIQUE NOT NULL,
    password NVARCHAR(256) NOT NULL,       -- SHA-256 hash
    full_name NVARCHAR(200),
    email NVARCHAR(200),
    phone NVARCHAR(50)
);

-- Bảng tài khoản ngân hàng
CREATE TABLE dbo.accounts (
    account_number NVARCHAR(50) PRIMARY KEY,  -- Format: A1001, A1002...
    customer_id INT NOT NULL REFERENCES dbo.customers(id),
    balance DECIMAL(18,2) NOT NULL DEFAULT 0,
    currency NVARCHAR(10) NOT NULL DEFAULT 'USD'
);

-- Bảng lịch sử giao dịch
CREATE TABLE dbo.transactions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    account_number NVARCHAR(50) NOT NULL,
    type NVARCHAR(50) NOT NULL,           -- 'transfer_out', 'transfer_in', 'withdraw', 'refund_in'
    amount DECIMAL(18,2) NOT NULL,
    counterpart NVARCHAR(50),             -- Tài khoản đối tác
    status NVARCHAR(50),                  -- 'success'
    created_at DATETIME NOT NULL DEFAULT GETDATE()
);

-- Bảng giao dịch đang chờ (dùng cho 2PC)
CREATE TABLE dbo.pending_txns (
    txn_id NVARCHAR(100) PRIMARY KEY,     -- UUID từ Coordinator
    source_account NVARCHAR(50),
    dest_account NVARCHAR(50),
    amount DECIMAL(18,2) NOT NULL,
    type NVARCHAR(20) NOT NULL,           -- 'debit' hoặc 'credit'
    created_at DATETIME NOT NULL DEFAULT GETDATE()
);
```

### 3.2. Schema Database — Bank B (PostgreSQL)

```sql
-- Bảng khách hàng
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,                -- SHA-256 hash
    full_name TEXT,
    email TEXT,
    phone TEXT
);

-- Bảng tài khoản ngân hàng
CREATE TABLE accounts (
    account_number TEXT PRIMARY KEY,       -- Format: B1001, B1002...
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD'
);

-- Bảng lịch sử giao dịch
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_number TEXT NOT NULL,
    type TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    counterpart TEXT,
    status TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bảng giao dịch đang chờ (dùng cho 2PC)
CREATE TABLE pending_txns (
    txn_id TEXT PRIMARY KEY,
    source_account TEXT,
    dest_account TEXT,
    amount NUMERIC(18,2) NOT NULL,
    type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.3. So sánh schema giữa hai DBMS

| Thuộc tính | SQL Server (Bank A) | PostgreSQL (Bank B) |
|---|---|---|
| Kiểu chuỗi | `NVARCHAR` | `TEXT` |
| Auto-increment | `IDENTITY(1,1)` | `SERIAL` |
| Kiểu số thực | `DECIMAL(18,2)` | `NUMERIC(18,2)` |
| Timestamp | `DATETIME` + `GETDATE()` | `TIMESTAMPTZ` + `NOW()` |
| Kết nối Python | `pyodbc` (ODBC Driver 18) | `psycopg2` |
| Trả về ID insert | `OUTPUT INSERTED.id` | `RETURNING id` |

### 3.4. Dữ liệu mẫu (Seed Data)

| Bank | Username | Password | Account Number | Balance | Currency |
|---|---|---|---|---|---|
| **Bank A** | alice | alice123 | A1001 | 1,000.00 | USD |
| **Bank A** | bob | bob123 | A1002 | 1,000.00 | USD |
| **Bank B** | charlie | charlie123 | B1001 | 1,000.00 | USD |
| **Bank B** | dave | dave123 | B1002 | 1,000.00 | USD |

### 3.5. Mô hình quan hệ (ERD)

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  customers   │ 1    N  │    accounts       │ 1    N  │  transactions    │
├──────────────┤─────────├──────────────────┤─────────├──────────────────┤
│ id (PK)      │         │ account_number(PK)│         │ id (PK)          │
│ username (U) │         │ customer_id (FK)  │         │ account_number   │
│ password     │         │ balance           │         │ type             │
│ full_name    │         │ currency          │         │ amount           │
│ email        │         └──────────────────┘         │ counterpart      │
│ phone        │                                       │ status           │
└──────────────┘                                       │ created_at       │
                                                       └──────────────────┘

                         ┌──────────────────┐
                         │  pending_txns    │  (Bảng tạm cho 2PC)
                         ├──────────────────┤
                         │ txn_id (PK)      │  ← UUID từ Coordinator
                         │ source_account   │
                         │ dest_account     │
                         │ amount           │
                         │ type             │  ← 'debit' / 'credit'
                         │ created_at       │
                         └──────────────────┘
```

### 3.6. Global Schema (Schema toàn cục)

Mặc dù dữ liệu được phân tán trên 2 DBMS khác nhau, **schema logic toàn cục** vẫn thống nhất. Coordinator không lưu trữ dữ liệu vĩnh viễn mà chỉ giữ trạng thái giao dịch tạm thời trong bộ nhớ (in-memory dictionary `txn_status`).

---

## 4. TRÌNH BÀY CÁCH CÀI ĐẶT

### 4.1. Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| Docker | 20+ |
| PostgreSQL | 14+ |
| SQL Server | 2019+ (qua Docker) |

### 4.2. Bước 1: Cài đặt Database

#### 4.2.1. SQL Server cho Bank A (sử dụng Docker)

```bash
# Kéo image và chạy SQL Server container
docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=Hao@DBMS2026' \
  -p 1433:1433 --name sqlserver \
  -d mcr.microsoft.com/mssql/server:2022-latest

# Đợi SQL Server khởi động (khoảng 30 giây)
sleep 30

# Cài đặt ODBC Driver 18 cho SQL Server (Ubuntu/Debian)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list)"
sudo apt-get update
sudo apt-get install -y msodbcsql18
```

> **Lưu ý:** Database `bank_a` sẽ được tự động tạo khi Bank A khởi động lần đầu (trong hàm `init_db()`).

#### 4.2.2. PostgreSQL cho Bank B

```bash
# Cài đặt PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Khởi động dịch vụ
sudo systemctl start postgresql

# PostgreSQL chạy trên port 15432 (cấu hình trong bank_b.py)
```

> **Lưu ý:** Database `bank_b` sẽ được tự động tạo khi Bank B khởi động lần đầu (trong hàm `init_db()`).

### 4.3. Bước 2: Cài đặt Backend (Python)

```bash
# Di chuyển vào thư mục backend
cd 2PC-Bank-Transfer/

# Cài đặt tất cả thư viện Python cần thiết
pip install -r requirements.txt
```

**Nội dung `requirements.txt`:**
- `Flask` — Web framework
- `flask-cors` — Cho phép Cross-Origin requests
- `requests` — HTTP client cho giao tiếp giữa các service
- `pyodbc` — Kết nối SQL Server (Bank A)
- `psycopg2-binary` — Kết nối PostgreSQL (Bank B)

### 4.4. Bước 3: Khởi chạy Backend Services

Mở **3 terminal riêng biệt**, mỗi terminal chạy 1 service:

```bash
# Terminal 1 — Coordinator (Port 5000)
python3 coordinator.py

# Terminal 2 — Bank A (Port 5001)
python3 bank_a.py

# Terminal 3 — Bank B (Port 5002)
python3 bank_b.py
```

**Hoặc chạy nhanh tất cả bằng script:**

```bash
./run_system.sh
```

### 4.5. Bước 4: Cài đặt và chạy Frontend

```bash
# Frontend cho Bank A (Port 3000)
cd novabank/
npm install
npm run dev

# Frontend cho Bank B (Port 3001) — mở terminal mới
cd novabank_b/
npm install
npm run dev
```

### 4.6. Bước 5: Kiểm tra hệ thống

```bash
# Health check tất cả services
curl http://localhost:5000/health   # Coordinator
curl http://localhost:5001/health   # Bank A
curl http://localhost:5002/health   # Bank B
```

**Kết quả mong đợi:**
```json
{"status": "healthy", "service": "Coordinator", ...}
{"status": "healthy", "service": "BankA", "database": "SQLServer"}
{"status": "healthy", "service": "BankB", "database": "PostgreSQL"}
```

### 4.7. Tổng quan các port

| Service | Port | URL |
|---|---|---|
| Coordinator | 5000 | http://localhost:5000 |
| Bank A (Backend) | 5001 | http://localhost:5001 |
| Bank B (Backend) | 5002 | http://localhost:5002 |
| NovaBank A (Frontend) | 3000 | http://localhost:3000 |
| NovaBank B (Frontend) | 3001 | http://localhost:3001 |
| SQL Server | 1433 | localhost:1433 |
| PostgreSQL | 15432 | localhost:15432 |

---

## 5. MÔ TẢ LUỒNG PHÂN TÁN

### 5.1. Luồng chuyển tiền liên ngân hàng (Two-Phase Commit)

Đây là luồng chính thể hiện tính phân tán của hệ thống. Khi người dùng chuyển tiền từ **Bank A** sang **Bank B**, giao thức **2PC (Two-Phase Commit)** được sử dụng.

#### Sequence Diagram

```
  Client          Coordinator           Bank A              Bank B
    │                  │                  │                    │
    │  POST /transfer  │                  │                    │
    │  {A1001→B1001,   │                  │                    │
    │   amount: 100}   │                  │                    │
    │─────────────────>│                  │                    │
    │                  │                  │                    │
    │                  │ ═══════════════════════════════════   │
    │                  │  PHASE 1: PREPARE (Bỏ phiếu)         │
    │                  │ ═══════════════════════════════════   │
    │                  │                  │                    │
    │                  │  POST /prepare   │                    │
    │                  │  {type: "debit", │                    │
    │                  │   amount: 100}   │                    │
    │                  │─────────────────>│                    │
    │                  │                  │ Kiểm tra số dư     │
    │                  │                  │ Trừ 100 (hold)     │
    │                  │                  │ Ghi pending_txns   │
    │                  │  {status:"ready"}│                    │
    │                  │<─────────────────│                    │
    │                  │                  │                    │
    │                  │  POST /prepare   │                    │
    │                  │  {type: "credit",│                    │
    │                  │   amount: 100}   │                    │
    │                  │─────────────────────────────────────>│
    │                  │                  │                    │ Kiểm tra TK đích
    │                  │                  │                    │ Ghi pending_txns
    │                  │                  │  {status:"ready"}  │
    │                  │<─────────────────────────────────────│
    │                  │                  │                    │
    │                  │ ═══════════════════════════════════   │
    │                  │  PHASE 2: COMMIT (Xác nhận)           │
    │                  │ ═══════════════════════════════════   │
    │                  │                  │                    │
    │                  │  POST /commit    │                    │
    │                  │  {txn_id: "..."}  │                    │
    │                  │─────────────────>│                    │
    │                  │                  │ Xóa pending_txns   │
    │                  │ {status:"committed"}                  │
    │                  │<─────────────────│                    │
    │                  │                  │                    │
    │                  │  POST /commit    │                    │
    │                  │  {txn_id: "..."}  │                    │
    │                  │─────────────────────────────────────>│
    │                  │                  │                    │ Cộng 100 vào TK
    │                  │                  │                    │ Ghi transactions
    │                  │                  │                    │ Xóa pending_txns
    │                  │                  │ {status:"committed"}│
    │                  │<─────────────────────────────────────│
    │                  │                  │                    │
    │ {status:         │                  │                    │
    │  "committed"}    │                  │                    │
    │<─────────────────│                  │                    │
```

### 5.2. Chi tiết từng phase

#### Phase 1: PREPARE (Giai đoạn chuẩn bị / Bỏ phiếu)

| Bước | Thành phần | Hành động | Kết quả |
|---|---|---|---|
| 1 | **Coordinator** | Tạo `txn_id` (UUID), ghi nhận giao dịch | `txn_status[txn_id] = {status: 'preparing'}` |
| 2 | **Coordinator → Bank A** | Gửi `POST /prepare` với `type: "debit"` | Yêu cầu Bank A chuẩn bị trừ tiền |
| 3 | **Bank A** | Kiểm tra số dư ≥ amount | Nếu đủ → tiếp tục; nếu không → `abort` |
| 4 | **Bank A** | Trừ tiền tạm (hold), ghi vào `pending_txns` | Trả về `{status: "ready"}` |
| 5 | **Coordinator → Bank B** | Gửi `POST /prepare` với `type: "credit"` | Yêu cầu Bank B chuẩn bị nhận tiền |
| 6 | **Bank B** | Kiểm tra tài khoản đích tồn tại | Ghi vào `pending_txns` |
| 7 | **Bank B** | Trả kết quả | `{status: "ready"}` |

#### Phase 2: COMMIT (Giai đoạn xác nhận)

| Bước | Thành phần | Hành động | Kết quả |
|---|---|---|---|
| 8 | **Coordinator** | Kiểm tra cả 2 Bank đều `ready` | Quyết định `GLOBAL COMMIT` |
| 9 | **Coordinator → Bank A** | Gửi `POST /commit` | Bank A xóa `pending_txns` (tiền đã trừ sẵn) |
| 10 | **Coordinator → Bank B** | Gửi `POST /commit` | Bank B cộng tiền + ghi `transactions` + xóa `pending_txns` |
| 11 | **Coordinator** | Cập nhật trạng thái | `txn_status[txn_id] = {status: 'committed'}` |

### 5.3. Luồng ABORT (Hủy giao dịch)

Khi **bất kỳ Bank nào** trả về `abort` trong Phase 1:

```
Coordinator                Bank A              Bank B
    │                        │                    │
    │  PREPARE failed!       │                    │
    │  (1 hoặc 2 bank abort) │                    │
    │                        │                    │
    │   POST /rollback       │                    │
    │───────────────────────>│                    │
    │                        │ Hoàn lại tiền      │
    │                        │ Xóa pending_txns   │
    │                        │                    │
    │   POST /rollback       │                    │
    │───────────────────────────────────────────>│
    │                        │                    │ Xóa pending_txns
    │                        │                    │
    │   status = "aborted"   │                    │
```

### 5.4. Luồng giả lập sự cố (Crash Simulation)

Hệ thống hỗ trợ giả lập 2 loại sự cố:

#### 5.4.1. Crash sau Phase 1 (`after_prepare`)

```
Coordinator           Bank A            Bank B
    │                   │                  │
    │  PREPARE OK ✓     │                  │
    │                   │                  │
    │  ⚡ CRASH!         │                  │
    │  (Mất kết nối)    │                  │
    │                   │                  │
    │  Tự động ROLLBACK │                  │
    │──────────────────>│                  │
    │──────────────────────────────────── >│
    │                   │ Hoàn tiền        │
```

#### 5.4.2. Crash giữa 2 lệnh commit (`after_source_commit`)

```
Coordinator           Bank A            Bank B
    │                   │                  │
    │  COMMIT Bank A ✓  │                  │
    │──────────────────>│                  │
    │                   │ Done             │
    │  ⚡ DELAY/CRASH!   │                  │
    │  (15 giây)        │                  │
    │                   │                  │
    │  COMMIT Bank B    │                  │
    │────────────────────────────────────>│
    │                   │                  │ Done
```

### 5.5. Luồng Recovery (Phục hồi tự động)

Coordinator chạy một **Recovery Worker Thread** nền, kiểm tra mỗi 10 giây:

```
Recovery Worker (mỗi 10s)
    │
    ├── GET /pending  →  Bank A
    │   └── Lấy danh sách giao dịch đang treo
    │
    ├── GET /pending  →  Bank B
    │   └── Lấy danh sách giao dịch đang treo
    │
    ├── Với mỗi giao dịch treo:
    │   ├── Nếu có quyết định (committed/aborted) → Thực hiện lại
    │   └── Nếu không có quyết định (hung > 30s) → Auto ROLLBACK
    │
    └── Ghi log recovery
```

Ngoài ra, khi mỗi Bank khởi động, hàm `recover_pending()` sẽ:
1. Đọc tất cả `pending_txns` trong database
2. Hỏi Coordinator trạng thái mỗi `txn_id`
3. Nếu `committed` → hoàn tất giao dịch
4. Nếu `aborted` hoặc `not found` → rollback

### 5.6. Luồng chuyển tiền nội bộ (Internal Transfer)

Khi cả 2 tài khoản cùng thuộc một Bank, **không cần 2PC**:

```
Client → Coordinator → Bank A  (internal/transfer)
                        │
                        ├── Kiểm tra số dư tài khoản nguồn
                        ├── Trừ tiền tài khoản nguồn
                        ├── Cộng tiền tài khoản đích
                        ├── Ghi 2 bản ghi transactions
                        └── Commit trong 1 transaction duy nhất
```

### 5.7. Luồng Frontend ↔ Backend

Frontend sử dụng **Vite Proxy** để định tuyến request:

```
NovaBank A (port 3000)
    │
    ├── /api/*         →  Proxy tới Bank A (port 5001)
    │   └── /api/login  →  http://localhost:5001/login
    │   └── /api/accounts  →  http://localhost:5001/accounts
    │
    └── /coordinator/* →  Proxy tới Coordinator (port 5000)
        └── /coordinator/transfer  →  http://localhost:5000/transfer
        └── /coordinator/simulate-crash  →  http://localhost:5000/simulate-crash
```

---

## PHỤ LỤC

### A. Danh sách API Endpoints

#### Coordinator (port 5000)

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/transfer` | Chuyển tiền liên ngân hàng (2PC) |
| GET | `/status/<txn_id>` | Trạng thái giao dịch |
| GET | `/transactions` | Danh sách tất cả giao dịch |
| GET | `/health` | Health check |
| POST | `/simulate-crash` | Bật/tắt giả lập sự cố |
| GET | `/simulate-crash` | Xem cấu hình crash |

#### Bank A (port 5001) / Bank B (port 5002)

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/register` | Đăng ký tài khoản |
| POST | `/login` | Đăng nhập |
| POST | `/logout` | Đăng xuất |
| GET | `/accounts` | Danh sách tài khoản |
| GET | `/accounts/<acc>/info` | Thông tin tài khoản |
| GET | `/accounts/<acc>/balance` | Số dư |
| GET | `/transactions/<acc>` | Lịch sử giao dịch |
| POST | `/withdraw` | Rút tiền |
| POST | `/internal/transfer` | Chuyển nội bộ |
| POST | `/prepare` | 2PC — Phase 1 |
| POST | `/commit` | 2PC — Phase 2 (xác nhận) |
| POST | `/rollback` | 2PC — Rollback |
| GET | `/pending` | Giao dịch đang treo |
| GET | `/health` | Health check |

### B. Cấu trúc thư mục dự án

```
CSDLPT/
├── 2PC-Bank-Transfer/          # Backend services
│   ├── coordinator.py          # Coordinator — Điều phối 2PC
│   ├── bank_a.py               # Bank A — SQL Server
│   ├── bank_b.py               # Bank B — PostgreSQL
│   ├── logger.py               # Module logging dùng chung
│   ├── requirements.txt        # Python dependencies
│   ├── run_system.sh           # Script chạy nhanh 3 services
│   ├── test_2pc_full.py        # Test end-to-end
│   ├── test_conn.py            # Test kết nối database
│   ├── SETUP.md                # Hướng dẫn cài đặt
│   ├── QUICKSTART.md           # Hướng dẫn nhanh
│   └── README.md               # Tài liệu tổng quan
│
├── novabank/                   # Frontend cho Bank A
│   ├── src/
│   │   ├── App.tsx             # Root component
│   │   ├── api.ts              # API helper
│   │   ├── components/         # UI components
│   │   │   ├── Login.tsx       # Màn hình đăng nhập
│   │   │   ├── Home.tsx        # Trang chủ
│   │   │   ├── Transfer.tsx    # Chuyển tiền (2PC + internal)
│   │   │   ├── History.tsx     # Lịch sử giao dịch
│   │   │   └── ...
│   │   └── main.tsx
│   ├── vite.config.ts          # Cấu hình Vite + Proxy
│   └── package.json
│
└── novabank_b/                 # Frontend cho Bank B
    ├── src/                    # Tương tự novabank
    ├── vite.config.ts          # Proxy → Bank B (5002)
    └── package.json
```

### C. Công nghệ sử dụng

| Layer | Công nghệ | Vai trò |
|---|---|---|
| Frontend | React, TypeScript, Vite, TailwindCSS | Giao diện người dùng |
| Backend | Python, Flask, Flask-CORS | REST API server |
| Database 1 | Microsoft SQL Server 2022 | CSDL cho Bank A |
| Database 2 | PostgreSQL 14+ | CSDL cho Bank B |
| Containerization | Docker | Chạy SQL Server |
| Protocol | HTTP/REST, 2PC | Giao tiếp phân tán |
| Logging | Python logging, JSON event logs | Theo dõi & gỡ lỗi |

---


