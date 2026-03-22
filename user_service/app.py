from flask import Flask
from flask.json import jsonify

from controller import user_bp
from db import init_db
from data_init import seed_data

app = Flask(__name__)
app.register_blueprint(user_bp, url_prefix="/api/users")


@app.route("/")
def index():
    return jsonify({"message": "User service running. Use /users/ endpoints."})

if __name__ == "__main__":
    init_db()
    seed_data()
    app.run(host="0.0.0.0", port=6000)
