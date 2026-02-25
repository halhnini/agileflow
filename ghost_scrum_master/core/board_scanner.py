"""
Board Scanner - Auto-discover Tickets from Git History
=======================================================
When no external board (Jira/Linear) is connected, this module
scans commit messages to build a virtual project board.
"""
import re
from collections import defaultdict


# Common ticket patterns across platforms
TICKET_PATTERNS = [
    r'\b([A-Z]{2,10}-\d+)\b',       # JIRA/Linear: TICKET-123, PROJ-456
    r'#(\d+)\b',                      # GitHub Issues: #42
    r'\bGH-(\d+)\b',                  # GitHub: GH-123
    r'\bFIX-(\d+)\b',                 # Custom: FIX-001
]


class BoardScanner:
    """Discovers tickets from commit messages and builds a virtual board."""

    def __init__(self, commits):
        self.commits = commits

    def discover_tickets(self):
        """
        Scan all commits for ticket references.
        Returns a board in the same format as project_board.json.
        """
        ticket_data = defaultdict(lambda: {
            'commits': [],
            'authors': set(),
            'first_seen': None,
            'last_seen': None,
            'messages': []
        })

        for commit in self.commits:
            msg = commit.get('message', '')
            date = commit.get('date', '')
            author = commit.get('author', '')

            ticket_ids = self._extract_tickets(msg)

            for ticket_id in ticket_ids:
                td = ticket_data[ticket_id]
                td['commits'].append(commit.get('hash', '')[:7])
                td['authors'].add(author)
                td['messages'].append(msg)

                if not td['first_seen'] or date < td['first_seen']:
                    td['first_seen'] = date
                if not td['last_seen'] or date > td['last_seen']:
                    td['last_seen'] = date

        return self._build_board(ticket_data)

    def _extract_tickets(self, message):
        """Extract all ticket IDs from a commit message."""
        tickets = []
        for pattern in TICKET_PATTERNS:
            matches = re.findall(pattern, message)
            for match in matches:
                # Normalize: GitHub issues get a # prefix
                if match.isdigit():
                    tickets.append(f'#{match}')
                else:
                    tickets.append(match)
        return list(set(tickets))  # Deduplicate

    def _build_board(self, ticket_data):
        """
        Build a virtual project board from discovered tickets.
        Returns the same format as project_board.json.
        """
        board = []

        for ticket_id, data in ticket_data.items():
            # Infer status from commit messages
            status = self._infer_status(data['messages'])

            # Infer title from the first commit referencing this ticket
            title = self._infer_title(ticket_id, data['messages'])

            board.append({
                'id': ticket_id,
                'title': title,
                'status': status,
                'assignee': list(data['authors'])[0] if data['authors'] else 'unassigned',
                'contributors': list(data['authors']),
                'commit_count': len(data['commits']),
                'first_seen': data['first_seen'],
                'last_seen': data['last_seen']
            })

        # Sort by most recent activity
        board.sort(key=lambda x: x.get('last_seen', ''), reverse=True)
        return board

    def _infer_status(self, messages):
        """Infer ticket status from associated commit messages."""
        all_text = ' '.join(messages).lower()

        # Check for completion signals
        done_signals = ['fix:', 'fixes', 'fixed', 'resolve', 'resolved',
                        'close', 'closed', 'complete', 'done']
        if any(signal in all_text for signal in done_signals):
            return 'Done'

        # Check for feature completion
        feat_signals = ['feat:', 'feature', 'implement', 'add:']
        if any(signal in all_text for signal in feat_signals):
            return 'Done'

        # Check for WIP signals
        wip_signals = ['wip', 'draft', 'partial', 'progress', 'refactor']
        if any(signal in all_text for signal in wip_signals):
            return 'In Progress'

        return 'In Progress'

    def _infer_title(self, ticket_id, messages):
        """Generate a human-readable title from commit messages."""
        if not messages:
            return f'Ticket {ticket_id}'

        # Use the first commit message, cleaned up
        first_msg = messages[0]
        # Remove conventional commit prefixes
        cleaned = re.sub(r'^(fix|feat|chore|refactor|docs|test|ci|style|perf|build):\s*', '', first_msg, flags=re.IGNORECASE)
        # Remove the ticket reference itself
        cleaned = re.sub(r'\[?' + re.escape(ticket_id) + r'\]?\s*', '', cleaned)
        cleaned = cleaned.strip()

        return cleaned if cleaned else f'Work on {ticket_id}'
