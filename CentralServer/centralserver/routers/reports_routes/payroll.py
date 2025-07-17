# pylint: disable=C0302
import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from centralserver.internals.auth_handler import (
    get_user,
    verify_access_token,
    verify_user_permission,
)
from centralserver.internals.db_handler import get_db_session
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models.reports.monthly_report import (
    MonthlyReport,
    ReportStatus,
)
from centralserver.internals.models.reports.payroll_report import (
    PayrollEntryRequest,
    PayrollEntryUpdateRequest,
    PayrollReport,
    PayrollReportEntry,
    PayrollReportUpdateRequest,
)
from centralserver.internals.models.reports.report_status_manager import (
    ReportStatusManager,
)
from centralserver.internals.models.reports.status_change_request import (
    StatusChangeRequest,
)
from centralserver.internals.models.school import School
from centralserver.internals.models.token import DecodedJWTToken

logger = LoggerFactory().get_logger(__name__)


async def get_school_assigned_noted_by(school_id: int, session: Session) -> str | None:
    """Get the assigned noted by user for a school."""
    school = session.get(School, school_id)
    if school and school.assignedNotedBy:
        return school.assignedNotedBy
    return None


router = APIRouter(prefix="/payroll")
logged_in_dep = Annotated[DecodedJWTToken, Depends(verify_access_token)]


@router.get("/{school_id}/{year}/{month}")
async def get_school_payroll_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
) -> PayrollReport:
    """Get payroll report of a school for a specific month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to get reports for.
        year: The year of the report.
        month: The month of the report.

    Returns:
        The payroll report for the specified school, year, and month.

    Raises:
        HTTPException: If the user is not found, lacks permission, or the report is not found.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:read" if user.schoolId == school_id else "reports:global:read"
    )
    logger.debug("Required permission for user %s: %s", token.id, required_permission)
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view payroll reports.",
        )

    logger.debug(
        "user `%s` requesting payroll report of school %s for %s-%s.",
        token.id,
        school_id,
        year,
        month,
    )
    try:
        selected_monthly_report = session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == datetime.date(year=year, month=month, day=1),
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()
        if selected_monthly_report.payroll_report is not None:
            return selected_monthly_report.payroll_report

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        )

    except NoResultFound as e:
        logger.warning(
            "Payroll report not found for school %s for %s-%s",
            school_id,
            year,
            month,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        ) from e


@router.get("/{school_id}/{year}/{month}/entries")
async def get_school_payroll_report_entries(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
) -> list[PayrollReportEntry]:
    """Get all payroll report entries for a school for a specific month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to get reports for.
        year: The year of the report.
        month: The month of the report.

    Returns:
        A list of payroll report entries for the specified school, year, and month.

    Raises:
        HTTPException: If the user is not found, lacks permission, or the report is not found.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:read" if user.schoolId == school_id else "reports:global:read"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view payroll report entries.",
        )

    logger.debug(
        "user `%s` requesting payroll report entries of school %s for %s-%s.",
        token.id,
        school_id,
        year,
        month,
    )

    try:
        selected_monthly_report = session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == datetime.date(year=year, month=month, day=1),
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()

    except NoResultFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        ) from e

    payroll_report = selected_monthly_report.payroll_report
    if payroll_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        )

    return list(payroll_report.entries)


