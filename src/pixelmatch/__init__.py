"""
Pixelmatch - Python port of mapbox/pixelmatch v7.1.0
https://github.com/mapbox/pixelmatch
"""

from importlib.metadata import version
from pathlib import Path
from typing import Union

import numpy as np
from numba import njit, prange
from PIL import Image

__version__ = version("pixelmatch-fast")

MAX_YIQ_DELTA = 35215.0  # Maximum possible value for the YIQ difference metric


@njit(cache=True)
def _blend_channel(c1, a1, c2, a2, background, da):
    """Blend single color channel with alpha compositing."""
    return (c1 * a1 - c2 * a2 - background * da) / 255.0


@njit(cache=True)
def _color_delta(img1, img2, k, m, y_only):
    """Calculate color difference using YIQ color space."""
    r1 = float(img1[k])
    g1 = float(img1[k + 1])
    b1 = float(img1[k + 2])
    a1 = float(img1[k + 3])
    r2 = float(img2[m])
    g2 = float(img2[m + 1])
    b2 = float(img2[m + 2])
    a2 = float(img2[m + 3])

    dr = r1 - r2
    dg = g1 - g2
    db = b1 - b2
    da = a1 - a2

    if dr == 0 and dg == 0 and db == 0 and da == 0:
        return 0.0

    if a1 < 255 or a2 < 255:
        rb = 48.0 + 159.0 * (k % 2)
        gb = 48.0 + 159.0 * (int(k / 1.618033988749895) % 2)
        bb = 48.0 + 159.0 * (int(k / 2.618033988749895) % 2)
        dr = _blend_channel(r1, a1, r2, a2, rb, da)
        dg = _blend_channel(g1, a1, g2, a2, gb, da)
        db = _blend_channel(b1, a1, b2, a2, bb, da)

    y = dr * 0.29889531 + dg * 0.58662247 + db * 0.11448223

    if y_only:
        return y

    i = dr * 0.59597799 - dg * 0.27417610 - db * 0.32180189
    q = dr * 0.21147017 - dg * 0.52261711 + db * 0.31114694

    delta = 0.5053 * y * y + 0.299 * i * i + 0.1957 * q * q

    if y > 0:
        return -delta
    return delta


@njit(cache=True)
def _has_many_siblings(img32, x1, y1, width, height):
    """Check if pixel has 3+ identical neighbors."""
    x0 = max(x1 - 1, 0)
    y0 = max(y1 - 1, 0)
    x2 = min(x1 + 1, width - 1)
    y2 = min(y1 + 1, height - 1)

    pos = y1 * width + x1
    val = img32[pos]

    if x1 == x0 or x1 == x2 or y1 == y0 or y1 == y2:
        zeroes = 1
    else:
        zeroes = 0

    for x in range(x0, x2 + 1):
        for y in range(y0, y2 + 1):
            if x == x1 and y == y1:
                continue
            if val == img32[y * width + x]:
                zeroes += 1
            if zeroes > 2:
                return True

    return False


@njit(cache=True)
def _antialiased(img, x1, y1, width, height, a32, b32):
    """Detect if pixel is anti-aliased."""
    x0 = max(x1 - 1, 0)
    y0 = max(y1 - 1, 0)
    x2 = min(x1 + 1, width - 1)
    y2 = min(y1 + 1, height - 1)

    pos = y1 * width + x1

    if x1 == x0 or x1 == x2 or y1 == y0 or y1 == y2:
        zeroes = 1
    else:
        zeroes = 0

    min_delta = 0.0
    max_delta = 0.0
    min_x = 0
    min_y = 0
    max_x = 0
    max_y = 0

    for x in range(x0, x2 + 1):
        for y in range(y0, y2 + 1):
            if x == x1 and y == y1:
                continue

            delta = _color_delta(img, img, pos * 4, (y * width + x) * 4, True)

            if delta == 0:
                zeroes += 1
                if zeroes > 2:
                    return False
            elif delta < min_delta:
                min_delta = delta
                min_x = x
                min_y = y
            elif delta > max_delta:
                max_delta = delta
                max_x = x
                max_y = y

    if min_delta == 0 or max_delta == 0:
        return False

    return (
        _has_many_siblings(a32, min_x, min_y, width, height)
        and _has_many_siblings(b32, min_x, min_y, width, height)
    ) or (
        _has_many_siblings(a32, max_x, max_y, width, height)
        and _has_many_siblings(b32, max_x, max_y, width, height)
    )


@njit(cache=True)
def _draw_pixel(output, pos, r, g, b):
    """Draw RGBA pixel at position in output array."""
    output[pos] = r
    output[pos + 1] = g
    output[pos + 2] = b
    output[pos + 3] = 255


