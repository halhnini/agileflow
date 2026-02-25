"""
Technical Debt Sentinel
-----------------------
Analyzes code diffs to detect complexity spikes and hotspot files.
When debt indicators exceed thresholds, automatically generates
"Refactor Tickets" for the next sprint.
"""
import re
from collections import Counter

class DebtSentinel:
    """Monitors code health by analyzing commit patterns and diffs."""

    # Debt signals and their weights
    DEBT_SIGNALS = {
        'todo': 2,        # TODO/FIXME/HACK comments
        'hotfix': 3,      # Emergency patches
        'workaround': 3,  # Workarounds indicate shortcuts
        'temp': 1,        # Temporary code
        'deprecated': 2,  # Using deprecated APIs
        'hardcode': 2,    # Hardcoded values
    }

    def __init__(self, history, board):
        self.history = history
        self.board = board

    def analyze_diffs(self):
        """Scan commit diffs for debt signals."""
        debt_items = []
        file_hotspots = Counter()

        for commit in self.history:
            diff = commit.get('diff', '')
            message = commit.get('message', '').lower()

            # Track file change frequency (hotspot detection)
            files_changed = re.findall(r'[+-]{3}\s[ab]/(.+)', diff)
            for f in files_changed:
                file_hotspots[f] += 1

            # Scan for debt signals in commit messages
            for signal, weight in self.DEBT_SIGNALS.items():
                if signal in message:
                    debt_items.append({
                        'signal': signal,
                        'weight': weight,
                        'source': commit['message'],
                        'author': commit['author'],
                        'hash': commit['hash'][:7]
                    })

            # Scan diffs for inline debt markers
            for line in diff.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    line_lower = line.lower()
                    for signal, weight in self.DEBT_SIGNALS.items():
                        if signal in line_lower:
                            debt_items.append({
                                'signal': signal,
                                'weight': weight,
                                'source': f"New code in {commit['hash'][:7]}",
                                'author': commit['author'],
                                'hash': commit['hash'][:7]
                            })

        return debt_items, file_hotspots

    def calculate_debt_score(self):
        """Return a debt score (0 = clean, higher = more debt)."""
        debt_items, hotspots = self.analyze_diffs()
        total_weight = sum(item['weight'] for item in debt_items)

        # Hotspot penalty: files changed more than 3 times get flagged
        hotspot_penalty = sum(1 for count in hotspots.values() if count >= 3) * 5

        return total_weight + hotspot_penalty, debt_items, hotspots

    def generate_refactor_tickets(self):
        """Auto-generate refactor ticket suggestions."""
        score, debt_items, hotspots = self.calculate_debt_score()
        tickets = []

        # Group debt by file hotspots
        critical_hotspots = {f: c for f, c in hotspots.items() if c >= 2}
        if critical_hotspots:
            for filepath, change_count in critical_hotspots.items():
                tickets.append({
                    'title': f'Refactor: {filepath} (changed {change_count}x recently)',
                    'priority': 'High' if change_count >= 3 else 'Medium',
                    'description': f'This file has been modified {change_count} times in recent commits. '
                                   f'Consider refactoring to reduce churn and improve maintainability.',
                    'type': 'REFACTOR'
                })

        # Generate tickets from debt signals
        signal_counts = Counter(item['signal'] for item in debt_items)
        for signal, count in signal_counts.items():
            if count >= 2:
                tickets.append({
                    'title': f'Tech Debt: Address "{signal}" markers ({count} occurrences)',
                    'priority': 'High' if self.DEBT_SIGNALS[signal] >= 3 else 'Medium',
                    'description': f'Found {count} instances of "{signal}" patterns in recent commits. '
                                   f'These should be resolved to prevent debt accumulation.',
                    'type': 'TECH_DEBT'
                })

        return score, tickets
