"""Tests for PrismFilesystemService"""
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from program.services.filesystem.prism_filesystem_service import (
    PrismFilesystemService,
    sanitize_title_for_prism,
)
from program.media.item import Movie, Episode, Season, Show
from program.media.state import States


def make_movie(title: str, year: int | None = 2024, imdb_id: str = "tt1234567") -> Movie:
    m = Movie({"title": title, "year": year, "imdb_id": imdb_id})
    m.last_state = States.Downloaded
    return m


def make_episode(show_title: str, season: int, episode: int) -> Episode:
    show = Show({"title": show_title, "imdb_id": "tt9999999"})
    s = Season({"number": season})
    s.parent = show
    ep = Episode({"number": episode, "title": f"Episode {episode}"})
    ep.parent = s
    ep.last_state = States.Downloaded
    return ep


class TestSanitizeTitleForPrism:
    def test_movie_with_year(self):
        assert sanitize_title_for_prism("The Dark Knight", year=2008) == "The Dark Knight (2008)"

    def test_movie_without_year(self):
        assert sanitize_title_for_prism("Unknown Film") == "Unknown Film"

    def test_strips_special_chars(self):
        # Colons and other chars Prism strips
        assert sanitize_title_for_prism("Mission: Impossible", year=1996) == "Mission Impossible (1996)"

    def test_episode(self):
        assert sanitize_title_for_prism("Breaking Bad", season=1, episode=1) == "Breaking Bad S01E01"


class TestPrismFilesystemService:
    def test_finds_movie_in_prism_mount(self, tmp_path):
        # Create a fake Prism movies directory with the expected title
        movies_dir = tmp_path / "movies" / "The Dark Knight (2008)"
        movies_dir.mkdir(parents=True)
        (movies_dir / "The Dark Knight (2008).mkv").touch()

        settings = MagicMock()
        settings.enabled = True
        settings.mount_path = tmp_path
        settings.poll_timeout_seconds = 5

        with patch("program.services.filesystem.prism_filesystem_service.settings_manager") as sm:
            sm.settings.prism = settings
            service = PrismFilesystemService()
            movie = make_movie("The Dark Knight", year=2008)
            results = list(service.run(movie))

        assert len(results) == 1
        assert results[0].media_items[0].last_state == States.Symlinked

    def test_times_out_and_still_advances(self, tmp_path):
        # Empty mount — file never appears. Should still advance after timeout.
        settings = MagicMock()
        settings.enabled = True
        settings.mount_path = tmp_path
        settings.poll_timeout_seconds = 1  # short for test

        with patch("program.services.filesystem.prism_filesystem_service.settings_manager") as sm:
            sm.settings.prism = settings
            service = PrismFilesystemService()
            movie = make_movie("Nonexistent Film", year=2024)
            start = time.monotonic()
            results = list(service.run(movie))
            elapsed = time.monotonic() - start

        assert elapsed >= 1.0
        assert len(results) == 1  # still advances
        assert results[0].media_items[0].last_state == States.Symlinked

    def test_finds_episode_in_shows_dir(self, tmp_path):
        shows_dir = tmp_path / "shows" / "Breaking Bad" / "Breaking Bad S01E01"
        shows_dir.mkdir(parents=True)
        (shows_dir / "Breaking Bad S01E01.mkv").touch()

        settings = MagicMock()
        settings.enabled = True
        settings.mount_path = tmp_path
        settings.poll_timeout_seconds = 5

        with patch("program.services.filesystem.prism_filesystem_service.settings_manager") as sm:
            sm.settings.prism = settings
            service = PrismFilesystemService()
            ep = make_episode("Breaking Bad", season=1, episode=1)
            results = list(service.run(ep))

        assert results[0].media_items[0].last_state == States.Symlinked
