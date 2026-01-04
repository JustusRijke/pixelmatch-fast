"""
Pixelmatch - Python port of mapbox/pixelmatch v7.1.0
https://github.com/mapbox/pixelmatch
"""

from importlib.metadata import version
from pathlib import Path
from typing import Union

import numpy as np
import numpy.typing as npt
from numba import njit, prange
from PIL import Image

__version__ = version("pixelmatch-fast")

MAX_YIQ_DELTA = 35215.0  # Maximum possible value for the YIQ difference metric


@njit(cache=True)
def _blend_channel(
    c1: float, a1: float, c2: float, a2: float, background: float, da: float
) -> float:
    """Blend single color channel with alpha compositing."""
    return (c1 * a1 - c2 * a2 - background * da) / 255.0


@njit(cache=True)
def _color_delta(
    img1: npt.NDArray[np.uint8],
    img2: npt.NDArray[np.uint8],
    k: int,
    m: int,
    y_only: bool,
) -> float:
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
def _has_many_siblings(
    img32: npt.NDArray[np.uint32], x1: int, y1: int, width: int, height: int
) -> bool:
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
def _antialiased(
    img: npt.NDArray[np.uint8],
    x1: int,
    y1: int,
    width: int,
    height: int,
    a32: npt.NDArray[np.uint32],
    b32: npt.NDArray[np.uint32],
) -> bool:
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
def _draw_pixel(
    output: npt.NDArray[np.uint8], pos: int, r: int, g: int, b: int
) -> None:
    """Draw RGBA pixel at position in output array."""
    output[pos] = r
    output[pos + 1] = g
    output[pos + 2] = b
    output[pos + 3] = 255


def _save_diff_output(
    output: Union[str, Path, Image.Image],
    output_arr: npt.NDArray[np.uint8],
) -> None:
    """Save or fill diff output image."""
    if isinstance(output, Image.Image):
        diff_img = Image.fromarray(output_arr, mode="RGBA")
        if output.size != diff_img.size:
            output.im = diff_img.im
            output._size = diff_img.size
        else:
            output.paste(diff_img)
    else:
        Image.fromarray(output_arr, mode="RGBA").save(Path(output), format="PNG")


@njit(cache=True)
def _compare_pixels(
    img1_flat: npt.NDArray[np.uint8],
    img2_flat: npt.NDArray[np.uint8],
    a32: npt.NDArray[np.uint32],
    b32: npt.NDArray[np.uint32],
    output_flat: npt.NDArray[np.uint8],
    width: int,
    height: int,
    max_delta: float,
    includeAA: bool,
    diff_mask: bool,
    aa_r: int,
    aa_g: int,
    aa_b: int,
    diff_r: int,
    diff_g: int,
    diff_b: int,
    diff_alt_r: int,
    diff_alt_g: int,
    diff_alt_b: int,
) -> int:
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
def _draw_gray_pixels(
    img_arr: npt.NDArray[np.uint8], output_arr: npt.NDArray[np.uint8], alpha: float
) -> None:
    """Draw grayscale background with alpha blending."""
    h, w = img_arr.shape[:2]
    for y in prange(h):  # type: ignore
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
    img1: Union[str, Path, Image.Image],
    img2: Union[str, Path, Image.Image],
    output: Union[str, Path, Image.Image, None] = None,
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
        img1: First image file path or PIL Image object
        img2: Second image file path or PIL Image object
        output: Optional output for diff image. Can be a path (str/Path) to save as PNG, or a PIL Image object to fill with diff data.
        threshold: Matching threshold (0 to 1); smaller is more sensitive.
        includeAA: Whether to count anti-aliased pixels as different.
        alpha: Opacity of original image in diff output.
        aa_color: Color of anti-aliased pixels in diff output. Default yellow.
        diff_color: Color of different pixels in diff output. Default red.
        diff_color_alt: Alternative color to differentiate between "added" and "removed" parts. Default same as diff_color.
        diff_mask: Draw the diff over a transparent background (a mask).

    Returns:
        Number of mismatched pixels
    """
    # Load images as RGBA arrays
    if isinstance(img1, Image.Image):
        pil_img1 = img1.convert("RGBA")
    else:
        try:  # pragma: no cover
            pil_img1 = Image.open(img1).convert("RGBA")
        except Exception as e:  # pragma: no cover
            raise FileNotFoundError(f"Cannot open image file: {img1}") from e

    if isinstance(img2, Image.Image):
        pil_img2 = img2.convert("RGBA")
    else:
        try:  # pragma: no cover
            pil_img2 = Image.open(img2).convert("RGBA")
        except Exception as e:  # pragma: no cover
            raise FileNotFoundError(f"Cannot open image file: {img2}") from e

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
        if output:  # pragma: no cover
            _save_diff_output(output, output_arr)
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

    # Save diff image if output provided
    if output:
        _save_diff_output(output, output_arr)

    return diff


__all__ = ["pixelmatch", "__version__"]
