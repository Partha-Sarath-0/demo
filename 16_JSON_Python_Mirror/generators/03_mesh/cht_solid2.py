"""
GRAIL — the roll-bond solid as two conformal structured blocks, for conjugate heat transfer.

The O-grid annulus attempt failed: mapping the wall ring onto the metal's outer outline by
arc length folds its own cells (measured overlap 47 %, and Laplace smoothing only reduced it
to 38 %), because a 8.0 mm concave floor has to stretch onto a 40 mm flat bottom while the
dome compresses onto a shorter shell. Documented, abandoned.

What makes the construction possible is a measured property of the CAD wall: split at the
two y-extremes, BOTH branches of the section are single-valued in y, so the metal can be laid
out on y columns.

The section's widest point is NOT at z = 0. Measured on channel y = -20 at the inlet station,
the extreme-y node sits at z = 0.447 mm and the wall reaches z = 0 only 0.54 mm further in -
the signature of the r = 0.5 mm fillet where the domed upper sheet blends into the flat lower
one. The earlier note in this file that the wall "meets z = 0 at the channel edges" was wrong
and is corrected here. Consequences are recorded under KNOWN DEFICIT below.

So the metal splits into two structured blocks on a SHARED set of y columns:

    lower   z from -t_lo up to the wall's floor branch   (= 0 outside the channel)
    upper   z from the wall's dome branch up by t_up     (= 0 .. t_up outside the channel)

They share every node on the bonded lands at z = 0, so the metal conducts laterally as one
piece. Over the channel each block's inner row IS the fluid's own wall nodes, so the coupled
interface is conformal by construction.

KNOWN DEFICIT - ENGINEERING_ASSUMPTION, quantified, not fudged
-------------------------------------------------------------
The CAD metal over one pitch is 93,881.8 mm3 (lower sheet 528,000 and upper sheet 598,581.6
mm3 over 12 pitches, both read from the STEP solids with occ.getMass). The column model, run
at NU = 192 and NU = 384 as a continuum integral so discretisation is excluded, gives
90,937 mm3: **-3.14 %, converged**. As actually meshed at NU = 96 the figure is 91,838 mm3,
-2.18 %, because the thickness clip described below adds back about a tenth of the deficit.

The missing metal is the fillet shoulder at each of the two channel corners. There the upper
sheet is not a shell at all: a 1 mm sheet cannot be offset across a 0.5 mm concave fillet
without the offset surface crossing itself, so in the CAD the sheet simply fills the corner
as solid metal. A column model that carries the upper sheet as a constant-thickness shell
over the dome branch cannot represent that, and no amount of grid refinement recovers it.

The deficit is therefore
  * bounded and measured, at -3.14 % of the metal,
  * localised within about 1 mm of the two channel corners, and
  * CONSERVATIVE for the claim being tested: less metal at the corner means less lateral
    conduction out of the channel, which understates the alternating-flow uniformity benefit
    rather than inflating it.

Any conjugate result from this mesh must be quoted with that deficit stated.
"""
import numpy as np

PITCH = 40.0
T_LO, T_UP = 1.0, 1.0


