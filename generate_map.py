"""
Publication-quality study-area map of Kentucky Mesonet stations.
Generates three styling alternatives (A, B, C) for review.
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
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

# ── styling alternatives ───────────────────────────────────────────────────────
ALTERNATIVES = {
    "A": {
        # Warm earth / parchment
        "label":      "A — Warm Earth",
        "ky_fill":    "#f5ebe0",   # warm cream
        "ky_edge":    "#2c1810",   # dark brown, sharp
        "neighbor":   "#ededea",   # warm light gray
        "county":     "#c8bdb5",   # warm gray
        "c_retain":   "#8b1a1a",   # deep red
        "c_match":    "#f0a500",   # amber gold
        "c_match_edge":"#7a4e00",
        "river":      "#90b8c8",
        "inset_ky":   "#cc2222",   # red, distinct from cream fill
        "inset_ky_edge": "#7a0000",
    },
    "B": {
        # Clean minimal / monochrome
        "label":      "B — Clean Minimal",
        "ky_fill":    "#f0f0f0",   # near white
        "ky_edge":    "#111111",   # near black, very sharp
        "neighbor":   "#d8d8d8",   # medium gray
        "county":     "#bbbbbb",
        "c_retain":   "#2b2b2b",   # dark charcoal
        "c_match":    "#d4a017",   # gold
        "c_match_edge":"#6b4c00",
        "river":      "#8ab0c8",
        "inset_ky":   "#cc2222",
        "inset_ky_edge": "#7a0000",
    },
    "C": {
        # Sage green / natural
        "label":      "C — Sage Green",
        "ky_fill":    "#e6efe6",   # light sage
        "ky_edge":    "#1a3a1a",   # dark forest green, sharp
        "neighbor":   "#ebebeb",
        "county":     "#b8ceb8",   # soft green-gray
        "c_retain":   "#2d6e2d",   # forest green
        "c_match":    "#f0c040",   # yellow-gold
        "c_match_edge":"#7a5e00",
        "river":      "#7aaccc",
        "inset_ky":   "#cc2222",
        "inset_ky_edge": "#7a0000",
    },
}


def build_map(style_key, style):
    fig = plt.figure(figsize=(10, 7), dpi=300)
    fig.patch.set_facecolor("white")

    ax = fig.add_axes([0.09, 0.08, 0.87, 0.84], projection=PROJ)
    ax.set_extent([-89.7, -81.8, 36.35, 39.25], crs=DATA_CRS)

    # ── basemap ───────────────────────────────────────────────────────────────
    ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="white", zorder=0)
    ax.add_feature(cfeature.LAND.with_scale("50m"),
                   facecolor=style["neighbor"], zorder=1)

    # KY fill
    for geom in ky_geom:
        ax.add_geometries([geom], DATA_CRS, facecolor=style["ky_fill"],
                          edgecolor="none", linewidth=0, zorder=2)

    # County edges
    ax.add_feature(
        cfeature.NaturalEarthFeature("cultural", "admin_2_counties", "10m",
                                     facecolor="none", edgecolor=style["county"],
                                     linewidth=0.35),
        zorder=3)

    # KY border — sharp, solid, no cap softness
    for geom in ky_geom:
        ax.add_geometries([geom], DATA_CRS, facecolor="none",
                          edgecolor=style["ky_edge"], linewidth=2.2,
                          zorder=4, capstyle="butt", joinstyle="miter")

    # State lines
    ax.add_feature(
        cfeature.NaturalEarthFeature("cultural",
                                     "admin_1_states_provinces_lines", "50m",
                                     facecolor="none", edgecolor="#666666",
                                     linewidth=0.9),
        zorder=4)

    # Rivers
    ax.add_feature(
        cfeature.NaturalEarthFeature("physical", "rivers_lake_centerlines", "10m",
                                     facecolor="none", edgecolor=style["river"],
                                     linewidth=0.5),
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
    gl.xlocator   = mticker.FixedLocator([-90, -89, -88, -87, -86, -85, -84, -83, -82])
    gl.ylocator   = mticker.FixedLocator([36, 36.5, 37, 37.5, 38, 38.5, 39, 39.5])
    gl.xformatter = LongitudeFormatter(degree_symbol="°")
    gl.yformatter = LatitudeFormatter(degree_symbol="°")
    gl.xlabel_style = {"size": 6.5, "color": "#333333"}
    gl.ylabel_style = {"size": 6.5, "color": "#333333"}

    # ── neighbor state labels ──────────────────────────────────────────────────
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

    # ── station markers ────────────────────────────────────────────────────────
    ax.scatter(retained["Lon"], retained["Lat"],
               s=48, marker="o", color=style["c_retain"],
               edgecolors="white", linewidths=0.6,
               transform=DATA_CRS, zorder=6)

    ax.scatter(matched["Lon"], matched["Lat"],
               s=110, marker="*", color=style["c_match"],
               edgecolors=style["c_match_edge"], linewidths=0.7,
               transform=DATA_CRS, zorder=7)

    # ── matched station labels ─────────────────────────────────────────────────
    label_offsets = {k: (5, 4) for k in MATCHED_STIDS}
    for _, row in matched.iterrows():
        dx, dy = label_offsets.get(row["STID"], (5, 4))
        ax.annotate(
            row["STID"],
            xy=(row["Lon"], row["Lat"]),
            xycoords=DATA_CRS._as_mpl_transform(ax),
            xytext=(dx, dy), textcoords="offset points",
            fontsize=6.5, fontweight="bold", color="#3d2b00",
            ha="left", va="bottom",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                      alpha=0.75, edgecolor="none"),
            zorder=8,
        )

    # ── legend ─────────────────────────────────────────────────────────────────
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

    # ── scale bar ─────────────────────────────────────────────────────────────
    sc_lat  = 36.62
    sc_lon1 = -82.3
    sc_lon0 = sc_lon1 - 100 / (111.0 * np.cos(np.radians(sc_lat)))
    for x0, x1, y0, y1 in [
        (sc_lon0, sc_lon1, sc_lat,        sc_lat),
        (sc_lon0, sc_lon0, sc_lat - 0.04, sc_lat + 0.04),
        (sc_lon1, sc_lon1, sc_lat - 0.04, sc_lat + 0.04),
    ]:
        ax.plot([x0, x1], [y0, y1], color="black", linewidth=2.0,
                transform=DATA_CRS, zorder=8, solid_capstyle="butt")
    ax.text((sc_lon0 + sc_lon1) / 2, sc_lat - 0.11, "100 km",
            ha="center", va="top", fontsize=7,
            transform=DATA_CRS, zorder=8)

    # ── north arrow ───────────────────────────────────────────────────────────
    ax.annotate("N", xy=(0.88, 0.115), xytext=(0.88, 0.055),
                xycoords="axes fraction",
                fontsize=11, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="black",
                                lw=1.8, mutation_scale=14),
                annotation_clip=False)

    # ── title ─────────────────────────────────────────────────────────────────
    ax.set_title("Study Area: Kentucky Mesonet Station Network",
                 fontsize=11, fontweight="bold", pad=10, fontfamily=FONT)

    # ── CONUS inset ───────────────────────────────────────────────────────────
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    leg_bb   = leg.get_window_extent(renderer).transformed(fig.transFigure.inverted())

    gap      = 0.010
    inset_h  = 0.185
    inset_w  = max(leg_bb.width, 0.215)
    ax_ins = fig.add_axes(
        [leg_bb.x0, leg_bb.y0 - gap - inset_h, inset_w, inset_h],
        projection=ccrs.LambertConformal(central_longitude=-96, central_latitude=39),
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

    # KY in inset: always red — distinct from main map fill, per Layout1 style
    for geom in ky_geom:
        ax_ins.add_geometries([geom], DATA_CRS,
                              facecolor=style["inset_ky"],
                              edgecolor=style["inset_ky_edge"],
                              linewidth=1.0, zorder=3)

    for spine in ax_ins.spines.values():
        spine.set_edgecolor("#333333")
        spine.set_linewidth(1.2)

    ax_ins.text(0.5, 0.08, "USA", transform=ax_ins.transAxes,
                fontsize=6, ha="center", va="bottom",
                fontweight="bold", color="#444444")
    ax_ins.set_title("Location in USA", fontsize=6.5, pad=3,
                     fontweight="bold", color="#222222")

    # ── save ──────────────────────────────────────────────────────────────────
    out_png = f"map_alt_{style_key}.png"
    out_pdf = f"map_alt_{style_key}.pdf"
    save_kw = dict(bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(out_png, dpi=300, **save_kw)
    print(f"Saved → {out_png}  ({style['label']})")
    fig.savefig(out_pdf, **save_kw)
    print(f"Saved → {out_pdf}")
    plt.close(fig)


for key, style in ALTERNATIVES.items():
    build_map(key, style)

print("Done — three alternatives: map_alt_A.png, map_alt_B.png, map_alt_C.png")
