import json
import os

PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profile.json")


def save_profile(profile: dict):
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)


def load_profile() -> dict | None:
    if not os.path.exists(PROFILE_PATH):
        return None
    try:
        with open(PROFILE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
