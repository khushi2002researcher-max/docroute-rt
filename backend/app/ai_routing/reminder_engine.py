from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


from sqlalchemy.orm import Session

from app.ai_routing.models import (
    RoutingReminder,
    RoutingDeadline,
    ReminderUnit,
    ReminderDirection,
    ReminderHistory,
    ReminderStatus,
)


def calculate_trigger_date(
    *,
    deadline_date: date,
    trigger_value: int | None,
    trigger_unit: ReminderUnit,
    direction: ReminderDirection | None,
) -> date:
    """
    DATE-ONLY trigger calculation.
    """

    base_date = deadline_date

    if trigger_unit == ReminderUnit.EXACT:
        return base_date

    if trigger_value is None or direction is None:
        return base_date

    if trigger_unit == ReminderUnit.DAY:
        delta = timedelta(days=trigger_value)
    elif trigger_unit == ReminderUnit.WEEK:
        delta = timedelta(weeks=trigger_value)
    elif trigger_unit == ReminderUnit.MONTH:
        delta = relativedelta(months=trigger_value)
    else:
        return base_date

    if direction == ReminderDirection.BEFORE:
        return base_date - delta
    else:
        return base_date + delta


def should_trigger_now(
    *,
    reminder: RoutingReminder,
    deadline: RoutingDeadline,
    today: date,
) -> bool:
    """
    Decide whether a reminder should fire (DATE-ONLY).
    """

    trigger_date = calculate_trigger_date(
        deadline_date=deadline.deadline_date,
        trigger_value=reminder.trigger_value,
        trigger_unit=reminder.trigger_unit,
        direction=reminder.direction,
    )

    return today >= trigger_date


def mark_reminder_sent(
    db: Session,
    reminder: RoutingReminder,
    history: ReminderHistory,
):
    history.status = ReminderStatus.SENT
    history.sent_on = date.today()  # ✅ correct column name

    reminder.active = False

    db.add(history)
    db.add(reminder)
    db.commit()