def resample_rings(W, n_floor=None):
    """Re-parameterise every wall ring so the two y-extreme corners sit at FIXED indices.

    Why this is needed. The ring that comes off the NURBS is sampled at uniform parameter,
    so the node nearest the section's widest point drifts with x. Measured on channel
    y = -20 at NU = 96: the dome's widest node is index 44 at the first station and 43 at
    every other one, and at the changeover the two candidates differ in y by 0.9 um while
    differing in z by 0.155 mm. Splitting the ring at a per-station argmax then gives
    branches of different lengths (43/55 at most stations, 44/54 at three of them), which
    cannot be assembled into a structured block; splitting at one fixed index instead leaves
    the branch doubling back by that 0.9 um, which inverts one cell per station.

    Both failures come from the same cause - the corner is not a node - so the fix is to
    make it one. Each branch is resampled at uniform arc length along the ring polyline
    between the two extreme nodes, endpoints included. The new nodes lie on the same
    polyline, so the ring still follows the CAD wall to the same chord error, the node count
    is unchanged, and the corner is now index 0 and index n_floor-1 at every station.

    The resampled ring is used for BOTH the fluid O-grid and the solid blocks, so the
    conjugate interface stays conformal by construction.
    """
    NXp, NU, _ = W.shape
    if n_floor is None:
        from collections import Counter
        c = Counter()
        for k in range(NXp):
            y = W[k][:, 1]
            il, ir = int(np.argmin(y)), int(np.argmax(y))
            c[(ir - il) % NU + 1] += 1
        n_floor = c.most_common(1)[0][0]
    n_dome = NU - n_floor + 2
    out = np.empty_like(W)
    for k in range(NXp):
        ring = W[k]
        y = ring[:, 1]
        il, ir = int(np.argmin(y)), int(np.argmax(y))
        fwd = [(il + j) % NU for j in range((ir - il) % NU + 1)]
        bwd = [(ir + j) % NU for j in range((il - ir) % NU + 1)]
        a, b = ring[fwd], ring[bwd]
        # the branch with the lower mean z is the floor
        if a[:, 2].mean() > b[:, 2].mean():
            a, b = b, a
        new = []
        for branch, n_new in ((a, n_floor), (b, n_dome)):
            s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(branch, axis=0),
                                                                axis=1))])
            # Keep the ORIGINAL node spacing, do not impose uniform arc length. The O-grid's
            # core block is a transfinite patch built on four corners at ring indices 0,
            # NU/4, NU/2, 3NU/4, so redistributing the ring moves those corners and distorts
            # the core: uniform-arc resampling took checkMesh's max skewness from 1.24 on the
            # validated fluid mesh to 3.34, and the pressure equation would not converge.
            # Interpolating each branch's own normalised arc-length positions onto the new
            # node count leaves every node where it was whenever the count is unchanged, and
            # shifts it by at most one spacing at the few stations where the corner index
            # moves - which is the whole reason the corners are being pinned.
            f_old = np.linspace(0.0, 1.0, len(branch))
            f_new = np.linspace(0.0, 1.0, n_new)
            t = np.interp(f_new, f_old, s)
            new.append(np.column_stack([np.interp(t, s, branch[:, c]) for c in range(3)]))
        # floor branch in full, then the dome branch without its two shared corner nodes
        out[k] = np.vstack([new[0], new[1][1:-1]])
    return out, n_floor


def fixed_split(W):
    """One pair of split indices for the whole channel.

    The two branches have to contain the SAME number of nodes at every axial station,
    otherwise the solid blocks are not structured and cannot be assembled into hexes.
    Taking argmin/argmax of y station by station does not give that: on the converging
    channel the extreme-y node index moves by one somewhere along the run (measured at
    NU = 96: i_right = 44 at the inlet station, 43 at all the others), because the ring's
    parameterisation and the section's shape drift relative to each other.

    The ring is generated from the same NURBS parameter values at every station, so node i
    is the same relative point on the perimeter all along the channel. Fixing the split at
    the modal index therefore picks the same physical corner everywhere; the caller checks
    that y is still monotone along each branch at every station, which is the property the
    construction actually needs.
    """
    from collections import Counter
    cl = Counter(); cr = Counter()
    for k in range(W.shape[0]):
        y = W[k][:, 1]
        cl[int(np.argmin(y))] += 1
        cr[int(np.argmax(y))] += 1
    i_left, i_right = cl.most_common(1)[0][0], cr.most_common(1)[0][0]
    # verify on the RAW walk order, before any sort: split_ring sorts each branch by y, and
    # a sort would hide exactly the defect this has to catch - a branch that doubles back in
    # y would come out of the sort as a polyline that zig-zags in z and folds its cells.
    n = W.shape[1]
    fwd = np.array([(i_left + k) % n for k in range((i_right - i_left) % n + 1)])
    bwd = np.array([(i_right + k) % n for k in range((i_left - i_right) % n + 1)])
    for k in range(W.shape[0]):
        y = W[k][:, 1]
        for br in (fwd, bwd):
            d = np.diff(y[br])
            assert np.all(d > 0) or np.all(d < 0), \
                ("station %d: the fixed split leaves a branch non-monotone in y; the "
                 "two-block construction is not valid on this ring" % k)
    return i_left, i_right


def split_ring(ring, split=None):
    """Floor branch and dome branch of the wall ring, each sorted by y.

    Returns (yf, zf, if_), (yd, zd, id_) where i* index back into the ring.
    `split` fixes the two corner indices; without it they are taken from this ring alone.
    """
    y, z = ring[:, 1], ring[:, 2]
    yc = 0.5 * (y.max() + y.min())
    if split is None:
        i_left, i_right = int(np.argmin(y)), int(np.argmax(y))
    else:
        i_left, i_right = split
    n = len(ring)
    # walk both ways round the ring between the two extreme-y nodes
    fwd = [(i_left + k) % n for k in range((i_right - i_left) % n + 1)]
    bwd = [(i_right + k) % n for k in range((i_left - i_right) % n + 1)]
    a, b = np.array(fwd), np.array(bwd)
    branch_a_is_floor = z[a].mean() < z[b].mean()
    f_idx, d_idx = (a, b) if branch_a_is_floor else (b, a)
    f_idx = f_idx[np.argsort(y[f_idx])]
    d_idx = d_idx[np.argsort(y[d_idx])]
    return (y[f_idx], z[f_idx], f_idx), (y[d_idx], z[d_idx], d_idx), yc


