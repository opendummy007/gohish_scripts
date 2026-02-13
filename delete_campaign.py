import os
from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import urllib3

# Disable HTTPS warnings (local testing only)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration – change these for your environment
GOPHISH_URL = os.environ.get("GOPHISH_URL", "https://127.0.0.1:3333")
API_KEY = os.environ.get(
    "GOPHISH_API_KEY",
    "2c26b5473e69169d6b5b704051e74da6e503472d9f34b6029b28d1129a383a9f",
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")


# -------------------------
# Helper functions
# -------------------------
def _api_get(path, **kwargs):
    """Helper for GET requests to the Gophish API."""
    params = kwargs.pop("params", {})
    params["api_key"] = API_KEY
    url = f"{GOPHISH_URL.rstrip('/')}/api{path}"
    resp = requests.get(url, params=params, verify=False, **kwargs)
    resp.raise_for_status()
    return resp.json()


def _api_delete(path, **kwargs):
    """Helper for DELETE requests to the Gophish API."""
    params = kwargs.pop("params", {})
    params["api_key"] = API_KEY
    url = f"{GOPHISH_URL.rstrip('/')}/api{path}"
    resp = requests.delete(url, params=params, verify=False, **kwargs)
    resp.raise_for_status()
    return resp.json()


# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET"])
def index():
    if not API_KEY:
        return (
            "GOPHISH_API_KEY is not set. "
            "Set it in your environment or hard-code API_KEY.",
            500,
        )

    # Fetch campaign summaries
    data = _api_get("/campaigns/summary")
    campaigns = data.get("campaigns", [])
    return render_template("bulk_campaigns.html", campaigns=campaigns)


@app.route("/delete", methods=["POST"])
def delete_campaigns():
    ids = request.form.getlist("campaign_id")
    if not ids:
        flash("No campaigns selected.", "error")
        return redirect(url_for("index"))

    last_error = None
    for cid in ids:
        try:
            # Delete the campaign itself
            # This removes the campaign and all captured results
            # Templates, landing pages, SMTP profiles, and groups are preserved
            _api_delete(f"/campaigns/{cid}")
        except Exception as e:
            last_error = e
            print(f"Error deleting campaign {cid}: {e}")

    if last_error:
        flash("One or more campaigns could not be deleted. Check logs.", "error")
    else:
        flash(
            "Selected campaigns and their captured data were deleted successfully. Resources are preserved.",
            "success",
        )

    return redirect(url_for("index"))


# -------------------------
# Run Flask
# -------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
