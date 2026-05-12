"""
Publication-quality study-area map of Kentucky Mesonet stations.
Generates three styling alternatives (A, B, C) for review.
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from shapely.ops import unary_union
import numpy as np

# ── data ──────────────────────────────────────────────────────────────────────
df = pd.read_csv("supplementary_table_updated.csv")
df = df.dropna(subset=["Lat", "Lon"])

MATCHED_STIDS = {"MRHD", "SCTV", "CRMT", "HCKM", "WDBY", "WLBT"}

retained = df[df["QC_Status"] == "Retained"]
matched  = df[df["STID"].isin(MATCHED_STIDS)]

# ── projections ───────────────────────────────────────────────────────────────
DATA_CRS = ccrs.PlateCarree()
PROJ     = ccrs.AlbersEqualArea(central_longitude=-86.0, central_latitude=37.8)

FONT = "DejaVu Sans"

# ── shared geometry ───────────────────────────────────────────────────────────
shpfile = natural_earth(resolution="10m", category="cultural",
                        name="admin_1_states_provinces")
ky_geom = [r.geometry for r in Reader(shpfile).records()
           if r.attributes.get("name") == "Kentucky"]

county_shp = natural_earth(resolution="10m", category="cultural",
                           name="admin_2_counties")
ky_county_geoms = [
    r.geometry for r in Reader(county_shp).records()
    if r.attributes.get("REGION", "") == "KY"
]

NEIGHBOR_STATES = {
    "Indiana", "Ohio", "Illinois", "Missouri",
    "Tennessee", "Virginia", "West Virginia",
}

# ── styling alternatives ──────────────────────────────────────────────────────
ALTERNATIVES = {
    "A": {
        "label":        "A — Warm Earth",
        "ky_fill":      "#f5ebe0",
        "ky_edge":      "#2c1810",
        "neighbor":     "#ededea",
        "county":       "#8a7060",   # warm dark brown-gray
        "c_retain":     "#8b1a1a",
        "c_match":      "#f0a500",
        "c_match_edge": "#7a4e00",
    },
    "B": {
        "label":        "B — Clean Minimal",
        "ky_fill":      "#f0f0f0",
        "ky_edge":      "#111111",
        "neighbor":     "#d8d8d8",
        "county":       "#555555",   # dark gray — clear on near-white background
        "c_retain":     "#2b2b2b",
        "c_match":      "#d4a017",
        "c_match_edge": "#6b4c00",
    },
    "C": {
        "label":        "C — Sage Green",
        "ky_fill":      "#e6efe6",
        "ky_edge":      "#1a3a1a",
        "neighbor":     "#ebebeb",
        "county":       "#3a5c3a",   # dark forest green
        "c_retain":     "#2d6e2d",
        "c_match":      "#f0c040",
        "c_match_edge": "#7a5e00",
    },
}


def draw_gis_scalebar(ax, renderer, bar_lon_ref=-85.0, bar_lat_ref=36.7):
    """
    Draw a GIS-standard alternating black/white scale bar in axes-fraction
    coordinates.  Width is calculated from the map's actual display pixels
    so the bar is always correct regardless of projection.
    """
    # Two geographic points separated by 100 km in longitude
    lon2 = bar_lon_ref + 100.0 / (111.0 * np.cos(np.radians(bar_lat_ref)))
    p1 = PROJ.transform_point(bar_lon_ref, bar_lat_ref, DATA_CRS)
    p2 = PROJ.transform_point(lon2,        bar_lat_ref, DATA_CRS)

    # Pixel positions → axes fraction width
    ax_bb = ax.get_window_extent(renderer)
    d1 = ax.transData.transform(p1)
    d2 = ax.transData.transform(p2)
    bar_w = abs(d2[0] - d1[0]) / ax_bb.width   # axes fraction

    # Bar geometry (axes fraction)
    right  = 0.970
    bot    = 0.052
    height = 0.030
    top    = bot + height
    left   = right - bar_w
    mid    = (left + right) / 2.0

    T = ax.transAxes
    Z = 12

    # Black segment (0–50 km)
    ax.add_patch(mpatches.Rectangle(
        (left, bot), bar_w / 2, height,
        fc="black", ec="none", transform=T, zorder=Z, clip_on=False))
    # White segment (50–100 km)
    ax.add_patch(mpatches.Rectangle(
        (mid, bot), bar_w / 2, height,
        fc="white", ec="none", transform=T, zorder=Z, clip_on=False))
    # Single crisp border around full bar
    ax.add_patch(mpatches.Rectangle(
        (left, bot), bar_w, height,
        fc="none", ec="black", lw=0.9, transform=T, zorder=Z+1, clip_on=False))
    # Centre divider
    ax.plot([mid, mid], [bot, top], color="black", lw=0.9,
            transform=T, zorder=Z+1, clip_on=False, solid_capstyle="butt")

    # Tick labels: slightly below bar
    lbl_y = bot - 0.010
    for xf, lbl in [(left, "0"), (mid, "50"), (right, "100 km")]:
        ax.text(xf, lbl_y, lbl, transform=T,
                ha="center", va="top", fontsize=6.5,
                fontfamily=FONT, zorder=Z+1, clip_on=False)

    return bot   # return bar bottom so north arrow can sit above it


def draw_gis_north_arrow(ax, sb_bot):
    """
    Draw a GIS-standard split black/white north arrow in axes-fraction
    coordinates, centred just above the scale bar.
    """
    na_x    = 0.955   # horizontal centre (axes fraction)
    gap     = 0.038   # gap between scale bar top and arrow base
    na_bot  = sb_bot + gap
    na_top  = na_bot + 0.110   # arrow height
    na_w    = 0.016            # half-width at base

    T = ax.transAxes
    Z = 12

    # Left half — black
    ax.add_patch(mpatches.Polygon(
        [[na_x - na_w, na_bot], [na_x, na_top], [na_x, na_bot]],
        closed=True, fc="black", ec="black", lw=0.5,
        transform=T, zorder=Z, clip_on=False))
    # Right half — white
    ax.add_patch(mpatches.Polygon(
        [[na_x + na_w, na_bot], [na_x, na_top], [na_x, na_bot]],
        closed=True, fc="white", ec="black", lw=0.5,
        transform=T, zorder=Z, clip_on=False))
    # Bold "N" above tip
    ax.text(na_x, na_top + 0.012, "N",
            transform=T, ha="center", va="bottom",
            fontsize=10, fontweight="bold", zorder=Z, clip_on=False)


def build_map(style_key, style):
    fig = plt.figure(figsize=(10, 7), dpi=300)
    fig.patch.set_facecolor("white")

    ax = fig.add_axes([0.09, 0.08, 0.87, 0.84], projection=PROJ)
    ax.set_extent([-89.7, -81.8, 36.35, 39.25], crs=DATA_CRS)

    # ── basemap layers ────────────────────────────────────────────────────────
    ax.add_feature(cfeature.OCEAN.with_scale("50m"),
                   facecolor="white", zorder=0)
    ax.add_feature(cfeature.LAND.with_scale("50m"),
                   facecolor=style["neighbor"], zorder=1)

    # Kentucky fill
    for geom in ky_geom:
        ax.add_geometries([geom], DATA_CRS, facecolor=style["ky_fill"],
                          edgecolor="none", linewidth=0, zorder=2)

    # Kentucky county lines — KY-only, dark for clear legibility
    ax.add_geometries(ky_county_geoms, DATA_CRS, facecolor="none",
                      edgecolor=style["county"], linewidth=0.8, zorder=3)

    # Neighboring state outlines
    neighbor_geoms = [r.geometry for r in Reader(shpfile).records()
                      if r.attributes.get("name") in NEIGHBOR_STATES]
    ax.add_geometries(neighbor_geoms, DATA_CRS, facecolor="none",
                      edgecolor="#666666", linewidth=0.7, zorder=4)

    # Kentucky border — single unified boundary, crisp miter/butt joins
    ky_union   = unary_union(ky_geom)
    boundary   = ky_union.boundary
    segs       = ([boundary] if boundary.geom_type == "LineString"
                  else list(boundary.geoms))
    for seg in segs:
        xs, ys = seg.xy
        ax.plot(xs, ys, transform=DATA_CRS, color=style["ky_edge"],
                linewidth=2.2, solid_capstyle="butt", solid_joinstyle="miter",
                zorder=5)

    # ── graticule ─────────────────────────────────────────────────────────────
    gl = ax.gridlines(
        crs=DATA_CRS, draw_labels=True,
        linewidth=0.45, color="#999999", alpha=0.65, linestyle="--",
        x_inline=False, y_inline=False,
    )
    gl.top_labels    = True
    gl.bottom_labels = True
    gl.left_labels   = True
    gl.right_labels  = True
    gl.xlocator   = mticker.FixedLocator([-90,-89,-88,-87,-86,-85,-84,-83,-82])
    gl.ylocator   = mticker.FixedLocator([36, 36.5, 37, 37.5, 38, 38.5, 39, 39.5])
    gl.xformatter = LongitudeFormatter(degree_symbol="°")
    gl.yformatter = LatitudeFormatter(degree_symbol="°")
    gl.xlabel_style = {"size": 6.5, "color": "#333333"}
    gl.ylabel_style = {"size": 6.5, "color": "#333333"}

    # ── neighbouring state labels ─────────────────────────────────────────────
    state_labels = [
        ("Indiana",       -86.40, 39.05),
        ("Ohio",          -83.20, 39.05),
        ("Illinois",      -89.45, 37.80),
        ("Missouri",      -89.55, 36.80),
        ("Tennessee",     -86.50, 36.50),
        ("Virginia",      -82.00, 37.25),
        ("West Virginia", -81.90, 38.20),
    ]
    for name, lon, lat in state_labels:
        ax.text(lon, lat, name, transform=DATA_CRS,
                fontsize=6, color="#444444", ha="center", va="center",
                fontstyle="italic", zorder=6,
                bbox=dict(boxstyle="round,pad=0.1", facecolor="white",
                          alpha=0.55, edgecolor="none"))

    # ── station markers ───────────────────────────────────────────────────────
    ax.scatter(retained["Lon"], retained["Lat"],
               s=48, marker="o", color=style["c_retain"],
               edgecolors="white", linewidths=0.6,
               transform=DATA_CRS, zorder=6)
    ax.scatter(matched["Lon"], matched["Lat"],
               s=110, marker="*", color=style["c_match"],
               edgecolors=style["c_match_edge"], linewidths=0.7,
               transform=DATA_CRS, zorder=7)

    # ── matched station labels ────────────────────────────────────────────────
    for _, row in matched.iterrows():
        ax.annotate(
            row["STID"],
            xy=(row["Lon"], row["Lat"]),
            xycoords=DATA_CRS._as_mpl_transform(ax),
            xytext=(5, 4), textcoords="offset points",
            fontsize=6.5, fontweight="bold", color="#3d2b00",
            ha="left", va="bottom",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                      alpha=0.75, edgecolor="none"),
            zorder=8,
        )

    # ── legend ────────────────────────────────────────────────────────────────
    legend_elements = [
        Line2D([0], [0], marker="o", color="w",
               label=f"Retained (n={len(retained)})",
               markerfacecolor=style["c_retain"], markeredgecolor="white",
               markeredgewidth=0.5, markersize=8),
        Line2D([0], [0], marker="*", color="w",
               label=f"Matched stations (n={len(matched)}, ≤2 km)",
               markerfacecolor=style["c_match"],
               markeredgecolor=style["c_match_edge"],
               markeredgewidth=0.6, markersize=11),
    ]
    leg = ax.legend(
        handles=legend_elements, loc="upper left",
        fontsize=7.5, framealpha=0.92, edgecolor="#888888",
        title="Kentucky Mesonet Stations", title_fontsize=8,
        frameon=True, borderpad=0.8,
    )
    leg._legend_box.align = "left"

    # ── title ─────────────────────────────────────────────────────────────────
    ax.set_title("Study Area: Kentucky Mesonet Station Network",
                 fontsize=11, fontweight="bold", pad=10, fontfamily=FONT)

    # ── first canvas draw — resolves pixel dimensions for cartographic items ──
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    # ── CONUS inset (positioned below legend) ─────────────────────────────────
    leg_bb  = leg.get_window_extent(renderer).transformed(
                  fig.transFigure.inverted())
    inset_h = 0.185
    inset_w = max(leg_bb.width, 0.215)
    ax_ins  = fig.add_axes(
        [leg_bb.x0, leg_bb.y0 - 0.010 - inset_h, inset_w, inset_h],
        projection=ccrs.LambertConformal(central_longitude=-96,
                                         central_latitude=39),
    )
    ax_ins.set_extent([-125, -66, 24, 50], crs=DATA_CRS)

    ax_ins.add_feature(cfeature.LAND.with_scale("50m"),
                       facecolor="#e0e0e0", edgecolor="none", zorder=1)
    ax_ins.add_feature(cfeature.OCEAN.with_scale("50m"),
                       facecolor="#c8dff0", zorder=0)
    ax_ins.add_feature(cfeature.LAKES.with_scale("50m"),
                       facecolor="#c8dff0", edgecolor="none", zorder=1)
    ax_ins.add_feature(cfeature.BORDERS.with_scale("50m"),
                       edgecolor="#888888", linewidth=0.6, zorder=2)
    ax_ins.add_feature(
        cfeature.NaturalEarthFeature("cultural",
                                     "admin_1_states_provinces_lines", "50m",
                                     facecolor="none", edgecolor="#aaaaaa",
                                     linewidth=0.3),
        zorder=2)
    for geom in ky_geom:
        ax_ins.add_geometries([geom], DATA_CRS,
                              facecolor=style["ky_fill"],
                              edgecolor=style["ky_edge"],
                              linewidth=1.0, zorder=3)
    for spine in ax_ins.spines.values():
        spine.set_edgecolor("#333333")
        spine.set_linewidth(1.2)
    ax_ins.text(0.5, 0.08, "USA", transform=ax_ins.transAxes,
                fontsize=6, ha="center", va="bottom",
                fontweight="bold", color="#444444")
    ax_ins.set_title("Location in USA", fontsize=6.5, pad=3,
                     fontweight="bold", color="#222222")

    # ── GIS scale bar — axes fraction, pixel-accurate width ───────────────────
    sb_bot = draw_gis_scalebar(ax, renderer)

    # ── GIS north arrow — split polygon, clearly above scale bar ─────────────
    draw_gis_north_arrow(ax, sb_bot)

    # ── save ──────────────────────────────────────────────────────────────────
    out_png = f"map_alt_{style_key}.png"
    out_pdf = f"map_alt_{style_key}.pdf"
    save_kw = dict(bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(out_png, dpi=300, **save_kw)
    print(f"Saved → {out_png}  ({style['label']})")
    fig.savefig(out_pdf, **save_kw)
    print(f"Saved → {out_pdf}")
    if style_key == "B":
        fig.savefig("kentucky_mesonet_study_area_map.png", dpi=300, **save_kw)
        fig.savefig("kentucky_mesonet_study_area_map.pdf", **save_kw)
        print("Saved → kentucky_mesonet_study_area_map.png / .pdf  (final)")
    plt.close(fig)


for key, style in ALTERNATIVES.items():
    build_map(key, style)

print("Done — three alternatives: map_alt_A.png, map_alt_B.png, map_alt_C.png")
