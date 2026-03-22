from flask import Flask, jsonify
from controller import reservations_bp
from data_init import seed_data
from db import init_db

app = Flask(__name__)
app.register_blueprint(reservations_bp, url_prefix="/api/reservations")

@app.route("/")
def index():
    return jsonify({"message": "Reservation service running. Use /reservations/ endpoints."})


if __name__ == "__main__":
    init_db()
    seed_data() # add a delay if needed
    app.run(host="0.0.0.0", port=3100)
