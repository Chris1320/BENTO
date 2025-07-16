# pylint: disable=C0302
import datetime
from typing import Annotated, Any, Dict, Union

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from centralserver.internals.auth_handler import (
    get_user,
    verify_access_token,
    verify_user_permission,
)
from centralserver.internals.db_handler import get_db_session
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models.reports.lr_administrative_expenses import (
    AdministrativeExpenseEntry,
    AdministrativeExpensesCertifiedBy,
    LiquidationReportAdministrativeExpenses,
)
from centralserver.internals.models.reports.lr_clinic_fund import (
    LiquidationReportClinicFund,
    LiquidationReportClinicFundCertifiedBy,
    LiquidationReportClinicFundEntry,
)
from centralserver.internals.models.reports.lr_faculty_stud_dev_fund import (
    FacultyAndStudentDevFundAuditedBy,
    FacultyAndStudentDevFundEntry,
    LiquidationReportFacultyAndStudentDevFund,
)
from centralserver.internals.models.reports.lr_he_fund import (
    LiquidationReportHEFund,
    LiquidationReportHEFundCertifiedBy,
    LiquidationReportHEFundEntry,
)
from centralserver.internals.models.reports.lr_operating_expenses import (
    LiquidationReportOperatingExpenses,
    OperatingExpenseEntry,
    OperatingExpensesCertifiedBy,
)
from centralserver.internals.models.reports.lr_revolving_fund import (
    LiquidationReportRevolvingFund,
    RevolvingFundCertifiedBy,
    RevolvingFundEntry,
)
from centralserver.internals.models.reports.lr_school_operation_fund import (
    LiquidationReportSchoolOperationFund,
    SchoolOperationFundCertifiedBy,
    SchoolOperationFundEntry,
)
from centralserver.internals.models.reports.lr_supplementary_feeding_fund import (
    LiquidationReportSupplementaryFeedingFund,
    SupplementaryFeedingFundCertifiedBy,
    SupplementaryFeedingFundEntry,
)
from centralserver.internals.models.reports.monthly_report import (
    MonthlyReport,
    ReportStatus,
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


router = APIRouter(prefix="/liquidation")
logged_in_dep = Annotated[DecodedJWTToken, Depends(verify_access_token)]

# Category mapping
LIQUIDATION_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "operating_expenses": {
        "model": LiquidationReportOperatingExpenses,
        "entry_model": OperatingExpenseEntry,
        "certified_model": OperatingExpensesCertifiedBy,
        "name": "Operating Expenses",
        "has_receipt": False,
        "has_qty_unit": True,
    },
    "administrative_expenses": {
        "model": LiquidationReportAdministrativeExpenses,
        "entry_model": AdministrativeExpenseEntry,
        "certified_model": AdministrativeExpensesCertifiedBy,
        "name": "Administrative Expenses",
        "has_receipt": False,
        "has_qty_unit": True,
    },
    "supplementary_feeding_fund": {
        "model": LiquidationReportSupplementaryFeedingFund,
        "entry_model": SupplementaryFeedingFundEntry,
        "certified_model": SupplementaryFeedingFundCertifiedBy,
        "name": "Supplementary Feeding Fund",
        "has_receipt": True,
        "has_qty_unit": False,
    },
    "clinic_fund": {
        "model": LiquidationReportClinicFund,
        "entry_model": LiquidationReportClinicFundEntry,
        "certified_model": LiquidationReportClinicFundCertifiedBy,
        "name": "Clinic Fund",
        "has_receipt": True,
        "has_qty_unit": False,
    },
    "faculty_stud_dev_fund": {
        "model": LiquidationReportFacultyAndStudentDevFund,
        "entry_model": FacultyAndStudentDevFundEntry,
        "certified_model": FacultyAndStudentDevFundAuditedBy,
        "name": "Faculty and Student Development Fund",
        "has_receipt": True,
        "has_qty_unit": True,
    },
    "he_fund": {
        "model": LiquidationReportHEFund,
        "entry_model": LiquidationReportHEFundEntry,
        "certified_model": LiquidationReportHEFundCertifiedBy,
        "name": "HE Fund",
        "has_receipt": True,
        "has_qty_unit": True,
    },
    "school_operations_fund": {
        "model": LiquidationReportSchoolOperationFund,
        "entry_model": SchoolOperationFundEntry,
        "certified_model": SchoolOperationFundCertifiedBy,
        "name": "School Operations Fund",
        "has_receipt": True,
        "has_qty_unit": True,
    },
    "revolving_fund": {
        "model": LiquidationReportRevolvingFund,
        "entry_model": RevolvingFundEntry,
        "certified_model": RevolvingFundCertifiedBy,
        "name": "Revolving Fund",
        "has_receipt": True,
        "has_qty_unit": True,
    },
}


