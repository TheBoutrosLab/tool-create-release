"""Tests for CHANGELOG parsing and reformatting."""

import datetime

import pytest

from bumpchanges.bump import update_changelog
from bumpchanges.changelog import Changelog


def test_formatting(changelog_update):
    """Confirm that an example CHANGELOG can be parsed and formatted."""
    changelog = Changelog(changelog_update.original, changelog_update.url)

    if changelog_update.version is not None:
        changelog.update_version(changelog_update.version, changelog_update.date)

    result_text = changelog.render()

    expected_text = changelog_update.expected.read_text(encoding="utf-8")

    assert expected_text == result_text


@pytest.mark.parametrize("unreleased", ["## Unreleased\n\n", ""])
def test_release_without_pending_changes(tmp_path, unreleased):
    """Empty or missing Unreleased sections leave room for future changes."""
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(
        f"# Changelog\n\n{unreleased}"
        "## 1.0.0 - 2024-01-01\n\n### Added\n\n- Original change\n",
        encoding="utf-8",
    )

    update_changelog(
        changelog_file,
        "https://github.com/foo/bar",
        "1.0.1",
        datetime.date(2024, 2, 1),
    )

    assert changelog_file.read_text(encoding="utf-8") == (
        "# Changelog\n\n## [Unreleased]\n\n"
        "## [1.0.1] - 2024-02-01\n\n"
        "## [1.0.0] - 2024-01-01\n\n### Added\n\n- Original change\n\n"
        "[1.0.0]: https://github.com/foo/bar/releases/tag/v1.0.0\n"
        "[1.0.1]: https://github.com/foo/bar/compare/v1.0.0...v1.0.1\n"
        "[unreleased]: https://github.com/foo/bar/compare/v1.0.1...HEAD\n"
    )


def test_successive_releases(tmp_path):
    """Reparse released output and move only new changes into the next release."""
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(
        "# Changelog\n\n## Unreleased\n\n### Added\n\n- First change\n",
        encoding="utf-8",
    )
    repo_url = "https://github.com/foo/bar"
    update_changelog(changelog_file, repo_url, "1.0.0", datetime.date(2024, 1, 1))

    first_release = changelog_file.read_text(encoding="utf-8")
    assert "## [Unreleased]\n\n## [1.0.0] - 2024-01-01" in first_release
    changelog_file.write_text(
        first_release.replace(
            "## [Unreleased]\n",
            "## [Unreleased]\n\n### Fixed\n\n- Second change\n",
        ),
        encoding="utf-8",
    )
    update_changelog(changelog_file, repo_url, "1.0.1", datetime.date(2024, 2, 1))

    assert changelog_file.read_text(encoding="utf-8") == (
        "# Changelog\n\n## [Unreleased]\n\n"
        "## [1.0.1] - 2024-02-01\n\n### Fixed\n\n- Second change\n\n"
        "## [1.0.0] - 2024-01-01\n\n### Added\n\n- First change\n\n"
        "[1.0.0]: https://github.com/foo/bar/releases/tag/v1.0.0\n"
        "[1.0.1]: https://github.com/foo/bar/compare/v1.0.0...v1.0.1\n"
        "[unreleased]: https://github.com/foo/bar/compare/v1.0.1...HEAD\n"
    )
