# pixelmatch-fast

[![Build](https://github.com/JustusRijke/pixelmatch-fast/actions/workflows/build.yml/badge.svg)](https://github.com/JustusRijke/pixelmatch-fast/actions/workflows/build.yml)
[![codecov](https://codecov.io/github/JustusRijke/pixelmatch-fast/graph/badge.svg?token=PXD6VY28LO)](https://codecov.io/github/JustusRijke/pixelmatch-fast)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/pixelmatch-fast)](https://pypi.org/project/pixelmatch-fast/)
[![PyPI - Downloads](https://img.shields.io/pypi/dw/pixelmatch-fast)](https://pypi.org/project/pixelmatch-fast/)

High-performance Python port of [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) for perceptual image comparison

Pixelmatch is a tool that automatically highlights differences between two images while ignoring anti-aliasing artifacts.

For more information about pixelmatch capabilities and examples, see the [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) repository.

This project tries to stay up to date with the current pixelmatch version (currently matches with v7.1.0).

## Similar Projects

This project is similar to [pixelmatch-py](https://github.com/whtsky/pixelmatch-py). The key difference is that pixelmatch-fast is much faster by leveraging [numpy](https://numpy.org/) for array operations and [numba](https://numba.pydata.org) for JIT compilation.

Use pixelmatch-py if you want a clean port with very little dependencies, use pixelmatch-fast if you need high performance.

## Installation

Install Python (v3.10 or higher) and install the package:

```bash
pip install pixelmatch-fast
```

## CLI Usage

```
$ pixelmatch --help

Usage: pixelmatch [OPTIONS] IMG1 IMG2

  Compare two images pixel-by-pixel and visualize differences.

Options:
  --version              Show the version and exit.
  -o, --output PATH      Path to save diff image (PNG format)
  -t, --threshold FLOAT  Matching threshold (0 to 1); smaller is more
                         sensitive  [default: 0.1]
  --include-aa           Count anti-aliased pixels as different
  -a, --alpha FLOAT      Opacity of original image in diff output  [default:
                         0.1]
  --aa-color TEXT        Color of anti-aliased pixels (R,G,B)  [default:
                         255,255,0]
  --diff-color TEXT      Color of different pixels (R,G,B)  [default: 255,0,0]
  --diff-color-alt TEXT  Alternative color to differentiate between "added" and "removed" parts (R,G,B)
  --diff-mask            Draw diff over transparent background
  --help                 Show this message and exit.
```

Example (using test images from the [mapbox/pixelmatch repository](https://github.com/mapbox/pixelmatch/tree/main/test/fixtures)):
```bash
$ pixelmatch 1a.png 1b.png -o diff.png
Mismatched pixels: 106
```

The CLI exits with code `0` if images match and `1` if they differ (i.e., one or more mismatched pixels).

## Library Usage

```python
from pixelmatch import pixelmatch

# Compare two images and get mismatch count
num_diff = pixelmatch(
    "image1.png",
    "image2.png",
    output="diff.png",  # Optional: save diff image
)

print(f"Found {num_diff} mismatched pixels")
```

### Arguments

- `img1`, `img2` — Image paths (str or Path) or PIL Image objects to compare. Note: image dimensions must be equal.
- `output` — Image output for the diff. Can be a file path (str or Path) to save as PNG, a PIL Image object to fill with diff data, or `None` if diff output is not needed.
- `threshold` — Matching threshold, ranges from `0` to `1`. Smaller values make the comparison more sensitive. `0.1` by default.
- `includeAA` — Whether to count anti-aliased pixels as different. `False` by default.
- `alpha` — Blending factor of unchanged pixels in the diff output. Ranges from `0` for pure white to `1` for original brightness. `0.1` by default.
- `aa_color` — Tuple of `(R, G, B)` color for anti-aliased pixels in diff output. `(255, 255, 0)` (yellow) by default.
- `diff_color` — Tuple of `(R, G, B)` color for different pixels in diff output. `(255, 0, 0)` (red) by default.
- `diff_color_alt` — Tuple of `(R, G, B)` for an alternative color to use for dark on light differences to differentiate between "added" and "removed" parts. If not provided, all differing pixels use `diff_color`.
- `diff_mask` — Draw the diff over a transparent background (a mask), rather than over the original image. `False` by default.


## Development

Install [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation). Then, install dependencies & activate the automatically generated virtual environment:

```bash
uv sync --locked
source .venv/bin/activate
```

Skip `--locked` to use the newest dependencies (this might modify `uv.lock`)

Run tests:
```bash
pytest
```

Run tests with coverage (disables numba JIT compilation):
```bash
NUMBA_DISABLE_JIT=1 pytest --cov
```

Check code quality:
```bash
ruff check
ruff format --check
ty check
```

Better yet, install the [pre-commit](.git/hooks/pre-commit) hook, which runs code quality checks before every commit:
```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The CI workflow automatically runs tests both with and without numba enabled, ensuring both the optimized and fallback code paths are tested.

## License

MIT

