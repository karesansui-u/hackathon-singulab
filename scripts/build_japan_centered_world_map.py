#!/usr/bin/env python3
"""
Build a Japan-centered world map SVG for the browser viewer.

The SVG is generated from Natural Earth admin-0 country polygons so the
browser viewer can stay dependency-free while still using a realistic map.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen


SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_110m_admin_0_countries.geojson"
)
WIDTH = 2000
HEIGHT = 1000
CENTER_LON = 140.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Japan-centered world SVG map.")
    parser.add_argument(
        "--cache",
        default="data/cache/ne_110m_admin_0_countries.geojson",
        help="Local cache path for the source GeoJSON.",
    )
    parser.add_argument(
        "--output",
        default="visualization/assets/world_admin_japan_centered.svg",
        help="Output SVG path.",
    )
    return parser.parse_args()


def ensure_geojson(cache_path: Path) -> dict:
    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(SOURCE_URL) as response:
            cache_path.write_bytes(response.read())
    return json.loads(cache_path.read_text(encoding="utf-8"))


def wrap_longitude(lon: float, center: float = CENTER_LON) -> float:
    return ((lon - center + 540.0) % 360.0) - 180.0


def project(lon: float, lat: float) -> tuple[float, float]:
    wrapped = wrap_longitude(lon)
    x = (wrapped + 180.0) / 360.0 * WIDTH
    y = (90.0 - lat) / 180.0 * HEIGHT
    return (x, y)


def ring_to_segments(ring: list[list[float]]) -> list[list[tuple[float, float]]]:
    if not ring:
        return []

    segments: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    previous_x: float | None = None

    for lon, lat, *_ in ring:
        x, y = project(lon, lat)
        if previous_x is not None and abs(x - previous_x) > WIDTH * 0.42:
            if len(current) >= 2:
                segments.append(current)
            current = []
        current.append((x, y))
        previous_x = x

    if len(current) >= 2:
        segments.append(current)
    return segments


def geometry_to_path(geometry: dict) -> str:
    commands: list[str] = []
    geom_type = geometry["type"]
    if geom_type == "Polygon":
        polygons = [geometry["coordinates"]]
    elif geom_type == "MultiPolygon":
        polygons = geometry["coordinates"]
    else:
        return ""

    for polygon in polygons:
        for ring in polygon:
            for segment in ring_to_segments(ring):
                if len(segment) < 2:
                    continue
                start_x, start_y = segment[0]
                commands.append(f"M {start_x:.2f} {start_y:.2f}")
                for x, y in segment[1:]:
                    commands.append(f"L {x:.2f} {y:.2f}")
                commands.append("Z")
    return " ".join(commands)


def graticule_path() -> str:
    commands: list[str] = []
    for lon in range(-180, 181, 30):
        shifted = lon + CENTER_LON
        for lat in range(-75, 76, 5):
            x, y = project(shifted, lat)
            prefix = "M" if lat == -75 else "L"
            commands.append(f"{prefix} {x:.2f} {y:.2f}")
    for lat in range(-60, 61, 30):
        for shifted_lon in range(-180, 181, 5):
            x, y = project(shifted_lon + CENTER_LON, lat)
            prefix = "M" if shifted_lon == -180 else "L"
            commands.append(f"{prefix} {x:.2f} {y:.2f}")
    return " ".join(commands)


def build_svg(geojson: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    country_paths = []
    for feature in geojson["features"]:
        path_data = geometry_to_path(feature["geometry"])
        if path_data:
            country_paths.append(path_data)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <linearGradient id="ocean" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#081321" />
      <stop offset="52%" stop-color="#0d2039" />
      <stop offset="100%" stop-color="#13325a" />
    </linearGradient>
    <radialGradient id="glow" cx="58%" cy="36%" r="80%">
      <stop offset="0%" stop-color="#4cc9f0" stop-opacity="0.18" />
      <stop offset="70%" stop-color="#4cc9f0" stop-opacity="0.03" />
      <stop offset="100%" stop-color="#4cc9f0" stop-opacity="0" />
    </radialGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="16" flood-color="#01060d" flood-opacity="0.32" />
    </filter>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#ocean)" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#glow)" />
  <path d="{graticule_path()}" fill="none" stroke="#b7ddff" stroke-opacity="0.10" stroke-width="1.15" />
  <g filter="url(#shadow)">
    <g fill="#1a3147" stroke="#96c3ea" stroke-opacity="0.36" stroke-width="0.7">
      {''.join(f'<path d="{path}" />' for path in country_paths)}
    </g>
  </g>
</svg>
"""
    output_path.write_text(svg, encoding="utf-8")


def main() -> None:
    args = parse_args()
    geojson = ensure_geojson(Path(args.cache))
    build_svg(geojson, Path(args.output))
    print(json.dumps({"output": args.output, "features": len(geojson["features"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
