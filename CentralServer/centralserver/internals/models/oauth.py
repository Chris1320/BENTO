from dataclasses import dataclass

from centralserver.internals.adapters.config import GoogleOAuthAdapterConfig


@dataclass
class OAuthConfigs:
    google: GoogleOAuthAdapterConfig | None = None
