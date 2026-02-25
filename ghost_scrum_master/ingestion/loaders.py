import json
from .models import Commit, Ticket, ProjectState

def load_git_history(filepath: str):
    with open(filepath, 'r') as f:
        data = json.load(f)
        return [Commit(**c) for c in data]

def load_project_board(filepath: str):
    with open(filepath, 'r') as f:
        data = json.load(f)
        return [Ticket(**t) for t in data]

def get_current_state(git_path: str, board_path: str):
    commits = load_git_history(git_path)
    tickets = load_project_board(board_path)
    return ProjectState(tickets=tickets, recent_commits=commits)
