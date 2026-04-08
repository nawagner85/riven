from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar, TypeAlias

from program.settings.models import Observable
from program.media.item import MediaItem


# Use TypeAlias for Python 3.12 compatibility (upstream uses Python 3.13+ 'type' syntax)
# TODO: migrate to `type MediaItemGenerator[T: MediaItem = MediaItem]` when Python 3.13+ is required
MediaItemGenerator: TypeAlias = Generator[
    "RunnerResult", None, "RunnerResult | None"
]

# For Python 3.12 compatibility, use a single TypeVar instead of 3 separate ones with defaults
# Upstream (Python 3.13+) would use TSettings and TService as separate params with defaults
TSettings = TypeVar("TSettings", bound=Observable | None)
TService = TypeVar("TService", bound=Any | None)
TRunnerReturnType = TypeVar("TRunnerReturnType")
TItemType = TypeVar("TItemType", bound=MediaItem)


@dataclass
class RunnerResult(Generic[TItemType]):
    media_items: list[TItemType]
    run_at: datetime | None = None


class Runner(ABC, Generic[TSettings]):
    """Base class for all runners

    In Python 3.13+, this would use Generic[TSettings, TService=None, TRunnerReturnType=MediaItemGenerator]
    For Python 3.12 compatibility, we provide __class_getitem__ to accept variable type parameters.
    """

    is_content_service: bool = False
    settings: TSettings
    services = dict[type[Any], Any]()

    def __class_getitem__(cls, params: Any) -> Any:
        """Allow variable number of type parameters for backward compatibility with Python 3.12"""
        # Just return the class to avoid TypeVar parameter mismatches
        return cls

    def __init__(self):
        super().__init__()

        self.key = self.get_key()
        self.initialized = False

    @classmethod
    def get_key(cls) -> str:
        """Get the key for the runner"""

        return cls.__name__.lower()

    @property
    def enabled(self) -> bool:
        """
        Check if the runner is enabled.

        Returns True for core runners without settings, else returns the `enabled` attribute from the runner's settings.
        """

        if not hasattr(self, "settings") or not hasattr(self.settings, "enabled"):
            return True

        return getattr(self.settings, "enabled", True)

    def validate(self) -> bool:
        """Validate the runner"""

        return True

    @abstractmethod
    def run(self, item: MediaItem) -> Any:
        """Run the base runner"""

        raise NotImplementedError

    def should_submit(self, item: MediaItem) -> bool:
        """Determine if the runner should submit an item for processing."""

        return True
