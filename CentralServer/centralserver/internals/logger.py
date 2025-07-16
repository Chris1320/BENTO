import logging
import os
import sys
from time import strftime

from concurrent_log_handler import ConcurrentRotatingFileHandler

from centralserver import info
from centralserver.internals.config_handler import app_config


class LoggerFactory:
    """A factory class for creating loggers with a specific configuration."""

    def __init__(
        self,
        log_level: int | str | None = None,
    ):
        """Create a new LoggerFactory object.

        Args:
            log_level: Override the log level with the provided value.
        """

        self.log_level = (
            log_level
            if log_level is not None
            else "DEBUG" if app_config.debug.enabled else "WARN"
        )

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the provided name.

        Args:
            name: The name of the logger.

        Returns:
            The logger object.
        """

        logger = logging.getLogger(name)
        if type(self.log_level) is int:
            logger.setLevel(self.log_level)
        elif type(self.log_level) is str:
            logger.setLevel(self.log_level.upper())
        else:
            raise ValueError("Invalid log level type. Must be int or str.")

        # Add a handler if one does not already exist.
        if not logger.handlers:
            # handlers
            stream_handler = logging.StreamHandler()

            # formatters
            formatter = logging.Formatter(
                fmt=app_config.logging.log_format,
                datefmt=app_config.logging.date_format,
            )

            # add formatters to handlers
            stream_handler.setFormatter(formatter)

            # add handlers to logger
            logger.addHandler(stream_handler)

            # Only add file handler if file logging is enabled
            if app_config.logging.file_logging_enabled:
                file_handler = ConcurrentRotatingFileHandler(
                    app_config.logging.filepath.format(strftime("%Y-%m-%d_%H-%M-%S")),
                    maxBytes=app_config.logging.max_bytes,
                    backupCount=app_config.logging.backup_count,
                    encoding=app_config.logging.encoding,
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        return logger


def log_app_info(logger: logging.Logger):
    """Log everything about the app.

    Args:
        logger: The logger to use.
    """

    stats: dict[str, str] = {}

    app_title = f"{info.Program.name} v{'.'.join(map(str, info.Program.version))}"
    border_length = len(app_title) + 2
    logger.info(f".{"-" * border_length}.")
    logger.info(f"| {app_title} |")
    logger.info(f"`{'-' * border_length}`")
    logger.info(f"Running on Python {sys.version} ({sys.platform})")

    stats["Loaded Configuration"] = str(app_config.filepath)
    stats["Configuration Encoding"] = app_config.encoding

    stats["Debug Mode"] = "Enabled" if app_config.debug.enabled else "Disabled"
    stats["Running via __main__"] = "Yes" if app_config.run_internal else "No"

    if app_config.debug.enabled:
        stats["AI Enabled"] = str(app_config.ai.enabled)
        stats["AI API Key"] = (
            f"{'*' * 8}{app_config.ai.gemini_api_key[-4:]}"
            if app_config.ai.gemini_api_key
            else "Not set"
        )
        stats["AI Model"] = app_config.ai.gemini_model or "Not set"

        # Debug
        stats["Log Environment Variables"] = (
            "Opted out" if app_config.debug.logenv_optout else "Enabled"
        )
        stats["Show SQL Queries"] = (
            "Enabled" if app_config.debug.show_sql else "Disabled"
        )
        stats["Hot Reload"] = "Enabled" if app_config.debug.hot_reload else "Disabled"

        # Connection
        stats["Host"] = app_config.connection.host or "Not set"
        stats["Port"] = str(app_config.connection.port) or "Not set"
        stats["Base URL"] = app_config.connection.base_url or "Not set"

        # Logging
        stats["File Logging"] = (
            "Enabled" if app_config.logging.file_logging_enabled else "Disabled"
        )
        stats["Log File Path"] = app_config.logging.filepath
        stats["Max Log File Size"] = (
            f"{app_config.logging.max_bytes / (1024 * 1024):.2f} MB"
        )
        stats["Backup Count"] = str(app_config.logging.backup_count)
        stats["Log Encoding"] = app_config.logging.encoding
        stats["Log Format"] = app_config.logging.log_format
        stats["Date Format"] = app_config.logging.date_format

        # Database
        for key, value in app_config.database.export().items():
            stats[f"Database {key.replace('_', ' ').title()}"] = str(value) or "Not set"

        # Object Storage
        for key, value in app_config.object_store.export().items():
            stats[f"Object Store {key.replace('_', ' ').title()}"] = (
                str(value) or "Not set"
            )

        # Authentication
        stats["Signing Secret Key"] = (
            f"{'*' * 8}{app_config.authentication.signing_secret_key[-4:]}"
            if app_config.authentication.signing_secret_key
            else "Not set"
        )
        stats["Refresh Signing Secret Key"] = (
            f"{'*' * 8}{app_config.authentication.refresh_signing_secret_key[-4:]}"
            if app_config.authentication.refresh_signing_secret_key
            else "Not set"
        )
        stats["Encryption Secret Key"] = (
            f"{'*' * 8}{app_config.authentication.encryption_secret_key[-4:]}"
            if app_config.authentication.encryption_secret_key
            else "Not set"
        )
        stats["Signing Algorithm"] = app_config.authentication.signing_algorithm
        stats["Encryption Algorithm"] = app_config.authentication.encryption_algorithm
        stats["Encrypt JWT"] = "Yes" if app_config.authentication.encrypt_jwt else "No"
        stats["Encrypted Data Encoding"] = app_config.authentication.encoding
        stats["Access Token Expiry"] = (
            f"{app_config.authentication.access_token_expire_minutes} minutes"
        )
        stats["Refresh Token Expiry"] = (
            f"{app_config.authentication.refresh_token_expire_minutes} minutes"
        )
        stats["Recovery Token Expiry"] = (
            f"{app_config.authentication.recovery_token_expire_minutes} minutes"
        )
        stats["OTP Nonce Expiry"] = (
            f"{app_config.authentication.otp_nonce_expire_minutes} minutes"
        )

        # Security
        stats["Allowed Origins"] = ", ".join(app_config.security.allow_origins)
        stats["Allow Credentials"] = (
            "Enabled" if app_config.security.allow_credentials else "Disabled"
        )
        stats["Allowed Methods"] = ", ".join(app_config.security.allow_methods)
        stats["Allowed Headers"] = ", ".join(app_config.security.allow_headers)
        stats["Failed Login Notify Attempts"] = str(
            app_config.security.failed_login_notify_attempts
        )
        stats["Failed Login Lockout Attempts"] = str(
            app_config.security.failed_login_lockout_attempts
        )
        stats["Failed Login Lockout Minutes"] = (
            f"{app_config.security.failed_login_lockout_minutes} minutes"
        )

        # Mailing
        stats["Mailing Enabled"] = (
            "Enabled" if app_config.mailing.enabled else "Disabled"
        )
        stats["Mailing Server"] = app_config.mailing.server or "Not set"
        stats["Mailing Port"] = str(app_config.mailing.port) or "Not set"
        stats["Mailing From Address"] = app_config.mailing.from_address or "Not set"
        stats["Mailing Username"] = app_config.mailing.username or "Not set"
        stats["Mailing Password"] = (
            f"{'*' * 8}" if app_config.mailing.password else "Not set"
        )
        stats["Templates Directory"] = app_config.mailing.templates_dir or "Not set"
        stats["Templates Encoding"] = app_config.mailing.templates_encoding or "Not set"

        # Environment Variables
        stats["Environment Variables"] = (
            "Opted Out" if app_config.debug.logenv_optout else str(os.environ)
        )

    max_key_length = max(map(len, stats))
    _l = logger.debug if app_config.debug.enabled else logger.info
    for key, value in stats.items():
        _l(f"{key.rjust(max_key_length)} : {value}")
