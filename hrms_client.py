import os
import requests
from dotenv import load_dotenv
from logger import logger

# load_dotenv() respects already-set system env variables (Portainer).
# On local it loads from .env file. On Portainer, system vars take priority.
load_dotenv()

_token = None  # cached token for this run


def get_hrms_token():
    """
    Login to HRMS and return JWT access token.
    Token is cached for the duration of the script run.
    """
    global _token
    if _token:
        return _token

    base_url = os.getenv("HRMS_BASE_URL")
    username = os.getenv("HRMS_USERNAME")
    password = os.getenv("HRMS_PASSWORD")

    url = f"{base_url}/api/auth/login/"
    payload = {"username": username, "password": password}

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        _token = data.get("access")
        if not _token:
            logger.error("HRMS login succeeded but no access token returned.")
            return None
        logger.info("HRMS login successful.")
        return _token
    except requests.exceptions.RequestException as e:
        logger.error(f"HRMS login failed: {e}")
        return None


def fetch_hrms_activities(badge_id, date_str):
    """
    Fetch attendance activities from HRMS for a specific employee and date.
    date_str format: YYYY-MM-DD
    Returns list of activity records sorted by clock_in ascending.
    """
    base_url = os.getenv("HRMS_BASE_URL")
    token = get_hrms_token()
    if not token:
        return None

    url = f"{base_url}/api/attendance/attendance-activity/"
    params = {"badge_id": badge_id, "date": date_str}
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            logger.error(f"HRMS activity fetch failed for badge {badge_id}: {data}")
            return None

        # Sort by clock_in to ensure correct order
        activities = sorted(
            data.get("data", []),
            key=lambda x: x.get("clock_in") or ""
        )
        return activities

    except requests.exceptions.RequestException as e:
        logger.error(f"HRMS fetch activities failed for badge {badge_id}: {e}")
        return None


def calculate_hrms_punch_count(activities):
    """
    Calculate how many punches are already recorded in HRMS.

    Each complete activity (clock_out not null) = 2 punches (IN + OUT)
    Last activity with clock_out = null = 1 punch (IN only, awaiting OUT)

    Example:
        Activity 1: clock_in=09:40, clock_out=09:53  -> 2 punches
        Activity 2: clock_in=10:04, clock_out=null   -> 1 punch
        Total = 3
    """
    if not activities:
        return 0

    count = 0
    for activity in activities:
        if activity.get("clock_out"):
            count += 2  # complete pair
        else:
            count += 1  # only clock-in recorded, awaiting clock-out
    return count


def batch_clock_in(employees):
    """
    Clock in multiple employees at once.
    employees: list of {"badge_id": ..., "datetime": "YYYY-MM-DDTHH:MM:SS"}
    Returns API response data.
    """
    base_url = os.getenv("HRMS_BASE_URL")
    token = get_hrms_token()
    if not token:
        return None

    url = f"{base_url}/api/attendance/admin/batch-clock-in/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"employees": employees}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"HRMS batch clock-in failed: {e}")
        return None


def batch_clock_out(employees):
    """
    Clock out multiple employees at once.
    employees: list of {"badge_id": ..., "datetime": "YYYY-MM-DDTHH:MM:SS"}
    Returns API response data.
    """
    base_url = os.getenv("HRMS_BASE_URL")
    token = get_hrms_token()
    if not token:
        return None

    url = f"{base_url}/api/attendance/admin/batch-clock-out/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"employees": employees}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"HRMS batch clock-out failed: {e}")
        return None