import datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class ReportAttachment(SQLModel, table=True):
    """A model representing an attachment for report entries."""

    __tablename__: str = "reportAttachments"  # type: ignore

    id: int | None = Field(default=None, primary_key=True, index=True)
    filename: str = Field(description="Original filename of the attachment")
    file_urn: str = Field(description="URN of the file in object storage")
    file_type: str = Field(description="MIME type of the file")
    file_size: int = Field(description="Size of the file in bytes")
    upload_date: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="Date when the attachment was uploaded",
    )
    description: str | None = Field(
        default=None, description="Optional description of the attachment"
    )


class AttachmentUploadResponse(BaseModel):
    """Response model for attachment uploads."""

    file_urn: str
    filename: str
    file_size: int
    file_type: str


class AttachmentMetadataResponse(BaseModel):
    """Response model for attachment metadata."""

    file_urn: str
    filename: str
    file_size: int
    file_type: str
