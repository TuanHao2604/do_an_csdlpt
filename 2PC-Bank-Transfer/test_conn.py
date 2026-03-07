"""
Test Flask services for 2PC Bank Transfer
"""
import requests
import json

def test_flask_services():
    """Test if Flask services are running"""
    print("🚀 Testing 2PC Bank Transfer Flask Services")
    print("=" * 50)
    
    services = {
        "Coordinator": "http://localhost:5000/health",
        "Bank A": "http://localhost:5001/health",
        "Bank B": "http://localhost:5002/health"
    }
    
    all_ok = True
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name:12} - {data.get('status', 'OK')}")
            else:
                print(f"❌ {name:12} - HTTP {response.status_code}")
                all_ok = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {name:12} - Connection refused (service not running)")
            all_ok = False
        except Exception as e:
            print(f"❌ {name:12} - Error: {str(e)[:40]}")
            all_ok = False
    
    print("=" * 50)
    if all_ok:
        print("✅ All services are running!")
        print("\nYou can now test with Postman or curl:")
        print("  curl http://localhost:5000/health")
        print("  curl http://localhost:5001/balance")
        print("  curl http://localhost:5002/balance")
    else:
        print("❌ Some services are not running")
        print("\nStart the services with:")
        print("  Terminal 1: python3 coordinator_simple.py")
        print("  Terminal 2: python3 bank_a_simple.py")
        print("  Terminal 3: python3 bank_b_simple.py")

def test_database_connections():
    """Test database connections (optional)"""
    print("\n\n🗄️  Testing Database Connections (Optional)")
    print("=" * 50)
    
    # Test PostgreSQL
    print("\n🐘 PostgreSQL:")
    try:
        import psycopg2
        try:
            conn = psycopg2.connect(
                dbname='postgres',
                user='postgres',
                password='Hao@DBMS2026',
                host='localhost',
                port=15432,
                connect_timeout=5
            )
            print("✅ PostgreSQL connection successful!")
            conn.close()
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {str(e)[:50]}")
    except ImportError:
        print("⚠️  psycopg2 not available - skipping PostgreSQL test")
    
    # Test SQL Server
    print("\n🔷 SQL Server:")
    try:
        import pyodbc
        try:
            conn_str = 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;DATABASE=master;UID=sa;PWD=Hao@DBMS2026;TrustServerCertificate=yes'
            conn = pyodbc.connect(conn_str, timeout=5)
            print("✅ SQL Server connection successful!")
            conn.close()
        except Exception as e:
            print(f"❌ SQL Server connection failed: {str(e)[:50]}")
    except ImportError as e:
        print(f"⚠️  pyodbc not available - skipping SQL Server test")
        print(f"   Error: {str(e)[:60]}")

if __name__ == '__main__':
    test_flask_services()
    test_database_connections()