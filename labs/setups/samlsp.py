from flask import Flask, redirect, request, session
from saml2 import BINDING_HTTP_POST
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# Server-side request store
outstanding_queries = {}

@app.route("/")
def index():
    return '<a href="/login">Login with SAML</a>'

@app.route("/login")
def login():
    client = Saml2Client(config=saml_config())
    reqid, info = client.prepare_for_authenticate()
    outstanding_queries[reqid] = "/"
    redirect_url = dict(info["headers"])["Location"]
    return redirect(redirect_url)

@app.route("/saml/acs", methods=["POST"])
def acs():
    client = Saml2Client(config=saml_config())
    authn_response = client.parse_authn_request_response(
        request.form["SAMLResponse"],
        BINDING_HTTP_POST,
        outstanding=outstanding_queries
    )
    authn_response.verify = lambda: True
    session["user"] = authn_response.get_subject().text
    return f"Logged in as: {session['user']}"
def saml_config():
    settings = {
        "entityid": "http://localhost:7001/saml/metadata",
        "service": {
            "sp": {
                "endpoints": {
                    "assertion_consumer_service": [
                        ("http://localhost:7001/saml/acs", BINDING_HTTP_POST)
                    ]
                },
                "security": {
                    "authn_requests_signed": False,
                    "want_assertions_signed": False,
                    "want_response_signed": False,
                }
            }
        },
        "metadata": {
            "remote": [{"url": "http://localhost:8080/realms/saml-lab/protocol/saml/descriptor"}]
        }
    }
    cfg = Saml2Config()
    cfg.load(settings)
    return cfg

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7001, debug=True)
