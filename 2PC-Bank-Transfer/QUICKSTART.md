"""
Quick Setup Guide - Get databases running fast!
Hướng dẫn nhanh - Chạy database ngay!
"""

# ===========================================
# QUICK START - PostgreSQL Only (Easier)
# ===========================================

# 1. Start PostgreSQL
sudo systemctl start postgresql

# 2. Create database and user
sudo -u postgres psql
postgres=# CREATE USER bankuser WITH PASSWORD 'bankpass123';
postgres=# CREATE DATABASE bank_a OWNER bankuser;
postgres=# GRANT ALL PRIVILEGES ON DATABASE bank_a TO bankuser;
postgres=# \\q

# 3. Test connection
python3 test_conn.py

# 4. Run with database
python3 test_with_db.py

# ===========================================
# FULL SETUP - Both PostgreSQL + SQL Server
# ===========================================

# PostgreSQL (as above) + SQL Server in Docker:

# 1. Install Docker if not installed
# sudo apt-get install docker.io

# 2. Run SQL Server in Docker
sudo docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=YourPassword123' \\
  -p 1433:1433 --name sqlserver --restart unless-stopped \\
  -d mcr.microsoft.com/mssql/server:2022-latest

# 3. Create database
# sqlcmd -S localhost -U sa -P YourPassword123
# > CREATE DATABASE bank_b;
# > GO
# > QUIT

# 4. Install ODBC drivers (Ubuntu/Debian)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
sudo apt-get update
sudo apt-get install msodbcsql18

# 5. Test everything
python3 test_conn.py
python3 test_with_db.py

# ===========================================
# TROUBLESHOOTING
# ===========================================

# If PostgreSQL won't start:
sudo systemctl status postgresql
sudo systemctl enable postgresql
sudo systemctl start postgresql

# If Docker SQL Server issues:
sudo docker ps -a
sudo docker logs sqlserver
sudo docker restart sqlserver

# If ODBC issues:
sudo apt-get install unixodbc-dev
pip install --upgrade pyodbc

# Test individual components:
python3 test_simple.py  # Works without databases
python3 test_conn.py    # Tests connections
python3 test_with_db.py # Full test with databases