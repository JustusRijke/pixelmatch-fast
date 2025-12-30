# pixelmatch-fast

[![Build](https://github.com/JustusRijke/pixelmatch-fast/actions/workflows/build.yml/badge.svg)](https://github.com/JustusRijke/pixelmatch-fast/actions/workflows/build.yml)
[![codecov](https://codecov.io/github/JustusRijke/pixelmatch-fast/graph/badge.svg?token=PXD6VY28LO)](https://codecov.io/github/JustusRijke/pixelmatch-fast)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dw/pixelmatch-fast)](https://pypi.org/project/pixelmatch-fast/)

High-performance Python port of [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) for perceptual image comparison

Pixelmatch is a tool that automatically highlights differences between two images while ignoring anti-aliasing artifacts.

For more information about pixelmatch capabilities and examples, see the [mapbox/pixelmatch repository](https://github.com/mapbox/pixelmatch).

This project tries to stay up to date with the current pixelmatch version (currently matches with v7.1.0).

## Similar Projects

This project is similar to [pixelmatch-py](https://github.com/whtsky/pixelmatch-py). The key difference is that pixelmatch-fast is much faster by leveraging [numpy](https://numpy.org/) for array operations and [numba](https://numba.pydata.org) for JIT compilation.

Use pixelmatch-py if you want a clean port with very little dependencies, use pixelmatch-fast if you need high performance.

## Installation

Install the package:
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
  --diff-color-alt TEXT  Alternative diff color for darkened pixels (R,G,B)
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
    diff_path="diff.png",  # Optional: save diff image
)

print(f"Found {num_diff} mismatched pixels")
```

## Development

Install with dev dependencies (pytest, ruff):
```bash
pip install -e .[dev]
```

Run tests:
```bash
pytest tests/
```

Run tests with coverage (disables numba JIT compilation):
```bash
NUMBA_DISABLE_JIT=1 pytest tests/ --cov
```

Check code quality:
```bash
ruff check
ruff format --check
```

Install pre-commit hook (runs ruff automatically before commits):
```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The CI workflow automatically runs tests both with and without numba enabled, ensuring both the optimized and fallback code paths are tested.


## License

MIT

