"""
GRAIL CFD — assembly-level mesh figures M6 - M10, on the CORRECTED geometry.

M6   complete collector assembly, surface mesh of every CAD body
M7   the CFD mesh in position inside the assembly
M8   cut-away through the CFD mesh
M9   the CFD mesh at the inlet end of the absorber
M10  the full 12-channel absorber, complete CFD mesh

Nothing here is an illustration: every triangle comes off the CAD surfaces and every
hexahedron is a cell of the mesh described in 03_mesh/plate/plate12.json.
"""
import sys, os, json, time
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap

sys.path.insert(0, "/home/claude/grail_cfd/tools")
import asm_common as A

pv.OFF_SCREEN = True
FIG = "/home/claude/grail_cfd/12_figures"
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.dpi": 150, "savefig.dpi": 150,
                     "savefig.bbox": "tight"})

AL, ALE = "#c8795c", "#7d3c1e"          # aluminium
WA, WAE = "#4a90c4", "#12436b"          # water
GH = "#9aa6b2"                          # ghosted enclosure
SHOT = (2400, 1150)


def shot(fn, cpos, size=SHOT, parallel=False, zoom=1.0, fit=True):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    fn(p)
    if parallel:
        p.enable_parallel_projection()
    p.camera_position = cpos
    if fit:
        p.reset_camera()
    p.camera.zoom(zoom)
    img = p.screenshot(return_img=True)
    p.close()
    return crop(img)


def crop(img, pad=14):
    """Trim the white margin the renderer leaves around the object."""
    ink = (np.asarray(img)[:, :, :3] < 246).any(axis=2)
    if not ink.any():
        return img
    r = np.where(ink.any(axis=1))[0]; c = np.where(ink.any(axis=0))[0]
    r0, r1 = max(r[0] - pad, 0), min(r[-1] + pad + 1, img.shape[0])
    c0, c1 = max(c[0] - pad, 0), min(c[-1] + pad + 1, img.shape[1])
    return img[r0:r1, c0:c1]


def compose(img, title, caption, legend=None, out=None, figw=14.6, legloc="upper left",
            legcols=1, legfs=8.6):
    h, w = img.shape[:2]
    ih = figw * h / w
    top, bot = 0.62, 0.78 + 0.17 * caption.count("\n")
    fh = ih + top + bot
    fig = plt.figure(figsize=(figw, fh))
    ax = fig.add_axes([0.0, bot / fh, 1.0, ih / fh])
    ax.imshow(img); ax.axis("off")
    fig.text(0.5, 1 - 0.16 / fh, title, ha="center", va="top", fontsize=15.5)
    fig.text(0.5, (bot - 0.20) / fh, caption, ha="center", va="top", fontsize=9.5,
             color="0.18", linespacing=1.6)
    if legend:
        ax.legend(handles=[Patch(facecolor=c, edgecolor="0.3", label=l) for l, c in legend],
                  loc=legloc, frameon=True, framealpha=0.93, fontsize=legfs, ncol=legcols,
                  borderpad=0.6, labelspacing=0.42, handlelength=1.5, edgecolor="0.7")
    fig.savefig(out); plt.close(fig)
    print("  wrote", os.path.basename(out), flush=True)


def compose2(imgs, subtitles, title, caption, legend=None, out=None, figw=15.2,
             legfs=8.6, legpanel=0, widths=(1.0, 1.0)):
    """Two panels side by side, one shared title, subtitles and caption."""
    hs = [i.shape[0] / i.shape[1] for i in imgs]
    wfrac = np.array(widths, float); wfrac /= wfrac.sum()
    ih = max(figw * wfrac[k] * hs[k] for k in range(2))
    top, bot = 0.68, 0.86 + 0.17 * caption.count("\n")
    fh = ih + top + bot
    fig = plt.figure(figsize=(figw, fh))
    x = 0.0
    for k, (im, st) in enumerate(zip(imgs, subtitles)):
        w = wfrac[k]
        ax = fig.add_axes([x + 0.004, bot / fh, w - 0.008, (ih - 0.30) / fh])
        ax.imshow(im); ax.axis("off")
        for s in ax.spines.values():
            s.set_visible(False)
        fig.text(x + w / 2, (bot + ih - 0.24) / fh, st, ha="center", va="bottom",
                 fontsize=10.6, color="0.1")
        if legend and k == legpanel:
            ax.legend(handles=[Patch(facecolor=c, edgecolor="0.3", label=l) for l, c in legend],
                      loc="upper left", frameon=True, framealpha=0.93, fontsize=legfs,
                      borderpad=0.6, labelspacing=0.42, handlelength=1.5, edgecolor="0.7")
        x += w
    fig.text(0.5, 1 - 0.17 / fh, title, ha="center", va="top", fontsize=15.5)
    fig.text(0.5, (bot - 0.22) / fh, caption, ha="center", va="top", fontsize=9.5,
             color="0.18", linespacing=1.6)
    fig.savefig(out); plt.close(fig)
    print("  wrote", os.path.basename(out), flush=True)