@router.patch("/{school_id}/{year}/{month}")
async def create_school_payroll_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    noted_by: str | None = None,
) -> PayrollReport:
    """Create or update a payroll report of a school for a specific month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to create or update the report for.
        year: The year of the report.
        month: The month of the report.
        noted_by: The user who noted the report (optional).

    Returns:
        The created or updated payroll report.

    Raises:
        HTTPException: If the user is not found or lacks permission.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:write" if user.schoolId == school_id else "reports:global:write"
    )
    logger.debug("Required permission for user %s: %s", token.id, required_permission)
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create payroll reports.",
        )

    logger.debug(
        "user `%s` creating or updating payroll report of school %s for %s-%s.",
        token.id,
        school_id,
        year,
        month,
    )

    # If no noted_by is provided, try to get it from the school's assignedNotedBy
    if noted_by is None:
        noted_by = await get_school_assigned_noted_by(school_id, session)

    selected_monthly_report = session.exec(
        select(MonthlyReport).where(
            MonthlyReport.id == datetime.date(year=year, month=month, day=1),
            MonthlyReport.submittedBySchool == school_id,
        )
    ).one_or_none()
    if selected_monthly_report is None:
        selected_monthly_report = MonthlyReport(
            id=datetime.date(year=year, month=month, day=1),
            name=f"Monthly Report for {datetime.date(year=year, month=month, day=1).strftime('%B %Y')}",
            submittedBySchool=school_id,
            reportStatus=ReportStatus.DRAFT,
            preparedBy=user.id,
            notedBy=noted_by,
        )
        session.add(selected_monthly_report)

    # Check if payroll report already exists for this monthly report
    existing_payroll_report = session.exec(
        select(PayrollReport).where(PayrollReport.parent == selected_monthly_report.id)
    ).one_or_none()

    if existing_payroll_report is None:
        new_payroll_report = PayrollReport(
            parent=selected_monthly_report.id,
            schoolId=school_id,
            preparedBy=user.id,  # Required field - always set to current user
            notedBy=noted_by,  # Nullable field - can be None
        )
        session.add(new_payroll_report)
        session.commit()
        session.refresh(selected_monthly_report)
        session.refresh(new_payroll_report)
        return new_payroll_report
    else:
        # Return the existing payroll report
        session.commit()  # Still commit in case monthly report was created
        session.refresh(selected_monthly_report)
        return existing_payroll_report


@router.post("/{school_id}/{year}/{month}/entries")
async def create_payroll_report_entry(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    entry_data: PayrollEntryRequest,
) -> PayrollReportEntry:
    """Create a new payroll report entry for a school for a specific month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to create the entry for.
        year: The year of the report.
        month: The month of the report.
        entry_data: The payroll entry data.

    Returns:
        The created payroll report entry.

    Raises:
        HTTPException: If the user is not found, lacks permission, or the report is not found.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:write" if user.schoolId == school_id else "reports:global:write"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create payroll report entries.",
        )

    logger.debug(
        "user `%s` creating payroll report entry for school %s for %s-%s, week %s, employee %s.",
        token.id,
        school_id,
        year,
        month,
        entry_data.week_number,
        "*" * len(entry_data.employee_name),
    )

    # Ensure the payroll report exists
    try:
        selected_monthly_report = session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == datetime.date(year=year, month=month, day=1),
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()

    except NoResultFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        ) from e

    payroll_report = selected_monthly_report.payroll_report
    if payroll_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found. Create the payroll report first.",
        )

    # Check if entry already exists (composite primary key: parent, weekNumber, employee_name)
    existing_entry = session.exec(
        select(PayrollReportEntry).where(
            PayrollReportEntry.parent == payroll_report.parent,
            PayrollReportEntry.weekNumber == entry_data.week_number,
            PayrollReportEntry.employeeName == entry_data.employee_name,
        )
    ).one_or_none()

    if existing_entry:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payroll entry for week {entry_data.week_number} and employee {entry_data.employee_name} already exists.",
        )

    new_entry = PayrollReportEntry(
        parent=payroll_report.parent,
        schoolId=school_id,
        weekNumber=entry_data.week_number,
        employeeName=entry_data.employee_name,
        sun=entry_data.sun,
        mon=entry_data.mon,
        tue=entry_data.tue,
        wed=entry_data.wed,
        thu=entry_data.thu,
        fri=entry_data.fri,
        sat=entry_data.sat,
        signature=entry_data.signature,
    )

    session.add(new_entry)
    session.commit()
    session.refresh(new_entry)
    return new_entry


