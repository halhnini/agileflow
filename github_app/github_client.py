"""
GitHub API Client
==================
Wraps the GitHub REST API for fetching PR data
and posting AgileFlow analysis comments.
"""
import os
import json
import urllib.request
import urllib.error
import logging

logger = logging.getLogger('agileflow')

# GitHub API base
API_BASE = 'https://api.github.com'


class GitHubClient:
    """Lightweight GitHub API client — no external dependencies."""

    def __init__(self, token=None):
        self.token = token or os.getenv('GITHUB_TOKEN', '')
        if not self.token:
            logger.warning("No GITHUB_TOKEN set — API calls will be unauthenticated")

    def _request(self, method, path, data=None):
        """Make an authenticated request to the GitHub API."""
        url = f"{API_BASE}{path}"
        headers = {
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'AgileFlow-Bot/1.0',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        body = json.dumps(data).encode() if data else None
        if body:
            headers['Content-Type'] = 'application/json'

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ''
            logger.error(f"GitHub API error: {e.code} {error_body[:200]}")
            raise
        except urllib.error.URLError as e:
            logger.error(f"GitHub API connection error: {e}")
            raise

    def get_pr(self, owner, repo, pr_number):
        """Fetch pull request details."""
        return self._request('GET', f'/repos/{owner}/{repo}/pulls/{pr_number}')

    def get_pr_files(self, owner, repo, pr_number):
        """Fetch files changed in a pull request."""
        return self._request('GET', f'/repos/{owner}/{repo}/pulls/{pr_number}/files')

    def get_pr_commits(self, owner, repo, pr_number):
        """Fetch commits in a pull request."""
        return self._request('GET', f'/repos/{owner}/{repo}/pulls/{pr_number}/commits')

    def post_comment(self, owner, repo, issue_number, body):
        """Post a comment on a PR (PRs are issues in GitHub API)."""
        return self._request('POST', f'/repos/{owner}/{repo}/issues/{issue_number}/comments', {
            'body': body
        })

    def update_comment(self, owner, repo, comment_id, body):
        """Update an existing comment."""
        return self._request('PATCH', f'/repos/{owner}/{repo}/issues/comments/{comment_id}', {
            'body': body
        })

    def find_bot_comment(self, owner, repo, issue_number):
        """Find an existing AgileFlow comment on a PR to update instead of duplicating."""
        comments = self._request('GET', f'/repos/{owner}/{repo}/issues/{issue_number}/comments')
        for comment in comments:
            if '<!-- agileflow-analysis -->' in comment.get('body', ''):
                return comment['id']
        return None

    def get_commit_diff(self, owner, repo, sha):
        """Fetch the diff for a specific commit."""
        # Use the compare endpoint for diff stats
        return self._request('GET', f'/repos/{owner}/{repo}/commits/{sha}')
