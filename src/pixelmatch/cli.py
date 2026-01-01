from typing import cast

import click

from . import pixelmatch


@click.command()
@click.version_option(package_name="pixelmatch-fast")
@click.argument("img1", type=click.Path(exists=True))
@click.argument("img2", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Path to save diff image (PNG format)",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.1,
    show_default=True,
    help="Matching threshold (0 to 1); smaller is more sensitive",
)
@click.option(
    "--include-aa",
    "includeAA",
    is_flag=True,
    default=False,
    help="Count anti-aliased pixels as different",
)
@click.option(
    "--alpha",
    "-a",
    type=float,
    default=0.1,
    show_default=True,
    help="Opacity of original image in diff output",
)
@click.option(
    "--aa-color",
    type=str,
    default="255,255,0",
    show_default=True,
    help="Color of anti-aliased pixels (R,G,B)",
)
@click.option(
    "--diff-color",
    type=str,
    default="255,0,0",
    show_default=True,
    help="Color of different pixels (R,G,B)",
)
@click.option(
    "--diff-color-alt",
    type=str,
    default=None,
    help='Alternative color to differentiate between "added" and "removed" parts (R,G,B)',
)
@click.option(
    "--diff-mask",
    is_flag=True,
    default=False,
    help="Draw diff over transparent background",
)
def cli(
    img1: str,
    img2: str,
    output: str | None,
    threshold: float,
    includeAA: bool,
    alpha: float,
    aa_color: str,
    diff_color: str,
    diff_color_alt: str | None,
    diff_mask: bool,
) -> None:
    """Compare two images pixel-by-pixel and visualize differences."""
    aa_color_tuple = cast(tuple[int, int, int], tuple(map(int, aa_color.split(","))))
    diff_color_tuple = cast(
        tuple[int, int, int], tuple(map(int, diff_color.split(",")))
    )
    diff_color_alt_tuple = (
        cast(tuple[int, int, int], tuple(map(int, diff_color_alt.split(","))))
        if diff_color_alt
        else None
    )

    num_diff = pixelmatch(
        img1=img1,
        img2=img2,
        output=output,
        threshold=threshold,
        includeAA=includeAA,
        alpha=alpha,
        aa_color=aa_color_tuple,
        diff_color=diff_color_tuple,
        diff_color_alt=diff_color_alt_tuple,
        diff_mask=diff_mask,
    )

    click.echo(f"Mismatched pixels: {num_diff}")

    if num_diff > 0:
        raise click.exceptions.Exit(1)
