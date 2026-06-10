# GitLab → Cursor filter

One-file Python server. GitLab sends every comment; this only forwards to Cursor when the comment has `/make-doc`. The **full** GitLab webhook JSON is passed through unchanged.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in values
export $(cat .env | xargs)
python app.py
```

## GitLab webhook

- URL: `https://<your-host>/webhooks/gitlab`
- Secret token: same as `GITLAB_WEBHOOK_SECRET`
- Trigger: **Comments**

## Railway

Deploy the repo — uses `Dockerfile`. Set the 3 env vars. Health check: `GET /health`.

## Test

```bash
curl -X POST http://localhost:3000/webhooks/gitlab \
  -H "Content-Type: application/json" \
  -H "X-Gitlab-Token: your-webhook-secret" \
  -d '{"object_kind":"note","object_attributes":{"id":1,"note":"/make-doc fix docs","noteable_type":"MergeRequest","action":"create","system":false}}'
```
