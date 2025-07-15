import datetime
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from minio.error import S3Error
from sqlmodel import Session, func, select

from centralserver.internals.auth_handler import (
    get_user,
    verify_access_token,
    verify_user_permission,
)
from centralserver.internals.db_handler import get_db_session
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models.school import (
    School,
    SchoolCreate,
    SchoolDelete,
    SchoolUpdate,
)
from centralserver.internals.models.token import DecodedJWTToken
from centralserver.internals.models.user import User
from centralserver.internals.school_handler import (
    create_school,
    get_school_logo,
    update_school_logo,
)

logger = LoggerFactory().get_logger(__name__)

router = APIRouter(
    prefix="/v1/schools",
    tags=["schools"],
)
logged_in_dep = Annotated[DecodedJWTToken, Depends(verify_access_token)]


@router.post("/create", response_model=School)
async def create_school_endpoint(
    school: SchoolCreate,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> Response:
    """Create a new school in the system."""

    if not await verify_user_permission("schools:create", session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create schools.",
        )

    new_school = await create_school(school, session)
    logger.debug("user %s created a new school with id %s", token.id, new_school.id)
    return Response(
        content=new_school.model_dump_json(),
        status_code=status.HTTP_201_CREATED,
        media_type="application/json",
    )


@router.get("/quantity", response_model=int)
async def get_schools_quantity_endpoint(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> int:
    """Get the total number of schools in the system."""

    if not await verify_user_permission("schools:global:read", session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view schools list.",
        )

    logger.debug("user %s fetching schools quantity", token.id)
    return session.exec(
        select(func.count()).select_from(School)  # pylint: disable=not-callable
    ).one()


@router.get("/me")
async def get_assigned_schools_endpoint(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> School | None:
    """Get the list of schools assigned to the user."""

    if not await verify_user_permission("schools:self:read", session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view your assigned schools.",
        )

    user = session.get(User, token.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user.school


@router.get("/all", response_model=list[School])
async def get_all_schools_endpoint(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    limit: int = 100,
    offset: int = 0,
    show_all: bool = False,
) -> list[School]:
    """Get all schools and their information.

    Args:
        limit: The maximum number of schools to return.
        offset: The number of schools to skip before starting to collect the result set.
        show_all: If True, include deactivated schools.
    """

    if not await verify_user_permission("schools:global:read", session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view all schools.",
        )

    if show_all:
        return list(session.exec(select(School).limit(limit).offset(offset)).all())

    return list(
        session.exec(
            select(School)
            .where(School.deactivated == False)  # pylint: disable=C0121
            .limit(limit)
            .offset(offset)
        ).all()
    )


@router.get("/", response_model=School)
async def get_school_endpoint(
    school_id: int,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> School:
    """Get the information of a specific school."""

    user = session.get(User, token.id)
    school = session.get(School, school_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    required_permission = (
        "schools:self:read" if user in school.users else "schools:global:read"
    )

    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this school.",
        )

    return school


@router.get("/logo", response_class=StreamingResponse)
async def get_school_logo_endpoint(
    fn: str,
    token: Annotated[DecodedJWTToken, Depends(verify_access_token)],
    session: Annotated[Session, Depends(get_db_session)],
) -> StreamingResponse:
    """Get the school's logo image by filename."""

    logged_in_user = await get_user(token.id, session=session, by_id=True)
    if not logged_in_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found."
        )

    required_permission = (
        "schools:global:read"
        if logged_in_user.school is None
        else (
            "schools:self:read"
            if logged_in_user in logged_in_user.school.users
            else "schools:global:read"
        )
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this school.",
        )

    try:
        bucket_object = await get_school_logo(fn)
        if bucket_object is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="School logo not found.",
            )

    except S3Error as e:
        logger.error("Error fetching school logo: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School logo not found.",
        ) from e

    return StreamingResponse(BytesIO(bucket_object.obj), media_type="image/*")


@router.patch("/", response_model=School)
async def update_school_endpoint(
    updated_school_info: SchoolUpdate,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> School:
    """Update the information of a specific school."""

    user = session.get(User, token.id)
    school = session.get(School, updated_school_info.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    required_permission = (
        "schools:self:modify" if user in school.users else "schools:global:modify"
    )

    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this school.",
        )

    if updated_school_info.name:
        school.name = updated_school_info.name

    if updated_school_info.address:
        school.address = updated_school_info.address

    if updated_school_info.phone:
        school.phone = updated_school_info.phone

    if updated_school_info.email:
        school.email = updated_school_info.email

    if updated_school_info.website:
        school.website = updated_school_info.website

    if updated_school_info.deactivated is not None:
        school.deactivated = updated_school_info.deactivated

    if updated_school_info.assignedNotedBy is not None:
        school.assignedNotedBy = updated_school_info.assignedNotedBy

    school.lastModified = datetime.datetime.now(datetime.timezone.utc)
    session.add(school)
    session.commit()
    session.refresh(school)

    logger.debug("user %s updated school with id %s", token.id, school.id)
    return school


@router.delete("/")
async def delete_school_info_endpoint(
    school: SchoolDelete,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> None:
    """Delete a school from the system."""

    user = session.get(User, token.id)
    selected_school = session.get(School, school.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not selected_school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    required_permission = (
        "schools:self:modify"
        if user in selected_school.users
        else "schools:global:modify"
    )

    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete information of this school.",
        )

    if school.address:
        selected_school.address = None

    if school.phone:
        selected_school.phone = None

    if school.email:
        selected_school.email = None

    if school.website:
        selected_school.website = None

    selected_school.lastModified = datetime.datetime.now(datetime.timezone.utc)

    session.commit()
    session.refresh(selected_school)
    logger.info("Selected fields for school `%s` removed.", selected_school.id)


@router.patch("/logo", response_model=School)
async def patch_school_logo(
    school_id: int,
    img: UploadFile,
    token: Annotated[DecodedJWTToken, Depends(verify_access_token)],
    session: Annotated[Session, Depends(get_db_session)],
) -> School:
    logged_in_user = await get_user(token.id, session=session, by_id=True)
    if not logged_in_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found."
        )

    required_permission = (
        "schools:global:modify"
        if logged_in_user.school is None
        else (
            "schools:self:modify"
            if logged_in_user in logged_in_user.school.users
            else "schools:global:modify"
        )
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this school.",
        )

    return await update_school_logo(school_id, img, session)


@router.delete("/logo", response_model=School)
async def delete_school_logo(
    school_id: int,
    token: Annotated[DecodedJWTToken, Depends(verify_access_token)],
    session: Annotated[Session, Depends(get_db_session)],
) -> School:
    """Delete the school's logo image."""

    logged_in_user = await get_user(token.id, session=session, by_id=True)
    if not logged_in_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found."
        )

    required_permission = (
        "schools:global:modify"
        if logged_in_user.school is None
        else (
            "schools:self:modify"
            if logged_in_user in logged_in_user.school.users
            else "schools:global:modify"
        )
    )
    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this school's logo.",
        )

    try:
        updated_school = await update_school_logo(school_id, None, session)
        return updated_school

    except S3Error as e:
        logger.error("Error deleting school logo: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School logo not found.",
        ) from e


async def get_school_assigned_noted_by(school_id: int, session: Session) -> str | None:
    """Get the assigned noted by user for a school."""
    school = session.get(School, school_id)
    if school and school.assignedNotedBy:
        return school.assignedNotedBy
    return None