t0 = time.time()
print("loading ...", flush=True)
asm, ameta, (pa, pb, pc), (ma, mb, mc) = A.load_assembly()
fluid, solid, pmeta = A.load_plate()
bb = ameta["bounds"]
ENV = (bb[1] - bb[0], bb[3] - bb[2], bb[5] - bb[4])
print("  assembly %d tri   fluid %d hex   solid %d hex   (%.0f s)"
      % (asm.n_cells, fluid.n_cells, solid.n_cells, time.time() - t0), flush=True)

CMAP = ListedColormap([f[2] for f in A.FAMILIES])
fam_used = np.unique(asm.cell_data["family"])
LEG_ASM = [(A.FAMILIES[i][1], A.FAMILIES[i][2]) for i in fam_used]

fsurf = fluid.extract_surface(algorithm="dataset_surface")
ssurf = solid.extract_surface(algorithm="dataset_surface")
print("  CFD surfaces: %d + %d faces (%.0f s)" % (fsurf.n_cells, ssurf.n_cells, time.time() - t0),
      flush=True)

CH = pmeta["channels"]
GAP = max(c["floor_interface_gap_mm"] for c in CH)
NHF, NHS = pmeta["nhex_fluid"], pmeta["nhex_solid"]
VF = pmeta["fluid_volume_mm3"]
CAD_SHEETS = 528000.0 + 598581.603   # ABSORBER_LOWER_SHEET + ABSORBER_UPPER_SHEET
CAD_CH_VOL = 18643.963      # h-refined CAD channel volume; occ.getMass over-integrates
VCAD = CAD_CH_VOL * len(CH)  # this enclosed volume by +0.27 % (CR-09)
SEC_F = pmeta["NU"] * pmeta["NR"] + pmeta["NC"] ** 2
SEC_S = NHS // 12 // pmeta["NX"]

# ---------------------------------------------------------------------------- M6
print("M6 ...", flush=True)
def a6(p):
    p.add_mesh(asm, scalars="family", cmap=CMAP, clim=(0, len(A.FAMILIES) - 1),
               show_edges=True, line_width=0.22, edge_color="#2b2b2b",
               show_scalar_bar=False, ambient=0.28, diffuse=0.75, specular=0.12)

img = shot(a6, [(1750, -1500, 1150), (0, 0, -20), (0, 0, 1)], zoom=1.55)
compose(img,
        "Fig M6 — Complete collector assembly, surface mesh",
        "Every body in the STEP export discretised - %d of its 129 solids, %s triangles, "
        "%.0f mm edge cap, tessellated surface area %.2f m$^2$, envelope %.0f x %.0f x %.0f mm.\n"
        "Geometry: Grail_Collector_2.step (corrected, converging channels, G = 0.539935). "
        "Planar and cylindrical faces are meshed by gmsh; the 1100 mm B-spline channel walls and\n"
        "domes are evaluated directly on their own NURBS parameterisation, the route verified at "
        "Gate 1 (wall area +0.007 %%, enclosed volume -0.0015 %% against CAD).\n"
        "The 129th solid, SELECTIVE_COATING, is excluded: it translated with negative volume "
        "(-111.8 mm$^3$) and is carried as a surface radiative property, alpha 0.95 / eps 0.04 "
        "(CR-03)."
        % (ameta["n_solids"], "{:,}".format(ameta["ntri"]), ameta["size_max_mm"],
           ameta["area_mm2"] / 1e6, ENV[0], ENV[1], ENV[2]),
        legend=LEG_ASM, legcols=2, legfs=8.2, legloc="lower left",
        out=FIG + "/M6_assembly_surface_mesh.png")

# ---------------------------------------------------------------------------- M7
print("M7 ...", flush=True)
ghost = asm.extract_cells(
    np.where(asm.cell_data["family"] != A.FAM_IDX["03_ABSORBER_ASSEMBLY"])[0]).extract_surface(
    algorithm="dataset_surface")

