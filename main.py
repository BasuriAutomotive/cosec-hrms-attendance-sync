from dotenv import load_dotenv
from logger import logger
from cosec_client import fetch_cosec_attendance
from sync import run_sync

# load_dotenv() respects already-set system env variables (Portainer).
# On local it loads from .env file. On Portainer, system vars take priority.
load_dotenv()


def main():
    logger.info("=" * 60)
    logger.info("COSEC -> HRMS Attendance Sync Started (Today)")
    logger.info("=" * 60)

    # Fetch today's attendance from COSEC (no date = today)
    cosec_records = fetch_cosec_attendance()

    if not cosec_records:
        logger.warning("No valid COSEC records found. Nothing to sync.")
        return

    logger.info(f"Processing {len(cosec_records)} employee record(s)...")

    results = run_sync(cosec_records)

    # Final summary
    total = len(results)
    in_sync = sum(1 for r in results if r.get("status") == "in_sync")
    pushed = sum(1 for r in results if r.get("status") == "done")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    errors = sum(1 for r in results if r.get("status") == "error")

    logger.info("=" * 60)
    logger.info(
        f"Sync Complete — Total: {total} | Pushed: {pushed} | "
        f"In-sync: {in_sync} | Skipped: {skipped} | Errors: {errors}"
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()