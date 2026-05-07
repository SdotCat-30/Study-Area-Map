"""
Publication-quality study-area map of Kentucky Mesonet stations — layout variant.

Layout changes vs generate_map.py
----------------------------------
- Figure: 12 × 7 (wider)
- Main map axes: [0.02, 0.08, 0.74, 0.86]  (left ~76 %)
- Right strip  x = [0.77, 0.99] contains three stacked elements:
    1. Legend axes          [0.775, 0.68, 0.21, 0.22]
    2. CONUS inset axes     [0.775, 0.20, 0.21, 0.44]
    3. Note text axes       [0.775, 0.10, 0.21, 0.08]
- Scale bar and north arrow remain inside the main map
- Title is centred over the main axes (not the full figure)
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
DATA_CRS   = ccrs.PlateCarree()
PROJ       = ccrs.AlbersEqualArea(central_longitude=-86.0, central_latitude=37.8)

C_RETAIN   = "#1a6dab"
C_MATCH    = "#f5c518"
C_KY_FILL  = "#dce9f5"
C_NEIGHBOR = "#f0f0f0"
C_KY_EDGE  = "#2c3e50"

FONT = "DejaVu Sans"

# ── figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(12, 7), dpi=300)
fig.patch.set_facecolor("white")

# ── main map axes ─────────────────────────────────────────────────────────────
ax = fig.add_axes([0.02, 0.08, 0.74, 0.86], projection=PROJ)
ax.set_extent([-89.7, -81.8, 36.35, 39.25], crs=DATA_CRS)

# ── basemap layers ────────────────────────────────────────────────────────────
ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="white",    zorder=0)
ax.add_feature(cfeature.LAND.with_scale("50m"),  facecolor=C_NEIGHBOR, zorder=1)

shpfile = natural_earth(resolution="10m", category="cultural",
                        name="admin_1_states_provinces")
ky_geom = [r.geometry for r in Reader(shpfile).records()
           if r.attributes.get("name") == "Kentucky"]

# 1) KY fill
for geom in ky_geom:
    ax.add_geometries([geom], DATA_CRS, facecolor=C_KY_FILL,
                      edgecolor="none", linewidth=0, zorder=2)

# 2) County edges
ax.add_feature(
    cfeature.NaturalEarthFeature("cultural", "admin_2_counties", "10m",
                                 facecolor="none", edgecolor="#aaaaaa",
                                 linewidth=0.35),
    zorder=3)

# 3) KY border redrawn on top
for geom in ky_geom:
    ax.add_geometries([geom], DATA_CRS, facecolor="none",
                      edgecolor=C_KY_EDGE, linewidth=1.4, zorder=4)

# 4) State lines
ax.add_feature(
    cfeature.NaturalEarthFeature("cultural",
                                 "admin_1_states_provinces_lines", "50m",
                                 facecolor="none", edgecolor="#555555",
                                 linewidth=0.9),
    zorder=4)

# 5) Rivers
ax.add_feature(
    cfeature.NaturalEarthFeature("physical", "rivers_lake_centerlines", "10m",
                                 facecolor="none", edgecolor="#7ab8d9",
                                 linewidth=0.5),
    zorder=5)

# ── station markers ───────────────────────────────────────────────────────────
ax.scatter(retained["Lon"], retained["Lat"],
           s=48, marker="o", color=C_RETAIN,
           edgecolors="white", linewidths=0.6,
           transform=DATA_CRS, zorder=6)

ax.scatter(matched["Lon"], matched["Lat"],
           s=110, marker="*", color=C_MATCH,
           edgecolors="#7a5c00", linewidths=0.7,
           transform=DATA_CRS, zorder=7)

# ── matched station labels (white-halo annotations) ───────────────────────────
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
        fontsize=6.5, fontweight="bold", color="#3d2b00",
        ha="left", va="bottom",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                  alpha=0.75, edgecolor="none"),
        zorder=8,
    )

# ── scale bar — lower-right, inside main map ──────────────────────────────────
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

# ── north arrow — lower-right, axes fraction ──────────────────────────────────
ax.annotate("N", xy=(0.88, 0.115), xytext=(0.88, 0.055),
            xycoords="axes fraction",
            fontsize=11, ha="center", fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color="black",
                            lw=1.8, mutation_scale=14),
            annotation_clip=False)

# ── title — centred over main axes ────────────────────────────────────────────
ax.set_title("Study Area: Kentucky Mesonet Station Network",
             fontsize=11, fontweight="bold", pad=8, fontfamily=FONT)

# ═════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — three stacked elements
# ═════════════════════════════════════════════════════════════════════════════

# ── 1. Legend axes ────────────────────────────────────────────────────────────
ax_leg = fig.add_axes([0.775, 0.68, 0.21, 0.22])
ax_leg.set_facecolor("white")
ax_leg.axis("off")

# Title
ax_leg.text(0.5, 0.93, "Kentucky Mesonet Stations",
            ha="center", va="top",
            fontsize=8, fontweight="bold",
            transform=ax_leg.transAxes)

# Row 1: retained blue circle
ax_leg.plot(0.10, 0.62, marker="o", color=C_RETAIN,
            markeredgecolor="white", markeredgewidth=0.5,
            markersize=8, linestyle="none",
            transform=ax_leg.transAxes)
ax_leg.text(0.20, 0.62, f"Retained (n={len(retained)})",
            ha="left", va="center",
            fontsize=7.5, transform=ax_leg.transAxes)

# Row 2: matched gold star
ax_leg.plot(0.10, 0.30, marker="*", color=C_MATCH,
            markeredgecolor="#7a5c00", markeredgewidth=0.6,
            markersize=11, linestyle="none",
            transform=ax_leg.transAxes)
ax_leg.text(0.20, 0.30, f"Matched stations\n(n={len(matched)}, ≤2 km)",
            ha="left", va="center",
            fontsize=7.5, transform=ax_leg.transAxes)

# Thin grey border
for spine in ax_leg.spines.values():
    spine.set_visible(True)
    spine.set_edgecolor("#888888")
    spine.set_linewidth(0.8)

# ── 2. CONUS inset ────────────────────────────────────────────────────────────
ax_ins = fig.add_axes(
    [0.775, 0.20, 0.21, 0.44],
    projection=ccrs.LambertConformal(central_longitude=-96, central_latitude=39),
)
ax_ins.set_extent([-125, -66, 24, 50], crs=DATA_CRS)

ax_ins.add_feature(cfeature.LAND.with_scale("50m"),
                   facecolor="#e8e8e8", edgecolor="none", zorder=1)
ax_ins.add_feature(cfeature.OCEAN.with_scale("50m"),
                   facecolor="#c8dff0", zorder=0)
ax_ins.add_feature(cfeature.BORDERS.with_scale("50m"),
                   edgecolor="#aaaaaa", linewidth=0.5, zorder=2)
ax_ins.add_feature(
    cfeature.NaturalEarthFeature("cultural",
                                 "admin_1_states_provinces_lines", "50m",
                                 facecolor="none", edgecolor="#888888",
                                 linewidth=0.35),
    zorder=2)

for geom in ky_geom:
    ax_ins.add_geometries([geom], DATA_CRS,
                          facecolor="#e84040", edgecolor="#800000",
                          linewidth=0.7, zorder=3)

for spine in ax_ins.spines.values():
    spine.set_edgecolor("#444444")
    spine.set_linewidth(1.0)

ax_ins.set_title("Location in USA", fontsize=7, pad=4)

# ── 3. Note text label ────────────────────────────────────────────────────────
ax_note = fig.add_axes([0.775, 0.10, 0.21, 0.08])
ax_note.axis("off")
ax_note.text(0.5, 0.5,
             "Kentucky Mesonet\nStation Network",
             ha="center", va="center",
             fontsize=7, style="italic", color="#555555",
             transform=ax_note.transAxes)

# ── save ──────────────────────────────────────────────────────────────────────
save_kw = dict(bbox_inches="tight", facecolor="white", edgecolor="none")
fig.savefig("map_v4_layout.png", dpi=300, **save_kw)
print("Saved → map_v4_layout.png")
fig.savefig("map_v4_layout.pdf", **save_kw)
print("Saved → map_v4_layout.pdf")
