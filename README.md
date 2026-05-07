# 🏦 NovaBank - Hệ thống Chuyển tiền Ngân hàng Phân tán (2PC)

Đồ án môn Cơ sở dữ liệu phân tán - Hệ thống chuyển tiền liên ngân hàng sử dụng giao thức **Two-Phase Commit (2PC)**.

## 📋 Tổng quan

Hệ thống mô phỏng việc chuyển tiền giữa 2 ngân hàng sử dụng 2 hệ quản trị cơ sở dữ liệu khác nhau:

| Thành phần | Công nghệ | Mô tả |
|-----------|-----------|-------|
| **Bank A** | SQL Server 2022 | Ngân hàng A - Flask API + pyodbc |
| **Bank B** | PostgreSQL 16 | Ngân hàng B - Flask API + psycopg2 |
| **Coordinator** | Flask (Python) | Điều phối giao dịch phân tán 2PC |
| **NovaBank A** | React + Vite + TailwindCSS | Giao diện web Bank A |
| **NovaBank B** | React + Vite + TailwindCSS | Giao diện web Bank B |

## 🚀 Hướng dẫn chạy dự án

### Cách 1: Sử dụng Docker (Khuyến nghị)

> Chỉ cần 1 lệnh để chạy toàn bộ hệ thống!

#### Yêu cầu
- [Docker Engine](https://docs.docker.com/engine/install/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0
- Ít nhất **4GB RAM** (SQL Server yêu cầu tối thiểu 2GB)

#### Khởi chạy

```bash
# Clone repository
git clone <repo-url>
cd CSDLPT

# Khởi chạy toàn bộ hệ thống
docker compose up --build

# Hoặc chạy nền (detached mode)
docker compose up --build -d
```

#### Truy cập

| Dịch vụ | URL |
|---------|-----|
| 🌐 NovaBank A (Frontend) | http://localhost:3000 |
| 🌐 NovaBank B (Frontend) | http://localhost:3001 |
| 🔧 Coordinator API | http://localhost:5000/health |
| 🔧 Bank A API | http://localhost:5001/health |
| 🔧 Bank B API | http://localhost:5002/health |

#### Quản lý Docker

```bash
# Xem logs tất cả services
docker compose logs -f

# Xem logs một service cụ thể
docker compose logs -f bank-a

# Dừng hệ thống
docker compose down

# Dừng và xóa toàn bộ dữ liệu (reset database)
docker compose down -v

# Kiểm tra trạng thái
docker compose ps
```

---

### Cách 2: Chạy thủ công (Manual)

#### Yêu cầu
- Python 3.10+
- Node.js 18+
- SQL Server 2019+ (port 1433)
- PostgreSQL 14+ (port 15432)
- ODBC Driver 18 for SQL Server

#### Bước 1: Cài đặt Database

**SQL Server** (cho Bank A):
- Cài đặt SQL Server và đảm bảo chạy trên port `1433`
- Tài khoản SA với mật khẩu được cấu hình trong `bank_a.py`

**PostgreSQL** (cho Bank B):
- Cài đặt PostgreSQL và chạy trên port `15432`
- Tài khoản postgres với mật khẩu được cấu hình trong `bank_b.py`

#### Bước 2: Chạy Backend

```bash
cd 2PC-Bank-Transfer

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy tất cả services (script tự động)
bash run_system.sh

# Hoặc chạy từng service riêng lẻ:
python coordinator.py  # Port 5000
python bank_a.py       # Port 5001
python bank_b.py       # Port 5002
```

#### Bước 3: Chạy Frontend

```bash
# Terminal 1 - NovaBank A
cd novabank
npm install
npm run dev    # Port 3000

# Terminal 2 - NovaBank B
cd novabank_b
npm install
npm run dev    # Port 3001
```

## 👥 Tài khoản mặc định

### Bank A (SQL Server)
| Username | Password | Số tài khoản | Số dư |
|----------|----------|--------------|-------|
| alice | alice123 | A1001 | $1,000 |
| bob | bob123 | A1002 | $1,000 |

### Bank B (PostgreSQL)
| Username | Password | Số tài khoản | Số dư |
|----------|----------|--------------|-------|
| charlie | charlie123 | B1001 | $1,000 |
| dave | dave123 | B1002 | $1,000 |

## 🔄 Tính năng chính

- **Chuyển tiền nội bộ**: Chuyển tiền giữa các tài khoản trong cùng ngân hàng
- **Chuyển tiền liên ngân hàng**: Chuyển tiền giữa Bank A ↔ Bank B sử dụng giao thức 2PC
- **Giả lập sự cố**: Mô phỏng crash/mất kết nối trong quá trình giao dịch
- **Phục hồi tự động**: Recovery worker tự động phát hiện và xử lý giao dịch treo
- **Lịch sử giao dịch**: Xem toàn bộ lịch sử giao dịch của tài khoản

## 🏗️ Kiến trúc hệ thống

```
┌──────────────┐     ┌──────────────┐
│  NovaBank A  │     │  NovaBank B  │
│  (React)     │     │  (React)     │
│  :3000       │     │  :3001       │
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│   Bank A     │     │   Bank B     │
│  (Flask)     │     │  (Flask)     │
│  :5001       │     │  :5002       │
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│  SQL Server  │     │  PostgreSQL  │
│  :1433       │     │  :5432       │
└──────────────┘     └──────────────┘
       │                    │
       └────────┬───────────┘
                │
         ┌──────▼──────┐
         │ Coordinator │
         │  (Flask)    │
         │  :5000      │
         └─────────────┘
```

## 📁 Cấu trúc thư mục

```
CSDLPT/
├── 2PC-Bank-Transfer/        # Backend services
│   ├── coordinator.py         # Điều phối viên 2PC
│   ├── bank_a.py              # API Bank A (SQL Server)
│   ├── bank_b.py              # API Bank B (PostgreSQL)
│   ├── logger.py              # Module logging dùng chung
│   ├── requirements.txt       # Python dependencies
│   ├── run_system.sh          # Script chạy hệ thống
│   └── Dockerfile             # Docker image cho backend
├── novabank/                  # Frontend Bank A
│   ├── src/                   # Source code React
│   ├── nginx.conf             # Nginx config (Docker)
│   └── Dockerfile             # Docker image
├── novabank_b/                # Frontend Bank B
│   ├── src/                   # Source code React
│   ├── nginx.conf             # Nginx config (Docker)
│   └── Dockerfile             # Docker image
├── docker-compose.yml         # Docker Compose orchestration
├── .env                       # Biến môi trường Docker
├── .gitignore                 # Git ignore rules
└── README.md                  # Hướng dẫn này
```

## ⚙️ Cấu hình môi trường

Các biến môi trường trong file `.env`:

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `SA_PASSWORD` | `Hao@DBMS2026` | Mật khẩu SQL Server SA |
| `POSTGRES_PASSWORD` | `Hao@DBMS2026` | Mật khẩu PostgreSQL |

## 🐛 Xử lý sự cố

| Vấn đề | Giải pháp |
|--------|-----------|
| SQL Server không khởi động | Đảm bảo máy có >= 2GB RAM trống. Xem logs: `docker compose logs sqlserver` |
| Port đã bị chiếm | Dừng services đang chạy trên ports 1433, 5432, 5000-5002, 3000-3001 |
| Bank A không kết nối DB | Kiểm tra SQL Server đã healthy: `docker compose ps` |
| Frontend trắng | Chờ backend services khởi động xong, kiểm tra `/health` endpoints |
