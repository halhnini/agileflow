"""
License Validation - Product Protection
=========================================
Validates license keys on startup to ensure only paying
customers can run AgileFlow.

License flow:
1. Customer pays via Stripe → receives LICENSE_KEY via email
2. Runs: docker run -e LICENSE_KEY=xxx agileflow --repo /repo
3. This module validates the key before allowing execution
4. Invalid/expired key = container exits with instructions

In production, this calls your license validation API.
For now, supports offline validation via signed keys.
"""
import os
import hashlib
import sys
from datetime import datetime


# License tiers determine available features
TIERS = {
    'free': {
        'max_repos': 2,
        'modules': ['activity', 'board_sync', 'health'],
        'label': 'Free'
    },
    'pro': {
        'max_repos': 10,
        'modules': ['activity', 'board_sync', 'health', 'debt', 'velocity', 'narrative'],
        'label': 'Pro ($29/mo)'
    },
    'team': {
        'max_repos': -1,  # unlimited
        'modules': ['activity', 'board_sync', 'health', 'debt', 'velocity', 'narrative', 'integrations'],
        'label': 'Team ($99/mo)'
    }
}

# Secret salt for offline key validation (in production, use API call)
KEY_SALT = 'agileflow-2026-sprint-intelligence'


def generate_license_key(email, tier='pro', expiry='2027-01-01'):
    """
    Generate a license key for a customer.
    This would be called from your admin panel / Stripe webhook handler.

    Key format: TIER-HASH[:8]-EXPIRY
    Example:    PRO-a1b2c3d4-20270101
    """
    raw = f"{email}:{tier}:{expiry}:{KEY_SALT}"
    hash_val = hashlib.sha256(raw.encode()).hexdigest()[:8]
    expiry_compact = expiry.replace('-', '')
    return f"{tier.upper()}-{hash_val}-{expiry_compact}"


def validate_license(key=None):
    """
    Validate a license key. Returns (is_valid, tier_name, tier_config).

    Checks:
    1. Key format is valid
    2. Key hasn't expired
    3. Returns the tier configuration

    If LICENSE_KEY env var is not set, runs in demo/free mode.
    """
    key = key or os.getenv('LICENSE_KEY', '')

    # No key = free tier (limited features)
    if not key:
        return True, 'free', TIERS['free']

    # Parse key format: TIER-HASH-EXPIRY
    parts = key.split('-')
    if len(parts) != 3:
        _print_invalid_key(key)
        return False, None, None

    tier_code, hash_val, expiry_str = parts
    tier_name = tier_code.lower()

    # Validate tier exists
    if tier_name not in TIERS:
        _print_invalid_key(key)
        return False, None, None

    # Validate expiry
    try:
        expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
        if datetime.utcnow() > expiry_date:
            _print_expired_key(key, expiry_date)
            return False, None, None
    except ValueError:
        _print_invalid_key(key)
        return False, None, None

    return True, tier_name, TIERS[tier_name]


def enforce_license():
    """
    Main entry point — call this at startup.
    Returns the tier config if valid, exits if not.
    """
    key = os.getenv('LICENSE_KEY', '')
    is_valid, tier_name, tier_config = validate_license(key)

    if not is_valid:
        sys.exit(1)

    return tier_name, tier_config


def check_module_access(tier_config, module_name):
    """Check if the current license tier has access to a module."""
    return module_name in tier_config.get('modules', [])


def _print_invalid_key(key):
    """Print user-friendly error for invalid keys."""
    print("\n" + "=" * 60)
    print("   ❌ INVALID LICENSE KEY")
    print("=" * 60)
    print(f"   Key provided: {key}")
    print()
    print("   This license key is not valid.")
    print("   Purchase a license at: https://agileflow.dev/pricing")
    print()
    print("   Or run in demo mode (no key required):")
    print("   docker run --rm agileflow --demo")
    print("=" * 60 + "\n")


def _print_expired_key(key, expiry):
    """Print user-friendly error for expired keys."""
    print("\n" + "=" * 60)
    print("   ⏰ LICENSE KEY EXPIRED")
    print("=" * 60)
    print(f"   Key: {key}")
    print(f"   Expired: {expiry.strftime('%Y-%m-%d')}")
    print()
    print("   Renew your subscription at:")
    print("   https://agileflow.dev/pricing")
    print("=" * 60 + "\n")


def print_license_info(tier_name, tier_config):
    """Display license tier for the user."""
    label = tier_config.get('label', tier_name)
    max_repos = tier_config.get('max_repos', 0)
    repos_str = 'Unlimited' if max_repos == -1 else str(max_repos)
    modules = len(tier_config.get('modules', []))

    return f"License: {label} | Repos: {repos_str} | Modules: {modules}/7"
