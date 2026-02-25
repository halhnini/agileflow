"""
Git Scanner - Live Repository Analyzer
========================================
Replaces mock JSON data with real git log analysis.
Uses subprocess to call git directly — no external dependencies.
"""
import subprocess
import json
import os
from datetime import datetime


class GitScanner:
    """Scans a real .git repository and extracts structured commit data."""

    def __init__(self, repo_path='.'):
        self.repo_path = os.path.abspath(repo_path)
        self._validate_repo()

    def _validate_repo(self):
        """Ensure the target directory is a valid git repository."""
        git_dir = os.path.join(self.repo_path, '.git')
        if not os.path.isdir(git_dir):
            raise ValueError(
                f"Not a git repository: {self.repo_path}\n"
                f"Hint: Run 'git init' first, or use --demo for mock data."
            )

    def _run_git(self, args):
        """Execute a git command and return stdout."""
        cmd = ['git', '-C', self.repo_path] + args
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def scan_commits(self, max_commits=50, since_days=14):
        """
        Extract recent commits in the same format as git_history.json.
        Returns: list of dicts with hash, author, date, message, files_changed, diff
        """
        # Custom format: hash|author|date|message
        fmt = '%H|%an|%aI|%s'
        since = f'--since={since_days} days ago' if since_days else ''

        raw = self._run_git([
            'log', f'--pretty=format:{fmt}',
            f'-n{max_commits}', since,
            '--no-merges'  # Skip merge commits for cleaner analysis
        ])

        if not raw:
            return []

        commits = []
        for line in raw.split('\n'):
            if not line.strip():
                continue
            parts = line.split('|', 3)
            if len(parts) < 4:
                continue

            hash_val, author, date, message = parts

            # Get files changed for this commit
            files = self._get_files_changed(hash_val)

            # Get diff stats
            diff = self._get_diff_summary(hash_val)

            commits.append({
                'hash': hash_val,
                'author': author,
                'date': date,
                'message': message,
                'files_changed': files,
                'diff': diff
            })

        return commits

    def _get_files_changed(self, commit_hash):
        """Get list of files changed in a specific commit."""
        try:
            raw = self._run_git([
                'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash
            ])
            return raw.split('\n') if raw else []
        except RuntimeError:
            return []

    def _get_diff_summary(self, commit_hash):
        """Get a compact diff summary (insertions/deletions) for a commit."""
        try:
            raw = self._run_git([
                'diff-tree', '--no-commit-id', '--stat', '-r', commit_hash
            ])
            return raw if raw else ''
        except RuntimeError:
            return ''

    def get_branch_info(self):
        """Get current branch and list of recent branches."""
        current = self._run_git(['rev-parse', '--abbrev-ref', 'HEAD'])
        try:
            branches_raw = self._run_git([
                'branch', '--sort=-committerdate', '--format=%(refname:short)'
            ])
            branches = branches_raw.split('\n')[:10] if branches_raw else []
        except RuntimeError:
            branches = [current]

        return {
            'current': current,
            'recent': branches
        }

    def get_contributors(self, since_days=14):
        """Get contributor summary for the sprint period."""
        try:
            raw = self._run_git([
                'shortlog', '-sn', '--no-merges',
                f'--since={since_days} days ago'
            ])
            contributors = []
            for line in raw.split('\n'):
                if not line.strip():
                    continue
                parts = line.strip().split('\t', 1)
                if len(parts) == 2:
                    contributors.append({
                        'commits': int(parts[0].strip()),
                        'author': parts[1].strip()
                    })
            return contributors
        except RuntimeError:
            return []

    def to_history_format(self, max_commits=50, since_days=14):
        """
        Returns data in the exact same format as git_history.json
        so all downstream modules work unchanged.
        """
        return self.scan_commits(max_commits, since_days)
