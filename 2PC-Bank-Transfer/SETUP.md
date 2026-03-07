"""
Setup and Installation Guide
Hướng dẫn cài đặt và cấu hình cho hệ thống 2PC với Flask Services
"""

# ============================================================
# 1. CÀI ĐẶT CÁC THƯ VIỆN CẦN THIẾT
# ============================================================

# Cài đặt tất cả dependencies
pip install -r requirements.txt

# Hoặc cài đặt từng thư viện:
pip install Flask requests psycopg2-binary pyodbc PyMySQL

# ============================================================
# 2. CẤU HÌNH DATABASE
# ============================================================

# 2.1 PostgreSQL cho Bank B
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# Tạo database cho Bank B
sudo -u postgres psql
postgres=# CREATE DATABASE bank_b;
postgres=# \\q

# 2.2 SQL Server cho Bank A (Docker)
docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=Hao@DBMS' \\
  -p 1433:1433 --name sqlserver \\
  -d mcr.microsoft.com/mssql/server:2022-latest

# Đợi SQL Server khởi động (khoảng 30 giây)
sleep 30

# Tạo database cho Bank A
sqlcmd -S localhost -U sa -P 'Hao@DBMS'
> CREATE DATABASE bank_a;
> GO
> QUIT

# ============================================================
# 3. CHẠY CÁC SERVICES
# ============================================================

# Terminal 1: Chạy Bank A (SQL Server) trên port 5001
python3 bank_a.py

# Terminal 2: Chạy Bank B (PostgreSQL) trên port 5002
python3 bank_b.py

# Terminal 3: Chạy Coordinator trên port 5000
python3 coordinator.py

# ============================================================
# 4. TEST HỆ THỐNG
# ============================================================

# Test chuyển tiền 100 từ Bank A sang Bank B
curl -X POST http://localhost:5000/transfer \\
  -H "Content-Type: application/json" \\
  -d '{"from_account": "A1001", "to_account": "B1001", "amount": 100}'

# Kiểm tra trạng thái giao dịch
curl http://localhost:5000/status/test_001

# ============================================================
# 5. CẤU HÌNH MẠNG (TUỲ CHỌN)
# ============================================================

# Nếu chạy trên các máy khác nhau, cập nhật URL trong coordinator.py:
BANK_A_URL = 'http://bank-a-server:5001'  # Thay đổi IP
BANK_B_URL = 'http://bank-b-server:5002'  # Thay đổi IP

# ============================================================
# 6. TROUBLESHOOTING
# ============================================================

# Kiểm tra services có chạy không:
curl http://localhost:5000/health  # Coordinator
curl http://localhost:5001/health  # Bank A
curl http://localhost:5002/health  # Bank B

# Xem logs:
tail -f logs/*.log

# Khởi động lại services nếu cần:
docker restart sqlserver
sudo systemctl restart postgresql