def columns(ring, n_land=10):
    """Shared y columns: land, then the ring's own dome y values, then land."""
    (yf, zf, fi), (yd, zd, di), yc = split_ring(ring)
    yL, yR = yc - PITCH / 2, yc + PITCH / 2
    left = np.linspace(yL, yd[0], n_land + 1)[:-1]
    right = np.linspace(yd[-1], yR, n_land + 1)[1:]
    return np.concatenate([left, yd, right]), (yf, zf, fi), (yd, zd, di), len(left)


def block_nodes(ring, n_land=10, nz_lo=3, nz_up=3):
    """Node coordinates for both blocks at one station, on shared y columns.

    Returns lower[(nz_lo+1, NY, 2)] and upper[(nz_up+1, NY, 2)] as (y, z), where
    lower[-1] is the top row and upper[0] is the bottom row. Over the channel those rows
    ARE the wall; outside it they both sit at z = 0 and coincide.
    """
    ys, (yf, zf, fi), (yd, zd, di), nL = columns(ring, n_land)
    NY = len(ys)
    in_ch = (ys >= yd[0] - 1e-9) & (ys <= yd[-1] + 1e-9)
    z_floor = np.zeros(NY)
    z_dome = np.zeros(NY)
    z_floor[in_ch] = np.interp(ys[in_ch], yf, zf)
    z_dome[in_ch] = np.interp(ys[in_ch], yd, zd)
    lower = np.empty((nz_lo + 1, NY, 2))
    upper = np.empty((nz_up + 1, NY, 2))
    for m in range(nz_lo + 1):
        t = m / nz_lo
        lower[m, :, 0] = ys
        lower[m, :, 1] = -T_LO + t * (z_floor + T_LO)
    # The upper sheet is 1 mm measured NORMAL to the dome. Offsetting the nodes along the
    # normal gets the thickness right but inverts a few cells at the dome foot, where the
    # offset direction turns sharply. Extruding VERTICALLY by t_up / n_z gives exactly the
    # same normal thickness - the area integral is t_up x arc length either way - while
    # every column moves straight up, so a cell cannot invert. n_z is floored so a near
    # vertical flank cannot demand an unbounded height.
    #
    # The floor value is a mesh-quality choice, not a physical one. Relaxing it from 0.35 to
    # 0.15 recovers 0.23 % more metal volume and then stops changing (0.10 and 0.05 give the
    # identical figure), with no inverted cells either way - but it lets a single cell in a
    # 1 mm sheet grow to 6.7 mm tall. 0.35 caps that at 2.9 mm and is kept for that reason.
    # ENGINEERING_ASSUMPTION; the 0.23 % is inside the -3.14 % deficit documented at the top.
    base = np.column_stack([ys, z_dome])
    tg = np.gradient(base, axis=0)
    tg /= (np.linalg.norm(tg, axis=1)[:, None] + 1e-12)
    n_z = np.abs(tg[:, 0])                      # z-component of the unit normal
    n_z[~in_ch] = 1.0
    h = T_UP / np.clip(n_z, 0.35, 1.0)
    for m in range(nz_up + 1):
        t = m / nz_up
        upper[m, :, 0] = ys
        upper[m, :, 1] = z_dome + t * h
    return lower, upper, in_ch, (fi, di), nL


def wall_column_map(ring, n_land=10):
    """For each y column inside the channel, the ring node index on each branch."""
    ys, (yf, zf, fi), (yd, zd, di), nL = columns(ring, n_land)
    in_ch = (ys >= yd[0] - 1e-9) & (ys <= yd[-1] + 1e-9)
    # the dome columns ARE the ring's dome nodes, in order
    dome_nodes = np.full(len(ys), -1, np.int64)
    dome_nodes[nL:nL + len(di)] = di
    # the floor branch is sampled at the same y values
    floor_nodes = np.full(len(ys), -1, np.int64)
    for c in np.where(in_ch)[0]:
        floor_nodes[c] = fi[int(np.argmin(np.abs(yf - ys[c])))]
    return in_ch, floor_nodes, dome_nodes, nL


