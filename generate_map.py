"""
Publication-quality study-area map of Kentucky Mesonet stations.
Includes a CONUS inset showing Kentucky's location.
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
import numpy as np

# ── data ─────────────────────────────────────────────────────────────────────
df = pd.read_csv("supplementary_table_updated.csv")

# Drop rows with missing coordinates
df = df.dropna(subset=["Lat", "Lon"])

retained   = df[df["QC_Status"] == "Retained"]
excl_first = df[df["QC_Status"].str.startswith("Excluded after first")]
excl_sec   = df[df["QC_Status"].str.startswith("Excluded after second")]

# ── style ─────────────────────────────────────────────────────────────────────
PROJ = ccrs.AlbersEqualArea(central_longitude=-86.0, central_latitude=37.8)
DATA_CRS = ccrs.PlateCarree()

C_RETAIN  = "#1a6dab"   # blue  – retained
C_EXCL1   = "#e07b00"   # amber – excluded after 1st QC
C_EXCL2   = "#c0392b"   # red   – excluded after 2nd QC
C_KY_FILL = "#dce9f5"   # light blue fill for KY
C_NEIGHBOR = "#f0f0f0"  # neighbouring states
C_OCEAN    = "white"
C_KY_EDGE  = "#2c3e50"

MARKER_SIZE = 52
FONT = "DejaVu Sans"

# ── figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(10, 7), dpi=300)
fig.patch.set_facecolor("white")

# ── main axes: Kentucky ───────────────────────────────────────────────────────
ax = fig.add_axes([0.02, 0.08, 0.96, 0.85], projection=PROJ)

# Extent: Kentucky + small buffer
ax.set_extent([-89.7, -81.8, 36.35, 39.25], crs=DATA_CRS)

# --- background features -----------------------------------------------------
ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor=C_OCEAN, zorder=0)
ax.add_feature(cfeature.LAND.with_scale("50m"),  facecolor=C_NEIGHBOR, zorder=1)

# Use shapereader to isolate Kentucky (needed early for zorder sequencing)
shpfile = natural_earth(resolution="10m", category="cultural",
                        name="admin_1_states_provinces")
reader  = Reader(shpfile)
ky_geom = [rec.geometry for rec in reader.records()
           if rec.attributes.get("name") == "Kentucky"]

# Kentucky fill drawn BEFORE counties so county lines render on top inside KY
for geom in ky_geom:
    ax.add_geometries([geom], DATA_CRS, facecolor=C_KY_FILL,
                      edgecolor="none", linewidth=0, zorder=2)

# County boundaries — drawn after KY fill so edges are visible inside KY too
counties = cfeature.NaturalEarthFeature(
    "cultural", "admin_2_counties", "10m",
    facecolor="none", edgecolor="#aaaaaa", linewidth=0.35
)
ax.add_feature(counties, zorder=3)

# Kentucky border on top of counties
for geom in ky_geom:
    ax.add_geometries([geom], DATA_CRS, facecolor="none",
                      edgecolor=C_KY_EDGE, linewidth=1.4, zorder=4)

# State boundaries
states = cfeature.NaturalEarthFeature(
    "cultural", "admin_1_states_provinces_lines", "50m",
    facecolor="none", edgecolor="#555555", linewidth=0.9
)
ax.add_feature(states, zorder=4)

# Rivers
rivers = cfeature.NaturalEarthFeature(
    "physical", "rivers_lake_centerlines", "10m",
    facecolor="none", edgecolor="#7ab8d9", linewidth=0.5
)
ax.add_feature(rivers, zorder=5)

# --- station scatter plots ---------------------------------------------------
common_kw = dict(transform=DATA_CRS, zorder=6, linewidths=0.6,
                 edgecolors="white")

ax.scatter(retained["Lon"], retained["Lat"],
           s=MARKER_SIZE, marker="o", color=C_RETAIN,
           label=f"Retained (n={len(retained)})", **common_kw)

ax.scatter(excl_first["Lon"], excl_first["Lat"],
           s=MARKER_SIZE, marker="^", color=C_EXCL1,
           label=f"Excluded – 1st QC (n={len(excl_first)})", **common_kw)

ax.scatter(excl_sec["Lon"], excl_sec["Lat"],
           s=MARKER_SIZE, marker="s", color=C_EXCL2,
           label=f"Excluded – 2nd QC (n={len(excl_sec)})", **common_kw)

# --- legend ------------------------------------------------------------------
legend_elements = [
    Line2D([0], [0], marker="o", color="w", label=f"Retained (n={len(retained)})",
           markerfacecolor=C_RETAIN,  markeredgecolor="white",
           markeredgewidth=0.5, markersize=8),
    Line2D([0], [0], marker="^", color="w", label=f"Excluded – 1st QC (n={len(excl_first)})",
           markerfacecolor=C_EXCL1,   markeredgecolor="white",
           markeredgewidth=0.5, markersize=8),
    Line2D([0], [0], marker="s", color="w", label=f"Excluded – 2nd QC (n={len(excl_sec)})",
           markerfacecolor=C_EXCL2,   markeredgecolor="white",
           markeredgewidth=0.5, markersize=8),
]

# Place legend in the upper-left (Indiana/Illinois territory, clear of Kentucky)
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

# --- scale bar (lower-left, over Missouri/Tennessee territory) ---------------
scale_lon_start = -89.4
scale_lat = 36.55
scale_km = 100  # km
deg_per_km = 1 / 111.0
scale_lon_end = scale_lon_start + scale_km * deg_per_km / np.cos(np.radians(scale_lat))

ax.plot([scale_lon_start, scale_lon_end], [scale_lat, scale_lat],
        color="black", linewidth=2, transform=DATA_CRS, zorder=7,
        solid_capstyle="butt")
ax.plot([scale_lon_start, scale_lon_start], [scale_lat - 0.04, scale_lat + 0.04],
        color="black", linewidth=1.5, transform=DATA_CRS, zorder=7)
ax.plot([scale_lon_end, scale_lon_end], [scale_lat - 0.04, scale_lat + 0.04],
        color="black", linewidth=1.5, transform=DATA_CRS, zorder=7)
ax.text((scale_lon_start + scale_lon_end) / 2, scale_lat - 0.12,
        "100 km", ha="center", va="top", fontsize=6.5,
        transform=DATA_CRS, zorder=7)

# --- north arrow (lower-left, just right of scale bar) ----------------------
ax.annotate("N", xy=(0.09, 0.12), xytext=(0.09, 0.055),
            xycoords="axes fraction",
            fontsize=10, ha="center", fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color="black",
                            lw=1.5, mutation_scale=12),
            annotation_clip=False)

# --- title -------------------------------------------------------------------
ax.set_title("Study Area: Kentucky Mesonet Station Network",
             fontsize=11, fontweight="bold", pad=8, fontfamily=FONT)

# ── inset: CONUS ─────────────────────────────────────────────────────────────
# Position: lower-right corner (Tennessee territory, well below Kentucky)
ax_inset = fig.add_axes([0.68, 0.09, 0.28, 0.22],
                        projection=ccrs.LambertConformal(
                            central_longitude=-96, central_latitude=39))

ax_inset.set_extent([-125, -66, 24, 50], crs=DATA_CRS)

ax_inset.add_feature(cfeature.LAND.with_scale("50m"),
                     facecolor="#e8e8e8", edgecolor="none", zorder=1)
ax_inset.add_feature(cfeature.OCEAN.with_scale("50m"),
                     facecolor="#c8dff0", zorder=0)
ax_inset.add_feature(cfeature.BORDERS.with_scale("50m"),
                     edgecolor="#aaaaaa", linewidth=0.5, zorder=2)

# Highlight Kentucky in the inset
for geom in ky_geom:
    ax_inset.add_geometries([geom], DATA_CRS,
                            facecolor="#e84040", edgecolor="#800000",
                            linewidth=0.7, zorder=3)

# State outlines
states_50m = cfeature.NaturalEarthFeature(
    "cultural", "admin_1_states_provinces_lines", "50m",
    facecolor="none", edgecolor="#888888", linewidth=0.35
)
ax_inset.add_feature(states_50m, zorder=2)

# Box around inset
for spine in ax_inset.spines.values():
    spine.set_edgecolor("#444444")
    spine.set_linewidth(1.0)

ax_inset.set_title("Location in USA", fontsize=6, pad=3)

# ── save ─────────────────────────────────────────────────────────────────────
out_path = "kentucky_mesonet_study_area_map.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight",
            facecolor="white", edgecolor="none")
print(f"Saved → {out_path}")

out_pdf = "kentucky_mesonet_study_area_map.pdf"
fig.savefig(out_pdf, bbox_inches="tight",
            facecolor="white", edgecolor="none")
print(f"Saved → {out_pdf}")
