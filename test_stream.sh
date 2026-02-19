#!/bin/bash

##############################################################################
# Test Streaming Endpoint
##############################################################################

echo "🧪 Testing /chat/stream endpoint..."
echo ""

curl -N -X POST http://localhost:8001/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-stream-001",
    "query": "โฉนดที่ดินคืออะไร"
  }'

echo ""
echo ""
echo "✅ Stream test completed!"