@njit(cache=True)
def _compare_pixels(
    img1_flat,
    img2_flat,
    a32,
    b32,
    output_flat,
    width,
    height,
    max_delta,
    includeAA,
    diff_mask,
    aa_r,
    aa_g,
    aa_b,
    diff_r,
    diff_g,
    diff_b,
    diff_alt_r,
    diff_alt_g,
    diff_alt_b,
):
    """Compare pixels and draw diff output. Returns mismatch count."""
    diff = 0
    for y in range(height):
        for x in range(width):
            i = y * width + x
            pos = i * 4

            if a32[i] == b32[i]:
                delta = 0.0
            else:
                delta = _color_delta(img1_flat, img2_flat, pos, pos, False)

            if abs(delta) > max_delta:
                is_aa = _antialiased(
                    img1_flat, x, y, width, height, a32, b32
                ) or _antialiased(img2_flat, x, y, width, height, b32, a32)

                if not includeAA and is_aa:
                    if not diff_mask:
                        _draw_pixel(output_flat, pos, aa_r, aa_g, aa_b)
                else:
                    if delta < 0:
                        _draw_pixel(
                            output_flat, pos, diff_alt_r, diff_alt_g, diff_alt_b
                        )
                    else:
                        _draw_pixel(output_flat, pos, diff_r, diff_g, diff_b)
                    diff += 1
    return diff


@njit(cache=True, parallel=True)
def _draw_gray_pixels(img_arr, output_arr, alpha):
    """Draw grayscale background with alpha blending."""
    h, w = img_arr.shape[:2]
    for y in prange(h):
        for x in range(w):
            r = float(img_arr[y, x, 0])
            g = float(img_arr[y, x, 1])
            b = float(img_arr[y, x, 2])
            a = float(img_arr[y, x, 3])
            brightness = r * 0.29889531 + g * 0.58662247 + b * 0.11448223
            val = 255.0 + (brightness - 255.0) * alpha * a / 255.0
            val_u8 = np.uint8(val)
            output_arr[y, x, 0] = val_u8
            output_arr[y, x, 1] = val_u8
            output_arr[y, x, 2] = val_u8
            output_arr[y, x, 3] = 255


def pixelmatch(
    img1: Union[str, Path],
    img2: Union[str, Path],
    diff_path: Union[str, Path, None] = None,
    threshold: float = 0.1,
    includeAA: bool = False,
    alpha: float = 0.1,
    aa_color: tuple[int, int, int] = (255, 255, 0),
    diff_color: tuple[int, int, int] = (255, 0, 0),
    diff_color_alt: tuple[int, int, int] | None = None,
    diff_mask: bool = False,
) -> int:
    """
    Compare two images and return number of mismatched pixels.

    Args:
        img1: First image file path
        img2: Second image file path
        diff_path: Optional path to save diff image as PNG
        threshold: Matching threshold (0 to 1); smaller is more sensitive.
        includeAA: Whether to count anti-aliased pixels as different.
        alpha: Opacity of original image in diff output.
        aa_color: Color of anti-aliased pixels in diff output. Default yellow.
        diff_color: Color of different pixels in diff output. Default red.
        diff_color_alt: Alternative diff color for darkened pixels. Default same as diff_color.
        diff_mask: Draw the diff over a transparent background (a mask).

    Returns:
        Number of mismatched pixels
    """
    # Load images as RGBA arrays
    pil_img1 = Image.open(img1).convert("RGBA")
    pil_img2 = Image.open(img2).convert("RGBA")
    arr1 = np.array(pil_img1, dtype=np.uint8)
    arr2 = np.array(pil_img2, dtype=np.uint8)

    height, width = arr1.shape[:2]
    height2, width2 = arr2.shape[:2]

    if (height, width) != (height2, width2):
        raise ValueError(
            f"Image dimensions must match: {width}x{height} vs {width2}x{height2}"
        )

    if not 0 <= alpha <= 1:  # pragma: no cover
        raise ValueError(f"alpha must be in range [0, 1], got {alpha}")

    # Flatten arrays and create output
    img1_flat = arr1.ravel()
    img2_flat = arr2.ravel()
    output_arr = np.zeros((height, width, 4), dtype=np.uint8)
    output_flat = output_arr.ravel()

    # Handle diff_color_alt default
    if diff_color_alt is None:
        diff_color_alt = diff_color

    # Create Uint32 views for fast pixel comparison
    a32 = img1_flat.view(np.uint32)
    b32 = img2_flat.view(np.uint32)

    # Fast path for identical images
    if np.array_equal(a32, b32):
        if not diff_mask:
            _draw_gray_pixels(arr1, output_arr, alpha)
        if diff_path:  # pragma: no cover
            Image.fromarray(output_arr, mode="RGBA").save(Path(diff_path), format="PNG")
        return 0

    max_delta = MAX_YIQ_DELTA * threshold * threshold

    if not diff_mask:
        _draw_gray_pixels(arr1, output_arr, alpha)

    diff = _compare_pixels(
        img1_flat,
        img2_flat,
        a32,
        b32,
        output_flat,
        width,
        height,
        max_delta,
        includeAA,
        diff_mask,
        aa_color[0],
        aa_color[1],
        aa_color[2],
        diff_color[0],
        diff_color[1],
        diff_color[2],
        diff_color_alt[0],
        diff_color_alt[1],
        diff_color_alt[2],
    )

    # Save diff image if path provided
    if diff_path:
        Image.fromarray(output_arr, mode="RGBA").save(Path(diff_path), format="PNG")

    return diff


__all__ = ["pixelmatch", "__version__"]
