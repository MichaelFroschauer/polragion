"""Transport-independent GitHub allowlist policy. Configuration errors deny access."""

import logging
from pathlib import Path

from pydantic import ValidationError

from polragion.models.user import GitHubUserConfig
from polragion.settings import Settings

logger = logging.getLogger(__name__)


class AccessDenied(Exception):
    pass


class PolicyUnavailable(Exception):
    pass


class AccessPolicy:
    def __init__(self, settings: Settings):
        self.settings = settings

    def load(self) -> GitHubUserConfig:
        if not self.settings.github_user_config_path:
            raise PolicyUnavailable("GitHub user allowlist is not configured")
        try:
            return GitHubUserConfig.model_validate_json(
                Path(self.settings.github_user_config_path).read_text(encoding="utf-8")
            )
        except (OSError, ValidationError) as exc:
            logger.error("Could not load GitHub user allowlist: %s", exc)
            raise PolicyUnavailable("GitHub user allowlist is unavailable") from exc

    @staticmethod
    def is_allowed(username: str, config: GitHubUserConfig) -> bool:
        return username.casefold() in {entry.userName.casefold() for entry in config.whiteList}

    def require_allowed(self, username: str) -> None:
        if not self.is_allowed(username, self.load()):
            raise AccessDenied("GitHub user is not allowed")
