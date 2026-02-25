"""
AgileFlow v5.0 - LLM-Powered Sprint Intelligence
==================================================
Unified entry point with AI intelligence:
1. AI Activity Analysis (LLM-powered commit understanding)
2. AI Board Sync (intent-based ticket mapping)
3. Predictive Health Scoring
4. Technical Debt Sentinel
5. Sprint Velocity Forecast
6. AI Sprint Narrative (natural-language report)
"""
import json
import os
from datetime import datetime

from core.predictive import PredictiveAgile
from core.debt_sentinel import DebtSentinel
from core.velocity import VelocityForecaster
from core.llm_client import LLMClient
from core.ai_analyser import AIAnalyser


def print_section(title, icon=""):
    print(f"\n{'='*60}")
    print(f" {icon}  {title}")
    print(f"{'='*60}")


def print_risk_badge(level):
    badges = {
        'LOW': '\033[92m[LOW RISK]\033[0m',
        'MEDIUM': '\033[93m[MEDIUM RISK]\033[0m',
        'HIGH': '\033[91m[HIGH RISK]\033[0m',
    }
    return badges.get(level, level)


def load_data(git_path, board_path):
    with open(git_path, 'r') as f:
        history = json.load(f)
    with open(board_path, 'r') as f:
        board = json.load(f)
    return history, board


def main():
    print("\n" + "="*60)
    print("   AGILEFLOW v5.0 - Sprint Intelligence Engine")
    print("   'Your team codes. I handle the rest.'")
    print("="*60)

    git_path = os.getenv('GIT_HISTORY_PATH', 'mocks/git_history.json')
    board_path = os.getenv('PROJECT_BOARD_PATH', 'mocks/project_board.json')

    history, board = load_data(git_path, board_path)

    # Initialize LLM
    llm = LLMClient()
    info = llm.get_provider_info()
    print(f"\n  AI Engine: {info['provider']} ({info['model']}) - {info['status']}")

    # Initialize AI Analyser
    ai = AIAnalyser(history, board, llm)

    # ---- 1. AI Activity Analysis ----
    print_section("AI ACTIVITY ANALYSIS", "1")
    print("  Recent commits:")
    for commit in history:
        print(f"    [{commit['hash'][:7]}] {commit['author']}: {commit['message']}")

    print("\n  AI Commit-to-Ticket Mapping:")
    mappings = ai.ai_commit_ticket_mapping()
    for m in mappings:
        commit = m['commit']
        print(f"\n    Commit: {commit['message'][:50]}...")
        try:
            parsed = json.loads(m['ai_analysis'])
            tm = parsed.get('ticket_mapping', {})
            if tm:
                print(f"    -> Maps to: {tm.get('ticket_id', 'N/A')} "
                      f"(confidence: {tm.get('confidence', 0):.0%})")
                print(f"    -> Reasoning: {tm.get('rationale', 'N/A')[:80]}")
            if parsed.get('side_effects'):
                for se in parsed['side_effects']:
                    print(f"    -> Side effect: {se}")
        except (json.JSONDecodeError, TypeError):
            print(f"    -> AI insight: {str(m['ai_analysis'])[:100]}")

    # ---- 2. AI Board Sync ----
    print_section("AI-POWERED BOARD SYNC", "2")
    updates = ai.ai_board_sync()
    if updates:
        for u in updates:
            confidence_bar = "=" * int(u.get('confidence', 0) * 10)
            print(f"  Ticket {u['id']} -> {u['status']} "
                  f"[{confidence_bar:<10}] {u.get('confidence', 0):.0%}")
            print(f"    Reason: {u['reason'][:80]}")
            for se in u.get('side_effects', []):
                print(f"    Side effect: {se}")
    else:
        print("  No confident mappings detected.")

    # ---- 3. Predictive Health ----
    print_section("PREDICTIVE HEALTH SCORE", "3")
    pa = PredictiveAgile(history, board)
    score, alerts = pa.calculate_health_score()
    print(f"  Project Health: {score}/100")
    for a in alerts:
        print(f"    -> {a}")
    if not alerts:
        print("    All clear. No health concerns detected.")

    # ---- 4. Technical Debt Sentinel ----
    print_section("TECHNICAL DEBT SENTINEL", "4")
    sentinel = DebtSentinel(history, board)
    debt_score, refactor_tickets = sentinel.generate_refactor_tickets()
    print(f"  Debt Score: {debt_score} (0=clean, higher=more debt)")

    if refactor_tickets:
        print(f"\n  Auto-Generated Refactor Tickets ({len(refactor_tickets)}):")
        for ticket in refactor_tickets:
            print(f"    [{ticket['priority']}] {ticket['title']}")
    else:
        print("  Codebase looks healthy!")

    # ---- 5. Sprint Velocity Forecast ----
    print_section("SPRINT VELOCITY FORECAST", "5")
    forecaster = VelocityForecaster(history, board, sprint_days=14, days_elapsed=7)
    forecast = forecaster.forecast_sprint()

    print(f"  Sprint Risk Level: {print_risk_badge(forecast['risk_level'])}")
    print(f"  Days Remaining: {forecast['days_remaining']}")
    print(f"  Velocity: {forecast['velocity']['avg_daily']} commits/day")
    print(f"  Progress: {forecast['progress']['completion_rate']}% done "
          f"(expected: {forecast['progress']['expected_rate']}%)")

    if forecast['risks']:
        print("\n  Risks:")
        for r in forecast['risks']:
            print(f"    ! {r}")

    if forecast['recommendations']:
        print("\n  AI Recommendations:")
        for rec in forecast['recommendations']:
            print(f"    >> {rec}")

    # ---- 6. AI Sprint Narrative ----
    print_section("AI SPRINT NARRATIVE", "6")
    narrative = ai.generate_sprint_narrative(
        health_score=score,
        velocity_data=forecast['velocity'],
        debt_data=debt_score
    )
    print(f"\n{narrative}")

    # ---- Summary ----
    print(f"\n{'='*60}")
    print("   AGILEFLOW SCAN COMPLETE")
    print(f"   AI Provider: {info['provider']} | Model: {info['model']}")
    print(f"   Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
