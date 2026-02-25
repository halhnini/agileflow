import json
from datetime import datetime, timedelta

class PredictiveAgile:
    def __init__(self, history, board):
        self.history = history
        self.board = board

    def calculate_health_score(self):
        # Health score starts at 100
        score = 100
        alerts = []

        # 1. Velocity Analysis: Check for stalled tickets
        total_tickets = len(self.board)
        stalled_tickets = 0
        for ticket in self.board:
            if ticket['status'] == 'In Progress':
                # Simulation: If a ticket is in progress but no recent commit matches it
                match_found = any(ticket['id'] in c['message'] for c in self.history)
                if not match_found:
                    stalled_tickets += 1
        
        if stalled_tickets > 0:
            score -= (stalled_tickets / total_tickets) * 30
            alerts.append(f"CRITICAL: {stalled_tickets} tickets appear stalled (no recent activity).")

        # 2. Tech Debt Sentinel: Complexity check (simulated)
        complexity_score = 0
        for commit in self.history:
            if "fix" in commit['message'].lower():
                complexity_score += 1 # Fixes often indicate technical debt surfacing
        
        if complexity_score > 3:
            score -= 15
            alerts.append("WARNING: High frequency of bug fixes detected. Tech debt may be increasing.")

        # 3. Burnout Detector: Commit timing (simulated)
        late_commits = 0
        for commit in self.history:
            # Simulation: late nights (after 10 PM)
            try:
                commit_time = datetime.strptime(commit['date'], "%Y-%m-%dT%H:%M:%SZ")
                if commit_time.hour > 20: 
                    late_commits += 1
            except:
                pass
        
        if late_commits > 2:
            score -= 10
            alerts.append("CAUTION: Late-night activity detected. Monitor team for burnout.")

        return max(0, score), alerts

if __name__ == "__main__":
    # Test logic
    with open('mocks/git_history.json') as f: history = json.load(f)
    with open('mocks/project_board.json') as f: board = json.load(f)
    
    pa = PredictiveAgile(history, board)
    score, alerts = pa.calculate_health_score()
    
    print(f"Project Health Score: {score}/100")
    for a in alerts:
        print(f"- {a}")