@router.post("/{school_id}/{year}/{month}/entries/bulk")
async def create_bulk_payroll_report_entries(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    entries: list[PayrollEntryRequest],
) -> list[PayrollReportEntry]:
    """Create multiple payroll report entries at once.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to create entries for.
        year: The year of the report.
        month: The month of the report.
        entries: List of payroll entry data.

    Returns:
        List of created payroll report entries.

    Raises:
        HTTPException: If the user is not found, lacks permission, or the report is not found.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:write" if user.schoolId == school_id else "reports:global:write"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create payroll report entries.",
        )

    if not entries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No entries provided.",
        )

    logger.debug(
        "user `%s` creating bulk payroll report entries for school %s for %s-%s.",
        token.id,
        school_id,
        year,
        month,
    )

    # Check if the monthly report exists, create if not
    monthly_report = session.exec(
        select(MonthlyReport).where(
            MonthlyReport.id == datetime.date(year=year, month=month, day=1),
            MonthlyReport.submittedBySchool == school_id,
        )
    ).one_or_none()

    if monthly_report is None:
        monthly_report = MonthlyReport(
            id=datetime.date(year=year, month=month, day=1),
            name=f"Monthly Report for {datetime.date(year=year, month=month, day=1).strftime('%B %Y')}",
            submittedBySchool=school_id,
            reportStatus=ReportStatus.DRAFT,
            preparedBy=user.id,
        )
        session.add(monthly_report)

    # Check if the payroll report exists, create if not
    payroll_report = session.exec(
        select(PayrollReport).where(
            PayrollReport.parent == datetime.date(year=year, month=month, day=1),
        )
    ).one_or_none()

    if payroll_report is None:
        # Get the school's assigned noted by user
        noted_by = await get_school_assigned_noted_by(school_id, session)

        payroll_report = PayrollReport(
            parent=datetime.date(year=year, month=month, day=1),
            schoolId=school_id,
            preparedBy=user.id,
            notedBy=noted_by,
        )
        session.add(payroll_report)

    # Check for existing entries
    existing_entries = session.exec(
        select(PayrollReportEntry).where(
            PayrollReportEntry.parent == datetime.date(year=year, month=month, day=1),
        )
    ).all()

    existing_entries_set = {
        (entry.weekNumber, entry.employeeName) for entry in existing_entries
    }

    # Create new entries, skip existing ones
    new_entries: list[PayrollReportEntry] = []
    skipped_entries: list[tuple[int, str]] = []

    for entry_data in entries:
        entry_key = (entry_data.week_number, entry_data.employee_name)
        if entry_key in existing_entries_set:
            skipped_entries.append(entry_key)
            continue

        new_entry = PayrollReportEntry(
            parent=datetime.date(year=year, month=month, day=1),
            schoolId=school_id,
            weekNumber=entry_data.week_number,
            employeeName=entry_data.employee_name,
            sun=entry_data.sun,
            mon=entry_data.mon,
            tue=entry_data.tue,
            wed=entry_data.wed,
            thu=entry_data.thu,
            fri=entry_data.fri,
            sat=entry_data.sat,
            signature=entry_data.signature,
        )
        new_entries.append(new_entry)
        session.add(new_entry)

    session.commit()

    # Refresh all new entries
    for entry in new_entries:
        session.refresh(entry)

    if skipped_entries:
        logger.info(
            "Skipped %d existing entries for user %s",
            len(skipped_entries),
            token.id,
        )

    return new_entries


@router.put("/{school_id}/{year}/{month}/entries/{week_number}/{employee_name}")
async def update_payroll_report_entry(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    week_number: int,
    employee_name: str,
    entry_data: PayrollEntryUpdateRequest,
) -> PayrollReportEntry:
    """Update an existing payroll report entry for a school for a specific month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to update the entry for.
        year: The year of the report.
        month: The month of the report.
        week_number: The week number in the month.
        employee_name: The employee name.
        entry_data: The updated entry data.

    Returns:
        The updated payroll report entry.

    Raises:
        HTTPException: If the user is not found, lacks permission, or the entry is not found.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:write" if user.schoolId == school_id else "reports:global:write"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update payroll report entries.",
        )

    logger.debug(
        "user `%s` updating payroll report entry for school %s for %s-%s, week %s, employee %s.",
        token.id,
        school_id,
        year,
        month,
        week_number,
        "*" * len(employee_name),
    )

    # Find the existing entry
    try:
        selected_monthly_report = session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == datetime.date(year=year, month=month, day=1),
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()

    except NoResultFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        ) from e

    payroll_report = selected_monthly_report.payroll_report
    if payroll_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        )

    existing_entry = session.exec(
        select(PayrollReportEntry).where(
            PayrollReportEntry.parent == payroll_report.parent,
            PayrollReportEntry.weekNumber == week_number,
            PayrollReportEntry.employeeName == employee_name,
        )
    ).one_or_none()

    if not existing_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll entry for week {week_number} and employee {employee_name} not found.",
        )

    # Update only the provided fields
    if entry_data.sun is not None:
        existing_entry.sun = entry_data.sun
    if entry_data.mon is not None:
        existing_entry.mon = entry_data.mon
    if entry_data.tue is not None:
        existing_entry.tue = entry_data.tue
    if entry_data.wed is not None:
        existing_entry.wed = entry_data.wed
    if entry_data.thu is not None:
        existing_entry.thu = entry_data.thu
    if entry_data.fri is not None:
        existing_entry.fri = entry_data.fri
    if entry_data.sat is not None:
        existing_entry.sat = entry_data.sat
    if entry_data.signature is not None:
        existing_entry.signature = entry_data.signature

    session.add(existing_entry)
    session.commit()
    session.refresh(existing_entry)
    return existing_entry