def a7(p):
    p.add_mesh(ghost, color=GH, opacity=0.085, show_edges=False, specular=0.0)
    p.add_mesh(ssurf, color=AL, show_edges=False, opacity=0.42,
               ambient=0.30, diffuse=0.70)
    p.add_mesh(fsurf, color="#1b6fb5", show_edges=False, ambient=0.40, diffuse=0.75)

img = shot(a7, [(1750, -1500, 1150), (0, 0, -20), (0, 0, 1)], zoom=1.55)
compose(img,
        "Fig M7 — The CFD mesh in position inside the assembly",
        "The enclosure is ghosted; the solved domain is drawn solid, in the collector's own "
        "coordinate frame.\n%s hexahedra in total - %s fluid + %s roll-bond solid - "
        "100 %% hexahedral, 0 inverted cells.\nOnly the absorber is solved in 3-D; every other "
        "body enters the model through its boundary condition or material property, not as a mesh."
        % ("{:,}".format(NHF + NHS), "{:,}".format(NHF), "{:,}".format(NHS)),
        legend=[("roll-bond absorber AA1050  (CFD solid region)", AL),
                ("water, 12 graded channels  (CFD fluid region)", WA),
                ("enclosure and non-CFD components  (ghosted)", GH)],
        out=FIG + "/M7_cfd_mesh_in_assembly.png")

# ---------------------------------------------------------------------------- M8
print("M8 ...", flush=True)
def slab(g, x0, x1, y0, y1):
    return g.clip_box([x0, x1, y0, y1, -50, 50], invert=False)


def cut_actors(x0, x1, y0, y1, lw):
    fsx = slab(fluid, x0, x1, y0, y1).extract_surface(algorithm="dataset_surface")
    ssx = slab(solid, x0, x1, y0, y1).extract_surface(algorithm="dataset_surface")

    def act(p):
        p.add_mesh(ssx, color=AL, show_edges=True, line_width=lw, edge_color=ALE,
                   ambient=0.34, diffuse=0.68)
        p.add_mesh(fsx, color=WA, show_edges=True, line_width=lw, edge_color=WAE,
                   ambient=0.36, diffuse=0.68)
    return act


imgA = shot(cut_actors(-310.0, -220.0, -245.0, -155.0, 0.55),
            [(30, -350, 120), (-265, -200, 1.0), (0, 0, 1)], size=(1750, 1250), zoom=1.35)
imgB = shot(cut_actors(-266.0, -238.0, -244.0, -196.0, 1.1),
            [(-120, -290, 46), (-252, -220, 2.0), (0, 0, 1)], size=(1350, 1150), zoom=1.35)
compose2([imgA, imgB],
         ["80 mm slab through two channels, x $\\approx$ -260 mm",
          "the same cut, one channel, cells resolved"],
         "Fig M8 — Cut-away through the CFD mesh",
         "Structured hexahedra run continuously through the lower sheet, the 0.5 mm root fillet, "
         "the dome and the O-grid channel core.\n"
         "%d fluid cells per section - %d graded ring layers of %d, wall-clustered at expansion "
         "ratio 1.18, plus a %dx%d transfinite core - and %d solid cells per section.\n"
         "The wetted interface is exactly conformal: the outermost fluid ring layer and the "
         "innermost solid shell layer are the same nodes, not an interpolation.\n"
         "The lower-sheet interface closes to %.1f $\\mu$m, which is the CAD surface's own offset "
         "from z = 0, not a meshing error."
         % (SEC_F, pmeta["NR"], pmeta["NU"], pmeta["NC"], pmeta["NC"], SEC_S, GAP * 1000),
         legend=[("aluminium AA1050, roll-bond sheet pair", AL), ("water", WA)],
         widths=(1.35, 1.0), out=FIG + "/M8_cutaway.png")

# ---------------------------------------------------------------------------- M9
print("M9 ...", flush=True)
def inlet_actors(x1, y0, y1, lw, op):
    f9 = fluid.clip_box([-551, x1, y0, y1, -50, 50], invert=False).extract_surface(
        algorithm="dataset_surface")
    s9 = solid.clip_box([-551, x1, y0, y1, -50, 50], invert=False).extract_surface(
        algorithm="dataset_surface")

    def act(p):
        p.add_mesh(s9, color=AL, show_edges=True, line_width=lw * 0.6, edge_color=ALE,
                   opacity=op, ambient=0.34, diffuse=0.68)
        p.add_mesh(f9, color=WA, show_edges=True, line_width=lw, edge_color=WAE,
                   ambient=0.36, diffuse=0.68)
    return act


