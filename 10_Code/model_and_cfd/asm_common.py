"""Shared loaders for the GRAIL assembly-level mesh figures."""
import json, re
import numpy as np
import pyvista as pv

ASM = "/home/claude/grail_cfd/02_geometry/asm"
PLATE = "/home/claude/grail_cfd/03_mesh/plate"

# component families, in the order they stack from the sun down
FAMILIES = [
    ("01_GLAZING",           "glazing: outer / inner pane, thermotropic layer", "#7fb3d5"),
    ("02_TIM",               "transparent insulation (TIM)",                    "#cfe2f3"),
    ("03_ABSORBER_ASSEMBLY", "roll-bond absorber, AA1050",                      "#c8795c"),
    ("04_MANIFOLD",          "manifold blocks and 12 branch ports",             "#8e7cc3"),
    ("05_PCM_TRAY",          "graded PCM trays",                                "#93c47d"),
    ("06_INSULATION",        "rear and edge insulation",                        "#e0c25e"),
    ("07_BACKSHEET",         "backsheet",                                       "#b7b7b7"),
    ("08_SEALS",             "seals and gaskets",                               "#6aa84f"),
    ("09_SENSING",           "sensors, pyranometer, ESP32 board",               "#e06666"),
    ("10_MOUNTING",          "mounting brackets and rails",                     "#999999"),
    ("00_FRAME",             "frame rails and corner blocks",                   "#666666"),
    ("FASTENER",             "M5 bezel fasteners",                              "#444444"),
]
FAM_IDX = {f[0]: i for i, f in enumerate(FAMILIES)}


def family_of(name):
    m = re.findall(r"(\d\d_[A-Z_]+)", name)
    if m:
        return m[-1]              # deepest component group wins (04_MANIFOLD sits under 01_GLAZING
    return "FASTENER"             # in the STEP tree; that is a tree nesting only)


def _poly(xyz, tris):
    f = np.empty((len(tris), 4), np.int64)
    f[:, 0] = 3; f[:, 1:] = tris
    return pv.PolyData(np.asarray(xyz, np.float64), f.ravel())


def load_assembly():
    """Every CAD body, as PolyData, with a 'family' cell array. Returns (mesh, meta)."""
    a = np.load(ASM + "/groupA.npz"); ma = json.load(open(ASM + "/groupA.json"))
    b = np.load(ASM + "/groupB.npz"); mb = json.load(open(ASM + "/groupB.json"))
    c = np.load(ASM + "/groupA_fallback.npz"); mc = json.load(open(ASM + "/groupA_fallback.json"))

    famA = np.array([FAM_IDX.get(family_of(s["name"]), FAM_IDX["FASTENER"])
                     for s in ma["solids"]], np.int32)[a["owner"]]
    # group B: owner 0 = upper sheet (absorber), 1..12 = fluid voids (absorber assembly)
    famB = np.full(len(b["tris"]), FAM_IDX["03_ABSORBER_ASSEMBLY"], np.int32)
    famC = np.full(len(c["tris"]), FAM_IDX["04_MANIFOLD"], np.int32)

    pa, pb, pc = _poly(a["xyz"], a["tris"]), _poly(b["xyz"], b["tris"]), _poly(c["xyz"], c["tris"])
    pa.cell_data["family"] = famA
    pb.cell_data["family"] = famB
    pb.cell_data["is_fluid"] = (b["owner"] > 0).astype(np.int32)
    pc.cell_data["family"] = famC
    m = pa.merge(pb).merge(pc)
    meta = {
        "n_solids": len(ma["solids"]) + len(mb["channels"]) + 1,
        "ntri": int(len(ma["solids"]) and ma["ntri"]) + mb["ntri"] + mc["ntri"],
        "area_mm2": ma["area_mm2"] + mb["area_mm2"] + mc["area_mm2"] - mc["port_correction_mm2"],
        "size_max_mm": ma["size_max_mm"],
        "bounds": m.bounds,
    }
    return m, meta, (pa, pb, pc), (ma, mb, mc)


def load_plate(tag="plate12"):
    """The CFD mesh: fluid O-grid + roll-bond solid, as two UnstructuredGrids."""
    d = np.load(PLATE + "/%s.npz" % tag)
    meta = json.load(open(PLATE + "/%s.json" % tag))
    P = np.asarray(d["points"], np.float64)

    def ug(H, extra=None):
        cells = np.empty((len(H), 9), np.int64)
        cells[:, 0] = 8; cells[:, 1:] = H
        g = pv.UnstructuredGrid(cells.ravel(),
                                np.full(len(H), pv.CellType.HEXAHEDRON, np.uint8), P)
        if extra is not None:
            g.cell_data["block"] = extra
        return g

    return ug(d["hex_fluid"]), ug(d["hex_solid"], d["reg_solid"]), meta
