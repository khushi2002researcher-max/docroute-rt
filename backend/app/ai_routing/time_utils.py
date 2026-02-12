from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import pytz

from app.ai_routing.models import ReminderUnit, ReminderDirection

TIMEZONE = pytz.timezone("Asia/Kolkata")
DEFAULT_SEND_TIME = time(9, 0)  # 9:00 AM IST


def calculate_trigger_datetime(
    *,
    deadline_date,
    trigger_value: int | None,
    trigger_unit: ReminderUnit,
    direction: ReminderDirection | None,
) -> datetime:
    """
    Calculate exact datetime when reminder should fire
    """

    base_datetime = datetime.combine(deadline_date, DEFAULT_SEND_TIME)
    base_datetime = TIMEZONE.localize(base_datetime)

    # ✅ EXACT = same day, default send time
    if trigger_unit == ReminderUnit.EXACT:
        return base_datetime

    # 🛡️ Safety: missing values fallback
    if not trigger_value or not direction:
        return base_datetime

    if trigger_unit == ReminderUnit.DAY:
        delta = timedelta(days=trigger_value)
    elif trigger_unit == ReminderUnit.WEEK:
        delta = timedelta(weeks=trigger_value)
    elif trigger_unit == ReminderUnit.MONTH:
        delta = relativedelta(months=trigger_value)
    else:
        return base_datetime

    if direction == ReminderDirection.BEFORE:
        return base_datetime - delta
    else:
        return base_datetime + delta
