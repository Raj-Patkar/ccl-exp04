from flask import Flask, request, jsonify
from datetime import datetime
from collections import deque
import random

app = Flask(__name__)

# Keep the last 100 processed requests in memory
processed_requests = deque(maxlen=100)

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "E-Learning Backend API",
        "status": "ok",
        "endpoints": {
            "POST /recommend": "Send { user_id, interests? } and receive recommendations",
            "GET /analytics": "View last 100 processed requests",
            "GET /health": "Health probe for Azure"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"})

@app.route("/recommend", methods=["POST"])
def recommend():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    interests = payload.get("interests", [])

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    catalog = {
        "python": ["Python Basics", "Flask for Web", "Data Analysis with Pandas"],
        "ml": ["Intro to ML", "Supervised Learning", "Model Deployment"],
        "cloud": ["Azure Fundamentals", "Deploying on App Service", "CI/CD Pipelines"],
        "default": ["Critical Thinking", "Time Management", "Learning How to Learn"]
    }

    pool = []
    for key in interests:
        pool.extend(catalog.get(key.lower(), []))
    if not pool:
        for v in catalog.values():
            pool.extend(v)

    k = 3 if len(pool) >= 3 else len(pool)
    recommendations = random.sample(pool, k=k) if pool else []

    result = {
        "user_id": user_id,
        "interests": interests,
        "recommendations": recommendations,
        "processed_at": datetime.utcnow().isoformat() + "Z"
    }

    processed_requests.appendleft(result)
    return jsonify(result), 200

@app.route("/analytics", methods=["GET"])
def analytics():
    return jsonify({"count": len(processed_requests), "items": list(processed_requests)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)