# Request/Response Models
class LiquidationReportEntryData(BaseModel):
    """Data for a liquidation report entry."""

    date: datetime.datetime
    particulars: str
    receiptNumber: str | None = None
    quantity: float | None = None
    unit: str | None = None
    unitPrice: float | None = None  # For reports with quantity/unit
    amount: float | None = None  # For reports without quantity/unit
    receipt_attachment_urns: str | None = Field(
        default=None,
        description="JSON string containing list of receipt attachment URNs",
    )
    schoolId: int | None = Field(
        default=None,
        description="The school ID for the entry (optional for request, required for database)",
    )


class LiquidationReportCreateRequest(BaseModel):
    """Request model for creating/updating liquidation reports."""

    schoolId: int | None = None
    notedBy: str | None = None
    preparedBy: str | None = None
    teacherInCharge: str | None = None
    memo: str | None = None
    entries: list[LiquidationReportEntryData] = []
    certifiedBy: list[str] = []


class LiquidationReportResponse(BaseModel):
    """Response model for liquidation reports."""

    category: str
    parent: datetime.date
    reportStatus: str | None = None
    notedBy: str | None = None
    preparedBy: str | None = None
    teacherInCharge: str | None = None
    memo: str | None = None
    entries: list[LiquidationReportEntryData] = []
    certifiedBy: list[str] = []
    totalAmount: float = 0.0


def _validate_category(category: str) -> dict[str, Any]:
    """Validate and return category configuration."""
    if category not in LIQUIDATION_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(LIQUIDATION_CATEGORIES.keys())}",
        )
    return LIQUIDATION_CATEGORIES[category]


def _get_field_value(obj: Any, *field_names: str, default: Any = None) -> Any:
    """Get field value from object, trying multiple field name variations."""
    for field_name in field_names:
        if hasattr(obj, field_name):
            return getattr(obj, field_name)
    return default


def _calculate_total_amount(entries: list[Any], has_qty_unit: bool) -> float:
    """Calculate total amount from entries."""
    total = 0.0
    for entry in entries:
        if has_qty_unit and hasattr(entry, "quantity") and entry.quantity:
            # For entries with quantity and unit price
            # Try different field name variations for unit price
            unit_price = (
                getattr(entry, "unit_price", None)
                or getattr(entry, "unitPrice", None)
                or getattr(entry, "amount", 0.0)
            )
            total += entry.quantity * unit_price
        else:
            # For entries with direct amount
            amount = getattr(entry, "amount", 0.0)
            total += amount
    return total


def _get_liquidation_report(
    session: Session,
    category_config: dict[str, Any],
    parent_date: datetime.date,
    school_id: int,
) -> Any:
    """Get liquidation report by category, parent date, and school."""
    model = category_config["model"]
    return session.exec(
        select(model).where(
            model.parent == parent_date,
            model.schoolId == school_id,
        )
    ).one_or_none()


