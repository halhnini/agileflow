"""
AgileFlow v6.0 - Sprint Intelligence Engine
=============================================
Production entry point with:
- Real git repository scanning (--repo /path)
- License key validation (LICENSE_KEY env var)
- Tier-based feature gating (Free/Pro/Team)
- LLM-powered AI analysis
- Demo mode fallback (--demo)

Usage:
  docker run -v /my/repo:/repo -e LICENSE_KEY=xxx agileflow --repo /repo
  docker run --rm agileflow --demo
"""
import json
import os
import sys
import argparse
from datetime import datetime

from core.predictive import PredictiveAgile
from core.debt_sentinel import DebtSentinel
from core.velocity import VelocityForecaster
from core.llm_client import LLMClient
from core.ai_analyser import AIAnalyser
from core.license import enforce_license, check_module_access, print_license_info


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


def load_mock_data(git_path, board_path):
    """Load demo data from JSON files."""
    with open(git_path, 'r') as f:
        history = json.load(f)
    with open(board_path, 'r') as f:
        board = json.load(f)
    return history, board


def load_real_data(repo_path, sprint_days=14):
    """Scan a real git repository for commit data."""
    from core.git_scanner import GitScanner
    from core.board_scanner import BoardScanner

    print(f"  Scanning repository: {repo_path}")

    scanner = GitScanner(repo_path)
    history = scanner.to_history_format(max_commits=50, since_days=sprint_days)

    if not history:
        print("  ⚠ No commits found in the last 14 days.")
        print("  Hint: Use --days 30 to scan a wider window.")
        sys.exit(0)

    print(f"  Found {len(history)} commits from {len(set(c['author'] for c in history))} contributors")

    # Auto-discover tickets from commit messages
    board_scanner = BoardScanner(history)
    board = board_scanner.discover_tickets()
    print(f"  Discovered {len(board)} tickets from commit messages")

    # Branch info
    branch_info = scanner.get_branch_info()
    print(f"  Current branch: {branch_info['current']}")

    return history, board


def parse_args():
    parser = argparse.ArgumentParser(
        description='AgileFlow - Sprint Intelligence Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agileflow --repo .                  Scan current directory
  agileflow --repo /path/to/project   Scan a specific repo
  agileflow --demo                    Run with mock data
  agileflow --repo . --days 30        Scan last 30 days
        """
    )
    parser.add_argument('--repo', type=str, help='Path to git repository to scan')
    parser.add_argument('--demo', action='store_true', help='Run with mock data (no repo needed)')
    parser.add_argument('--days', type=int, default=14, help='Number of days to scan (default: 14)')
    parser.add_argument('--sprint-days', type=int, default=14, help='Sprint length in days (default: 14)')
    parser.add_argument('--days-elapsed', type=int, default=7, help='Days elapsed in sprint (default: 7)')
    return parser.parse_args()


def main():
    args = parse_args()

    # ---- License Validation ----
    tier_name, tier_config = enforce_license()

    print("\n" + "=" * 60)
    print("   AGILEFLOW v6.0 - Sprint Intelligence Engine")
    print("   'Your team codes. I handle the rest.'")
    print("=" * 60)

    # ---- License Info ----
    license_info = print_license_info(tier_name, tier_config)
    print(f"\n  {license_info}")

    # ---- Data Loading ----
    if args.demo or (not args.repo):
        if not args.demo and not args.repo:
            print("\n  No --repo specified. Running in demo mode.")
            print("  Hint: Use --repo /path/to/project for real analysis.\n")
        git_path = os.getenv('GIT_HISTORY_PATH', 'mocks/git_history.json')
        board_path = os.getenv('PROJECT_BOARD_PATH', 'mocks/project_board.json')
        history, board = load_mock_data(git_path, board_path)
        mode = "DEMO"
    else:
        history, board = load_real_data(args.repo, args.days)
        mode = "LIVE"

    # Initialize LLM
    llm = LLMClient()
    info = llm.get_provider_info()
    print(f"  AI Engine: {info['provider']} ({info['model']}) - {info['status']}")
    print(f"  Mode: {mode}")

    # Initialize AI Analyser
    ai = AIAnalyser(history, board, llm)

    # ---- 1. AI Activity Analysis (all tiers) ----
    if check_module_access(tier_config, 'activity'):
        print_section("AI ACTIVITY ANALYSIS", "1")
        print("  Recent commits:")
        for commit in history:
            print(f"    [{commit['hash'][:7]}] {commit.get('author', 'unknown')}: {commit['message']}")

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

    # ---- 2. AI Board Sync (all tiers) ----
    if check_module_access(tier_config, 'board_sync'):
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

    # ---- 3. Predictive Health (all tiers) ----
    if check_module_access(tier_config, 'health'):
        print_section("PREDICTIVE HEALTH SCORE", "3")
        pa = PredictiveAgile(history, board)
        score, alerts = pa.calculate_health_score()
        print(f"  Project Health: {score}/100")
        for a in alerts:
            print(f"    -> {a}")
        if not alerts:
            print("    All clear. No health concerns detected.")

    # ---- 4. Technical Debt Sentinel (Pro/Team) ----
    if check_module_access(tier_config, 'debt'):
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
    else:
        print_section("TECHNICAL DEBT SENTINEL 🔒", "4")
        print("  ⬆ Upgrade to Pro to unlock this module.")

    # ---- 5. Sprint Velocity Forecast (Pro/Team) ----
    if check_module_access(tier_config, 'velocity'):
        print_section("SPRINT VELOCITY FORECAST", "5")
        sprint_days = args.sprint_days if hasattr(args, 'sprint_days') else 14
        days_elapsed = args.days_elapsed if hasattr(args, 'days_elapsed') else 7
        forecaster = VelocityForecaster(history, board,
                                        sprint_days=sprint_days,
                                        days_elapsed=days_elapsed)
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
    else:
        print_section("SPRINT VELOCITY FORECAST 🔒", "5")
        print("  ⬆ Upgrade to Pro to unlock this module.")

    # ---- 6. AI Sprint Narrative (Pro/Team) ----
    if check_module_access(tier_config, 'narrative'):
        print_section("AI SPRINT NARRATIVE", "6")
        health_score = score if 'score' in dir() else 50
        vel_data = forecast['velocity'] if 'forecast' in dir() else {'avg_daily': 0}
        debt_val = debt_score if 'debt_score' in dir() else 0

        narrative = ai.generate_sprint_narrative(
            health_score=health_score,
            velocity_data=vel_data,
            debt_data=debt_val
        )
        print(f"\n{narrative}")
    else:
        print_section("AI SPRINT NARRATIVE 🔒", "6")
        print("  ⬆ Upgrade to Pro to unlock AI-generated sprint narratives.")

    # ---- Summary ----
    print(f"\n{'='*60}")
    print("   AGILEFLOW SCAN COMPLETE")
    print(f"   {license_info}")
    print(f"   AI Provider: {info['provider']} | Model: {info['model']}")
    print(f"   Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
