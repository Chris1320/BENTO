import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import ForeignKeyConstraint

from centralserver.internals.models.reports.report_status import ReportStatus

if TYPE_CHECKING:
    from centralserver.internals.models.reports.monthly_report import MonthlyReport


class DailyFinancialReport(SQLModel, table=True):
    """A model representing the daily sales and purchases report.

    Document Name: Financial Report for the Month of [MONTH], [YEAR]
    """

    __tablename__: str = "dailyFinancialReports"  # type: ignore

    parent: datetime.date = Field(
        primary_key=True,
        index=True,
    )
    schoolId: int = Field(
        primary_key=True,
        index=True,
        foreign_key="schools.id",
        description="The school that submitted the report.",
    )
    reportStatus: ReportStatus | None = Field(
        default=ReportStatus.DRAFT,
        description="The status of the report.",
    )
    preparedBy: str = Field(foreign_key="users.id")
    notedBy: str | None = Field(default=None, foreign_key="users.id")
    
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of monthlyReports
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            ["monthlyReports.id", "monthlyReports.submittedBySchool"],
            name="fk_daily_financial_report_monthly_report"
        ),
    )

    parent_report: "MonthlyReport" = Relationship(
        back_populates="daily_financial_report"
    )
    entries: list["DailyFinancialReportEntry"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )


class DailyFinancialReportEntry(SQLModel, table=True):
    """A model representing an entry in the daily sales and purchases report."""

    __tablename__: str = "dailyFinancialReportsEntries"  # type: ignore

    day: int = Field(  # The day of the month (1-31, depending on the month)
        primary_key=True,
        index=True,
    )
    parent: datetime.date = Field(
        primary_key=True
    )
    school: int = Field(primary_key=True, foreign_key="schools.id", index=True)
    sales: float  # Positive float representing the total sales for the day
    purchases: float  # Positive float representing the total purchases for the day

    __table_args__ = (
        # Composite foreign key to reference the composite primary key of dailyFinancialReports
        ForeignKeyConstraint(
            ["parent", "school"],
            ["dailyFinancialReports.parent", "dailyFinancialReports.schoolId"],
            name="fk_daily_financial_report_entry_daily_report"
        ),
    )

    parent_report: DailyFinancialReport = Relationship(back_populates="entries")


class DailyEntryData(SQLModel):
    """Model for creating daily sales and purchases entries."""

    day: int = Field(..., ge=1, le=31, description="Day of the month (1-31)")
    sales: float = Field(..., ge=0, description="Total sales for the day")
    purchases: float = Field(..., ge=0, description="Total purchases for the day")
    schoolId: int = Field(..., description="The school that submitted the entry")