def _convert_to_response(
    report: Any, category: str, category_config: dict[str, Any]
) -> LiquidationReportResponse:
    """Convert database model to response model."""
    if not report:
        return LiquidationReportResponse(
            category=category,
            parent=datetime.date.today(),
            reportStatus=None,
            memo=None,
            entries=[],
            certifiedBy=[],
            totalAmount=0.0,
        )

    # Convert entries
    entries: list[LiquidationReportEntryData] = []
    for entry in report.entries:
        entry_data = LiquidationReportEntryData(
            date=entry.date,
            particulars=entry.particulars,
        )

        # Set amount or unitPrice based on the entry type
        if hasattr(entry, "amount"):
            entry_data.amount = entry.amount
        else:
            entry_data.unitPrice = _get_field_value(
                entry, "unitPrice", "unit_price", default=0.0
            )

        # Add receipt number if applicable
        receipt_num = _get_field_value(entry, "receiptNumber", "receipt")
        if receipt_num:
            entry_data.receiptNumber = receipt_num

        # Add quantity and unit if applicable
        quantity = _get_field_value(entry, "quantity")
        if quantity is not None:
            entry_data.quantity = quantity

        unit = _get_field_value(entry, "unit")
        if unit is not None:
            entry_data.unit = unit

        # Add receipt attachment URNs if available
        receipt_attachment_urns = _get_field_value(entry, "receipt_attachment_urns")
        if receipt_attachment_urns is not None:
            entry_data.receipt_attachment_urns = receipt_attachment_urns

        entries.append(entry_data)

    # Get certified by users
    certified_by: list[str] = []
    certified_by_attr = _get_field_value(report, "certified_by", "audited_by")
    if certified_by_attr:
        certified_by = [cert.user for cert in certified_by_attr]

    # Get report signatories
    noted_by = _get_field_value(report, "notedBy", "notedby")
    prepared_by = _get_field_value(report, "preparedBy", "preparedby")
    teacher_in_charge = _get_field_value(report, "teacherInCharge")
    report_status = _get_field_value(report, "reportStatus")
    memo = _get_field_value(report, "memo")

    return LiquidationReportResponse(
        category=category,
        parent=report.parent,
        reportStatus=report_status,
        notedBy=noted_by,
        preparedBy=prepared_by,
        teacherInCharge=teacher_in_charge,
        memo=memo,
        entries=entries,
        certifiedBy=certified_by,
        totalAmount=_calculate_total_amount(entries, category_config["has_qty_unit"]),
    )


@router.get("/{school_id}/{year}/{month}/{category}")
async def get_liquidation_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    category: str,
) -> LiquidationReportResponse:
    """Get a liquidation report for a specific category, school, and month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to get the report for.
        year: The year of the report.
        month: The month of the report.
        category: The liquidation report category.

    Returns:
        The liquidation report for the specified parameters.
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
            detail="You do not have permission to view liquidation reports.",
        )

    category_config = _validate_category(category)

    logger.debug(
        "user `%s` requesting liquidation report (%s) of school %s for %s-%s.",
        token.id,
        category,
        school_id,
        year,
        month,
    )

    try:
        parent_date = datetime.date(year=year, month=month, day=1)
        session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == parent_date,
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()

        report = _get_liquidation_report(
            session, category_config, parent_date, school_id
        )
        return _convert_to_response(report, category, category_config)

    except NoResultFound as e:
        logger.warning(
            "Liquidation report (%s) not found for school %s for %s-%s",
            category,
            school_id,
            year,
            month,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liquidation report not found.",
        ) from e


@router.get("/{school_id}/{year}/{month}/{category}/entries")
async def get_liquidation_report_entries(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    category: str,
) -> list[LiquidationReportEntryData]:
    """Get all liquidation report entries for a specific category, school, and month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to get entries for.
        year: The year of the report.
        month: The month of the report.
        category: The liquidation report category.

    Returns:
        A list of liquidation report entries.
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
            detail="You do not have permission to view liquidation report entries.",
        )

    category_config = _validate_category(category)

    logger.debug(
        "user `%s` requesting liquidation report entries (%s) of school %s for %s-%s.",
        token.id,
        category,
        school_id,
        year,
        month,
    )

    try:
        parent_date = datetime.date(year=year, month=month, day=1)
        session.exec(
            select(MonthlyReport).where(
                MonthlyReport.id == parent_date,
                MonthlyReport.submittedBySchool == school_id,
            )
        ).one()

        report = _get_liquidation_report(
            session, category_config, parent_date, school_id
        )
        if not report:
            return []

        response = _convert_to_response(report, category, category_config)
        return response.entries

    except NoResultFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        ) from e


