import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from centralserver.internals.models.reports.report_status import ReportStatus

if TYPE_CHECKING:
    from centralserver.internals.models.reports.monthly_report import MonthlyReport


class LiquidationReportSupplementaryFeedingFund(SQLModel, table=True):
    """A model representing the liquidation (Supplementary Feeding Fund) reports."""

    __tablename__: str = "liquidationReportSupplementaryFeedingFund"  # type: ignore

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

    entries: list["SupplementaryFeedingFundEntry"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    certified_by: list["SupplementaryFeedingFundCertifiedBy"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    parent_report: "MonthlyReport" = Relationship(
        back_populates="supplementary_feeding_fund_report"
    )


class SupplementaryFeedingFundCertifiedBy(SQLModel, table=True):
    __tablename__: str = "liquidationReportSupplementaryFeedingFundCertifiedBy"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
        foreign_key="liquidationReportSupplementaryFeedingFund.parent",
    )
    user: str = Field(primary_key=True, foreign_key="users.id")
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )

    parent_report: "LiquidationReportSupplementaryFeedingFund" = Relationship(
        back_populates="certified_by"
    )


class SupplementaryFeedingFundEntry(SQLModel, table=True):
    __tablename__: str = "liquidationReportSupplementaryFeedingFundEntries"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
        foreign_key="liquidationReportSupplementaryFeedingFund.parent",
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
    receipt: str | None = Field(description="Receipt or voucher number")
    particulars: str = Field(primary_key=True, description="Item description")
    amount: float = Field(description="Total amount for the item")

    parent_report: "LiquidationReportSupplementaryFeedingFund" = Relationship(
        back_populates="entries"
    )
