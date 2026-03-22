from flask import Flask, jsonify

from controller import payments_bp
from data_init import seed_data
from db import init_db

app = Flask(__name__)
app.register_blueprint(payments_bp, url_prefix="/api/payments")

@app.route("/")
def index():
    return jsonify({"message": "Payment service running. Use /payments/ endpoints."})

if __name__ == "__main__":
    init_db()
    seed_data()
    app.run(host="0.0.0.0", port=4000)