def build_solid(W, wall_idx, first_idx, n_land=10, nz_lo=3, nz_up=3, yc0=None):
    """Both solid blocks for one channel, sharing nodes with the fluid and with each other.

    wall_idx[(NXp, NU)] are the fluid's wall-ring node indices. New solid nodes are numbered
    from first_idx. Returns (points, hexes, n_new).

    Node sharing, which is what makes the conjugate interface conformal:
      * over the channel, the lower block's top row IS the fluid's floor-branch nodes and
        the upper block's bottom row IS the fluid's dome-branch nodes
      * over the bonded lands, both blocks use the SAME new z = 0 nodes, so the metal is
        one connected piece and the lateral bridge can conduct
      * the two branches share the extreme-y nodes, so the blocks also meet each other at
        the channel edge
    """
    NXp, NU, _ = W.shape
    pts, hexes = [], []
    # the previous station's node-index grid, one per block. Kept in a dict rather than in
    # the hex list: a numpy hex array and a bookkeeping tuple cannot share a list without
    # h_[0] meaning two different things.
    prev_idx = {"lower": None, "upper": None}
    split = fixed_split(W)
    n = first_idx
    for k in range(NXp):
        ring = W[k]
        x = ring[0, 0]
        (yf, zf, fi), (yd, zd, di), yc = split_ring(ring, split)
        assert abs(yf[0] - yd[0]) < 1e-12 and abs(yf[-1] - yd[-1]) < 1e-12, \
            "branches must share the extreme-y nodes"
        # The pitch window must be the SAME at every station, or the land columns wobble in
        # y with x and the two channels' blocks no longer share a node column where they
        # abut. Taking yc from each ring's own extremes does wobble: measured drift over the
        # run is a few microns, enough that only 2 of 11 stations lined up. yc0 pins the
        # window to the nominal channel centre instead; the ring's own centre sits 5.2 um
        # off it, which shifts the channel within its pitch by that much and nothing else.
        yw = yc if yc0 is None else yc0
        yL, yR = yw - PITCH / 2, yw + PITCH / 2
        land_l = np.linspace(yL, yd[0], n_land + 1)[:-1]
        land_r = np.linspace(yd[-1], yR, n_land + 1)[1:]
        nl, nr = len(land_l), len(land_r)

        # ---- shared land nodes at z = 0, created once and used by both blocks
        land_y = np.concatenate([land_l, land_r])
        land_id = np.arange(n, n + len(land_y)); n += len(land_y)
        pts.append(np.column_stack([np.full(len(land_y), x), land_y,
                                    np.zeros(len(land_y))]))

        # fi / di index the RING; the mesh needs the fluid's GLOBAL node numbers for the
        # same nodes, which is the whole point of sharing them.
        gw = wall_idx[k]
        for which in ("lower", "upper"):
            if which == "lower":
                ys = np.concatenate([land_l, yf, land_r])
                z_in = np.concatenate([np.zeros(nl), zf, np.zeros(nr)])
                inner_id = np.concatenate([land_id[:nl], gw[fi], land_id[nl:]])
                nz, z0, sgn = nz_lo, -T_LO, +1
            else:
                ys = np.concatenate([land_l, yd, land_r])
                z_in = np.concatenate([np.zeros(nl), zd, np.zeros(nr)])
                inner_id = np.concatenate([land_id[:nl], gw[di], land_id[nl:]])
                tg = np.gradient(np.column_stack([ys, z_in]), axis=0)
                tg /= (np.linalg.norm(tg, axis=1)[:, None] + 1e-12)
                n_z = np.abs(tg[:, 0])
                n_z[:nl] = 1.0; n_z[len(ys) - nr:] = 1.0
                h = T_UP / np.clip(n_z, 0.35, 1.0)
                nz, sgn = nz_up, -1
            NY = len(ys)
            idx = np.empty((nz + 1, NY), np.int64)
            if which == "lower":
                idx[nz] = inner_id                       # top row is the wall / land
                for m in range(nz):
                    t = m / nz
                    zz = z0 + t * (z_in - z0)
                    idx[m] = np.arange(n, n + NY); n += NY
                    pts.append(np.column_stack([np.full(NY, x), ys, zz]))
            else:
                idx[0] = inner_id                        # bottom row is the wall / land
                for m in range(1, nz + 1):
                    t = m / nz
                    zz = z_in + t * h
                    idx[m] = np.arange(n, n + NY); n += NY
                    pts.append(np.column_stack([np.full(NY, x), ys, zz]))
            prev = prev_idx[which]
            if prev is not None:
                m_ = np.arange(nz)[:, None]; i_ = np.arange(NY - 1)[None, :]
                H = np.stack([prev[m_, i_], prev[m_, i_ + 1], prev[m_ + 1, i_ + 1],
                              prev[m_ + 1, i_],
                              idx[m_, i_], idx[m_, i_ + 1], idx[m_ + 1, i_ + 1],
                              idx[m_ + 1, i_]], axis=-1).reshape(-1, 8)
                hexes.append(H)
            prev_idx[which] = idx
    H = np.vstack(hexes)
    return np.vstack(pts), H, n - first_idx
