"""
Webhook Handler
================
Routes GitHub webhook events to the appropriate
analysis modules and formats the output as PR comments.
"""
import os
import sys
import logging

# Add parent dir to path so we can import core modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ghost_scrum_master'))

from github_client import GitHubClient
from core.llm_client import LLMClient
from core.ai_analyser import AIAnalyser
from core.predictive import PredictiveAgile
from core.debt_sentinel import DebtSentinel

logger = logging.getLogger('agileflow')


class WebhookHandler:
    """Handles GitHub webhook events and posts analysis comments."""

    def __init__(self):
        self.github = GitHubClient()
        self.llm = LLMClient()

    def handle(self, event_type, payload):
        """Route event to the correct handler."""
        action = payload.get('action', '')

        if event_type == 'pull_request' and action in ('opened', 'synchronize'):
            return self._handle_pr(payload)
        elif event_type == 'push':
            return self._handle_push(payload)
        else:
            logger.info(f"Ignoring event: {event_type}.{action}")
            return {'status': 'ignored', 'event': event_type, 'action': action}

    def _handle_pr(self, payload):
        """Analyze a pull request and post results as a comment."""
        pr = payload['pull_request']
        repo = payload['repository']

        owner = repo['owner']['login']
        repo_name = repo['name']
        pr_number = pr['number']
        pr_title = pr['title']
        pr_author = pr['user']['login']

        logger.info(f"Analyzing PR #{pr_number}: {pr_title} by {pr_author}")

        # Fetch PR data
        files = self.github.get_pr_files(owner, repo_name, pr_number)
        commits = self.github.get_pr_commits(owner, repo_name, pr_number)

        # Convert to our internal format
        history = self._commits_to_history(commits)
        board = self._infer_board_from_pr(pr, files)

        # Run AI analysis
        ai = AIAnalyser(history, board, self.llm)
        mappings = ai.ai_commit_ticket_mapping()

        # Run health analysis
        pa = PredictiveAgile(history, board)
        health_score, health_alerts = pa.calculate_health_score()

        # Run debt analysis
        sentinel = DebtSentinel(history, board)
        debt_score, refactor_tickets = sentinel.generate_refactor_tickets()

        # Format the comment
        comment_body = self._format_pr_comment(
            pr_title=pr_title,
            pr_author=pr_author,
            files=files,
            commits=commits,
            mappings=mappings,
            health_score=health_score,
            health_alerts=health_alerts,
            debt_score=debt_score,
            refactor_tickets=refactor_tickets
        )

        # Post or update the comment
        existing = self.github.find_bot_comment(owner, repo_name, pr_number)
        if existing:
            self.github.update_comment(owner, repo_name, existing, comment_body)
            logger.info(f"Updated existing comment on PR #{pr_number}")
        else:
            self.github.post_comment(owner, repo_name, pr_number, comment_body)
            logger.info(f"Posted new comment on PR #{pr_number}")

        return {'status': 'analyzed', 'pr': pr_number}

    def _handle_push(self, payload):
        """Handle push events — log for sprint tracking."""
        ref = payload.get('ref', '')
        commits = payload.get('commits', [])
        repo = payload['repository']

        logger.info(f"Push to {ref}: {len(commits)} commits in {repo['full_name']}")

        # Only analyze pushes to the default branch
        default_branch = repo.get('default_branch', 'main')
        if ref != f'refs/heads/{default_branch}':
            return {'status': 'ignored', 'reason': 'not default branch'}

        return {'status': 'tracked', 'commits': len(commits)}

    def _commits_to_history(self, commits):
        """Convert GitHub API commit format to our internal format."""
        history = []
        for c in commits:
            commit = c.get('commit', {})
            history.append({
                'hash': c.get('sha', ''),
                'author': commit.get('author', {}).get('name', 'unknown'),
                'date': commit.get('author', {}).get('date', ''),
                'message': commit.get('message', ''),
                'files_changed': [f['filename'] for f in c.get('files', [])],
            })
        return history

    def _infer_board_from_pr(self, pr, files):
        """Build a virtual board from PR data."""
        import re
        board = []

        # Extract ticket refs from PR title and body
        title = pr.get('title', '')
        body = pr.get('body', '') or ''
        text = f"{title} {body}"

        patterns = [r'\b([A-Z]{2,10}-\d+)\b', r'#(\d+)\b']
        for pattern in patterns:
            for match in re.findall(pattern, text):
                ticket_id = f'#{match}' if match.isdigit() else match
                board.append({
                    'id': ticket_id,
                    'title': title[:60],
                    'status': 'In Progress',
                    'assignee': pr['user']['login']
                })

        # If no tickets found, create one from the PR itself
        if not board:
            board.append({
                'id': f'PR-{pr["number"]}',
                'title': title[:60],
                'status': 'In Progress',
                'assignee': pr['user']['login']
            })

        return board

    def _format_pr_comment(self, **data):
        """Format the analysis result as a GitHub-flavored markdown comment."""
        pr_title = data['pr_title']
        files = data['files']
        commits = data['commits']
        health_score = data['health_score']
        health_alerts = data['health_alerts']
        debt_score = data['debt_score']
        refactor_tickets = data['refactor_tickets']
        mappings = data['mappings']

        # Header
        lines = [
            '<!-- agileflow-analysis -->',
            '## ⚡ AgileFlow Analysis',
            '',
            f'**PR:** {pr_title}',
            f'**Files Changed:** {len(files)} | **Commits:** {len(commits)}',
            '',
        ]

        # Health Score
        health_emoji = '🟢' if health_score >= 70 else '🟡' if health_score >= 40 else '🔴'
        lines.append(f'### {health_emoji} Health Score: {health_score}/100')
        if health_alerts:
            for alert in health_alerts:
                lines.append(f'- ⚠️ {alert}')
        else:
            lines.append('- ✅ All clear')
        lines.append('')

        # Debt Score
        if debt_score > 0:
            lines.append(f'### 🛡️ Tech Debt Score: {debt_score}')
            if refactor_tickets:
                for ticket in refactor_tickets[:3]:
                    lines.append(f'- `[{ticket["priority"]}]` {ticket["title"]}')
            lines.append('')

        # AI Insights
        if mappings:
            lines.append('### 🧠 AI Insights')
            for m in mappings[:5]:
                commit = m['commit']
                msg = commit['message'][:60]
                lines.append(f'- `{commit["hash"][:7]}` {msg}')
            lines.append('')

        # Files changed summary
        lines.append('<details>')
        lines.append('<summary>📁 Files Changed</summary>')
        lines.append('')
        for f in files[:20]:
            status = '➕' if f['status'] == 'added' else '✏️' if f['status'] == 'modified' else '🗑️'
            lines.append(f'- {status} `{f["filename"]}`')
        if len(files) > 20:
            lines.append(f'- ... and {len(files) - 20} more')
        lines.append('')
        lines.append('</details>')
        lines.append('')

        # Footer
        lines.append('---')
        lines.append('*Powered by [AgileFlow](https://agileflow.dev) — Sprint intelligence that runs itself.*')

        return '\n'.join(lines)
