from abc import ABC, abstractmethod

import httpx

from centralserver.internals.adapters.config import GoogleOAuthAdapterConfig


class OAuthAdapter(ABC):
    @abstractmethod
    async def get_authorization_url(self) -> dict[str, str]:
        """Returns the URL to redirect the user for authorization."""

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> dict[str, str]:
        """Exchanges the authorization code for an access token."""


class GoogleOAuthAdapter(OAuthAdapter):
    def __init__(self, config: GoogleOAuthAdapterConfig):
        self.config: GoogleOAuthAdapterConfig = config

    async def get_authorization_url(
        self, redirect_uri: str | None = None
    ) -> dict[str, str]:
        """Get authorization URL with optional custom redirect URI."""
        uri = redirect_uri or self.config.redirect_uri
        return {
            "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={self.config.client_id}&redirect_uri={uri}&scope=openid%20profile%20email&access_type=offline"
        }

    async def exchange_code_for_token(
        self, code: str, redirect_uri: str | None = None
    ) -> dict[str, str]:
        """Exchange code for token with optional custom redirect URI."""
        token_url = "https://accounts.google.com/o/oauth2/token"
        uri = redirect_uri or self.config.redirect_uri

        data = {
            "code": code,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "redirect_uri": uri,
            "grant_type": "authorization_code",
        }
        response = httpx.post(token_url, data=data)
        access_token = response.json().get("access_token")
        user_info = httpx.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return user_info.json()
