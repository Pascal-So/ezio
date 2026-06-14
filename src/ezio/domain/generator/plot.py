from dataclasses import dataclass
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from pydantic_geojson import LineStringModel

from ezio.domain.geo import (
    earth_surface_distance_km,
    get_elevations,
    smoothed_elevations,
)


def setup_plot_style(ax: Axes) -> None:
    figure_width = 5
    figure_height = 2

    ax.set_frame_on(False)

    matplotlib.style.use("fivethirtyeight")
    matplotlib.rc("font", family="sans-serif", size=12)
    matplotlib.rc("figure", figsize=(figure_width, figure_height))
    matplotlib.rc("axes", linewidth=1)
    matplotlib.rc("lines", linewidth=2)

    plt.tick_params(top="off", right="off", which="both")

    ax.yaxis.set_tick_params(labelleft=False)


def extract_xy(
    tracks: list[LineStringModel], smoothing_size: int
) -> tuple[list[float], list[float]]:
    """
    Given multiple tracks, merge them all together and return the distances as
    x and elevations as y data.

    Smoothing is done before merging, so sudden elevation jumps between tracks
    don't bleed into each other.
    """

    all_x: list[list[float]] = []
    all_y: list[list[float]] = []

    total_distance: float = 0.0

    for track in tracks:
        elevations = get_elevations(track)
        if elevations is None:
            raise Exception("Track does not contain elevation data")

        distances: list[float] = []

        coords = track.coordinates

        for a, b in zip(coords, coords[1:]):
            distances.append(total_distance)
            segment_dist = earth_surface_distance_km(a.lat, a.lon, b.lat, b.lon)
            total_distance += segment_dist

        distances.append(total_distance)

        all_x.append(distances[::smoothing_size])
        all_y.append(smoothed_elevations(elevations, smoothing_size))

    def flatten(nested: list[list[float]]) -> list[float]:
        return [elem for inner in nested for elem in inner]

    flattened_x = flatten(all_x)
    flattened_y = flatten(all_y)

    assert len(flattened_x) == len(flattened_y)
    return flattened_x, flattened_y


@dataclass
class PlotBounds:
    lower: float
    upper: float
    tick_spacing: float


def get_plot_bounds(elevations: list[float]) -> PlotBounds:
    tick_spacing: float = 100
    min_range: float = 180

    min_y = float(np.min(elevations))
    max_y = float(np.max(elevations))

    if max_y - min_y > 600:
        tick_spacing = 200

    mid_y = (min_y + max_y) / 2
    lower_line = (mid_y // tick_spacing) * tick_spacing
    upper_line = lower_line + tick_spacing

    lower_unpadded = min(min_y, lower_line)
    upper_unpadded = max(max_y, upper_line)
    range = upper_unpadded - lower_unpadded

    lower = lower_unpadded - range * 0.05
    upper = upper_unpadded + range * 0.05
    range = upper - lower
    if range < min_range:
        tick_spacing = 50
        remaining = min_range - range
        lower = max(lower - remaining / 3, min(lower, 0))
        upper = lower + min_range

    return PlotBounds(lower=lower, upper=upper, tick_spacing=tick_spacing)


def plot_segment(segment: list[LineStringModel], output_path: Path) -> None:
    smoothing_size = 6
    x, y = extract_xy(segment, smoothing_size)

    bounds = get_plot_bounds(y)

    plt.ylim(bounds.lower, bounds.upper)
    plt.yticks(
        np.arange(
            np.ceil(bounds.lower / bounds.tick_spacing + 0.05) * bounds.tick_spacing,
            bounds.upper,
            step=bounds.tick_spacing,
        )
    )
    plt.xticks([])

    ax = plt.gca()

    setup_plot_style(ax)

    gridline_col = "#ccc"
    line_col = "#abb"

    for tick in ax.yaxis.get_major_ticks():
        tick_y = tick.get_loc()
        ax.text(
            0.99,
            tick_y,
            f"{tick_y:.0f}m",
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="bottom",
            fontsize=14,
            color=gridline_col,
        )
    ax.yaxis.grid(True, color=gridline_col)

    plt.tight_layout(pad=0, w_pad=0, h_pad=0)

    plt.plot(x, y, c=line_col)
    plt.savefig(output_path)
    plt.cla()
