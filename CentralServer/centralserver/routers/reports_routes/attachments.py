from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from centralserver.internals.attachment_handler import (
    delete_report_attachment,
    get_report_attachment,
    get_report_attachment_metadata,
    upload_report_attachment,
)
from centralserver.internals.auth_handler import verify_access_token
from centralserver.internals.db_handler import get_db_session
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models.reports.attachments import (
    AttachmentMetadataResponse,
    AttachmentUploadResponse,
)
from centralserver.internals.models.token import DecodedJWTToken

logger = LoggerFactory().get_logger(__name__)

router = APIRouter(
    prefix="/attachments",
    tags=["reports", "attachments"],
)

logged_in_dep = Annotated[DecodedJWTToken, Depends(verify_access_token)]


@router.post("/upload", response_model=AttachmentUploadResponse)
async def upload_attachment_endpoint(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    file: UploadFile = File(...),
    description: str | None = None,
) -> AttachmentUploadResponse:
    """Upload a receipt attachment for report entries.

    Args:
        token: The access token of the logged-in user.
        session: The session to the database.
        file: The receipt image file to upload.
        description: Optional description of the attachment.

    Returns:
        AttachmentUploadResponse with file details.
    """
    logger.debug("User %s is uploading report attachment: %s", token.id, file.filename)

    # TODO: Add permission checking based on user role and report access
    # For now, we'll allow any authenticated user to upload attachments

    return await upload_report_attachment(file, session, description)


@router.get("/{file_urn}", response_class=StreamingResponse)
async def get_attachment_endpoint(
    file_urn: str,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> StreamingResponse:
    """Get a receipt attachment.

    Args:
        file_urn: The URN of the attachment to retrieve.
        token: The access token of the logged-in user.
        session: The session to the database.

    Returns:
        StreamingResponse with the attachment file.
    """
    logger.debug("User %s is retrieving report attachment: %s", token.id, file_urn)

    # TODO: Add permission checking based on user role and report access
    # For now, we'll allow any authenticated user to retrieve attachments

    try:
        file_content, filename, content_type = await get_report_attachment(
            file_urn, session
        )

        # Return as streaming response
        from io import BytesIO

        file_stream = BytesIO(file_content)

        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error("Failed to retrieve attachment %s: %s", file_urn, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve attachment: {str(e)}",
        ) from e


@router.delete("/{file_urn}")
async def delete_attachment_endpoint(
    file_urn: str,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    """Delete a receipt attachment.

    Args:
        file_urn: The URN of the attachment to delete.
        token: The access token of the logged-in user.
        session: The session to the database.

    Returns:
        Success message.
    """
    logger.debug("User %s is deleting report attachment: %s", token.id, file_urn)

    # TODO: Add permission checking based on user role and report access
    # For now, we'll allow any authenticated user to delete attachments

    await delete_report_attachment(file_urn, session)

    return {"message": "Attachment deleted successfully"}


@router.post("/metadata", response_model=list[AttachmentMetadataResponse])
async def get_attachments_metadata_endpoint(
    file_urns: list[str],
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> list[AttachmentMetadataResponse]:
    """Get metadata for a list of receipt attachments.

    Args:
        file_urns: The list of URNs of the attachments to retrieve metadata for.
        token: The access token of the logged-in user.
        session: The session to the database.

    Returns:
        List of metadata dictionaries for the requested attachments.
    """
    logger.debug(
        "User %s is retrieving metadata for report attachments: %s", token.id, file_urns
    )

    # TODO: Add permission checking based on user role and report access
    # For now, we'll allow any authenticated user to retrieve attachment metadata

    metadata_list: list[AttachmentMetadataResponse] = []
    for file_urn in file_urns:
        try:
            metadata = await get_report_attachment_metadata(file_urn, session)
            metadata_response = AttachmentMetadataResponse(
                file_urn=str(metadata["file_urn"]),
                filename=str(metadata["filename"]),
                file_size=int(metadata["file_size"]),
                file_type=str(metadata["file_type"]),
            )
            metadata_list.append(metadata_response)
        except Exception as e:
            logger.error(
                "Failed to retrieve metadata for attachment %s: %s", file_urn, str(e)
            )
            # Skip attachments that can't be found rather than including error entries
            continue

    return metadata_list
