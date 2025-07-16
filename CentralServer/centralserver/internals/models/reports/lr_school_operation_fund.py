import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import ForeignKeyConstraint

from centralserver.internals.models.reports.report_status import ReportStatus

if TYPE_CHECKING:
    from centralserver.internals.models.reports.monthly_report import MonthlyReport


class LiquidationReportSchoolOperationFund(SQLModel, table=True):
    """A model representing the liquidation (School Operation Fund) reports."""

    __tablename__: str = "liquidationReportSchoolOperationFund"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True, index=True
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

    __table_args__ = (
        # Composite foreign key to reference the composite primary key of monthlyReports
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            ["monthlyReports.id", "monthlyReports.submittedBySchool"],
            name="fk_school_operation_fund_monthly_report"
        ),
    )

    certified_by: list["SchoolOperationFundCertifiedBy"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    entries: list["SchoolOperationFundEntry"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    parent_report: "MonthlyReport" = Relationship(
        back_populates="school_operation_fund_report"
    )


class SchoolOperationFundCertifiedBy(SQLModel, table=True):
    """A model representing the liquidation (School Operation Fund) reports."""

    __tablename__: str = "liquidationReportSchoolOperationFundCertifiedBy"  # type: ignore

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

    __table_args__ = (
        # Composite foreign key to reference the composite primary key of liquidationReportSchoolOperationFund
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            ["liquidationReportSchoolOperationFund.parent", "liquidationReportSchoolOperationFund.schoolId"],
            name="fk_lr_school_operation_fund_certified_by"
        ),
    )

    parent_report: LiquidationReportSchoolOperationFund = Relationship(
        back_populates="certified_by"
    )


class SchoolOperationFundEntry(SQLModel, table=True):
    __tablename__: str = "liquidationReportSchoolOperationFundEntries"  # type: ignore

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
    receipt: str | None
    particulars: str = Field(primary_key=True)
    unit: str | None = Field(default=None)
    quantity: float | None = Field(default=None)
    unitPrice: float
    receipt_attachment_urns: str | None = Field(
        default=None,
        description="JSON string containing list of receipt attachment URNs",
    )

    __table_args__ = (
        # Composite foreign key to reference the composite primary key of liquidationReportSchoolOperationFund
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            ["liquidationReportSchoolOperationFund.parent", "liquidationReportSchoolOperationFund.schoolId"],
            name="fk_lr_school_operation_fund_entry"
        ),
    )

    parent_report: LiquidationReportSchoolOperationFund = Relationship(
        back_populates="entries"
    )
