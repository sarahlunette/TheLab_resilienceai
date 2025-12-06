#!/bin/bash
set -e

# -----------------------------
#  Configuration from env vars
# -----------------------------
: "${QDRANT_URL:?QDRANT_URL is not set}"
: "${QDRANT_API_KEY:?QDRANT_API_KEY is not set}"
COLLECTION="${COLLECTION:-island_docs}"
PORT="${PORT:-8080}"

echo "💡 Cloud Run PORT: $PORT"
echo "💡 Qdrant URL: $QDRANT_URL"
echo "💡 Collection: $COLLECTION"

# -----------------------------
#  Start FastAPI server
# -----------------------------
echo "🚀 Starting FastAPI..."
uvicorn main:app --host 0.0.0.0 --port $PORT &
FASTAPI_PID=$!

# -----------------------------
#  Wait for Qdrant to be ready
# -----------------------------
MAX_RETRIES=120
COUNTER=0
echo "⏳ Waiting for Qdrant collections endpoint..."

until curl -s -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections" | jq empty >/dev/null 2>&1; do
    COUNTER=$((COUNTER+1))
    if [[ $COUNTER -ge $MAX_RETRIES ]]; then
        echo "❌ Qdrant not ready after $MAX_RETRIES seconds. Exiting."
        exit 1
    fi
    echo "   …waiting ($COUNTER/$MAX_RETRIES)"
    sleep 1
done

echo "🟢 Qdrant is ready."

# -----------------------------
#  Ensure collection exists
# -----------------------------
EXISTS=$(curl -s -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections/$COLLECTION/exists" | jq -r '.result.exists // false')

if [[ "$EXISTS" == "true" ]]; then
    echo "✔ Collection '$COLLECTION' already exists."
else
    echo "⚠ Collection '$COLLECTION' missing — creating it..."
    curl -s -X PUT "$QDRANT_URL/collections/$COLLECTION" \
      -H "Content-Type: application/json" \
      -H "api-key: $QDRANT_API_KEY" \
      --data '{
        "vectors": {
          "size": 384,
          "distance": "Cosine"
        }
      }'
    echo "✔ Collection created."
fi

# -----------------------------
#  Launch vectorstore build in background
# -----------------------------
echo "🚀 Launching vectorstore build..."
(
    if python build_vectorstore.py; then
        echo "🟢 Vectorstore ready."
    else
        echo "⚠ Vectorstore build failed — continuing anyway."
    fi
) &

# -----------------------------
#  Keep FastAPI running
# -----------------------------
wait $FASTAPI_PID
