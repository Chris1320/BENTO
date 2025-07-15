import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from centralserver.internals.models.user import User


class School(SQLModel, table=True):
    """A model representing schools in the system."""

    __tablename__: str = "schools"  # type: ignore

    id: int | None = Field(
        default=None,
        primary_key=True,
        index=True,
        description="The unique identifier for the school.",
    )
    # NOTE: I did not make `name` unique because I think there can be
    #       multiple schools with the same name.
    name: str = Field(index=True, description="The name of the school.")
    address: str | None = Field(default=None, description="The address of the school.")

    # NOTE: verification are not implemented for these fields.
    phone: str | None = Field(
        default=None, description="The phone number of the school."
    )
    email: EmailStr | None = Field(
        default=None, description="The email address of the school."
    )
    website: str | None = Field(default=None, description="The website of the school.")

    logoUrn: str | None = Field(
        default=None,
        description="A link or identifier to the schools's logo within the file storage server.",
    )
    deactivated: bool = Field(
        default=False,
        description="Indicates whether the school is deactivated or not.",
    )

    assignedNotedBy: str | None = Field(
        default=None, description="The user that should approve the school reports."
    )

    dateCreated: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="The timestamp when the record was created.",
    )
    lastModified: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="The last time the user information was modified.",
    )

    # lastModifiedBy: "User" = Relationship(back_populates="lastModifiedSchools")
    users: list["User"] = Relationship(back_populates="school")


class SchoolUpdate(SQLModel):
    """A model for updating school information."""

    id: int
    name: str
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    website: str | None = None
    deactivated: bool | None = None
    assignedNotedBy: str | None = None


class SchoolCreate(SQLModel):
    """A model for creating a new school."""

    name: str
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    website: str | None = None
    assignedNotedBy: str | None = None


class SchoolDelete(SQLModel):
    """A model for deleting a school."""

    id: int
    address: bool = False
    phone: bool = False
    email: bool = False
    website: bool = False
