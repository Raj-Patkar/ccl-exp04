from flask import Flask, request, jsonify
from datetime import datetime
from collections import deque
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__)

# Keep last 100 processed requests for analytics
processed_requests = deque(maxlen=100)

# Load course dataset
courses = pd.read_csv("courses.csv", quotechar='"')

# Ensure 'id' column is integer
courses["id"] = courses["id"].astype(int)

# Handle missing descriptions
courses["description"] = courses["description"].fillna("")

# Create TF-IDF matrix
vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(courses["description"])
similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "Edu Analytics ML API",
        "status": "ok",
        "endpoints": {
            "GET /health": "Health probe for Azure",
            "GET /courses": "List all courses",
            "POST /recommend": "Send { user_id, course_id } and get similar courses",
            "GET /analytics": "Last 100 processed recommendation requests"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"})

@app.route("/courses", methods=["GET"])
def list_courses():
    return jsonify(courses[["id", "title"]].to_dict(orient="records"))

@app.route("/recommend", methods=["POST"])
def recommend():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    course_id = payload.get("course_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    if course_id is None:
        return jsonify({"error": "course_id is required"}), 400

    try:
        course_id = int(course_id)
    except ValueError:
        return jsonify({"error": "course_id must be an integer"}), 400

    if course_id not in courses["id"].values:
        return jsonify({"error": f"Course ID {course_id} not found"}), 404

    # Find index of the selected course
    idx = courses[courses["id"] == course_id].index[0]

    # Get similarity scores
    sim_scores = list(enumerate(similarity_matrix[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:4]  # top 3 similar courses

    recommendations = [{
        "id": int(courses.iloc[i[0]]["id"]),
        "title": courses.iloc[i[0]]["title"],
        "description": courses.iloc[i[0]]["description"]
    } for i in sim_scores]

    result = {
        "user_id": user_id,
        "course_id": course_id,
        "recommendations": recommendations,
        "processed_at": datetime.utcnow().isoformat() + "Z"
    }

    processed_requests.appendleft(result)
    return jsonify(result), 200

@app.route("/analytics", methods=["GET"])
def analytics():
    return jsonify({"count": len(processed_requests), "items": list(processed_requests)})

# Azure WSGI entry point
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
