import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKeyConstraint
from sqlmodel import Field, Relationship, SQLModel

from centralserver.internals.models.reports.report_status import ReportStatus

if TYPE_CHECKING:
    from centralserver.internals.models.reports.monthly_report import MonthlyReport


class LiquidationReportClinicFund(SQLModel, table=True):
    """A model representing the liquidation (Clinic Fund) reports.

    Document Name: Liquidation Report > Clinic Fund
    """

    __tablename__: str = "liquidationReportClinicFund"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of monthlyReports
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            ["monthlyReports.id", "monthlyReports.submittedBySchool"],
            name="fk_liquidation_report_clinic_fund_monthly_report",
        ),
    )

    parent: datetime.date = Field(primary_key=True, index=True)
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

    parent_report: "MonthlyReport" = Relationship(back_populates="clinic_fund_report")
    certified_by: list["LiquidationReportClinicFundCertifiedBy"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    entries: list["LiquidationReportClinicFundEntry"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )


class LiquidationReportClinicFundCertifiedBy(SQLModel, table=True):
    __tablename__: str = "liquidationReportClinicFundCertifiedBy"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of liquidationReportClinicFund
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            [
                "liquidationReportClinicFund.parent",
                "liquidationReportClinicFund.schoolId",
            ],
            name="fk_lr_clinic_fund_certified_by",
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

    parent_report: LiquidationReportClinicFund = Relationship(
        back_populates="certified_by"
    )


class LiquidationReportClinicFundEntry(SQLModel, table=True):
    __tablename__: str = "liquidationReportClinicFundEntries"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of liquidationReportClinicFund
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            [
                "liquidationReportClinicFund.parent",
                "liquidationReportClinicFund.schoolId",
            ],
            name="fk_lr_clinic_fund_entry",
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
    receiptNumber: str | None = Field(description="Receipt or voucher number.")
    particulars: str = Field(primary_key=True, description="Item description.")
    amount: float = Field(description="Amount of the expense.")

    parent_report: LiquidationReportClinicFund = Relationship(back_populates="entries")
