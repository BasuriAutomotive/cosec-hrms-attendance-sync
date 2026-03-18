import os
from dotenv import load_dotenv
from logger import logger
from cosec_client import fetch_cosec_attendance
from sync import run_sync

# Load environment variables from .env file
load_dotenv()


def main():
    logger.info("=" * 60)
    logger.info("COSEC → HRMS Attendance Sync Started")
    logger.info("=" * 60)

    # Step 1: Fetch today's attendance from COSEC
    cosec_records = fetch_cosec_attendance()

    if not cosec_records:
        logger.warning("No valid COSEC records found. Sync complete (nothing to do).")
        return

    logger.info(f"Processing {len(cosec_records)} employee record(s)...")

    # Step 2: Compare with HRMS and push new punches
    results = run_sync(cosec_records)

    # Step 3: Final summary
    total = len(results)
    in_sync = sum(1 for r in results if r.get("status") == "in_sync")
    pushed = sum(1 for r in results if r.get("status") == "pending")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    errors = sum(1 for r in results if r.get("status") == "error")

    logger.info("=" * 60)
    logger.info(f"Sync Complete — Total: {total} | "
                f"Pushed: {pushed} | In-sync: {in_sync} | "
                f"Skipped: {skipped} | Errors: {errors}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()