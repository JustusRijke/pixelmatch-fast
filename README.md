# pixelmatch-fast

[![Build](https://github.com/JustusRijke/pixelmatch-fast/actions/workflows/build.yml/badge.svg)](https://github.com/JustusRijke/pixelmatch-fast/actions/workflows/build.yml)
[![codecov](https://codecov.io/github/JustusRijke/pixelmatch-fast/graph/badge.svg?token=PXD6VY28LO)](https://codecov.io/github/JustusRijke/pixelmatch-fast)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/pixelmatch-fast)](https://pypi.org/project/pixelmatch-fast/)
[![PyPI - Downloads](https://img.shields.io/pypi/dw/pixelmatch-fast)](https://pypi.org/project/pixelmatch-fast/)

High-performance Python port of [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) for image comparison.

Pixelmatch is a tool that automatically highlights differences between two images while ignoring anti-aliasing artifacts. For more information about pixelmatch capabilities and examples, see the [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) repository.

## Installation

Install Python (v3.10 or higher) and install the package:

```bash
pip install pixelmatch-fast
```

## CLI Usage

```bash
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

## Similar Projects

- **[mapbox/pixelmatch](https://github.com/mapbox/pixelmatch)**: The original pixelmatch implementation (JavaScript).
- **[pixelmatch-py](https://github.com/whtsky/pixelmatch-py)**: A pure-Python port with no dependencies. Best for environments where speed isn't critical or where you cannot install heavy libraries.
- **[pybind11-pixelmatch](https://github.com/cubao/pybind11_pixelmatch)**: Python bindings for the C++ port of pixelmatch. Offers the highest raw performance but may require a C++ compiler if wheels aren't available for your platform and can encounter issues with modern installers like `uv`.

### Performance Comparison

Test conditions: 500×100 RGBA images, Python 3.11.2.

| Variant | Cold Start | Warm Start (JIT) | Relative Speed |
| - | - | - | - |
| mapbox/pixelmatch (JS) | 139 ms | 113 ms | **1.00x** |
| pixelmatch-py | 12,397 ms | 12,216 ms | **0.01x** |
| pybind11-pixelmatch | 88 ms | 81 ms | **1.40x** |
| pixelmatch-fast | 1972 ms | 101 ms | **1.12x** |

**Why is the warm start faster?**
`pixelmatch-fast` leverages [numba](https://numba.pydata.org) for Just-In-Time (JIT) compilation. The "Cold Start" includes the one-time overhead of Numba compiling the Python code into optimized machine code. Subsequent "Warm Start" executions run at full compiled speed.

**Why choose pixelmatch-fast?**
While `pybind11-pixelmatch` is faster, `pixelmatch-fast` tries to stay up to date with the current `mapbox/pixelmatch` version (currently v7.1.0), provides a more Pythonic experience and is compatible with modern tooling like `uv`. It delivers a **100x speedup** over the pure-Python baseline without the complexities of C++ extensions.

## Development

Install [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation). Then, install dependencies & activate the automatically generated virtual environment:

```bash
uv sync --locked
source .venv/bin/activate
```

Skip `--locked` to use the newest dependencies (this might modify `uv.lock`)

### Testing

Run tests:

```bash
pytest
```

Run tests with coverage (disables numba JIT compilation):

```bash
NUMBA_DISABLE_JIT=1 pytest --cov
```

### Quality Assurance (QA)

Automatically run code quality checks before every commit using [pre-commit](https://pre-commit.com/):

```bash
pre-commit install
```

This installs git hooks that run ruff, type checks, and other checks before each commit. You can run manually at any time with:

```bash
pre-commit run --all-files
```

The CI workflow automatically runs tests both with and without numba enabled, ensuring both the optimized and fallback code paths are tested.

## License

MIT
