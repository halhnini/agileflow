"""
AI Analyser - LLM-Powered Project Intelligence
================================================
Replaces all string-matching logic with genuine AI reasoning.
Uses the LLM client for:
1. Commit-to-ticket mapping (understanding intent, not just keywords)
2. PR intent analysis (does the code fulfill the ticket's goal?)
3. Sprint narrative generation (natural language health reports)
"""
import json
from .llm_client import LLMClient


class AIAnalyser:
    """LLM-powered project analysis engine."""

    def __init__(self, history, board, llm=None):
        self.history = history
        self.board = board
        self.llm = llm or LLMClient()

    def ai_commit_ticket_mapping(self):
        """Use LLM to understand commit intent and map to tickets."""
        results = []

        tickets_summary = "\n".join(
            f"- {t['id']}: {t['title']} (Status: {t['status']}, Assignee: {t['assignee']})"
            for t in self.board
        )

        for commit in self.history:
            prompt = (
                f"Analyze this commit and determine which project ticket it relates to.\n\n"
                f"COMMIT:\n"
                f"  Hash: {commit['hash']}\n"
                f"  Author: {commit['author']}\n"
                f"  Message: {commit['message']}\n"
                f"  Diff:\n{commit.get('diff', 'N/A')}\n\n"
                f"OPEN TICKETS:\n{tickets_summary}\n\n"
                f"Return a JSON object with: reasoning, ticket_mapping (ticket_id, confidence, "
                f"suggested_status, rationale), and side_effects."
            )

            response = self.llm.query(prompt)
            results.append({
                'commit': commit,
                'ai_analysis': response
            })

        return results

    def ai_pr_review(self, pr_data):
        """Use LLM to analyze a PR's intent and code quality."""
        tickets_summary = "\n".join(
            f"- {t['id']}: {t['title']} ({t['description']})"
            for t in self.board
        )

        prompt = (
            f"Review this Pull Request and assess its alignment with project goals.\n\n"
            f"PR DETAILS:\n"
            f"  Title: {pr_data.get('title', 'Unknown')}\n"
            f"  Author: {pr_data.get('author', 'Unknown')}\n"
            f"  Description: {pr_data.get('description', 'No description')}\n"
            f"  Files Changed: {pr_data.get('files', [])}\n\n"
            f"PROJECT TICKETS:\n{tickets_summary}\n\n"
            f"Return a JSON object with: intent_analysis, ticket_alignment "
            f"(ticket_id, alignment_score, gaps), and code_quality (issues, suggestions)."
        )

        return self.llm.query(prompt)

    def generate_sprint_narrative(self, health_score, velocity_data, debt_data):
        """Generate a natural-language sprint health report."""
        commits_summary = "\n".join(
            f"  - [{c['date']}] {c['author']}: {c['message']}"
            for c in self.history
        )

        board_summary = "\n".join(
            f"  - {t['id']}: {t['title']} -> {t['status']} (Assigned: {t['assignee']})"
            for t in self.board
        )

        prompt = (
            f"Generate a sprint health narrative for the engineering team.\n\n"
            f"PROJECT STATISTICS:\n"
            f"  Health Score: {health_score}/100\n"
            f"  Velocity: {velocity_data.get('avg_daily', 'N/A')} commits/day\n"
            f"  Debt Score: {debt_data}\n"
            f"  Sprint Progress: {len([t for t in self.board if t['status'] == 'Done'])}"
            f"/{len(self.board)} tickets done\n\n"
            f"RECENT COMMITS:\n{commits_summary}\n\n"
            f"BOARD STATE:\n{board_summary}\n\n"
            f"Write a concise, actionable sprint summary. Highlight risks, recommend "
            f"scope adjustments, and flag any team health concerns. Use markdown formatting."
        )

        return self.llm.query(prompt)

    def ai_board_sync(self):
        """Use LLM to intelligently map commits to ticket status updates."""
        mappings = self.ai_commit_ticket_mapping()
        updates = []

        for mapping in mappings:
            analysis = mapping['ai_analysis']
            # Try to parse structured JSON from LLM response
            try:
                parsed = json.loads(analysis)
                ticket_map = parsed.get('ticket_mapping', {})
                if ticket_map and ticket_map.get('confidence', 0) > 0.7:
                    updates.append({
                        'id': ticket_map['ticket_id'],
                        'status': ticket_map.get('suggested_status', 'In Progress'),
                        'confidence': ticket_map['confidence'],
                        'reason': ticket_map.get('rationale', 'AI-inferred mapping'),
                        'side_effects': parsed.get('side_effects', [])
                    })
            except (json.JSONDecodeError, TypeError):
                # LLM returned free-text; extract what we can
                updates.append({
                    'id': 'UNKNOWN',
                    'status': 'Needs Review',
                    'confidence': 0.0,
                    'reason': f'AI analysis: {str(analysis)[:100]}...',
                    'side_effects': []
                })

        return updates
