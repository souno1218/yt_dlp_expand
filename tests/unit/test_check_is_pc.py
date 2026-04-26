"""check_is_pc() のユニットテスト。 / Unit tests for check_is_pc()."""

import platform
from unittest.mock import patch

import pytest

from yt_dlp_expand.main_script import check_is_pc


@pytest.mark.parametrize(
    "os_name, platform_str, expected",
    [
        # macOS (PC)
        ("Darwin", "macOS-14.0-x86_64", True),
        # iPhone
        ("Darwin", "iOS-17.0-iPhone14,3", False),
        # iPad
        ("Darwin", "iPadOS-17.0-iPad13,4", False),
        # Linux
        ("Linux", "Linux-5.15-x86_64", True),
        # Windows
        ("Windows", "Windows-10-x86_64", True),
        # iOS (system() returns "iOS" directly on some environments)
        ("iOS", "iOS-17.0-iPhone14,3", False),
        # iPadOS
        ("iPadOS", "iPadOS-17.0-iPad13,4", False),
    ],
)
def test_check_is_pc(os_name: str, platform_str: str, expected: bool) -> None:
    with (
        patch.object(platform, "system", return_value=os_name),
        patch.object(platform, "platform", return_value=platform_str),
    ):
        assert check_is_pc() == expected


def test_check_is_pc_unsupported_os() -> None:
    with (
        patch.object(platform, "system", return_value="FreeBSD"),
        patch.object(platform, "platform", return_value="FreeBSD-13.0"),
    ):
        with pytest.raises(ValueError, match="Unsupported operating system"):
            check_is_pc()
