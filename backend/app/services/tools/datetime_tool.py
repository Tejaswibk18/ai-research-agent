from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_time(
    timezone: str = "Asia/Kolkata"
) -> dict:
    """
    Get the current date and time for a timezone.

    Args:
        timezone: IANA timezone such as Asia/Kolkata,
                  America/New_York, or Europe/London.

    Returns:
        Current date and time information.
    """

    try:
        tz = ZoneInfo(timezone)

        now = datetime.now(tz)

        return {
            "timezone": timezone,
            "datetime": now.isoformat(),
            "date": now.strftime(
                "%Y-%m-%d"
            ),
            "time": now.strftime(
                "%H:%M:%S"
            ),
            "day": now.strftime(
                "%A"
            ),
        }

    except Exception as exc:
        return {
            "error": (
                f"Invalid timezone or "
                f"unable to get time: {str(exc)}"
            )
        }