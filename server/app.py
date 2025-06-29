from flask import Flask

from server.routes import routes

app = Flask(__name__)
app.register_blueprint(routes)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
