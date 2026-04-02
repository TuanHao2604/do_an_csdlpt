#!/bin/bash
# Script để chạy toàn bộ hệ thống 2PC Bank Transfer

echo "🚀 Starting 2PC Bank Transfer System"
echo "===================================="

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Kill old processes on these ports
echo "Cleaning up old processes..."
for port in 5000 5001 5002; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        kill $pid 2>/dev/null
        echo "  Killed process on port $port (PID: $pid)"
    fi
done
sleep 1

# Check ports
echo ""
echo "Checking ports..."
check_port 5000 && check_port 5001 && check_port 5002

if [ $? -ne 0 ]; then
    echo "Some ports are still in use. Please stop other services first."
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
echo "  Coordinator PID: $COORDINATOR_PID (port 5000)"
echo "  Bank A PID: $BANKA_PID (port 5001)"
echo "  Bank B PID: $BANKB_PID (port 5002)"
echo ""
echo "Frontend:"
echo "  NovaBank A: cd ../novabank && npm run dev  (port 3000)"
echo "  NovaBank B: cd ../novabank_b && npm run dev (port 3001)"
echo ""
echo "Test: python3 test_2pc_full.py"
echo ""
echo "Stop: kill $COORDINATOR_PID $BANKA_PID $BANKB_PID"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for interrupt
trap "echo 'Stopping services...'; kill $COORDINATOR_PID $BANKA_PID $BANKB_PID 2>/dev/null; exit" INT
wait