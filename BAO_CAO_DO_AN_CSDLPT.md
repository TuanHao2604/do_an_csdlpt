# BÁO CÁO ĐỒ ÁN MÔN CƠ SỞ DỮ LIỆU PHÂN TÁN

## Đề tài: Hệ thống chuyển tiền liên ngân hàng sử dụng giao thức Two-Phase Commit (2PC)

**Tên ứng dụng:** NovaBank – Hệ thống ngân hàng phân tán  
**Sinh viên thực hiện:** Nguyễn Tuấn Hào  
**Ngày nộp:** Tháng 4/2026

---

## MỤC LỤC

1. [Phân tán vật lý — Chi tiết kiến trúc & tác dụng](#1-phân-tán-vật-lý--chi-tiết-kiến-trúc--tác-dụng)
2. [Phân tán ngang — Nguyên lý, tác dụng & áp dụng](#2-phân-tán-ngang--nguyên-lý-tác-dụng--áp-dụng)
3. [Phân tích Database](#3-phân-tích-database)
4. [Trình bày cách cài đặt](#4-trình-bày-cách-cài-đặt)
5. [Mô tả luồng phân tán](#5-mô-tả-luồng-phân-tán)

---

## 1. PHÂN TÁN VẬT LÝ — CHI TIẾT KIẾN TRÚC & TÁC DỤNG

### 1.1. Khái niệm phân tán vật lý (Physical Distribution)

Phân tán vật lý là kiểu triển khai trong đó **dữ liệu và dịch vụ xử lý được đặt trên nhiều node (máy chủ/tiến trình) khác nhau**, giao tiếp qua mạng. Mỗi node hoạt động **độc lập**, có bộ nhớ riêng, hệ quản trị CSDL riêng, và có thể bị lỗi mà **không ảnh hưởng trực tiếp** đến các node khác.

### 1.2. Tác dụng của phân tán vật lý trong hệ thống NovaBank

| Tác dụng | Giải thích cụ thể trong NovaBank |
|---|---|
| **Độ tin cậy (Reliability)** | Nếu Bank A (SQL Server) gặp sự cố, Bank B (PostgreSQL) vẫn hoạt động bình thường. Giao dịch nội bộ của Bank B không bị ảnh hưởng. |
| **Khả năng mở rộng (Scalability)** | Có thể thêm Bank C, Bank D… bằng cách triển khai thêm Flask instance + DBMS mới, chỉ cần đăng ký URL với Coordinator. |
| **Hiệu suất (Performance)** | Mỗi ngân hàng xử lý truy vấn trên DBMS riêng, giảm tải I/O. Truy vấn cục bộ (local query) không cần đi qua mạng. |
| **Tự trị địa phương (Local Autonomy)** | Mỗi Bank tự quản lý schema, seed data, auth, và nghiệp vụ nội bộ mà không phụ thuộc node khác. |
| **Phản ánh thực tế (Real-world Modeling)** | Mô phỏng đúng thực tế — mỗi ngân hàng là một tổ chức độc lập với hạ tầng CNTT riêng biệt. |
| **Khả năng chịu lỗi (Fault Tolerance)** | Hệ thống có Recovery Worker tự động phát hiện và phục hồi giao dịch treo khi một node gặp sự cố. |

### 1.3. Sơ đồ kiến trúc vật lý

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HỆ THỐNG NOVABANK — KIẾN TRÚC VẬT LÝ                    │
│                                                                             │
│  ┌───────────────────┐                                                      │
│  │    Coordinator     │ ◄── Bộ não điều phối: KHÔNG lưu dữ liệu vĩnh viễn  │
│  │    Flask :5000     │     Chỉ giữ txn_status{} trong RAM                  │
│  │                    │     + Recovery Worker Thread (mỗi 10s)               │
│  └─────────┬──────────┘                                                     │
│        HTTP│REST                                                            │
│    ┌───────┴────────┐                                                       │
│    │                │                                                       │
│  ┌─▼──────────┐  ┌──▼─────────┐                                            │
│  │  Bank A     │  │  Bank B     │                                            │
│  │  Flask:5001 │  │  Flask:5002 │                                            │
│  │  pyodbc     │  │  psycopg2   │                                            │
│  └─────┬───────┘  └──────┬──────┘                                            │
│        │                 │                                                   │
│  ┌─────▼───────┐  ┌──────▼──────┐                                           │
│  │ SQL Server   │  │ PostgreSQL  │  ◄── Hai DBMS khác hãng (Heterogeneous)  │
│  │ Docker:1433  │  │ Native:15432│                                           │
│  │ DB: bank_a   │  │ DB: bank_b  │                                           │
│  └─────────────┘  └─────────────┘                                           │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                                 │
│  │ NovaBank A (Web)  │  │ NovaBank B (Web)  │  ◄── Frontend Layer           │
│  │ React+Vite :3000  │  │ React+Vite :3001  │                               │
│  │ Proxy→:5001,:5000 │  │ Proxy→:5002,:5000 │                               │
│  └──────────────────┘  └──────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.4. Bảng phân bố node vật lý

| Thành phần | Vai trò | Công nghệ | Port | Database Engine |
|---|---|---|---|---|
| **Coordinator** | Điều phối 2PC, Recovery | Flask (Python) | 5000 | In-memory (`dict`) |
| **Bank A** | Nghiệp vụ ngân hàng A | Flask + `pyodbc` | 5001 | SQL Server 2022 |
| **Bank B** | Nghiệp vụ ngân hàng B | Flask + `psycopg2` | 5002 | PostgreSQL 14+ |
| **NovaBank A** | Giao diện Web Bank A | React + Vite + Tailwind | 3000 | — |
| **NovaBank B** | Giao diện Web Bank B | React + Vite + Tailwind | 3001 | — |

### 1.5. Đặc điểm nổi bật

- **Heterogeneous DBMS (Đa hệ QTCSDL):** SQL Server ≠ PostgreSQL → chứng minh khả năng tích hợp hệ thống không đồng nhất.
- **Giao tiếp RESTful:** Tất cả node giao tiếp qua HTTP JSON → dễ dàng chuyển sang triển khai multi-server thực tế chỉ cần thay đổi URL.
- **Phân tách tiến trình:** 5 tiến trình (3 backend + 2 frontend) chạy trên 7 port khác nhau.

---

## 2. PHÂN TÁN NGANG — NGUYÊN LÝ, TÁC DỤNG & ÁP DỤNG

### 2.1. Khái niệm phân tán ngang (Horizontal Fragmentation)

Phân tán ngang là kỹ thuật chia một bảng (relation) thành nhiều **fragment theo hàng** (tuple). Mỗi fragment chứa một tập con các bản ghi thỏa mãn một **điều kiện chọn (selection predicate)**, được lưu tại các site khác nhau.

**Công thức toán học:**

```
R = σ(p₁)(R) ∪ σ(p₂)(R) ∪ ... ∪ σ(pₙ)(R)
```

Trong đó `σ(pᵢ)` là phép chọn với điều kiện `pᵢ`, và các `pᵢ` đôi một loại trừ nhau.

### 2.2. Tác dụng của phân tán ngang

| Tác dụng | Giải thích |
|---|---|
| **Tăng hiệu suất truy vấn cục bộ** | Mỗi site chỉ lưu dữ liệu liên quan → truy vấn nhanh, không quét toàn bộ bảng toàn cục. |
| **Giảm lưu lượng mạng** | 90%+ thao tác là cục bộ (xem số dư, lịch sử giao dịch) → không truyền dữ liệu qua mạng. |
| **Tăng tính song song** | Nhiều site xử lý đồng thời mà không tranh chấp tài nguyên (lock, I/O). |
| **Tăng tính sẵn sàng** | Một site lỗi → chỉ mất dữ liệu fragment đó, các fragment khác vẫn phục vụ bình thường. |
| **Phản ánh cấu trúc tổ chức** | Mỗi ngân hàng chỉ quản lý khách hàng của mình — đúng thực tế nghiệp vụ. |
| **Bảo mật dữ liệu** | Bank A không thể truy cập trực tiếp dữ liệu khách hàng của Bank B, đảm bảo quyền riêng tư. |

### 2.3. Áp dụng trong NovaBank

#### 2.3.1. Tiêu chí phân tán: Prefix số tài khoản

```
Fragment 1 (Bank A — SQL Server):  σ(account_number LIKE 'A%')
Fragment 2 (Bank B — PostgreSQL):  σ(account_number LIKE 'B%')
```

Code thực tế trong `coordinator.py`:

```python
def _get_bank_url(account_number: str) -> str | None:
    if account_number.startswith('A'):
        return BANK_A_URL   # http://localhost:5001 → SQL Server
    if account_number.startswith('B'):
        return BANK_B_URL   # http://localhost:5002 → PostgreSQL
    return None
```

#### 2.3.2. Minh họa phân tán ngang

```
                    BẢNG LOGIC TOÀN CỤC: accounts
    ┌──────────────────┬──────────┬──────────┬─────────┐
    │ account_number   │ cust_id  │ balance  │ currency│
    ├──────────────────┼──────────┼──────────┼─────────┤
    │ A1001 (Alice)    │ 1        │ 1000.00  │ USD     │ ─┐
    │ A1002 (Bob)      │ 2        │ 1000.00  │ USD     │ ─┤ Fragment 1
    ├──────────────────┼──────────┼──────────┼─────────┤  │ → Bank A
    │ B1001 (Charlie)  │ 1        │ 1000.00  │ USD     │ ─┤ (SQL Server)
    │ B1002 (Dave)     │ 2        │ 1000.00  │ USD     │ ─┘
    └──────────────────┴──────────┴──────────┴─────────┘
                                                          Fragment 2
                                                          → Bank B
                                                          (PostgreSQL)
```

#### 2.3.3. Tất cả 4 bảng đều phân tán ngang

| Bảng | Fragment tại Bank A | Fragment tại Bank B | Điều kiện phân tán |
|---|---|---|---|
| `customers` | alice, bob | charlie, dave | Theo ngân hàng đăng ký |
| `accounts` | A1001, A1002 | B1001, B1002 | `account_number LIKE 'A%'` / `'B%'` |
| `transactions` | Giao dịch của A10xx | Giao dịch của B10xx | Theo `account_number` |
| `pending_txns` | Pending liên quan Bank A | Pending liên quan Bank B | Theo vai trò trong 2PC |

#### 2.3.4. Kiểm chứng 3 tính chất bắt buộc

| Tính chất | Trạng thái | Chứng minh |
|---|---|---|
| **Completeness** (Đầy đủ) | ✅ | Mọi tài khoản đều bắt đầu bằng `A` hoặc `B` → luôn thuộc 1 fragment |
| **Reconstruction** (Tái tạo) | ✅ | `SELECT * FROM bank_a.accounts UNION SELECT * FROM bank_b.accounts` = toàn bộ dữ liệu |
| **Disjointness** (Không giao) | ✅ | Prefix `A` và `B` loại trừ nhau → không có bản ghi nào trùng lặp |

#### 2.3.5. Tại sao chọn phân tán ngang thay vì phân tán dọc?

- **Phân tán dọc (Vertical):** Chia bảng theo **cột**, mỗi site lưu một nhóm cột khác nhau + khóa chính. Phù hợp khi các nhóm cột được truy cập bởi các ứng dụng khác nhau.
- **Trong NovaBank:** Mỗi bank cần **tất cả các cột** (số dư, tên, email…) để phục vụ nghiệp vụ. Chỉ khác nhau về **tập khách hàng/tài khoản** → **phân tán ngang** là phương án duy nhất hợp lý.

---

## 3. PHÂN TÍCH DATABASE

### 3.1. Schema — Bank A (SQL Server)

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
    type NVARCHAR(50) NOT NULL,           -- 'transfer_out','transfer_in','withdraw','refund_in'
    amount DECIMAL(18,2) NOT NULL,
    counterpart NVARCHAR(50),             -- Tài khoản đối tác
    status NVARCHAR(50),                  -- 'success'
    created_at DATETIME NOT NULL DEFAULT GETDATE()
);

-- Bảng giao dịch đang chờ xử lý (phục vụ 2PC)
CREATE TABLE dbo.pending_txns (
    txn_id NVARCHAR(100) PRIMARY KEY,     -- UUID từ Coordinator
    source_account NVARCHAR(50),
    dest_account NVARCHAR(50),
    amount DECIMAL(18,2) NOT NULL,
    type NVARCHAR(20) NOT NULL,           -- 'debit' hoặc 'credit'
    created_at DATETIME NOT NULL DEFAULT GETDATE()
);
```

### 3.2. Schema — Bank B (PostgreSQL)

```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT, email TEXT, phone TEXT
);

CREATE TABLE accounts (
    account_number TEXT PRIMARY KEY,       -- Format: B1001, B1002...
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD'
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_number TEXT NOT NULL,
    type TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    counterpart TEXT, status TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pending_txns (
    txn_id TEXT PRIMARY KEY,
    source_account TEXT, dest_account TEXT,
    amount NUMERIC(18,2) NOT NULL,
    type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.3. So sánh cú pháp giữa hai DBMS

| Đặc điểm | SQL Server (Bank A) | PostgreSQL (Bank B) |
|---|---|---|
| Kiểu chuỗi | `NVARCHAR(n)` | `TEXT` |
| Auto-increment | `IDENTITY(1,1)` | `SERIAL` |
| Kiểu số thực | `DECIMAL(18,2)` | `NUMERIC(18,2)` |
| Timestamp | `DATETIME` + `GETDATE()` | `TIMESTAMPTZ` + `NOW()` |
| Driver Python | `pyodbc` (ODBC Driver 18) | `psycopg2` |
| Trả về ID insert | `OUTPUT INSERTED.id` | `RETURNING id` |
| Parameterized query | `?` placeholder | `%s` placeholder |
| Kiểm tra bảng tồn tại | `IF OBJECT_ID('dbo.X','U') IS NULL` | `CREATE TABLE IF NOT EXISTS` |

### 3.4. Mô hình quan hệ (ERD)

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
                         │  pending_txns    │  (Bảng tạm cho giao thức 2PC)
                         ├──────────────────┤
                         │ txn_id (PK)      │  ← UUID do Coordinator sinh ra
                         │ source_account   │
                         │ dest_account     │
                         │ amount           │
                         │ type             │  ← 'debit' / 'credit'
                         │ created_at       │
                         └──────────────────┘
```

### 3.5. Dữ liệu mẫu (Seed Data)

| Bank | Username | Password | Full Name | Account | Balance |
|---|---|---|---|---|---|
| Bank A | alice | alice123 | Alice Nguyen | A1001 | $1,000 |
| Bank A | bob | bob123 | Bob Tran | A1002 | $1,000 |
| Bank B | charlie | charlie123 | Charlie Le | B1001 | $1,000 |
| Bank B | dave | dave123 | Dave Pham | B1002 | $1,000 |

### 3.6. Vai trò từng bảng trong hệ thống phân tán

| Bảng | Vai trò | Ghi chú |
|---|---|---|
| `customers` | Lưu thông tin đăng nhập & cá nhân | Password hash SHA-256 |
| `accounts` | Lưu số dư, là đối tượng chính của giao dịch | Account number = khóa định tuyến phân tán |
| `transactions` | Nhật ký giao dịch vĩnh viễn | Audit trail, không bao giờ xóa |
| `pending_txns` | Bản ghi tạm trong quá trình 2PC | Xóa khi commit/rollback xong — nếu còn tồn tại = giao dịch treo cần recovery |

---

## 4. TRÌNH BÀY CÁCH CÀI ĐẶT

### 4.1. Yêu cầu hệ thống

| Thành phần | Phiên bản | Ghi chú |
|---|---|---|
| Python | 3.10+ | Cú pháp `str \| None` |
| Node.js | 18+ | Cho frontend React |
| Docker | 20+ | Chạy SQL Server container |
| PostgreSQL | 14+ | Cài native hoặc Docker |

### 4.2. Bước 1 — Cài đặt SQL Server (Docker)

```bash
# Pull và chạy SQL Server 2022 container
docker run -e 'ACCEPT_EULA=Y' \
           -e 'SA_PASSWORD=Hao@DBMS2026' \
           -p 1433:1433 \
           --name sqlserver \
           -d mcr.microsoft.com/mssql/server:2022-latest

# Đợi SQL Server khởi động hoàn toàn (~30 giây)
sleep 30

# Cài ODBC Driver 18 cho Linux (Ubuntu/Debian)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository \
  "$(curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list)"
sudo apt-get update && sudo apt-get install -y msodbcsql18
```

> **Lưu ý:** Database `bank_a` được tạo tự động bởi hàm `init_db()` trong `bank_a.py` khi service khởi chạy lần đầu.

### 4.3. Bước 2 — Cài đặt PostgreSQL

```bash
# Cài đặt PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Khởi động dịch vụ
sudo systemctl start postgresql

# Cấu hình chạy trên port 15432 (hoặc sửa trong bank_b.py)
```

> **Lưu ý:** Database `bank_b` cũng được tạo tự động bởi `init_db()` trong `bank_b.py`.

### 4.4. Bước 3 — Cài đặt Backend Python

```bash
cd 2PC-Bank-Transfer/
pip install -r requirements.txt
```

**Các thư viện chính:**
- `Flask==2.3.3` — Web framework cho REST API
- `flask-cors==4.0.0` — Hỗ trợ Cross-Origin requests
- `requests==2.31.0` — HTTP client (giao tiếp giữa các service)
- `pyodbc==4.0.39` — Kết nối SQL Server qua ODBC
- `psycopg2-binary==2.9.9` — Kết nối PostgreSQL

### 4.5. Bước 4 — Khởi chạy 3 Backend Services

**Cách 1: Mở 3 terminal riêng biệt**

```bash
# Terminal 1 — Coordinator
python3 coordinator.py          # Chạy trên port 5000

# Terminal 2 — Bank A
python3 bank_a.py               # Chạy trên port 5001, tự init_db() + recover_pending()

# Terminal 3 — Bank B
python3 bank_b.py               # Chạy trên port 5002, tự init_db() + recover_pending()
```

**Cách 2: Script tự động**

```bash
chmod +x run_system.sh
./run_system.sh
# Script sẽ: kill tiến trình cũ → kiểm tra port → chạy 3 service nền
```

### 4.6. Bước 5 — Khởi chạy Frontend

```bash
# Terminal 4 — NovaBank A (port 3000)
cd novabank/ && npm install && npm run dev

# Terminal 5 — NovaBank B (port 3001)
cd novabank_b/ && npm install && npm run dev
```

### 4.7. Bước 6 — Kiểm tra hệ thống

```bash
# Health check
curl http://localhost:5000/health   # → {"status":"healthy","service":"Coordinator"}
curl http://localhost:5001/health   # → {"status":"healthy","service":"BankA","database":"SQLServer"}
curl http://localhost:5002/health   # → {"status":"healthy","service":"BankB","database":"PostgreSQL"}

# Chạy test suite tự động (7 test cases)
python3 test_2pc_full.py
```

### 4.8. Tổng quan Port & URL

| Service | Port | URL | Vai trò |
|---|---|---|---|
| Coordinator | 5000 | http://localhost:5000 | Điều phối 2PC |
| Bank A Backend | 5001 | http://localhost:5001 | API nghiệp vụ Bank A |
| Bank B Backend | 5002 | http://localhost:5002 | API nghiệp vụ Bank B |
| NovaBank A Frontend | 3000 | http://localhost:3000 | Giao diện Bank A |
| NovaBank B Frontend | 3001 | http://localhost:3001 | Giao diện Bank B |
| SQL Server | 1433 | localhost:1433 | CSDL Bank A |
| PostgreSQL | 15432 | localhost:15432 | CSDL Bank B |

---

## 5. MÔ TẢ LUỒNG PHÂN TÁN

### 5.1. Luồng chính: Chuyển tiền liên ngân hàng qua 2PC

Khi người dùng Alice (Bank A) chuyển 100 USD cho Charlie (Bank B), hệ thống sử dụng giao thức **Two-Phase Commit** để đảm bảo tính **ACID phân tán**.

#### Sequence Diagram chi tiết

```
  Client (Web)      Coordinator:5000      Bank A:5001         Bank B:5002
       │                  │                  │                    │
       │  POST /transfer  │                  │                    │
       │  {A1001→B1001,   │                  │                    │
       │   amount: 100}   │                  │                    │
       │─────────────────>│                  │                    │
       │                  │                  │                    │
       │                  │  Sinh txn_id = UUID                   │
       │                  │  txn_status[id] = 'preparing'         │
       │                  │                  │                    │
       │                  │ ════════════════════════════════════  │
       │                  │  PHASE 1: PREPARE (Bỏ phiếu)         │
       │                  │ ════════════════════════════════════  │
       │                  │                  │                    │
       │                  │  POST /prepare   │                    │
       │                  │  {type:"debit",  │                    │
       │                  │   amount: 100}   │                    │
       │                  │─────────────────>│                    │
       │                  │                  │ ① Kiểm tra số dư   │
       │                  │                  │ ② Trừ 100 (hold)   │
       │                  │                  │ ③ INSERT pending   │
       │                  │                  │ ④ INSERT txn log   │
       │                  │  {status:"ready"}│                    │
       │                  │<─────────────────│                    │
       │                  │                  │                    │
       │                  │  POST /prepare   │                    │
       │                  │  {type:"credit"} │                    │
       │                  │──────────────────────────────────────>│
       │                  │                  │                    │ ① Kiểm tra TK đích
       │                  │                  │                    │ ② INSERT pending
       │                  │                  │  {status:"ready"}  │
       │                  │<──────────────────────────────────────│
       │                  │                  │                    │
       │                  │  Cả 2 đều READY → GLOBAL COMMIT      │
       │                  │                  │                    │
       │                  │ ════════════════════════════════════  │
       │                  │  PHASE 2: COMMIT (Xác nhận)           │
       │                  │ ════════════════════════════════════  │
       │                  │                  │                    │
       │                  │  POST /commit    │                    │
       │                  │─────────────────>│                    │
       │                  │                  │ DELETE pending     │
       │                  │  {committed}     │ (tiền đã trừ sẵn) │
       │                  │<─────────────────│                    │
       │                  │                  │                    │
       │                  │  POST /commit    │                    │
       │                  │──────────────────────────────────────>│
       │                  │                  │                    │ UPDATE +100
       │                  │                  │                    │ INSERT txn log
       │                  │                  │                    │ DELETE pending
       │                  │                  │  {committed}       │
       │                  │<──────────────────────────────────────│
       │                  │                  │                    │
       │  {status:        │  txn_status = 'committed'             │
       │   "committed"}   │                  │                    │
       │<─────────────────│                  │                    │
```

### 5.2. Chi tiết Phase 1 — PREPARE

| Bước | Thành phần | Hành động | SQL thực thi |
|---|---|---|---|
| 1 | Coordinator | Sinh UUID, ghi `txn_status` | — (in-memory) |
| 2 | Coordinator → Bank A | Gửi `POST /prepare {type:"debit"}` | — |
| 3 | Bank A | Kiểm tra `balance >= amount` | `SELECT balance FROM accounts WHERE account_number = ?` |
| 4 | Bank A | Trừ tiền tạm (hold) | `UPDATE accounts SET balance = balance - 100 WHERE account_number = 'A1001'` |
| 5 | Bank A | Ghi pending | `INSERT INTO pending_txns (txn_id, ...) VALUES (...)` |
| 6 | Coordinator → Bank B | Gửi `POST /prepare {type:"credit"}` | — |
| 7 | Bank B | Kiểm tra tài khoản đích | `SELECT account_number FROM accounts WHERE account_number = 'B1001'` |
| 8 | Bank B | Ghi pending | `INSERT INTO pending_txns (txn_id, ...) VALUES (...)` |

### 5.3. Chi tiết Phase 2 — COMMIT

| Bước | Thành phần | Hành động | SQL thực thi |
|---|---|---|---|
| 9 | Coordinator | Kiểm tra `ready_source AND ready_dest` | — |
| 10 | Bank A (commit) | Xóa pending (tiền đã trừ sẵn ở Phase 1) | `DELETE FROM pending_txns WHERE txn_id = ?` |
| 11 | Bank B (commit) | Cộng tiền + ghi log + xóa pending | `UPDATE accounts SET balance = balance + 100`, `INSERT INTO transactions ...`, `DELETE FROM pending_txns ...` |

### 5.4. Luồng ABORT — Hủy giao dịch

Khi **bất kỳ Bank nào** trả về `abort` trong Phase 1 (ví dụ: không đủ số dư, tài khoản không tồn tại):

```
Coordinator                Bank A              Bank B
    │                        │                    │
    │  Một/cả hai bank ABORT │                    │
    │                        │                    │
    │  POST /rollback ──────>│                    │
    │                        │ Hoàn lại 100 USD   │
    │                        │ INSERT refund_in   │
    │                        │ DELETE pending     │
    │                        │                    │
    │  POST /rollback ──────────────────────────>│
    │                        │                    │ DELETE pending
    │                        │                    │
    │  txn_status = 'aborted'│                    │
```

### 5.5. Luồng Recovery — Phục hồi tự động

Hệ thống có **2 cơ chế recovery**:

**Cơ chế 1: Recovery Worker Thread (Coordinator)**
```
Thread nền chạy mỗi 10 giây:
  ├── GET /pending → Bank A  (lấy danh sách giao dịch treo)
  ├── GET /pending → Bank B
  └── Với mỗi giao dịch treo:
      ├── Nếu txn_status = committed → gửi POST /commit
      ├── Nếu txn_status = aborted  → gửi POST /rollback
      └── Nếu không tìm thấy (hung) → tự động rollback
```

**Cơ chế 2: Startup Recovery (mỗi Bank)**
```
Khi bank_a.py hoặc bank_b.py khởi động:
  recover_pending():
    ├── Đọc tất cả pending_txns trong DB
    ├── Hỏi Coordinator: GET /status/<txn_id>
    ├── Nếu committed → hoàn tất giao dịch
    ├── Nếu aborted/not found → rollback
    └── Nếu lỗi kết nối → giữ lại, đợi Recovery Worker xử lý
```

### 5.6. Luồng giả lập sự cố (Crash Simulation)

Hệ thống hỗ trợ giả lập 2 loại crash:

| Loại crash | Thời điểm | Hành vi |
|---|---|---|
| `after_prepare` | Sau Phase 1, trước Phase 2 | Coordinator hủy giao dịch, rollback cả hai bank, hoàn tiền cho Bank A |
| `after_source_commit` | Sau khi commit Bank A, trước khi commit Bank B | Delay N giây → rồi mới commit Bank B (mô phỏng mất kết nối tạm thời) |

### 5.7. Luồng chuyển tiền nội bộ (Internal Transfer)

Khi cả 2 tài khoản cùng 1 Bank → **KHÔNG cần 2PC**, xử lý trong 1 transaction đơn:

```
Client → Coordinator (phát hiện source_bank == dest_bank)
              │
              └──→ POST /internal/transfer → Bank A
                        │
                        ├── SELECT balance (kiểm tra số dư)
                        ├── UPDATE -100 WHERE account = 'A1001'
                        ├── UPDATE +100 WHERE account = 'A1002'
                        ├── INSERT 2 bản ghi transactions
                        └── COMMIT (1 transaction duy nhất, atomic)
```

### 5.8. Luồng Frontend ↔ Backend

Frontend dùng **Vite Proxy** để định tuyến request, tránh vấn đề CORS:

```
NovaBank A (port 3000)
    │
    ├── /api/*         → Proxy tới Bank A (port 5001)
    │   ├── /api/login          → http://localhost:5001/login
    │   ├── /api/accounts       → http://localhost:5001/accounts
    │   └── /api/transactions/* → http://localhost:5001/transactions/*
    │
    └── /coordinator/* → Proxy tới Coordinator (port 5000)
        ├── /coordinator/transfer        → http://localhost:5000/transfer
        └── /coordinator/simulate-crash  → http://localhost:5000/simulate-crash
```

---

## PHỤ LỤC

### A. Danh sách API Endpoints

#### Coordinator (port 5000)

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/transfer` | Chuyển tiền liên ngân hàng (2PC) |
| GET | `/status/<txn_id>` | Trạng thái giao dịch |
| GET | `/transactions` | Liệt kê tất cả giao dịch |
| GET | `/health` | Health check |
| POST | `/simulate-crash` | Bật/tắt giả lập sự cố |
| GET | `/simulate-crash` | Xem cấu hình crash |

#### Bank A (port 5001) / Bank B (port 5002)

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/register` | Đăng ký tài khoản mới |
| POST | `/login` | Đăng nhập |
| POST | `/logout` | Đăng xuất |
| GET | `/accounts` | Danh sách tài khoản |
| GET | `/accounts/<acc>/info` | Thông tin chi tiết tài khoản |
| GET | `/accounts/<acc>/balance` | Số dư |
| GET | `/transactions/<acc>` | Lịch sử giao dịch |
| POST | `/withdraw` | Rút tiền |
| POST | `/internal/transfer` | Chuyển tiền nội bộ |
| POST | `/prepare` | 2PC Phase 1 |
| POST | `/commit` | 2PC Phase 2 (xác nhận) |
| POST | `/rollback` | 2PC Rollback |
| GET | `/pending` | Giao dịch đang treo |
| GET | `/health` | Health check |

### B. Cấu trúc thư mục dự án

```
CSDLPT/
├── 2PC-Bank-Transfer/          # Backend services
│   ├── coordinator.py          # Coordinator — Điều phối 2PC + Recovery Worker
│   ├── bank_a.py               # Bank A — Flask + pyodbc + SQL Server
│   ├── bank_b.py               # Bank B — Flask + psycopg2 + PostgreSQL
│   ├── logger.py               # Module logging dùng chung (Singleton pattern)
│   ├── requirements.txt        # Python dependencies
│   ├── run_system.sh           # Script chạy nhanh toàn bộ backend
│   ├── test_2pc_full.py        # Test suite 7 test cases
│   └── test_conn.py            # Test kết nối database
│
├── novabank/                   # Frontend cho Bank A (React + Vite)
│   ├── src/
│   │   ├── App.tsx             # Root component + routing
│   │   ├── api.ts              # API helper (fetch wrapper)
│   │   ├── types.ts            # TypeScript interfaces
│   │   ├── components/
│   │   │   ├── Login.tsx       # Đăng nhập
│   │   │   ├── Home.tsx        # Trang chủ
│   │   │   ├── Dashboard.tsx   # Dashboard tổng quan
│   │   │   ├── Transfer.tsx    # Chuyển tiền (2PC + internal + crash sim)
│   │   │   ├── History.tsx     # Lịch sử giao dịch
│   │   │   ├── Layout.tsx      # Layout chính
│   │   │   └── ...
│   │   └── main.tsx
│   ├── vite.config.ts          # Proxy: /api→:5001, /coordinator→:5000
│   └── package.json
│
└── novabank_b/                 # Frontend cho Bank B (cấu trúc tương tự)
    ├── src/                    # Proxy: /api→:5002, /coordinator→:5000
    └── vite.config.ts
```

### C. Công nghệ sử dụng

| Layer | Công nghệ | Vai trò |
|---|---|---|
| Frontend | React, TypeScript, Vite, TailwindCSS | Giao diện người dùng |
| Backend | Python 3.10+, Flask, Flask-CORS | REST API server |
| Database 1 | Microsoft SQL Server 2022 (Docker) | CSDL phân tán cho Bank A |
| Database 2 | PostgreSQL 14+ (Native) | CSDL phân tán cho Bank B |
| Containerization | Docker | Chạy SQL Server |
| Protocol | HTTP/REST, Two-Phase Commit | Giao tiếp & đồng bộ phân tán |
| Logging | Python logging, JSON event logs | Theo dõi & gỡ lỗi |
| Security | SHA-256 password hashing, Flask session | Xác thực người dùng |

### D. Bảng Test Cases

| # | Test Case | Mô tả | Kết quả mong đợi |
|---|---|---|---|
| 1 | Happy Path | Chuyển 100 USD từ A1001 → B1001 | `committed`, số dư thay đổi đúng |
| 2 | Insufficient Balance | Chuyển 999,999 USD (vượt số dư) | `aborted`, số dư không đổi |
| 3 | Invalid Account | Chuyển tới B9999 (không tồn tại) | `aborted`, số dư không đổi |
| 4 | Internal Transfer | Chuyển 50 USD A1001 → A1002 (nội bộ) | `success`, không qua 2PC |
| 5 | Crash Simulation | Giả lập crash sau Prepare | `aborted`, hoàn tiền, số dư không đổi |
| 6 | Recovery Check | Kiểm tra pending_txns | Không còn giao dịch treo |
| 7 | Concurrent Transfers | 3 giao dịch đồng thời | Ít nhất 1 committed, số dư nhất quán |

---
