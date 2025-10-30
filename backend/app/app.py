from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

cors = CORS(
    app,
    resources={
        r"/search/*": {"origin": "*"},
        r"/test/*": {"origin": "*"},
    }
)
@app.route("/search", methods=['GET'])
def get_images():
    return "<p>Hello, World!</p>"