#!/bin/bash

# BookLink Load Balancer Monitor
# Real-time dashboard for monitoring NGINX load balancer

echo "🚀 Starting BookLink Load Balancer Monitor..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "📊 BookLink Load Balancer Dashboard - $(date)"
    echo "=================================================="
    echo ""
    
    # Check if load balancer is running
    LB_STATUS=$(curl -s http://localhost/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ Load Balancer Status: $LB_STATUS"
    else
        echo "❌ Load Balancer Status: DOWN"
    fi
    echo ""
    
    # NGINX Statistics
    echo "📈 NGINX Statistics:"
    echo "-------------------"
    curl -s http://localhost:8080/nginx_status 2>/dev/null | while read line; do
        echo "   $line"
    done
    echo ""
    
    # Detailed Status
    echo "🔧 Configuration Status:"
    echo "----------------------"
    curl -s http://localhost:8080/status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "   Status endpoint not available"
    echo ""
    
    # Test User Service Response Time
    echo "⏱️  Response Times:"
    echo "------------------"
    START_TIME=$(date +%s%N)
    curl -s http://localhost/users/ > /dev/null 2>&1
    END_TIME=$(date +%s%N)
    if [ $? -eq 0 ]; then
        RESPONSE_TIME=$(echo "scale=3; ($END_TIME - $START_TIME) / 1000000" | bc)
        echo "   User Service: ${RESPONSE_TIME}ms ✅"
    else
        echo "   User Service: FAILED ❌"
    fi
    echo ""
    
    # Container Status
    echo "🐳 Container Status:"
    echo "------------------"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(nginx|user_service|catalog|reservation|payment)" | head -5
    echo ""
    
    # Recent NGINX Logs (last 3 lines)
    echo "📝 Recent Access Logs:"
    echo "--------------------"
    docker logs booklink_nginx_lb --tail 3 2>/dev/null | grep -v "GET /health" | tail -3 || echo "   No recent logs"
    echo ""
    
    echo "🔄 Refreshing in 5 seconds... (Ctrl+C to exit)"
    sleep 5
done
