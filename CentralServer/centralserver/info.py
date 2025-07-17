import os
from enum import Enum
from pathlib import Path
from typing import Final

# Configuration keys that are forbidden from being modified via the web interface
# Future developers can easily add keys here to prevent them from being editable
FORBIDDEN_CONFIG_KEYS = {
    "debug": ["hot_reload"],  # Hot reload can cause instability in production
    "connection": ["host", "port"],  # Changing these could break the server connection
    "authentication": [
        "signing_key",
        "encryption_key",
        "signing_algorithm",
        "encryption_algorithm",
    ],  # Security-critical keys that should not be changed via web
    "mailing": ["password"],  # Sensitive credentials (though we allow this for now)
}


class AnnouncementRecipients(Enum):
    ALL = "all"
    ROLE = "role"
    SCHOOL = "school"
    USERS = "users"


class Program:
    """General program information."""

    name: Final[str] = "Bento Central Server"
    version: Final[tuple[int, int, int]] = (0, 7, 0)


class Database:
    """Default user credentials in the database."""

    default_user: Final[str] = "bento"
    default_password: Final[str] = "ProjectSCARS1"


class Configuration:
    """Default configuration file information."""

    default_filepath: Final[Path] = Path(os.getcwd(), "config.json")
    default_encoding: Final[str] = "utf-8"
