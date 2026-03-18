from datetime import datetime
from cosec_client import get_cosec_punches
from hrms_client import (
    fetch_hrms_activities,
    calculate_hrms_punch_count,
    batch_clock_in,
    batch_clock_out
)
from logger import logger


def convert_cosec_date(processdate):
    """
    Convert COSEC date format DD/MM/YYYY to YYYY-MM-DD (HRMS format).
    """
    dt = datetime.strptime(processdate, "%d/%m/%Y")
    return dt.strftime("%Y-%m-%d")


def build_datetime_str(date_str, time_str):
    """
    Combine date (YYYY-MM-DD) and time (HH:MM:SS) into ISO datetime string.
    e.g. "2026-03-16T09:40:53"
    """
    return f"{date_str}T{time_str}"


def push_single_punch(badge_id, username, position, datetime_str):
    """
    Push a single punch to HRMS as clock-in or clock-out based on position.
    Odd position = Clock-IN, Even position = Clock-OUT.
    Returns True if successful, False if failed.
    """
    action = "Clock-IN" if position % 2 == 1 else "Clock-OUT"
    employee_payload = [{"badge_id": badge_id, "datetime": datetime_str}]

    if position % 2 == 1:
        response = batch_clock_in(employee_payload)
    else:
        response = batch_clock_out(employee_payload)

    if not response:
        logger.error(
            f"[{username}] Punch {position} ({action}) — "
            f"No response from HRMS at {datetime_str}"
        )
        return False

    result = response.get("results", [{}])[0]
    if result.get("success"):
        logger.info(
            f"[{username}] Punch {position} ({action}) OK — {datetime_str}"
        )
        return True
    else:
        logger.warning(
            f"[{username}] Punch {position} ({action}) FAILED — "
            f"{datetime_str} | reason: {result.get('error', 'unknown')}"
        )
        return False


def process_employee(record):
    """
    Compare COSEC punches vs HRMS activities for one employee
    and push any new punches to HRMS sequentially (IN -> OUT -> IN -> OUT).
    """
    badge_id = record.get("integration_reference", "").strip()
    username = record.get("username", "unknown")
    processdate = record.get("processdate", "")

    # Convert date format
    try:
        date_str = convert_cosec_date(processdate)
    except ValueError:
        logger.error(f"[{username}] Invalid processdate format: {processdate}")
        return {"badge_id": badge_id, "status": "error", "reason": "invalid date"}

    # Get punches from COSEC
    cosec_punches = get_cosec_punches(record)
    cosec_count = len(cosec_punches)

    if cosec_count == 0:
        logger.info(f"[{username}] No punches in COSEC today. Skipping.")
        return {"badge_id": badge_id, "status": "skipped", "reason": "no cosec punches"}

    # Get activities from HRMS
    hrms_activities = fetch_hrms_activities(badge_id, date_str)
    if hrms_activities is None:
        logger.error(f"[{username}] Could not fetch HRMS activities. Skipping.")
        return {"badge_id": badge_id, "status": "error", "reason": "hrms fetch failed"}

    hrms_count = calculate_hrms_punch_count(hrms_activities)

    logger.info(
        f"[{username}] COSEC punches: {cosec_count} | HRMS punches: {hrms_count}"
    )

    # Nothing new to push
    if cosec_count <= hrms_count:
        logger.info(f"[{username}] No new punches. Already in sync.")
        return {"badge_id": badge_id, "status": "in_sync"}

    # Find new punches (everything after what HRMS already has)
    new_punches = cosec_punches[hrms_count:]
    logger.info(
        f"[{username}] {len(new_punches)} new punch(es) to push: {new_punches}"
    )

    pushed = 0
    failed = 0

    # Push each punch one by one in strict order IN -> OUT -> IN -> OUT
    for i, punch_time in enumerate(new_punches):
        # Position in full punch sequence (1-based)
        position = hrms_count + i + 1
        datetime_str = build_datetime_str(date_str, punch_time)

        success = push_single_punch(badge_id, username, position, datetime_str)

        if success:
            pushed += 1
        else:
            failed += 1
            # Stop pushing further punches for this employee on failure.
            # Next run will re-compare with HRMS and pick up from correct position.
            logger.warning(
                f"[{username}] Stopping further punches due to failure at "
                f"punch {position}. Will retry on next run."
            )
            break

    return {
        "badge_id": badge_id,
        "status": "done",
        "pushed": pushed,
        "failed": failed
    }


def run_sync(cosec_records):
    """
    Process all COSEC records and push new punches to HRMS.
    """
    results = []

    for record in cosec_records:
        result = process_employee(record)
        results.append(result)

    return results