imgA = shot(inlet_actors(-300.0, -260, 260, 0.30, 0.45),
            [(-1150, -560, 420), (-460, -20, 1.0), (0, 0, 1)], size=(1900, 1250), zoom=1.55)
imgB = shot(inlet_actors(-495.0, -246, -154, 1.0, 0.80),
            [(-655, -320, 70), (-530, -200, 2.0), (0, 0, 1)], size=(1350, 1150), zoom=1.30)
compose2([imgA, imgB],
         ["all 12 channels at the inlet plane, $\\xi$ = 0",
          "two inlet sections, cells resolved"],
         "Fig M9 — CFD mesh, inlet end of the absorber",
         "Hexahedra are swept along every channel and graded towards the wetted wall "
         "(expansion ratio 1.18 over %d radial layers), %d axial stations over 1100 mm.\n"
         "Flow enters at $\\xi$ = 0 with $D_h$ = 5.199 mm and the section SHRINKS continuously "
         "to $D_h$ = 2.807 mm at $\\xi$ = 1  (G = 0.539935, $\\lambda_G$ = 1.0), so Re RISES "
         "downstream.\n"
         "This replaces the superseded figure, which showed the section GROWING to "
         "$D_h$ = 8.300 mm: that diverging geometry is withdrawn under CR-01 and is not used "
         "anywhere in this study."
         % (pmeta["NR"], pmeta["NX"]),
         legend=[("water, inlet sections", WA), ("roll-bond absorber (half-tone)", AL)],
         widths=(1.55, 1.0), out=FIG + "/M9_inlet_end.png")

# ---------------------------------------------------------------------------- M10
print("M10 ...", flush=True)
def a10(p):
    p.add_mesh(ssurf, color=AL, show_edges=True, line_width=0.10, edge_color=ALE,
               opacity=0.42, ambient=0.34, diffuse=0.68)
    p.add_mesh(fsurf, color=WA, show_edges=True, line_width=0.12, edge_color=WAE,
               ambient=0.36, diffuse=0.68)


imgA = shot(a10, [(-520, -1180, 700), (0, 0, 0), (0, 0, 1)], zoom=1.62)
imgB = shot(cut_actors(-560.0, -440.0, -248.0, -132.0, 0.45),
            [(-270, -430, 175), (-505, -190, 1.5), (0, 0, 1)], size=(1350, 1150), zoom=1.35)
compose2([imgA, imgB],
         ["the complete plate: 12 channels, 1100 mm, 40 mm pitch",
          "detail at the inlet corner"],
         "Fig M10 — Full 12-channel absorber, complete CFD mesh",
         "The periodic section is swept 1100 mm along every one of the 12 channels on a 40 mm "
         "pitch, leaving a 31.286 mm conductive bridge between neighbours.\n"
         "%s hexahedra (%s fluid + %s roll-bond solid), %s nodes, 100 %% hexahedral, "
         "0 inverted cells, smallest cell %.2e mm$^3$.\n"
         "Meshed fluid volume %.1f mm$^3$ against %.1f mm$^3$ in the CAD: %+.3f %%. That "
         "deviation is chordal - the O-grid ring is a polygon inscribed in the NURBS wall - "
         "and shrinks under refinement.\n"
         "Solid region %.0f mm$^3$ at a nominal 1.0 mm sheet thickness, %+.2f %% against the "
         "CAD sheet pair (ENGINEERING_ASSUMPTION: the real roll-bond sheet thins over the dome, "
         "measured 0.22 - 1.32 mm)."
         % ("{:,}".format(NHF + NHS), "{:,}".format(NHF), "{:,}".format(NHS),
            "{:,}".format(pmeta["nnode"]), pmeta["min_fluid_cell_volume_mm3"],
            VF, VCAD, 100 * (VF - VCAD) / VCAD,
            pmeta["solid_volume_mm3"], 100 * (pmeta["solid_volume_mm3"] - CAD_SHEETS) / CAD_SHEETS),
         legend=[("water, 12 graded channels", WA), ("roll-bond absorber (half-tone)", AL)],
         widths=(1.6, 1.0), out=FIG + "/M10_full_plate_mesh.png")

print("done (%.0f s)" % (time.time() - t0))