@router.patch("/{school_id}/{year}/{month}/{category}")
async def create_or_update_liquidation_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    category: str,
    request_data: LiquidationReportCreateRequest,
) -> LiquidationReportResponse:
    """Create or update a liquidation report for a specific category, school, and month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to create/update the report for.
        year: The year of the report.
        month: The month of the report.
        category: The liquidation report category.
        request_data: The liquidation report data.

    Returns:
        The created or updated liquidation report.
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
            detail="You do not have permission to create/update liquidation reports.",
        )

    category_config = _validate_category(category)

    logger.debug(
        "user `%s` creating/updating liquidation report (%s) of school %s for %s-%s.",
        token.id,
        category,
        school_id,
        year,
        month,
    )

    parent_date = datetime.date(year=year, month=month, day=1)

    # Get or create monthly report
    selected_monthly_report = session.exec(
        select(MonthlyReport).where(
            MonthlyReport.id == parent_date,
            MonthlyReport.submittedBySchool == school_id,
        )
    ).one_or_none()

    # If no notedBy is provided, try to get it from the school's assignedNotedBy
    noted_by = request_data.notedBy
    if noted_by is None:
        noted_by = await get_school_assigned_noted_by(school_id, session)

    if selected_monthly_report is None:
        selected_monthly_report = MonthlyReport(
            id=parent_date,
            name=f"{category_config['name']} Report for {parent_date.strftime('%B %Y')}",
            submittedBySchool=school_id,
            reportStatus=ReportStatus.DRAFT,
            preparedBy=user.id,
            notedBy=noted_by,
        )
        session.add(selected_monthly_report)

    # Create liquidation report data
    model = category_config["model"]
    report_data: Dict[str, Any] = {
        "parent": parent_date,
        "schoolId": request_data.schoolId or school_id,
        "preparedBy": request_data.preparedBy or user.id,
        "notedBy": noted_by,
        "teacherInCharge": request_data.teacherInCharge,
        "memo": request_data.memo,
    }

    # Delete existing report if it exists
    existing_report = _get_liquidation_report(
        session, category_config, parent_date, school_id
    )
    if existing_report:
        # First, manually delete certified_by entries to avoid constraint issues
        certified_model = category_config["certified_model"]
        existing_certified_entries = session.exec(
            select(certified_model).where(
                certified_model.parent == parent_date,
                certified_model.schoolId == school_id,
            )
        ).all()
        for cert_entry in existing_certified_entries:
            session.delete(cert_entry)

        session.delete(existing_report)

    # Create new report
    new_report = model(**report_data)
    session.add(new_report)
    session.flush()  # To get the report in the session

    # Add entries
    entry_model = category_config["entry_model"]
    for entry_data in request_data.entries:
        entry_dict: Dict[str, Any] = {
            "parent": parent_date,
            "date": entry_data.date,
            "particulars": entry_data.particulars,
            "schoolId": entry_data.schoolId
            or school_id,  # Use entry schoolId if provided, otherwise use path schoolId
        }

        # Add receipt attachment URNs if available
        if (
            hasattr(entry_data, "receipt_attachment_urns")
            and entry_data.receipt_attachment_urns
        ):
            entry_dict["receipt_attachment_urns"] = entry_data.receipt_attachment_urns

        # Handle receipt number field variations based on model type
        if entry_data.receiptNumber:
            entry_model_name = (
                entry_model.__name__
                if hasattr(entry_model, "__name__")
                else str(entry_model)
            )
            if (
                "OperatingExpense" in entry_model_name
                or "AdministrativeExpense" in entry_model_name
            ):
                # These don't have receipt fields
                pass
            elif "ClinicFund" in entry_model_name:
                entry_dict["receiptNumber"] = entry_data.receiptNumber
            else:
                entry_dict["receipt"] = entry_data.receiptNumber

        # Handle quantity and unit
        if entry_data.quantity is not None:
            entry_dict["quantity"] = entry_data.quantity
        if entry_data.unit is not None:
            entry_dict["unit"] = entry_data.unit

        # Handle unit price field variations based on model type
        entry_model_name = (
            entry_model.__name__
            if hasattr(entry_model, "__name__")
            else str(entry_model)
        )

        # Handle amount vs unitPrice based on model type
        if (
            "SupplementaryFeedingFund" in entry_model_name
            or "ClinicFund" in entry_model_name
        ):
            # Use amount field for supplementary feeding fund and clinic fund
            amount_value = entry_data.amount or entry_data.unitPrice or 0.0
            entry_dict["amount"] = amount_value
        elif (
            "OperatingExpense" in entry_model_name
            or "AdministrativeExpense" in entry_model_name
            or "HEFund" in entry_model_name
        ):
            entry_dict["unit_price"] = entry_data.unitPrice or entry_data.amount or 0.0
        else:
            entry_dict["unitPrice"] = entry_data.unitPrice or entry_data.amount or 0.0

        entry = entry_model(**entry_dict)
        session.add(entry)

    # Add certified by entries
    certified_model = category_config["certified_model"]
    for user_id in request_data.certifiedBy:
        certified_entry = certified_model(
            parent=parent_date, user=user_id, schoolId=school_id
        )
        session.add(certified_entry)

    session.commit()
    session.refresh(new_report)
    session.refresh(selected_monthly_report)

    return _convert_to_response(new_report, category, category_config)


@router.put("/{school_id}/{year}/{month}/{category}/entries")
async def update_liquidation_report_entries(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    category: str,
    entries: list[LiquidationReportEntryData],
) -> list[LiquidationReportEntryData]:
    """Update liquidation report entries for a specific category, school, and month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to update entries for.
        year: The year of the report.
        month: The month of the report.
        category: The liquidation report category.
        entries: The new entries data.

    Returns:
        The updated entries.
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
            detail="You do not have permission to update liquidation report entries.",
        )

    category_config = _validate_category(category)

    logger.debug(
        "user `%s` updating liquidation report entries (%s) of school %s for %s-%s.",
        token.id,
        category,
        school_id,
        year,
        month,
    )

    parent_date = datetime.date(year=year, month=month, day=1)

    # Verify monthly report exists
    selected_monthly_report = session.exec(
        select(MonthlyReport).where(
            MonthlyReport.id == parent_date,
            MonthlyReport.submittedBySchool == school_id,
        )
    ).one_or_none()

    if selected_monthly_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        )

    # Verify liquidation report exists
    report = _get_liquidation_report(session, category_config, parent_date, school_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liquidation report not found.",
        )

    # Delete existing entries
    entry_model = category_config["entry_model"]
    existing_entries = session.exec(
        select(entry_model).where(
            entry_model.parent == parent_date,
            entry_model.schoolId == school_id,
        )
    ).all()
    for entry in existing_entries:
        session.delete(entry)

    # Add new entries
    for entry_data in entries:
        entry_dict: Dict[str, Any] = {
            "parent": parent_date,
            "date": entry_data.date,
            "particulars": entry_data.particulars,
            "schoolId": entry_data.schoolId
            or school_id,  # Use entry schoolId if provided, otherwise use path schoolId
        }

        # Handle receipt number field variations based on model type
        if entry_data.receiptNumber:
            entry_model_name = (
                entry_model.__name__
                if hasattr(entry_model, "__name__")
                else str(entry_model)
            )
            if (
                "OperatingExpense" in entry_model_name
                or "AdministrativeExpense" in entry_model_name
            ):
                # These don't have receipt fields
                pass
            elif "ClinicFund" in entry_model_name:
                entry_dict["receiptNumber"] = entry_data.receiptNumber
            else:
                entry_dict["receipt"] = entry_data.receiptNumber

        # Handle quantity and unit
        if entry_data.quantity is not None:
            entry_dict["quantity"] = entry_data.quantity
        if entry_data.unit is not None:
            entry_dict["unit"] = entry_data.unit

        # Handle unit price field variations based on model type
        entry_model_name = (
            entry_model.__name__
            if hasattr(entry_model, "__name__")
            else str(entry_model)
        )

        # Handle amount vs unitPrice based on model type
        if (
            "SupplementaryFeedingFund" in entry_model_name
            or "ClinicFund" in entry_model_name
        ):
            # Use amount field for supplementary feeding fund and clinic fund
            amount_value = entry_data.amount or entry_data.unitPrice or 0.0
            entry_dict["amount"] = amount_value
        elif (
            "OperatingExpense" in entry_model_name
            or "AdministrativeExpense" in entry_model_name
            or "HEFund" in entry_model_name
        ):
            entry_dict["unit_price"] = entry_data.unitPrice or entry_data.amount or 0.0
        else:
            entry_dict["unitPrice"] = entry_data.unitPrice or entry_data.amount or 0.0

        entry = entry_model(**entry_dict)
        session.add(entry)

    session.commit()

    # Return updated entries
    return entries


