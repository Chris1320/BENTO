import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKeyConstraint
from sqlmodel import Field, Relationship, SQLModel

from centralserver.internals.models.reports.report_status import ReportStatus

if TYPE_CHECKING:
    from centralserver.internals.models.reports.monthly_report import MonthlyReport


class LiquidationReportFacultyAndStudentDevFund(SQLModel, table=True):
    """A model representing the liquidation (Faculty and Student Development Fund) reports."""

    __tablename__: str = "liquidationReportFacultyAndStudentDevFund"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of monthlyReports
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            ["monthlyReports.id", "monthlyReports.submittedBySchool"],
            name="fk_faculty_student_dev_fund_monthly_report",
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

    audited_by: list["FacultyAndStudentDevFundAuditedBy"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    entries: list["FacultyAndStudentDevFundEntry"] = Relationship(
        back_populates="parent_report", cascade_delete=True
    )
    parent_report: "MonthlyReport" = Relationship(
        back_populates="faculty_and_student_dev_fund_report"
    )


class FacultyAndStudentDevFundAuditedBy(SQLModel, table=True):
    __tablename__: str = "liquidationReportFacultyAndStudentDevFundAuditedBy"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of liquidationReportFacultyAndStudentDevFund
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            [
                "liquidationReportFacultyAndStudentDevFund.parent",
                "liquidationReportFacultyAndStudentDevFund.schoolId",
            ],
            name="fk_faculty_student_dev_fund_audited_by",
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

    parent_report: LiquidationReportFacultyAndStudentDevFund = Relationship(
        back_populates="audited_by"
    )


class FacultyAndStudentDevFundEntry(SQLModel, table=True):
    __tablename__: str = "liquidationReportFacultyAndStudentDevFundEntries"  # type: ignore
    __table_args__ = (
        # Composite foreign key to reference the composite primary key of liquidationReportFacultyAndStudentDevFund
        ForeignKeyConstraint(
            ["parent", "schoolId"],
            [
                "liquidationReportFacultyAndStudentDevFund.parent",
                "liquidationReportFacultyAndStudentDevFund.schoolId",
            ],
            name="fk_faculty_student_dev_fund_entry",
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
    receipt: str | None
    particulars: str = Field(primary_key=True)
    unit: str | None = Field(default=None)
    quantity: float | None = Field(default=None)
    unitPrice: float

    receipt_attachment_urns: str | None = Field(
        default=None,
        description="JSON string containing list of receipt attachment URNs",
    )

    parent_report: "LiquidationReportFacultyAndStudentDevFund" = Relationship(
        back_populates="entries"
    )
