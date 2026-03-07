#!/bin/bash
"""
Script để chạy toàn bộ hệ thống 2PC
Run all 2PC services
"""

echo "🚀 Starting 2PC Bank Transfer System"
echo "===================================="

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Check ports
echo "Checking ports..."
check_port 5000 && check_port 5001 && check_port 5002

if [ $? -ne 0 ]; then
    echo "Some ports are in use. Please stop other services first."
    exit 1
fi

echo ""
echo "Starting services in background..."
echo "Coordinator (port 5000)..."
python3 coordinator.py &
COORDINATOR_PID=$!

echo "Bank A - SQL Server (port 5001)..."
python3 bank_a.py &
BANKA_PID=$!

echo "Bank B - PostgreSQL (port 5002)..."
python3 bank_b.py &
BANKB_PID=$!

echo ""
echo "Services started!"
echo "Coordinator PID: $COORDINATOR_PID"
echo "Bank A PID: $BANKA_PID"
echo "Bank B PID: $BANKB_PID"
echo ""
echo "Test with: python3 test_flask_system.py"
echo ""
echo "Stop with: kill $COORDINATOR_PID $BANKA_PID $BANKB_PID"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for interrupt
trap "echo 'Stopping services...'; kill $COORDINATOR_PID $BANKA_PID $BANKB_PID 2>/dev/null; exit" INT
wait