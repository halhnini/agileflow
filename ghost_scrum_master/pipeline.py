import os
from ingestion.loaders import get_current_state
from core.analyser import ScrumAI

def run_pipeline():
    # Paths relative to execution directory
    git_history_path = os.path.join('ghost_scrum_master', 'mocks', 'git_history.json')
    project_board_path = os.path.join('ghost_scrum_master', 'mocks', 'project_board.json')
    
    print("--- AgileFlow Pipeline Start ---")
    
    state = get_current_state(git_history_path, project_board_path)
    ai = ScrumAI(state)
    
    print("\n[Activity Analysis]")
    standup = ai.generate_daily_standup()
    print(standup)
    
    print("[Suggested Board Updates]")
    updates = ai.suggest_ticket_updates()
    if not updates:
        print("No matches found between commits and tickets.")
    for update in updates:
        print(f"Ticket {update['ticket_id']} -> {update['new_status']} ({update['reason']})")
    
    print("\n--- Pipeline Complete ---")

if __name__ == "__main__":
    run_pipeline()
