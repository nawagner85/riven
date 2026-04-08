"""Prism-aware filesystem service.

Instead of mounting a FUSE VFS, this service polls the Prism mount path
for the expected sanitized title after a download completes. When found
(or after timeout), it advances the item to Symlinked state so the Plex
updater can scan.
"""

import re
import time
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from program.media.item import Episode, MediaItem, Movie
from program.media.state import States
from program.core.runner import MediaItemGenerator, Runner, RunnerResult
from program.settings import settings_manager
from program.settings.models import PrismModel

if TYPE_CHECKING:
    pass


def sanitize_title_for_prism(
    title: str,
    year: int | None = None,
    season: int | None = None,
    episode: int | None = None,
) -> str:
    """Approximate Prism's sanitizeName output for path matching.

    Prism strips quality tags, converts dots/dashes to spaces, and formats as:
      - Movie: "Title (Year)"
      - Episode: "Title S01E01"
    We replicate only what's needed for directory lookup — exact match not
    required, we do a fuzzy scan of the directory listing.
    """
    # Strip characters Prism strips (colons, special punctuation)
    cleaned = re.sub(r"[:/\\]", " ", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if season is not None and episode is not None:
        return f"{cleaned} S{season:02d}E{episode:02d}"

    if year is not None:
        return f"{cleaned} ({year})"

    return cleaned


def _find_in_directory(base: Path, expected: str) -> Path | None:
    """Case-insensitive fuzzy search for expected title in base directory."""
    if not base.exists():
        return None

    expected_lower = expected.lower()
    for entry in base.iterdir():
        if entry.name.lower().startswith(expected_lower[:20]):
            return entry

    return None


class PrismFilesystemService(Runner[PrismModel]):
    """Filesystem service that polls the Prism FUSE mount for completed downloads.

    Replaces FilesystemService (RivenVFS) for Prism-mode operation.
    Does not require pyfuse3.
    """

    def __init__(self):
        super().__init__()
        self.settings = settings_manager.settings.prism
        self.initialized = self.validate()

    @classmethod
    def get_key(cls) -> str:
        return "filesystem"

    def validate(self) -> bool:
        if not self.settings.enabled:
            return False

        mount_path = Path(self.settings.mount_path)
        if not mount_path.exists():
            logger.error(f"PrismFilesystemService: mount path does not exist: {mount_path}")
            return False

        logger.success(f"PrismFilesystemService initialized (mount: {mount_path})")
        return True

    def run(self, item: MediaItem) -> MediaItemGenerator:
        """Poll Prism mount for item, then mark Symlinked."""

        mount_path = Path(self.settings.mount_path)
        timeout = self.settings.poll_timeout_seconds

        if isinstance(item, Movie):
            expected = sanitize_title_for_prism(item.title, year=item.year)
            search_dir = mount_path / "movies"
        elif isinstance(item, Episode):
            expected = sanitize_title_for_prism(
                item.parent.parent.title,
                season=item.parent.number,
                episode=item.number,
            )
            search_dir = mount_path / "shows" / sanitize_title_for_prism(item.parent.parent.title)
        else:
            # For show/season containers, advance without polling (leaf items drive state)
            item.store_state(States.Symlinked)
            yield RunnerResult(media_items=[item])
            return

        found = self._poll_for_path(search_dir, expected, timeout)

        if found:
            logger.info(f"Found {item.log_string} in Prism mount at {found}")
        else:
            logger.warning(
                f"PrismFilesystemService: {item.log_string} not found in Prism mount "
                f"after {timeout}s — advancing anyway (Plex will pick it up on next scan)"
            )

        item.store_state(States.Symlinked)
        yield RunnerResult(media_items=[item])

    def _poll_for_path(self, search_dir: Path, expected: str, timeout: int) -> Path | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found = _find_in_directory(search_dir, expected)
            if found:
                return found
            time.sleep(1)
        return None
