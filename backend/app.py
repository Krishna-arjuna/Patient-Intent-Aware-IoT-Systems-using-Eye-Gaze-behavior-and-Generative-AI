from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import time

from state import latest, gaze_history, blink_history, genai_history, data_lock

# ---------------- INIT ----------------

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/patient/<pid>")
def patient(pid):
    return render_template("patient.html", patient={"id": pid})


# ---------------- DATA APIs ----------------

@app.route("/api/update", methods=["POST"])
def update():
    data = request.get_json()
    ts = time.time()

    with data_lock:
        latest["gaze"] = data.get("dominant_region", "UNKNOWN")
        latest["blink_count"] = data.get("blink_count", 0)
        latest["blink_rate"] = data.get("blink_rate", 0)
        latest["timestamp"] = ts

        gaze_history.append({"t": ts, "gaze": latest["gaze"]})
        blink_history.append({"t": ts, "blinks": latest["blink_rate"]})

    return jsonify({"status": "ok"})


@app.route("/api/genai", methods=["POST"])
def genai():
    data = request.get_json()
    ts = time.time()

    entry = {
        "t": ts,
        "intent": data.get("intent", ""),
        "urgency": data.get("urgency", ""),
        "action": data.get("action", ""),
        "anomaly_score": data.get("anomaly_score", 0),
        "anomaly_level": data.get("anomaly_level", "LOW"),
        "reasons": data.get("reasons", [])
    }

    with data_lock:
        latest["genai"] = entry
        genai_history.append(entry)

    return jsonify({"status": "ok"})


@app.route("/api/state")
def state():
    with data_lock:
        return jsonify({
            "latest": latest,
            "gaze_history": list(gaze_history)[-20:],
            "blink_history": list(blink_history)[-20:],
            "genai_history": list(genai_history)[-5:]
        })


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)