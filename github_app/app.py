"""
AgileFlow GitHub App — Webhook Server
=======================================
Flask server that receives GitHub webhooks and posts
AI analysis directly on pull requests.

Events handled:
- pull_request.opened → Full AI analysis comment
- pull_request.synchronize → Updated analysis on new commits
- push → Sprint health update (on default branch)
"""
import os
import hmac
import hashlib
import logging
from flask import Flask, request, jsonify

from github_client import GitHubClient
from webhook_handler import WebhookHandler

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('agileflow')

# Configuration
WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', '')
APP_ID = os.getenv('GITHUB_APP_ID', '')
PRIVATE_KEY_PATH = os.getenv('GITHUB_PRIVATE_KEY_PATH', 'private-key.pem')


def verify_signature(payload, signature):
    """Verify the webhook signature from GitHub (HMAC-SHA256)."""
    if not WEBHOOK_SECRET:
        logger.warning("No WEBHOOK_SECRET set — skipping signature verification")
        return True

    if not signature:
        return False

    expected = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'agileflow-github-app',
        'version': '1.0.0'
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint — receives events from GitHub."""
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_signature(request.data, signature):
        logger.warning("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 401

    # Parse event
    event_type = request.headers.get('X-GitHub-Event', 'ping')
    payload = request.json

    logger.info(f"Received event: {event_type}")

    if event_type == 'ping':
        return jsonify({'message': 'pong'})

    # Handle the event
    try:
        handler = WebhookHandler()
        result = handler.handle(event_type, payload)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """Landing page for the GitHub App."""
    return '''
    <html>
    <head><title>AgileFlow GitHub App</title></head>
    <body style="font-family: sans-serif; text-align: center; padding: 80px; background: #0a0a0f; color: #f1f1f4;">
        <h1>⚡ AgileFlow GitHub App</h1>
        <p style="color: #9a9ab0;">Sprint intelligence for your pull requests.</p>
        <p style="color: #6366f1;">Status: Running</p>
    </body>
    </html>
    '''


if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
