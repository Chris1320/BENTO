from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from centralserver.internals.adapters.oauth import GoogleOAuthAdapter
from centralserver.internals.auth_handler import (
    oauth_google_authenticate,
    oauth_google_link,
    verify_access_token,
)
from centralserver.internals.config_handler import app_config
from centralserver.internals.db_handler import get_db_session
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models.token import DecodedJWTToken, JWTToken
from centralserver.internals.models.user import User

logger = LoggerFactory().get_logger(__name__)
router = APIRouter(prefix="/oauth")
logged_in_dep = Annotated[DecodedJWTToken, Depends(verify_access_token)]
google_oauth_adapter = (
    GoogleOAuthAdapter(app_config.authentication.oauth.google)
    if app_config.authentication.oauth.google is not None
    else None
)


@router.get("/google/login")
async def google_oauth_login():
    """Handle Google OAuth login."""
    if google_oauth_adapter is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    return await google_oauth_adapter.get_authorization_url()


@router.get("/google/login/link")
async def google_oauth_login_link():
    """Handle Google OAuth login specifically for account linking."""
    if google_oauth_adapter is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    # Create a custom redirect URI for linking flow
    original_redirect_uri = google_oauth_adapter.config.redirect_uri
    # Replace the login path with the account oauth-callback path
    link_redirect_uri = original_redirect_uri.replace(
        "/login/oauth/google", "/account/oauth-callback"
    )

    return await google_oauth_adapter.get_authorization_url(
        redirect_uri=link_redirect_uri
    )


@router.get("/google/callback")
async def google_oauth_callback(
    code: str,
    session: Annotated[Session, Depends(get_db_session)],
    request: Request,
):
    """Handle Google OAuth callback."""

    if google_oauth_adapter is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    result = await oauth_google_authenticate(
        code=code,
        google_oauth_adapter=google_oauth_adapter,
        session=session,
        request=request,
    )

    if result[0] != status.HTTP_200_OK:
        logger.error("Google OAuth authentication failed: %s", result[1])
        raise HTTPException(
            status_code=result[0],
            detail=result[1],
        )

    if isinstance(result[1], JWTToken):
        return result[1]

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected response from Google OAuth authentication.",
    )


@router.get("/google/link")
async def oauth_link_google(
    code: str,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    redirect_uri: str | None = None,
) -> dict[str, str]:
    """Link a Google account for OAuth."""

    if google_oauth_adapter is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    # If no redirect_uri provided, try to determine if this is a popup flow
    actual_redirect_uri = redirect_uri
    if not actual_redirect_uri:
        # Default to the configured redirect URI for backward compatibility
        actual_redirect_uri = google_oauth_adapter.config.redirect_uri

    if await oauth_google_link(
        code=code,
        user_id=token.id,
        google_oauth_adapter=google_oauth_adapter,
        session=session,
        redirect_uri=actual_redirect_uri,
    ):
        logger.info("Google OAuth linking successful for user: %s", token.id)
        return {"message": "Google account linked successfully."}

    logger.error("Google OAuth linking failed for user: %s", token.id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to link Google account. Please try again.",
    )


@router.get("/google/unlink")
async def oauth_unlink_google(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    """Unlink a Google account from the user's profile."""

    if google_oauth_adapter is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    user = session.get(User, token.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.oauthLinkedGoogleId = None
    session.commit()
    session.refresh(user)

    logger.info("Google OAuth unlinked successfully for user: %s", token.id)
    return {"message": "Google account unlinked successfully."}


@router.get("/microsoft/login")
async def microsoft_oauth_login():
    """Handle Microsoft OAuth login."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Microsoft OAuth login is not implemented yet.",
    )


@router.get("/microsoft/callback")
async def microsoft_oauth_callback():
    """Handle Microsoft OAuth callback."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Microsoft OAuth callback is not implemented yet.",
    )


@router.get("/facebook/login")
async def facebook_oauth_login():
    """Handle Facebook OAuth login."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Facebook OAuth login is not implemented yet.",
    )


@router.get("/facebook/callback")
async def facebook_oauth_callback():
    """Handle Facebook OAuth callback."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Facebook OAuth callback is not implemented yet.",
    )
