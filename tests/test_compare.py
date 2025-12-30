"""
Tests are identical to https://github.com/mapbox/pixelmatch/blob/v7.1.0/test/test.js
"""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pixelmatch import pixelmatch


@pytest.mark.parametrize(
    "img1, img2, diff, options, num_diffs",
    [
        ("1a", "1b", None, {"threshold": 0.05}, 143),
        ("1a", "1b", None, {}, 106),
        (
            "1a",
            "1b",
            "1diffmask",
            {"threshold": 0.05, "includeAA": False, "diff_mask": True},
            143,
        ),
        ("1a", "1a", "1emptydiffmask", {"threshold": 0, "diff_mask": True}, 0),
        (
            "2a",
            "2b",
            "2diff",
            {
                "threshold": 0.05,
                "alpha": 0.5,
                "aa_color": (0, 192, 0),
                "diff_color": (255, 0, 255),
            },
            12437,
        ),
        ("3a", "3b", "3diff", {"threshold": 0.05}, 212),
        ("4a", "4b", "4diff", {"threshold": 0.05}, 36049),
        ("5a", "5b", "5diff", {"threshold": 0.05}, 6),
        ("6a", "6b", "6diff", {}, 51),
        ("6a", "6a", "6empty", {"threshold": 0}, 0),
        ("7a", "7b", "7diff", {"diff_color_alt": (0, 255, 0)}, 2448),
        ("8a", "5b", "8diff", {"threshold": 0.05}, 32896),
    ],
)
def test_compare(img1, img2, diff, options, num_diffs, tmp_path):
    diff_path = tmp_path / "diff.png" if diff else None
    result_num_diffs = pixelmatch(
        Path(f"tests/fixtures/{img1}.png"),
        Path(f"tests/fixtures/{img2}.png"),
        diff_path=diff_path,
        **options,
    )

    assert result_num_diffs == num_diffs

    if diff:
        assert diff_path is not None
        expected_diff_image = Image.open(Path(f"tests/fixtures/{diff}.png")).convert(
            "RGBA"
        )
        actual_diff_image = Image.open(diff_path).convert("RGBA")
        assert np.array_equal(
            np.array(actual_diff_image), np.array(expected_diff_image)
        )


def test_compare_with_dimension_mismatch_raises_error(tmp_path):
    img1_path = tmp_path / "img1.png"
    img2_path = tmp_path / "img2.png"

    img1 = np.full((10, 10, 4), 255, dtype=np.uint8)
    img2 = np.full((20, 15, 4), 255, dtype=np.uint8)

    Image.fromarray(img1, mode="RGBA").save(img1_path)
    Image.fromarray(img2, mode="RGBA").save(img2_path)

    with pytest.raises(ValueError, match="Image dimensions must match"):
        pixelmatch(img1_path, img2_path)


def test_compare_with_pil_images():
    pil_img1 = Image.open(Path("tests/fixtures/1a.png"))
    pil_img2 = Image.open(Path("tests/fixtures/1b.png"))

    result_num_diffs = pixelmatch(pil_img1, pil_img2, threshold=0.05)

    assert result_num_diffs == 143
