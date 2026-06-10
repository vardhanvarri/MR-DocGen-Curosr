"""GitLab comment filter → forwards /make-doc webhooks to Cursor."""

import json
import os
import re
import threading
import urllib.request
from flask import Flask, request

app = Flask(__name__)

GITLAB_SECRET = os.environ["GITLAB_WEBHOOK_SECRET"]
CURSOR_URL = os.environ["CURSOR_WEBHOOK_URL"]
CURSOR_TOKEN = os.environ["CURSOR_WEBHOOK_TOKEN"]
PORT = int(os.environ.get("PORT", 3000))

MAKE_DOC = re.compile(r"/make-doc\b", re.I)
seen_notes: set[int] = set()


def should_trigger(payload: dict) -> bool:
    if payload.get("object_kind") != "note":
        return False
    attrs = payload.get("object_attributes") or {}
    if attrs.get("action") != "create" or attrs.get("system"):
        return False
    if attrs.get("noteable_type") not in ("MergeRequest", "Issue"):
        return False
    return bool(MAKE_DOC.search(attrs.get("note", "")))

def forward_to_cursor(payload: dict) -> None:
    try:
        data = json.dumps(payload).encode()

        req = urllib.request.Request(
            CURSOR_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {CURSOR_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            app.logger.info(f"Cursor OK {resp.status}")

    except Exception as e:
        app.logger.exception(f"Cursor forwarding failed: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhooks/gitlab")
def gitlab_webhook():
    if request.headers.get("X-Gitlab-Token") != GITLAB_SECRET:
        return {"status": "error", "reason": "invalid_token"}, 401

    payload = request.get_json(force=True, silent=True) or {}
    if not should_trigger(payload):
        return {"status": "ignored", "reason": "no_trigger"}

    threading.Thread(target=forward_to_cursor, args=(payload,), daemon=True).start()
    return {"status": "triggered", "note_id": note_id}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
