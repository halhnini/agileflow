"""
Sprint Velocity Forecaster
--------------------------
Analyzes commit cadence, ticket completion rates, and team activity
to predict whether the current sprint goal is at risk.
"""
from datetime import datetime, timedelta
from collections import defaultdict

class VelocityForecaster:
    """Predicts sprint health based on commit velocity and ticket progress."""

    def __init__(self, history, board, sprint_days=14, days_elapsed=7):
        self.history = history
        self.board = board
        self.sprint_days = sprint_days
        self.days_elapsed = days_elapsed

    def get_commit_velocity(self):
        """Calculate commits per day and per author."""
        daily_commits = defaultdict(int)
        author_commits = defaultdict(int)

        for commit in self.history:
            try:
                dt = datetime.strptime(commit['date'], "%Y-%m-%dT%H:%M:%SZ")
                day_key = dt.strftime("%Y-%m-%d")
                daily_commits[day_key] += 1
                author_commits[commit['author']] += 1
            except:
                pass

        avg_daily = len(self.history) / max(self.days_elapsed, 1)
        return {
            'total_commits': len(self.history),
            'avg_daily': round(avg_daily, 2),
            'daily_breakdown': dict(daily_commits),
            'author_breakdown': dict(author_commits)
        }

    def get_ticket_progress(self):
        """Analyze ticket completion rates."""
        total = len(self.board)
        done = sum(1 for t in self.board if t['status'] == 'Done')
        in_progress = sum(1 for t in self.board if t['status'] == 'In Progress')
        todo = sum(1 for t in self.board if t['status'] == 'Todo')

        completion_rate = (done / total * 100) if total > 0 else 0
        expected_rate = (self.days_elapsed / self.sprint_days) * 100

        return {
            'total': total,
            'done': done,
            'in_progress': in_progress,
            'todo': todo,
            'completion_rate': round(completion_rate, 1),
            'expected_rate': round(expected_rate, 1),
            'on_track': completion_rate >= expected_rate * 0.7  # 70% threshold
        }

    def forecast_sprint(self):
        """Generate a sprint health forecast."""
        velocity = self.get_commit_velocity()
        progress = self.get_ticket_progress()

        risk_level = "LOW"
        risks = []
        recommendations = []

        # Risk: Completion rate is behind schedule
        if not progress['on_track']:
            risk_level = "HIGH"
            deficit = progress['expected_rate'] - progress['completion_rate']
            risks.append(
                f"Sprint is behind schedule: {progress['completion_rate']}% done vs "
                f"{progress['expected_rate']}% expected ({deficit:.0f}% deficit)."
            )
            recommendations.append(
                "Consider scope reduction: identify lowest-priority tickets to defer to next sprint."
            )

        # Risk: Uneven workload distribution
        if velocity['author_breakdown']:
            max_commits = max(velocity['author_breakdown'].values())
            min_commits = min(velocity['author_breakdown'].values())
            if max_commits > 0 and (min_commits / max_commits) < 0.3:
                if risk_level == "LOW":
                    risk_level = "MEDIUM"
                risks.append(
                    "Uneven workload detected: some team members have significantly fewer commits."
                )
                recommendations.append(
                    "Rebalance work assignments to prevent bottlenecks and reduce bus factor."
                )

        # Risk: Low velocity in recent activity
        if velocity['avg_daily'] < 1.0 and self.days_elapsed > 2:
            if risk_level == "LOW":
                risk_level = "MEDIUM"
            risks.append(
                f"Low commit velocity: averaging {velocity['avg_daily']} commits/day."
            )
            recommendations.append(
                "Check for blockers: team might be stuck on complex tasks or waiting on reviews."
            )

        # Risk: Too many tickets still in progress
        if progress['in_progress'] > progress['done'] and self.days_elapsed > self.sprint_days * 0.5:
            if risk_level == "LOW":
                risk_level = "MEDIUM"
            risks.append(
                f"Too many open items: {progress['in_progress']} in progress vs {progress['done']} done."
            )
            recommendations.append(
                "Focus on finishing active work before starting new tickets. Apply WIP limits."
            )

        return {
            'risk_level': risk_level,
            'velocity': velocity,
            'progress': progress,
            'risks': risks,
            'recommendations': recommendations,
            'days_remaining': self.sprint_days - self.days_elapsed
        }
