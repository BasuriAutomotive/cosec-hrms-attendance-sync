import os
import requests
from requests.auth import HTTPBasicAuth
from logger import logger

FIELDS = ",".join([
    "userid", "username", "processdate",
    "punch1_time", "punch2_time", "punch3_time",
    "punch4_time", "punch5_time", "punch6_time",
    "outpunch_time", "workingshift", "latein",
    "earlyout", "overtime", "worktime", "integration_reference"
])


def format_cosec_date(date_str):
    """
    Convert YYYY-MM-DD to COSEC date format DDMMYYYY.
    e.g. "2026-03-17" -> "17032026"
    """
    parts = date_str.split("-")
    return f"{parts[2]}{parts[1]}{parts[0]}"


def fetch_cosec_attendance(date_str=None):
    """
    Fetch attendance records from COSEC Centra.

    - If date_str is None  -> fetches today's records (default behaviour)
    - If date_str provided -> fetches that specific date (format: YYYY-MM-DD)

    Skips employees with empty integration_reference.
    Returns list of valid attendance records.
    """
    base_url = os.getenv("COSEC_BASE_URL")
    username = os.getenv("COSEC_USERNAME")
    password = os.getenv("COSEC_PASSWORD")

    # Build URL based on whether a date is provided or not
    if date_str:
        cosec_date = format_cosec_date(date_str)
        url = (
            f"{base_url}/COSEC/api.svc/v2/attendance-daily"
            f"?action=get;format=json"
            f";date-range={cosec_date}-{cosec_date}"
            f";field-name={FIELDS}"
        )
        logger.info(f"COSEC: Fetching records for date {date_str}...")
    else:
        url = (
            f"{base_url}/COSEC/api.svc/v2/attendance-daily"
            f"?action=get;format=json;field-name={FIELDS}"
        )
        logger.info("COSEC: Fetching today's records...")

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        all_records = data.get("attendance-daily", [])

        # Filter out employees with empty integration_reference
        valid_records = []
        skipped = 0
        for record in all_records:
            ref = record.get("integration_reference", "").strip()
            if not ref:
                logger.warning(
                    f"Skipping employee '{record.get('username')}' "
                    f"(userid: {record.get('userid')}) — empty integration_reference"
                )
                skipped += 1
            else:
                valid_records.append(record)

        logger.info(
            f"COSEC: Fetched {len(all_records)} records. "
            f"Valid: {len(valid_records)}, Skipped (no ref): {skipped}"
        )
        return valid_records

    except requests.exceptions.RequestException as e:
        logger.error(f"COSEC fetch failed: {e}")
        return []


def get_cosec_punches(record):
    """
    Extract non-empty punch times from a COSEC record in order.
    Returns list of time strings e.g. ['09:40:53', '09:53:06', '10:04:53']
    """
    punch_fields = [
        "punch1_time", "punch2_time", "punch3_time",
        "punch4_time", "punch5_time", "punch6_time"
    ]
    return [
        record[field].strip()
        for field in punch_fields
        if record.get(field, "").strip()
    ]