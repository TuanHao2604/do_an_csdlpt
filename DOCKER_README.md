# 🐳 Docker - Hệ thống Chuyển tiền Ngân hàng Phân tán (2PC)

## Yêu cầu

- [Docker Engine](https://docs.docker.com/engine/install/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0
- Ít nhất **4GB RAM** (SQL Server yêu cầu tối thiểu 2GB)

## Khởi chạy nhanh

```bash
# Build và chạy toàn bộ hệ thống
docker compose up --build

# Hoặc chạy nền (detached)
docker compose up --build -d
```

## Truy cập

| Dịch vụ | URL | Mô tả |
|---------|-----|-------|
| NovaBank A | http://localhost:3000 | Giao diện ngân hàng A |
| NovaBank B | http://localhost:3001 | Giao diện ngân hàng B |
| Coordinator | http://localhost:5000/health | API điều phối 2PC |
| Bank A API | http://localhost:5001/health | API ngân hàng A (SQL Server) |
| Bank B API | http://localhost:5002/health | API ngân hàng B (PostgreSQL) |

## Tài khoản mặc định

### Bank A (SQL Server)
| Username | Password | Số tài khoản | Số dư |
|----------|----------|---------------|-------|
| alice | alice123 | A1001 | $1,000 |
| bob | bob123 | A1002 | $1,000 |

### Bank B (PostgreSQL)
| Username | Password | Số tài khoản | Số dư |
|----------|----------|---------------|-------|
| charlie | charlie123 | B1001 | $1,000 |
| dave | dave123 | B1002 | $1,000 |

## Lệnh hữu ích

```bash
# Xem logs tất cả services
docker compose logs -f

# Xem logs của một service cụ thể
docker compose logs -f bank-a

# Dừng hệ thống
docker compose down

# Dừng và xóa dữ liệu (reset database)
docker compose down -v

# Rebuild một service cụ thể
docker compose build bank-a
docker compose up -d bank-a

# Kiểm tra trạng thái
docker compose ps
```

## Kiến trúc Docker

```
┌─────────────────────────────────────────────────────┐
│                  Docker Network                     │
│                                                     │
│  ┌───────────┐  ┌───────────┐                       │
│  │ SQL Server│  │ PostgreSQL│                       │
│  │  :1433    │  │  :5432    │                       │
│  └─────┬─────┘  └─────┬─────┘                       │
│        │              │                             │
│  ┌─────▼─────┐  ┌─────▼─────┐                       │
│  │  Bank A   │  │  Bank B   │                       │
│  │  :5001    │  │  :5002    │                       │
│  └─────┬─────┘  └─────┬─────┘                       │
│        │              │                             │
│        └──────┬───────┘                             │
│               │                                     │
│        ┌──────▼──────┐                               │
│        │ Coordinator │                               │
│        │   :5000     │                               │
│        └──────┬──────┘                               │
│               │                                     │
│     ┌─────────┼─────────┐                           │
│     │                   │                           │
│  ┌──▼──────┐     ┌──────▼──┐                        │
│  │NovaBank │     │NovaBank │                        │
│  │  A :3000│     │  B :3001│                        │
│  └─────────┘     └─────────┘                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Cấu hình

Biến môi trường trong file `.env`:

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `SA_PASSWORD` | `Hao@DBMS2026` | Mật khẩu SQL Server SA |
| `POSTGRES_PASSWORD` | `Hao@DBMS2026` | Mật khẩu PostgreSQL |

## Xử lý sự cố

### SQL Server không khởi động
- Đảm bảo máy có >= 2GB RAM trống
- Kiểm tra logs: `docker compose logs sqlserver`

### Port đã bị chiếm
- Dừng các services đang chạy trên ports 1433, 5432, 5000-5002, 3000-3001
- Hoặc thay đổi port mapping trong `docker-compose.yml`
