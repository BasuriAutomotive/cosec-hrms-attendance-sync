from datetime import datetime, timedelta
from dotenv import load_dotenv
from logger import logger
from cosec_client import fetch_cosec_attendance
from sync import run_sync

# load_dotenv() respects already-set system env variables (Portainer).
# On local it loads from .env file. On Portainer, system vars take priority.
load_dotenv()


def sync_date(date_str):
    """
    Run full sync for a specific date.
    date_str format: YYYY-MM-DD
    """
    logger.info("=" * 60)
    logger.info(f"Backfill Sync — Date: {date_str}")
    logger.info("=" * 60)

    cosec_records = fetch_cosec_attendance(date_str=date_str)

    if not cosec_records:
        logger.warning(f"No valid COSEC records found for {date_str}. Skipping.")
        return

    logger.info(f"Processing {len(cosec_records)} employee record(s) for {date_str}...")

    results = run_sync(cosec_records)

    # Summary for this date
    total = len(results)
    in_sync = sum(1 for r in results if r.get("status") == "in_sync")
    pushed = sum(1 for r in results if r.get("status") == "done")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    errors = sum(1 for r in results if r.get("status") == "error")

    logger.info(
        f"Date {date_str} Complete — Total: {total} | Pushed: {pushed} | "
        f"In-sync: {in_sync} | Skipped: {skipped} | Errors: {errors}"
    )


def main():
    today = datetime.now().date()

    # Calculate last 3 days (not including today — today is handled by main.py)
    backfill_dates = [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, 4)  # 1, 2, 3 days ago
    ]

    logger.info("=" * 60)
    logger.info(f"Backfill Sync Started — Dates: {backfill_dates}")
    logger.info("=" * 60)

    for date_str in backfill_dates:
        sync_date(date_str)

    logger.info("=" * 60)
    logger.info("Backfill Sync Completed for all 3 days")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()