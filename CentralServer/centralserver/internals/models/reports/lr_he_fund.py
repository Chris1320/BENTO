import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from centralserver.internals.models.reports.report_status import ReportStatus

if TYPE_CHECKING:
    from centralserver.internals.models.reports.monthly_report import MonthlyReport


class LiquidationReportHEFund(SQLModel, table=True):
    __tablename__: str = "liquidationReportHEFund"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True, index=True, foreign_key="monthlyReports.id"
    )
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )
    certified_by: list["LiquidationReportHEFundCertifiedBy"] = Relationship(
        back_populates="parent_report"
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

    entries: list["LiquidationReportHEFundEntry"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    parent_report: "MonthlyReport" = Relationship(back_populates="he_fund_report")


class LiquidationReportHEFundCertifiedBy(SQLModel, table=True):
    """A model representing the liquidation (HE Fund) reports."""

    __tablename__: str = "liquidationReportHEFundCertifiedBy"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
        foreign_key="liquidationReportHEFund.parent",
    )
    user: str = Field(primary_key=True, foreign_key="users.id")
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )

    parent_report: LiquidationReportHEFund = Relationship(back_populates="certified_by")


class LiquidationReportHEFundEntry(SQLModel, table=True):
    __tablename__: str = "liquidationReportHEFundEntries"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
        foreign_key="liquidationReportHEFund.parent",
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
    unit_price: float
    receipt_attachment_urns: str | None = Field(
        default=None,
        description="JSON string containing list of receipt attachment URNs",
    )

    parent_report: LiquidationReportHEFund = Relationship(back_populates="entries")
