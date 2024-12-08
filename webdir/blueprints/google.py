from flask import redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user

from models import User

google_bp = make_google_blueprint(
    client_id="1062303461917-0fag7np6rtah09jpm5ptuch0bj3vl03l.apps.googleusercontent.com",
    client_secret="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",
    scope=["profile", "email"],
    redirect_to="index"
)


@google_bp.route("/google_login", methods=['POST', 'GET'])
def index():
    if not google.authorized:
        return redirect(url_for("google.login", _external=True, _scheme='https'))
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    email = resp.json()["email"]
    user = User.get(email)
    if not user:
        user = User(user_email=email)
        user.save()
    login_user(user)
    return redirect(url_for("main", _external=True, _scheme='https'))