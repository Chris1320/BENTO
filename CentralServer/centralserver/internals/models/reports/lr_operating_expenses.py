import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKeyConstraint
from sqlmodel import Field, Relationship, SQLModel

from centralserver.internals.models.reports.report_status import ReportStatus

if TYPE_CHECKING:
    from centralserver.internals.models.reports.monthly_report import MonthlyReport


class LiquidationReportOperatingExpenses(SQLModel, table=True):
    """A model representing the liquidation (Operating Expenses) reports.

    Document Name: Liquidation Report > Operating Expenses
    """

    __tablename__: str = "liquidationReportOperatingExpenses"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of monthlyReports
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            ["monthlyReports.id", "monthlyReports.submittedBySchool"],
            name="fk_liquidation_report_operating_expenses_monthly_report",
        ),
    )

    parent: datetime.date = Field(primary_key=True, index=True)
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )
    teacherInCharge: str = Field(foreign_key="users.id")
    preparedBy: str = Field(foreign_key="users.id")
    notedBy: str = Field(foreign_key="users.id")
    reportStatus: ReportStatus = Field(
        default=ReportStatus.DRAFT,
        description="The status of the report.",
    )
    memo: str | None = Field(
        default=None,
        description="Optional memo/notes for the liquidation report.",
    )

    parent_report: "MonthlyReport" = Relationship(
        back_populates="operating_expenses_report"
    )
    certified_by: list["OperatingExpensesCertifiedBy"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    entries: list["OperatingExpenseEntry"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )


class OperatingExpensesCertifiedBy(SQLModel, table=True):
    """A model representing the "Certified By" field in the operating expenses report."""

    __tablename__: str = "liquidationReportOperatingExpensesCertifiedBy"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of liquidationReportOperatingExpenses
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            [
                "liquidationReportOperatingExpenses.parent",
                "liquidationReportOperatingExpenses.schoolId",
            ],
            name="fk_lr_operating_expenses_certified_by",
        ),
    )

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
    )
    user: str = Field(primary_key=True, foreign_key="users.id")
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )

    parent_report: "LiquidationReportOperatingExpenses" = Relationship(
        back_populates="certified_by"
    )


class OperatingExpenseEntry(SQLModel, table=True):
    """A model representing an entry in the operating expenses report."""

    __tablename__: str = "liquidationReportOperatingExpensesEntries"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of liquidationReportOperatingExpenses
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            [
                "liquidationReportOperatingExpenses.parent",
                "liquidationReportOperatingExpenses.schoolId",
            ],
            name="fk_lr_operating_expenses_entry",
        ),
    )

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
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
        description="The description/name of the expense item (e.g., LPG, Rice, Water).",
    )
    unit: str  # currency (PHP), weight (kg), etc.
    quantity: float  # NOTE: This is float because it could be a (for example) weight
    unit_price: float
    receipt_attachment_urns: str | None = Field(
        default=None,
        description="JSON string containing list of receipt attachment URNs",
    )

    parent_report: "LiquidationReportOperatingExpenses" = Relationship(
        back_populates="entries"
    )
