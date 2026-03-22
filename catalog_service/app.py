from flask import Flask, jsonify

from data_init import seed_data
from db import init_db
from controller import catalog_bp

app = Flask(__name__)
app.register_blueprint(catalog_bp, url_prefix="/api/catalog")

@app.route("/")
def index():
    return jsonify({"message": "Catalog service running. Use /catalog/ endpoints."})

if __name__ == "__main__":
    init_db()
    seed_data()
    app.run(host="0.0.0.0", port=7001)
