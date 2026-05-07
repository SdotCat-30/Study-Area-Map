"""
Publication-quality study-area map of Kentucky Mesonet stations.
Includes a CONUS inset (right-margin strip, no overlap with KY) and
highlights matched stations (MRHD, SCTV, CRMT, HCKM, WDBY, WLBT).
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

retained   = df[df["QC_Status"] == "Retained"]
excl_first = df[df["QC_Status"].str.startswith("Excluded after first")]
excl_sec   = df[df["QC_Status"].str.startswith("Excluded after second")]
matched    = df[df["STID"].isin(MATCHED_STIDS)]

# ── colours / sizes ───────────────────────────────────────────────────────────
DATA_CRS   = ccrs.PlateCarree()
PROJ       = ccrs.AlbersEqualArea(central_longitude=-86.0, central_latitude=37.8)

C_RETAIN   = "#1a6dab"
C_EXCL1    = "#e07b00"
C_EXCL2    = "#c0392b"
C_MATCH    = "#f5c518"   # gold star for matched stations
C_KY_FILL  = "#dce9f5"
C_NEIGHBOR = "#f0f0f0"
C_KY_EDGE  = "#2c3e50"

SZ  = 52    # regular marker size
SZM = 90    # matched-station star size
FONT = "DejaVu Sans"

# ── figure layout ─────────────────────────────────────────────────────────────
# 11 × 7 inches – main map takes left 78 %, right strip (~2.2 in) holds inset
fig = plt.figure(figsize=(11, 7), dpi=300)
fig.patch.set_facecolor("white")

# Main map axes
ax = fig.add_axes([0.02, 0.08, 0.77, 0.86], projection=PROJ)
ax.set_extent([-89.7, -81.8, 36.35, 39.25], crs=DATA_CRS)

# ── basemap layers (strict zorder so KY counties are visible) ─────────────────
ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="white",  zorder=0)
ax.add_feature(cfeature.LAND.with_scale("50m"),  facecolor=C_NEIGHBOR, zorder=1)

# Isolate Kentucky geometry once (reused in inset)
shpfile = natural_earth(resolution="10m", category="cultural",
                        name="admin_1_states_provinces")
ky_geom = [r.geometry for r in Reader(shpfile).records()
           if r.attributes.get("name") == "Kentucky"]

# 1) KY fill (zorder 2) — drawn before counties
for geom in ky_geom:
    ax.add_geometries([geom], DATA_CRS, facecolor=C_KY_FILL,
                      edgecolor="none", linewidth=0, zorder=2)

# 2) County edges visible inside KY (zorder 3)
ax.add_feature(
    cfeature.NaturalEarthFeature("cultural", "admin_2_counties", "10m",
                                 facecolor="none", edgecolor="#aaaaaa",
                                 linewidth=0.35),
    zorder=3)

# 3) KY border redrawn on top of counties (zorder 4)
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
ckw = dict(transform=DATA_CRS, zorder=6, linewidths=0.6, edgecolors="white")

ax.scatter(retained["Lon"],   retained["Lat"],
           s=SZ,  marker="o", color=C_RETAIN, **ckw)
ax.scatter(excl_first["Lon"], excl_first["Lat"],
           s=SZ,  marker="^", color=C_EXCL1,  **ckw)
ax.scatter(excl_sec["Lon"],   excl_sec["Lat"],
           s=SZ,  marker="s", color=C_EXCL2,  **ckw)

# Matched stations: gold star on top (zorder 7 so it sits above base markers)
ax.scatter(matched["Lon"], matched["Lat"],
           s=SZM, marker="*", color=C_MATCH,
           edgecolors="#7a5c00", linewidths=0.7,
           transform=DATA_CRS, zorder=7)

# ── legend (upper-left → Indiana/Illinois territory, clear of KY) ─────────────
legend_elements = [
    Line2D([0], [0], marker="o", color="w",
           label=f"Retained (n={len(retained)})",
           markerfacecolor=C_RETAIN, markeredgecolor="white",
           markeredgewidth=0.5, markersize=8),
    Line2D([0], [0], marker="^", color="w",
           label=f"Excluded – 1st QC (n={len(excl_first)})",
           markerfacecolor=C_EXCL1, markeredgecolor="white",
           markeredgewidth=0.5, markersize=8),
    Line2D([0], [0], marker="s", color="w",
           label=f"Excluded – 2nd QC (n={len(excl_sec)})",
           markerfacecolor=C_EXCL2, markeredgecolor="white",
           markeredgewidth=0.5, markersize=8),
    Line2D([0], [0], marker="*", color="w",
           label=f"Matched stations (n={len(matched)}, ≤2 km)",
           markerfacecolor=C_MATCH, markeredgecolor="#7a5c00",
           markeredgewidth=0.6, markersize=11),
]

leg = ax.legend(
    handles=legend_elements,
    loc="upper left",
    fontsize=7.5,
    framealpha=0.92,
    edgecolor="#888888",
    title="Kentucky Mesonet Stations",
    title_fontsize=8,
    frameon=True,
    borderpad=0.8,
)
leg._legend_box.align = "left"

# ── scale bar (lower-left, over Missouri/Tennessee — clearly outside KY) ──────
sc_lon0 = -89.4
sc_lat  = 36.52
sc_lon1 = sc_lon0 + 100 / 111.0 / np.cos(np.radians(sc_lat))

for x0, x1, y0, y1 in [
    (sc_lon0, sc_lon1, sc_lat, sc_lat),
    (sc_lon0, sc_lon0, sc_lat - 0.04, sc_lat + 0.04),
    (sc_lon1, sc_lon1, sc_lat - 0.04, sc_lat + 0.04),
]:
    ax.plot([x0, x1], [y0, y1], color="black", linewidth=1.8,
            transform=DATA_CRS, zorder=8, solid_capstyle="butt")

ax.text((sc_lon0 + sc_lon1) / 2, sc_lat - 0.13, "100 km",
        ha="center", va="top", fontsize=6.5,
        transform=DATA_CRS, zorder=8)

# ── north arrow (just right of scale bar, lower-left) ─────────────────────────
ax.annotate("N", xy=(0.095, 0.115), xytext=(0.095, 0.055),
            xycoords="axes fraction",
            fontsize=10, ha="center", fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color="black",
                            lw=1.5, mutation_scale=12),
            annotation_clip=False)

# ── title ─────────────────────────────────────────────────────────────────────
ax.set_title("Study Area: Kentucky Mesonet Station Network",
             fontsize=11, fontweight="bold", pad=8, fontfamily=FONT)

# ── inset: CONUS (right-margin strip — entirely outside main axes) ─────────────
# Main axes right edge is at figure x ≈ 0.02 + 0.77 = 0.79
# Inset lives in [0.805, 0.32, 0.185, 0.56] — no geographic overlap possible
ax_ins = fig.add_axes(
    [0.805, 0.30, 0.185, 0.58],
    projection=ccrs.LambertConformal(central_longitude=-96, central_latitude=39)
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

ax_ins.set_title("Location\nin USA", fontsize=6.5, pad=3, linespacing=1.3)

# ── save ──────────────────────────────────────────────────────────────────────
for path, kw in [
    ("kentucky_mesonet_study_area_map.png",
     dict(dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")),
    ("kentucky_mesonet_study_area_map.pdf",
     dict(bbox_inches="tight", facecolor="white", edgecolor="none")),
]:
    fig.savefig(path, **kw)
    print(f"Saved → {path}")