@router.delete("/{school_id}/{year}/{month}/{category}")
async def delete_liquidation_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    category: str,
) -> None:
    """Delete a liquidation report for a specific category, school, and month.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school to delete the report for.
        year: The year of the report.
        month: The month of the report.
        category: The liquidation report category.
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
            detail="You do not have permission to delete liquidation reports.",
        )

    category_config = _validate_category(category)

    logger.debug(
        "user `%s` deleting liquidation report (%s) of school %s for %s-%s.",
        token.id,
        category,
        school_id,
        year,
        month,
    )

    parent_date = datetime.date(year=year, month=month, day=1)

    # Verify monthly report exists
    selected_monthly_report = session.exec(
        select(MonthlyReport).where(
            MonthlyReport.id == parent_date,
            MonthlyReport.submittedBySchool == school_id,
        )
    ).one_or_none()

    if selected_monthly_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        )

    # Delete liquidation report if it exists
    report = _get_liquidation_report(session, category_config, parent_date, school_id)
    if report:
        session.delete(report)
        session.commit()


@router.get("/categories")
async def get_liquidation_categories() -> dict[str, dict[str, Union[str, bool]]]:
    """Get all available liquidation report categories.

    Returns:
        A dictionary of available categories with their configurations.
    """
    categories: dict[str, dict[str, Union[str, bool]]] = {}
    for key, config in LIQUIDATION_CATEGORIES.items():
        categories[key] = {
            "name": config["name"],
            "has_receipt": config["has_receipt"],
            "has_qty_unit": config["has_qty_unit"],
        }
    return categories


@router.patch("/{school_id}/{year}/{month}/{category}/status")
async def change_liquidation_report_status(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    category: str,
    status_change: StatusChangeRequest,
) -> Union[
    LiquidationReportOperatingExpenses,
    LiquidationReportAdministrativeExpenses,
    LiquidationReportSupplementaryFeedingFund,
    LiquidationReportClinicFund,
    LiquidationReportFacultyAndStudentDevFund,
    LiquidationReportHEFund,
    LiquidationReportSchoolOperationFund,
    LiquidationReportRevolvingFund,
]:
    """Change the status of a liquidation report based on user role and permissions.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school the report belongs to.
        year: The year of the report.
        month: The month of the report.
        category: The category of liquidation report.
        status_change: The status change request containing new status and optional comments.

    Returns:
        The updated liquidation report.

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

    # Validate category
    if category not in LIQUIDATION_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {category}",
        )

    logger.debug(
        "user `%s` (role %s) attempting to change status of %s liquidation report for school %s, %s-%s to %s",
        token.id,
        user.roleId,
        category,
        school_id,
        year,
        month,
        status_change.new_status.value,
    )

    # Get the monthly report and then the liquidation report
    # Note: We don't actually need monthly_report here, just checking it exists
    ReportStatusManager.get_monthly_report(session, school_id, year, month)

    # Get the specific liquidation report
    parent_date = datetime.date(year=year, month=month, day=1)
    category_config = LIQUIDATION_CATEGORIES[category]
    liquidation_report = _get_liquidation_report(
        session, category_config, parent_date, school_id
    )

    if liquidation_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{LIQUIDATION_CATEGORIES[category]['name']} report not found.",
        )

    # Use the generic status manager to change the status
    return await ReportStatusManager.change_report_status(
        session=session,
        user=user,
        report=liquidation_report,
        status_change=status_change,
        report_type="liquidation",
        school_id=school_id,
        year=year,
        month=month,
        category=category,
    )


