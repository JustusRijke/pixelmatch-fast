import numpy as np
from click.testing import CliRunner
from PIL import Image

from pixelmatch.cli import cli


def test_cli_compares_identical_images() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        img = np.full((10, 10, 4), 255, dtype=np.uint8)
        Image.fromarray(img, mode="RGBA").save("img1.png")
        Image.fromarray(img, mode="RGBA").save("img2.png")

        result = runner.invoke(cli, ["img1.png", "img2.png"])

        assert result.exit_code == 0
        assert "Mismatched pixels: 0" in result.output


def test_cli_exit_code_on_identical_images() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        img = np.full((10, 10, 4), 255, dtype=np.uint8)
        Image.fromarray(img, mode="RGBA").save("img1.png")
        Image.fromarray(img, mode="RGBA").save("img2.png")

        result = runner.invoke(cli, ["img1.png", "img2.png"])

        assert result.exit_code == 0


def test_cli_exit_code_on_different_images() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        img1 = np.full((10, 10, 4), 255, dtype=np.uint8)
        img2 = np.full((10, 10, 4), 128, dtype=np.uint8)
        Image.fromarray(img1, mode="RGBA").save("img1.png")
        Image.fromarray(img2, mode="RGBA").save("img2.png")

        result = runner.invoke(cli, ["img1.png", "img2.png"])

        assert result.exit_code == 1
