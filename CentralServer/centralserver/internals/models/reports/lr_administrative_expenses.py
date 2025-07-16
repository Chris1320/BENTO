import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from centralserver.internals.models.reports.report_status import ReportStatus

if TYPE_CHECKING:
    from centralserver.internals.models.reports.monthly_report import MonthlyReport


class LiquidationReportAdministrativeExpenses(SQLModel, table=True):
    """A model representing the liquidation (Administrative Expenses) reports.

    Document Name: Liquidation Report > Administrative Expenses
    """

    __tablename__: str = "liquidationReportAdministrativeExpenses"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True, index=True, foreign_key="monthlyReports.id"
    )
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )
    notedBy: str = Field(foreign_key="users.id")
    preparedBy: str = Field(foreign_key="users.id")
    teacherInCharge: str = Field(foreign_key="users.id")
    reportStatus: ReportStatus = Field(
        default=ReportStatus.DRAFT,
        description="The status of the report.",
    )
    memo: str | None = Field(
        default=None,
        description="Optional memo/notes for the liquidation report.",
    )

    parent_report: "MonthlyReport" = Relationship(
        back_populates="administrative_expenses_report"
    )
    certified_by: list["AdministrativeExpensesCertifiedBy"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    entries: list["AdministrativeExpenseEntry"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )


class AdministrativeExpensesCertifiedBy(SQLModel, table=True):
    __tablename__: str = "liquidationReportAdministrativeExpensesCertifiedBy"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
        foreign_key="liquidationReportAdministrativeExpenses.parent",
    )
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )
    user: str = Field(primary_key=True, foreign_key="users.id")

    parent_report: "LiquidationReportAdministrativeExpenses" = Relationship(
        back_populates="certified_by"
    )


class AdministrativeExpenseEntry(SQLModel, table=True):
    """A model representing an entry in the administrative expenses report."""

    __tablename__: str = "liquidationReportAdministrativeExpensesEntries"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
        foreign_key="liquidationReportAdministrativeExpenses.parent",
    )
    date: datetime.datetime = Field(
        primary_key=True,
        index=True,
        description="The date of the expense entry.",
    )
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )
    particulars: str = Field(
        primary_key=True,
        description="The description/name of the expense item.",
    )
    unit: str
    quantity: float
    unit_price: float

    parent_report: LiquidationReportAdministrativeExpenses = Relationship(
        back_populates="entries"
    )
