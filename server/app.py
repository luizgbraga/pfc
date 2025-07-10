from flask import Flask

from server.routes import routes

# Set up Flask app with static files
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.register_blueprint(routes)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
