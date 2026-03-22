#!/bin/bash

# Comprehensive Health Check for BookLink with Load Balancer

echo "🔍 BookLink Health Check with Load Balancer - $(date)"
echo "======================================================="

# Function to test endpoint and measure response time
test_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name... "
    
    start_time=$(date +%s%N)
    response=$(curl -s -w "%{http_code}" -o /tmp/response.txt "$url" 2>/dev/null)
    end_time=$(date +%s%N)
    
    if [ $? -eq 0 ] && [ "$response" -eq "$expected_status" ]; then
        response_time=$(echo "scale=2; ($end_time - $start_time) / 1000000" | bc 2>/dev/null || echo "N/A")
        echo "✅ OK (${response_time}ms)"
        return 0
    else
        echo "❌ FAILED (HTTP: $response)"
        return 1
    fi
}

# Load Balancer Tests
echo "🔧 Load Balancer Tests:"
echo "-----------------------"
test_endpoint "http://localhost/health" "LB Health Check"
test_endpoint "http://localhost:8080/nginx_status" "NGINX Status"
test_endpoint "http://localhost:8080/status" "Detailed Status"
echo ""

# Service Tests through Load Balancer
echo "🎯 Services through Load Balancer:"
echo "----------------------------------"
test_endpoint "http://localhost/users/" "User Service (via LB)"
echo ""

# Direct Service Tests (for comparison)
echo "🔗 Direct Service Tests:"
echo "-----------------------"
test_endpoint "http://localhost:6000/" "User Service (direct)" 404  # Should fail - no external port
echo ""

# Container Health
echo "🐳 Container Health:"
echo "-------------------"
containers=("booklink_nginx_lb" "user_service" "postgres_users")
for container in "${containers[@]}"; do
    status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
    if [ "$status" = "running" ]; then
        echo "✅ $container: Running"
    else
        echo "❌ $container: $status"
    fi
done
echo ""

# Load Balancer Statistics
echo "📊 Load Balancer Statistics:"
echo "---------------------------"
curl -s http://localhost:8080/nginx_status 2>/dev/null || echo "❌ Statistics not available"
echo ""

# Summary
echo "📋 Summary:"
echo "----------"
lb_status=$(curl -s http://localhost/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Load Balancer: Operational"
    echo "✅ Monitoring: Available on http://localhost:8080"
    echo "✅ Main Endpoint: http://localhost/"
else
    echo "❌ Load Balancer: Failed"
fi