@router.delete("/{school_id}/{year}/{month}/entries/{week_number}/{employee_name}")
async def delete_payroll_report_entry(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    week_number: int,
    employee_name: str,
) -> dict[str, str]:
    """Delete a payroll report entry for a school for a specific month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to delete the entry for.
        year: The year of the report.
        month: The month of the report.
        week_number: The week number in the month.
        employee_name: The employee name.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: If the user is not found, lacks permission, or the entry is not found.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:write" if user.schoolId == school_id else "reports:global:write"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete payroll report entries.",
        )

    logger.debug(
        "user `%s` deleting payroll report entry for school %s for %s-%s, week %s, employee %s.",
        token.id,
        school_id,
        year,
        month,
        week_number,
        "*" * len(employee_name),
    )

    # Find the existing entry
    try:
        selected_monthly_report = session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == datetime.date(year=year, month=month, day=1),
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()

    except NoResultFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        ) from e

    payroll_report = selected_monthly_report.payroll_report
    if payroll_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        )

    existing_entry = session.exec(
        select(PayrollReportEntry).where(
            PayrollReportEntry.parent == payroll_report.parent,
            PayrollReportEntry.weekNumber == week_number,
            PayrollReportEntry.employeeName == employee_name,
        )
    ).one_or_none()

    if not existing_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll entry for week {week_number} and employee {employee_name} not found.",
        )

    session.delete(existing_entry)
    session.commit()
    return {
        "message": f"Payroll entry for week {week_number} and employee {employee_name} deleted successfully."
    }


@router.put("/{school_id}/{year}/{month}")
async def update_payroll_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    update_data: PayrollReportUpdateRequest,
) -> PayrollReport:
    """Update payroll report metadata for a school for a specific month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to update the report for.
        year: The year of the report.
        month: The month of the report.
        update_data: The fields to update.

    Returns:
        The updated payroll report.

    Raises:
        HTTPException: If the user is not found, lacks permission, or the report is not found.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:write" if user.schoolId == school_id else "reports:global:write"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update payroll reports.",
        )

    logger.debug(
        "user `%s` updating payroll report metadata for school %s for %s-%s.",
        token.id,
        school_id,
        year,
        month,
    )

    try:
        selected_monthly_report = session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == datetime.date(year=year, month=month, day=1),
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()

    except NoResultFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        ) from e

    payroll_report = selected_monthly_report.payroll_report
    if payroll_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        )

    # Update only the provided fields
    if update_data.prepared_by is not None:
        if (
            not update_data.prepared_by.strip()
        ):  # Validation: preparedBy cannot be empty
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="preparedBy cannot be empty.",
            )
        payroll_report.preparedBy = update_data.prepared_by
    if update_data.noted_by is not None:
        payroll_report.notedBy = update_data.noted_by

    session.add(payroll_report)
    session.commit()
    session.refresh(payroll_report)
    return payroll_report


