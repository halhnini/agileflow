from ..core.models import ProjectState, Ticket, Commit
from typing import List, Dict

class ScrumAI:
    def __init__(self, state: ProjectState):
        self.state = state

    def generate_daily_standup(self) -> str:
        summary = "## AgileFlow Stand-up Report\n\n"
        for commit in self.state.recent_commits:
            summary += f"- **{commit.author}** worked on: {commit.message} (Hash: {commit.hash[:7]})\n"
        
        # Simple heuristic for now: if a commit message mentions a ticket-like ID, link it.
        return summary

    def suggest_ticket_updates(self) -> List[Dict]:
        updates = []
        for commit in self.state.recent_commits:
            for ticket in self.state.tickets:
                # Basic string matching for simulation
                if ticket.title.lower() in commit.message.lower() or ticket.id.lower() in commit.message.lower():
                    updates.append({
                        "ticket_id": ticket.id,
                        "new_status": "Done" if "fix" in commit.message.lower() or "feat" in commit.message.lower() else "In Progress",
                        "reason": f"Mapped from commit: {commit.message}"
                    })
        return updates
