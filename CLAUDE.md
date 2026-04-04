# Riven Fork — Session Guide

Fork of rivenmedia/riven. Adds Prism filesystem integration (Phase 1) and music content type (Phase 2).

## Key differences from upstream
- `PrismFilesystemService` replaces `FilesystemService` / RivenVFS
- `Artist`, `Album`, `Track` media types (Phase 2)
- `MusicBrainzIndexer`, `SpotifyContent`, music scrapers (Phase 2)

## Running locally
See `pyproject.toml` for dependencies. Requires Python 3.12.

## Design spec
`../docs/superpowers/specs/2026-04-04-riven-fork-design.md`