@router.delete("/{school_id}/{year}/{month}")
async def delete_school_payroll_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
) -> dict[str, str]:
    """Delete a payroll report for a school for a specific month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to delete the report for.
        year: The year of the report.
        month: The month of the report.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: If the user is not found, lacks permission, or the report is not found.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:write" if user.schoolId == school_id else "reports:global:write"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete payroll reports.",
        )

    logger.debug(
        "user `%s` deleting payroll report of school %s for %s-%s.",
        token.id,
        school_id,
        year,
        month,
    )

    try:
        selected_monthly_report = session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == datetime.date(year=year, month=month, day=1),
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()

    except NoResultFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        ) from e

    payroll_report = selected_monthly_report.payroll_report
    if payroll_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        )

    # Reason: Deleting the payroll report will cascade delete all entries due to foreign key constraints
    session.delete(payroll_report)
    session.commit()
    return {"message": "Payroll report deleted successfully."}


@router.patch("/{school_id}/{year}/{month}/status")
async def change_payroll_report_status(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    status_change: StatusChangeRequest,
) -> PayrollReport:
    """Change the status of a payroll report based on user role and permissions.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school the report belongs to.
        year: The year of the report.
        month: The month of the report.
        status_change: The status change request containing new status and optional comments.

    Returns:
        The updated payroll report.

    Raises:
        HTTPException: If user doesn't have permission, report not found, or invalid transition.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    # Check basic permission to read reports
    required_permission = (
        "reports:local:read" if user.schoolId == school_id else "reports:global:read"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this report.",
        )

    logger.debug(
        "user `%s` (role %s) attempting to change status of payroll report for school %s, %s-%s to %s",
        token.id,
        user.roleId,
        school_id,
        year,
        month,
        status_change.new_status.value,
    )

    # Get the monthly report and then the payroll report
    monthly_report = ReportStatusManager.get_monthly_report(
        session, school_id, year, month
    )

    payroll_report = monthly_report.payroll_report
    if payroll_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        )

    # Use the generic status manager to change the status
    return await ReportStatusManager.change_report_status(
        session=session,
        user=user,
        report=payroll_report,
        status_change=status_change,
        report_type="payroll",
        school_id=school_id,
        year=year,
        month=month,
    )


@router.get("/{school_id}/{year}/{month}/valid-transitions")
async def get_payroll_valid_status_transitions(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
) -> dict[str, str | list[str]]:
    """Get the valid status transitions for a payroll report based on user role.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school the report belongs to.
        year: The year of the report.
        month: The month of the report.

    Returns:
        A dictionary containing the current status and valid transitions.
    """

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    # Check basic permission to read reports
    required_permission = (
        "reports:local:read" if user.schoolId == school_id else "reports:global:read"
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this report.",
        )

    # Get the monthly report and then the payroll report
    monthly_report = ReportStatusManager.get_monthly_report(
        session, school_id, year, month
    )

    payroll_report = monthly_report.payroll_report
    if payroll_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll report not found.",
        )

    # Get valid transitions for this user role and current status
    return ReportStatusManager.get_valid_transitions_response(user, payroll_report)
