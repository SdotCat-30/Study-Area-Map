"""
Terrain/physical-style study-area map of Kentucky Mesonet stations.
- Kentucky fill: muted sage green  (#c8d8a8)
- Neighbouring states: sandy beige (#d9cdb0)
- Ocean/background: pale blue      (#aacce0)
- Rivers more prominent; lakes added
- Stations: forest-green circles; bright-orange stars for matched
- CONUS inset auto-positioned below legend
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
import numpy as np

# ── data ──────────────────────────────────────────────────────────────────────
df = pd.read_csv("supplementary_table_updated.csv")
df = df.dropna(subset=["Lat", "Lon"])

MATCHED_STIDS = {"MRHD", "SCTV", "CRMT", "HCKM", "WDBY", "WLBT"}

retained = df[df["QC_Status"] == "Retained"]
matched  = df[df["STID"].isin(MATCHED_STIDS)]

# ── projection / colours ──────────────────────────────────────────────────────
DATA_CRS = ccrs.PlateCarree()
PROJ     = ccrs.AlbersEqualArea(central_longitude=-86.0, central_latitude=37.8)

C_KY_FILL  = "#c8d8a8"   # muted sage green — vegetation-like
C_NEIGHBOR = "#d9cdb0"   # sandy beige — surrounding states
C_OCEAN    = "#aacce0"   # pale blue — water / background

C_COUNTY_EDGE = "#b0a080"  # warm tan county lines
C_KY_EDGE     = "#3d2b00"  # dark brown KY border
C_STATE_LINE  = "#8B7355"  # mid-brown state lines
C_RIVER       = "#5b9dc0"  # steel-blue rivers
C_LAKE_FACE   = "#aacce0"  # same pale blue as ocean
C_LAKE_EDGE   = "#5b9dc0"

C_RETAIN = "#2d5a27"   # dark forest green circles
C_MATCH  = "#ff6600"   # bright orange stars

FONT = "DejaVu Sans"

# ── figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(10, 7), dpi=300)
fig.patch.set_facecolor(C_OCEAN)

ax = fig.add_axes([0.02, 0.08, 0.96, 0.85], projection=PROJ)
ax.set_extent([-89.7, -81.8, 36.35, 39.25], crs=DATA_CRS)

# ── basemap layers ────────────────────────────────────────────────────────────
# Background ocean/water colour
ax.add_feature(cfeature.OCEAN.with_scale("50m"),
               facecolor=C_OCEAN, zorder=0)
# Neighbouring land (all states, clipped by extent)
ax.add_feature(cfeature.LAND.with_scale("50m"),
               facecolor=C_NEIGHBOR, zorder=1)

# Load KY geometry from Natural Earth 10 m states shapefile
shpfile = natural_earth(resolution="10m", category="cultural",
                        name="admin_1_states_provinces")
ky_geom = [r.geometry for r in Reader(shpfile).records()
           if r.attributes.get("name") == "Kentucky"]

# 1) KY fill (sage green)
for geom in ky_geom:
    ax.add_geometries([geom], DATA_CRS,
                      facecolor=C_KY_FILL, edgecolor="none",
                      linewidth=0, zorder=2)

# 2) County edges — warm tan, thin
ax.add_feature(
    cfeature.NaturalEarthFeature("cultural", "admin_2_counties", "10m",
                                 facecolor="none",
                                 edgecolor=C_COUNTY_EDGE,
                                 linewidth=0.3),
    zorder=3)

# 3) Lakes — same pale blue as ocean, with river-blue edge
ax.add_feature(
    cfeature.NaturalEarthFeature("physical", "lakes", "10m",
                                 facecolor=C_LAKE_FACE,
                                 edgecolor=C_LAKE_EDGE,
                                 linewidth=0.5),
    zorder=3.5)

# 4) KY border redrawn prominently on top
for geom in ky_geom:
    ax.add_geometries([geom], DATA_CRS,
                      facecolor="none",
                      edgecolor=C_KY_EDGE, linewidth=1.6,
                      zorder=4)

# 5) State lines (brown, medium weight)
ax.add_feature(
    cfeature.NaturalEarthFeature("cultural",
                                 "admin_1_states_provinces_lines", "50m",
                                 facecolor="none",
                                 edgecolor=C_STATE_LINE,
                                 linewidth=0.9),
    zorder=4)

# 6) Rivers — more prominent than original
ax.add_feature(
    cfeature.NaturalEarthFeature("physical", "rivers_lake_centerlines", "10m",
                                 facecolor="none",
                                 edgecolor=C_RIVER,
                                 linewidth=0.7),
    zorder=5)

# ── station markers ───────────────────────────────────────────────────────────
# Retained stations — dark forest-green circles
ax.scatter(retained["Lon"], retained["Lat"],
           s=48, marker="o", color=C_RETAIN,
           edgecolors="white", linewidths=0.6,
           transform=DATA_CRS, zorder=6)

# Matched stations — bright orange stars
ax.scatter(matched["Lon"], matched["Lat"],
           s=110, marker="*", color=C_MATCH,
           edgecolors="#7a2d00", linewidths=0.8,
           transform=DATA_CRS, zorder=7)

# ── matched station labels ────────────────────────────────────────────────────
label_offsets = {
    "MRHD": ( 5,  4),
    "SCTV": ( 5,  4),
    "CRMT": ( 5,  4),
    "HCKM": ( 5,  4),
    "WDBY": ( 5,  4),
    "WLBT": ( 5,  4),
}

for _, row in matched.iterrows():
    dx, dy = label_offsets.get(row["STID"], (5, 4))
    ax.annotate(
        row["STID"],
        xy=(row["Lon"], row["Lat"]),
        xycoords=DATA_CRS._as_mpl_transform(ax),
        xytext=(dx, dy),
        textcoords="offset points",
        fontsize=6.5, fontweight="bold", color="#3d1a00",
        ha="left", va="bottom",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                  alpha=0.80, edgecolor="none"),
        zorder=8,
    )

# ── legend (upper-left) ───────────────────────────────────────────────────────
legend_elements = [
    Line2D([0], [0], marker="o", color="w",
           label=f"Retained (n={len(retained)})",
           markerfacecolor=C_RETAIN, markeredgecolor="white",
           markeredgewidth=0.5, markersize=8),
    Line2D([0], [0], marker="*", color="w",
           label=f"Matched stations (n={len(matched)}, ≤2 km)",
           markerfacecolor=C_MATCH, markeredgecolor="#7a2d00",
           markeredgewidth=0.8, markersize=11),
]

leg = ax.legend(
    handles=legend_elements,
    loc="upper left",
    fontsize=7.5,
    framealpha=0.95,
    facecolor="#fffff0",    # ivory
    edgecolor="#8B7355",    # warm brown frame
    title="Kentucky Mesonet Stations",
    title_fontsize=8,
    frameon=True,
    borderpad=0.8,
)
leg._legend_box.align = "left"

# ── scale bar — lower-right corner ───────────────────────────────────────────
sc_lat  = 36.62
sc_lon1 = -82.3
sc_lon0 = sc_lon1 - 100 / (111.0 * np.cos(np.radians(sc_lat)))

for x0, x1, y0, y1 in [
    (sc_lon0, sc_lon1, sc_lat,        sc_lat),
    (sc_lon0, sc_lon0, sc_lat - 0.04, sc_lat + 0.04),
    (sc_lon1, sc_lon1, sc_lat - 0.04, sc_lat + 0.04),
]:
    ax.plot([x0, x1], [y0, y1],
            color=C_KY_EDGE, linewidth=2.0,
            transform=DATA_CRS, zorder=8, solid_capstyle="butt")

ax.text((sc_lon0 + sc_lon1) / 2, sc_lat - 0.11, "100 km",
        ha="center", va="top", fontsize=7, color=C_KY_EDGE,
        transform=DATA_CRS, zorder=8)

# ── north arrow — lower-right, axes fraction ─────────────────────────────────
ax.annotate("N", xy=(0.88, 0.115), xytext=(0.88, 0.055),
            xycoords="axes fraction",
            fontsize=11, ha="center", fontweight="bold", color=C_KY_EDGE,
            arrowprops=dict(arrowstyle="-|>", color=C_KY_EDGE,
                            lw=1.8, mutation_scale=14),
            annotation_clip=False)

# ── title ─────────────────────────────────────────────────────────────────────
ax.set_title("Study Area: Kentucky Mesonet Station Network",
             fontsize=11, fontweight="bold", pad=8, fontfamily=FONT)

# ── CONUS inset — auto-positioned just below the legend ──────────────────────
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
leg_bb   = leg.get_window_extent(renderer).transformed(
               fig.transFigure.inverted())

gap       = 0.012
inset_h   = 0.19
inset_w   = max(leg_bb.width, 0.20)
inset_left = leg_bb.x0
inset_bot  = leg_bb.y0 - gap - inset_h

ax_ins = fig.add_axes(
    [inset_left, inset_bot, inset_w, inset_h],
    projection=ccrs.LambertConformal(central_longitude=-96, central_latitude=39),
)
ax_ins.set_extent([-125, -66, 24, 50], crs=DATA_CRS)

# Inset land: sandy beige; ocean: pale blue
ax_ins.add_feature(cfeature.LAND.with_scale("50m"),
                   facecolor="#d9cdb0", edgecolor="none", zorder=1)
ax_ins.add_feature(cfeature.OCEAN.with_scale("50m"),
                   facecolor="#aacce0", zorder=0)
ax_ins.add_feature(cfeature.BORDERS.with_scale("50m"),
                   edgecolor="#aaaaaa", linewidth=0.5, zorder=2)
ax_ins.add_feature(
    cfeature.NaturalEarthFeature("cultural",
                                 "admin_1_states_provinces_lines", "50m",
                                 facecolor="none", edgecolor="#8B7355",
                                 linewidth=0.35),
    zorder=2)

# KY highlight: bright orange fill, dark-brown edge
for geom in ky_geom:
    ax_ins.add_geometries([geom], DATA_CRS,
                          facecolor="#ff6600", edgecolor="#7a2d00",
                          linewidth=0.7, zorder=3)

for spine in ax_ins.spines.values():
    spine.set_edgecolor("#8B7355")
    spine.set_linewidth(1.0)

ax_ins.set_title("Location in USA", fontsize=6, pad=3)

# ── save ──────────────────────────────────────────────────────────────────────
save_kw = dict(bbox_inches="tight", facecolor=C_OCEAN, edgecolor="none")
fig.savefig("map_v2_terrain.png", dpi=300, **save_kw)
print("Saved → map_v2_terrain.png")
fig.savefig("map_v2_terrain.pdf", **save_kw)
print("Saved → map_v2_terrain.pdf")