@router.get("/{school_id}/{year}/{month}/{category}/valid-transitions")
async def get_liquidation_valid_status_transitions(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    category: str,
) -> dict[str, str | list[str]]:
    """Get the valid status transitions for a liquidation report based on user role.

    Args:
        token: The decoded JWT token of the logged-in user.
        session: The database session.
        school_id: The ID of the school the report belongs to.
        year: The year of the report.
        month: The month of the report.
        category: The category of liquidation report.

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

    # Validate category
    if category not in LIQUIDATION_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {category}",
        )

    # Get the monthly report and then the liquidation report
    # Note: We don't actually need monthly_report here, just checking it exists
    ReportStatusManager.get_monthly_report(session, school_id, year, month)

    # Get the specific liquidation report
    parent_date = datetime.date(year=year, month=month, day=1)
    category_config = LIQUIDATION_CATEGORIES[category]
    liquidation_report = _get_liquidation_report(
        session, category_config, parent_date, school_id
    )

    if liquidation_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{LIQUIDATION_CATEGORIES[category]['name']} report not found.",
        )

    # Get valid transitions for this user role and current status
    return ReportStatusManager.get_valid_transitions_response(user, liquidation_report)


def get_liquidation_expenses_by_category(
    session: Session, monthly_report: MonthlyReport | None, school_id: int
) -> Dict[str, float]:
    """Get liquidation expenses by category for a specific monthly report and school.

    This function directly queries the entry tables to get expenses, regardless of
    whether the liquidation reports exist or not.

    Args:
        session: Database session
        monthly_report: Monthly report to get expenses for
        school_id: School ID to filter by

    Returns:
        Dictionary with category names as keys and total amounts as values
    """
    if not monthly_report:
        return {}

    expenses_by_category: Dict[str, float] = {}
    parent_date = monthly_report.id

    # Iterate through all liquidation categories and query entries directly
    for category_key, category_config in LIQUIDATION_CATEGORIES.items():
        entry_model = category_config["entry_model"]
        has_qty_unit = category_config["has_qty_unit"]

        # Query entries directly from the entry table
        entries = session.exec(
            select(entry_model).where(
                entry_model.parent == parent_date,
                entry_model.schoolId == school_id,
            )
        ).all()

        if entries:
            # Calculate total amount for this category
            total_amount = _calculate_total_amount(list(entries), has_qty_unit)
            expenses_by_category[category_key] = total_amount
        else:
            expenses_by_category[category_key] = 0.0

    return expenses_by_category
