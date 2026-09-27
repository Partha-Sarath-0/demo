import sys
"""
GRAIL — figures for the domain-equivalence study, the PCM filing and the thermotropic filing.

D1  domain equivalence: which reduced domain may be used, and what a symmetry plane costs
P1  PCM: what the tray does in charge, cloud and stagnation
P2  thermotropic: whether the layer ever reaches its own switching band
V1  validation against the analytical Hottel-Whillier-Bliss model
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import figstyle as FS
FS.use()

FIG = "/home/claude/grail_cfd/12_figures"
CO, AL, NEU, WARN = FS.CO, FS.AL, "#3d7a5a", "#c47b20"


def load(p):
    return json.load(open(p)) if os.path.exists(p) else None


# ------------------------------------------------------------------ D1 domain equivalence
D = load("/home/claude/grail_cfd/06_domain_equiv/domain_study.json")
if D:
    names = ["3ch-adiabatic", "3ch-periodic", "2ch-adiabatic", "2ch-periodic"]
    fig, ax = plt.subplots(1, 3, figsize=(13.80, 5.23), layout="constrained")
    x = np.arange(len(names))
    for k, (key, lab, unit) in enumerate((
            ("d_eta_pct", "efficiency", "%"),
            ("d_Tp_std_vs_ref_interior_pct", "plate temperature spread", "%"),
            ("bridge_per_midline_W", "lateral bridge conduction", "W per midline"))):
        for tag, c, off in (("alternating", AL, -0.19), ("co_current", CO, +0.19)):
            v = [D["summary_vs_full_plate"][tag][n][key] for n in names]
            ax[k].bar(x + off, v, 0.38, color=c, label=tag.replace("_", "-"))
        if key == "bridge_per_midline_W":
            ref = D["summary_vs_full_plate"]["alternating"]["2ch-periodic"]["ref_bridge_per_midline_W"]
            ax[k].axhline(ref, color=AL, ls="--", lw=1.2)
            # Anchored at the left edge this label printed over the first bar pair. The
            # right-hand end of this panel is empty, so it goes there instead.
            ax[k].text(0.985, ref, " full plate, %.2f W " % ref, fontsize=10.2, color=AL,
                       va="bottom", ha="right",
                       transform=ax[k].get_yaxis_transform(),
                       bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c9ccd1", lw=0.8))
        else:
            ax[k].axhline(0.0, color="0.3", lw=0.9)
        ax[k].set_xticks(x)
        ax[k].set_xticklabels(names, rotation=18, ha="right", fontsize=9.8)
        ax[k].set_ylabel("deviation from the full plate  [%s]" % unit)
        ax[k].set_title(lab, fontsize=11.6)
        ax[k].legend(frameon=True, framealpha=0.94, fontsize=9.6)
    fig.suptitle("Fig D1 — Domain equivalence (CR-03). Under alternating flow only the "
                 "2-channel PERIODIC domain reproduces the full plate; an adiabatic symmetry "
                 "plane inflates bridge conduction by 67 %.", fontsize=11.8, y=1.05)
    fig.savefig(FIG + "/D1_domain_equivalence.png"); plt.close(fig)
    print("wrote D1")

# ------------------------------------------------------------------ P1 PCM
P = load("/home/claude/grail_cfd/07_mechanism/pcm_study.json")
if P:
    sc = P["scenarios"]
    fig, ax = plt.subplots(1, 3, figsize=(14.01, 5.23), layout="constrained")
    for k, (name, ttl) in enumerate((("charge", "Charge — cold start, design point"),
                                     ("cloud", "Cloud — irradiance to zero"),
                                     ("stagnation", "Stagnation — flow cut to 2 %"))):
        a, b = sc[name]["pcm"], sc[name]["no_pcm"]
        t = np.array(a["t_s"]) / 3600.0
        ax[k].plot(t, np.array(a["Tp_mean_K"]) - 273.15, color=NEU, lw=1.9,
                   label="with PCM tray")
        ax[k].plot(np.array(b["t_s"]) / 3600.0, np.array(b["Tp_mean_K"]) - 273.15,
                   color=WARN, lw=1.6, ls="--", label="tray as resistance only")
        ax[k].axhspan(51.0, 57.0, color="#9dc3e6", alpha=0.28, lw=0)
        ax[k].text(0.02, 0.025, "melting band 51 - 57 $^\\circ$C", transform=ax[k].transAxes,
                   fontsize=9.2, color=FS.CO)
        d = P["summary"][name]
        ax[k].set_xlabel("time  [h]"); ax[k].set_ylabel("mean plate T  [$^\\circ$C]")
        ax[k].set_title("%s\nlargest difference %+.1f K" % (ttl, d["max_difference_K"]),
                        fontsize=11.4)
        ax[k].legend(frameon=True, framealpha=0.94, fontsize=9.6, loc="best")
    fig.suptitle("Fig P1 — Graded PCM tray, RT55 + 10 %% EG, latent heat 170 kJ/kg across "
                 "51 - 57 $^\\circ$C. Stagnation peak falls from %.0f to %.0f $^\\circ$C."
                 % (P["summary"]["stagnation"]["peak_Tp_max_without_pcm_K"] - 273.15,
                    P["summary"]["stagnation"]["peak_Tp_max_with_pcm_K"] - 273.15),
                 fontsize=12.0, y=1.05)
    fig.savefig(FIG + "/P1_pcm_transient.png"); plt.close(fig)
    print("wrote P1")

# ------------------------------------------------------------------ P2 thermotropic
T = load("/home/claude/grail_cfd/07_mechanism/thermotropic_study.json")
if T:
    grid = T["operating_map"]
    flows = []
    for g in grid:
        if g["flow"] not in flows:
            flows.append(g["flow"])
    fig, ax = plt.subplots(1, 2, figsize=(12.77, 5.36), layout="constrained")
    # The four flow levels are ORDERED, so a sequential ramp is right; viridis
    # was not, because its yellow end sits at about 1.5:1 against a white page.
    cmap = FS.SEQ
    for i, fl in enumerate(flows):
        sub = [g for g in grid if g["flow"] == fl]
        G = [s["G_T"] for s in sub]
        ax[0].plot(G, [s["Tg_max_C"] for s in sub], "o-", color=FS.ordinal(len(flows))[i],
                   lw=1.7, ms=5, label="glass, %s flow" % fl)
        ax[1].plot(G, [s["Tp_max_C"] for s in sub], "s-", color=FS.ordinal(len(flows))[i],
                   lw=1.7, ms=5, label="absorber, %s flow" % fl)
    for a, who in ((ax[0], "glazing"), (ax[1], "absorber")):
        a.axhspan(72.0, 78.0, color=WARN, alpha=0.3, lw=0)
        a.text(0.02, 0.90, "switching band 72 - 78 $^\\circ$C", transform=a.transAxes,
               fontsize=9.6, color="#8a5a10")
        a.set_xlabel("irradiance  $G_T$  [W/m$^2$]")
        a.set_ylabel("peak %s temperature  [$^\\circ$C]" % who)
        a.legend(frameon=True, framealpha=0.94, fontsize=9.4)
    ax[0].set_title("What the layer sees if it sits in the glazing", fontsize=11.6)
    ax[1].set_title("What it would see on the absorber", fontsize=11.6)
    reach_g = T.get("glass_ever_reaches_band")
    fig.suptitle("Fig P2 — Thermotropic switching. The glazing %s reaches its own switching "
                 "band anywhere in the operating envelope; the absorber does."
                 % ("DOES" if reach_g else "never"), fontsize=12.0, y=1.04)
    fig.savefig(FIG + "/P2_thermotropic.png"); plt.close(fig)
    print("wrote P2")

# ------------------------------------------------------------------ V1 HWB
H = load("/home/claude/grail_cfd/05_validation/hwb_validation.json")
if H:
    fig, ax = plt.subplots(1, 2, figsize=(11.95, 5.23), layout="constrained")
    tags = list(H["cases"].keys())
    xs = np.arange(len(tags))
    sv = [H["cases"][t]["solver"]["eta"] for t in tags]
    hv = [H["cases"][t]["hwb"]["eta"] for t in tags]
    # Thinner bars with a real gap between the pair; the two used to meet edge to edge,
    # which reads as one bar with a colour change in the middle.
    ax[0].bar(xs - 0.175, sv, 0.32, color=CO, label="conjugate solver")
    ax[0].bar(xs + 0.175, hv, 0.32, color=FS.REF, label="Hottel-Whillier-Bliss")
    # headroom for the legend, which the automatic placer puts above the bars
    ax[0].set_ylim(0, max(max(sv), max(hv)) * 1.34)
    for i, t in enumerate(tags):
        ax[0].annotate("%+.2f %%" % H["cases"][t]["d_eta_pct"],
                       xy=(i, max(sv[i], hv[i])), xytext=(0, 7),
                       textcoords="offset points", ha="center", fontsize=11, color=FS.INK)
    ax[0].set_xticks(xs); ax[0].set_xticklabels([t.replace("_", "-") for t in tags])
    ax[0].set_ylabel("collector efficiency")
    ax[0].set_title("Efficiency: solver against the analytical model", fontsize=11.6)
    ax[0].legend(frameon=True, framealpha=0.94, fontsize=9.6)

    co = H["cases"][tags[0]]["hwb"]
    labels = ["fin efficiency F\n(inlet)", "fin efficiency F\n(outlet)",
              "collector factor F'", "heat removal F$_R$"]
    vals = [co["F_fin_inlet"], co["F_fin_outlet"], co["F_prime_avg"], co["F_R"]]
    ax[1].barh(np.arange(len(vals)), vals, 0.56, color=CO)
    ax[1].set_yticks(np.arange(len(vals))); ax[1].set_yticklabels(labels, fontsize=10.5)
    ax[1].set_xlim(0, 1.22); ax[1].set_xlabel("value")
    # The tip labels used to be placed 0.012 past the bar in DATA units against an xlim of
    # 1.05, so the two longest ran off the axis. Offsetting in points with headroom fixes it.
    for i, v in enumerate(vals):
        ax[1].annotate("%.4f" % v, xy=(v, i), xytext=(8, 0), textcoords="offset points",
                       va="center", fontsize=11, color=FS.INK)
    ax[1].set_title("Analytical chain, co-current", fontsize=11.6)
    fig.suptitle("Fig V1 \u2014 Validation against Hottel-Whillier-Bliss\n"
                 "$U_L$ is taken from the solver's own loss balance, not fitted, so this "
                 "tests the fin and flow solution.")
    fig.savefig(FIG + "/V1_hwb_validation.png"); plt.close(fig)
    print("wrote V1")

print("done")


# ------------------------------------------------------------------ D2 domain fields
FZ = "/home/claude/grail_cfd/06_domain_equiv/domain_fields.npz"
FM = "/home/claude/grail_cfd/06_domain_equiv/domain_fields.json"
if os.path.exists(FZ):
    d = np.load(FZ); meta = json.load(open(FM))
    names = ["full-12-adiabatic", "2ch-periodic", "2ch-adiabatic"]
    titles = ["Full 12-channel plate\n(reference, two central channels)",
              "2-channel PERIODIC\n(valid)", "2-channel ADIABATIC\n(symmetry planes)"]
    chy = d["full-12-adiabatic_chy"]; yc_f = d["full-12-adiabatic_yc"]
    mid = len(chy) // 2
    win = (yc_f >= chy[mid - 1] - 20.0) & (yc_f <= chy[mid] + 20.0)
    fields = [d["full-12-adiabatic_Tp"][:, win], d["2ch-periodic_Tp"], d["2ch-adiabatic_Tp"]]
    ys = [yc_f[win] - chy[mid - 1]] + [d[n + "_yc"] - d[n + "_chy"][0] for n in names[1:]]
    xs = [d["full-12-adiabatic_xc"]] + [d[n + "_xc"] for n in names[1:]]
    # the axial gradient is an order of magnitude larger than the lateral pattern and hides
    # it, so each field is shown as its deviation from its own axial mean
    dev = [f - f.mean(axis=1, keepdims=True) for f in fields]
    lim = max(np.abs(v).max() for v in dev)

    # The suptitle ran three lines long and the gridspec's explicit top=0.80 left no room
    # for it, so the figure title and the three panel titles were printed on top of one
    # another. constrained_layout is allowed to place them instead, and the title is two
    # lines rather than three.
    fig = plt.figure(figsize=(16.2, 6.1), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.10, h_pad=0.12, wspace=0.05)
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 0.05, 1.20])
    axs = [fig.add_subplot(gs[0, k]) for k in range(3)]
    cax = fig.add_subplot(gs[0, 3])
    axp = fig.add_subplot(gs[0, 4])
    for k in range(3):
        im = axs[k].pcolormesh(xs[k], ys[k], dev[k].T, cmap="RdBu_r",
                               vmin=-lim, vmax=lim, shading="auto")
        axs[k].set_xlabel("x  [mm]"); axs[k].set_title(titles[k])
        if k == 0:
            axs[k].set_ylabel("y from the first channel  [mm]")
        m = meta[names[k]]
        axs[k].text(0.03, 0.05, "bridge %.2f W" % m["bridge_W_per_midline"],
                    transform=axs[k].transAxes, fontsize=10.2,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.7", alpha=0.85))
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("T $-$ axial mean  [K]", fontsize=10.2, labelpad=2)
    for k, c, lab in ((0, "#222222", "full plate"), (1, NEU, "2ch periodic"),
                      (2, AL, "2ch adiabatic")):
        i = dev[k].shape[0] // 2
        axp.plot(ys[k], dev[k][i], color=c, lw=1.9, label=lab)
    for yv in (0.0, 40.0):
        axp.axvline(yv, color="0.75", ls=":", lw=1.0)
    axp.axvline(20.0, color=WARN, ls="--", lw=1.1)
    axp.text(20.8, 0.02, "bridge\nmidline", transform=axp.get_xaxis_transform(),
             fontsize=9.2, color="#8a5a10", va="bottom")
    axp.set_xlabel("y from the first channel  [mm]")
    axp.set_ylabel("T $-$ axial mean  [K]")
    axp.set_title("Lateral profile at x = 0", fontsize=11.2)
    axp.legend(frameon=True, framealpha=0.94, fontsize=9.6)
    fig.suptitle("Fig D2 \u2014 The same alternating solution on three domains, as deviation "
                 "from each field's own axial mean\nAdiabatic symmetry planes force 67 % more "
                 "flux through the one interior bridge")
    fig.savefig(FIG + "/D2_domain_fields.png"); plt.close(fig)
    print("wrote D2")

# ------------------------------------------------------------------ P3 PCM state
if P:
    sc = P["scenarios"]
    fig, ax = plt.subplots(1, 3, figsize=(14.01, 4.96), layout="constrained")
    for k, name in enumerate(("charge", "cloud", "stagnation")):
        a = sc[name]["pcm"]
        t = np.array(a["t_s"]) / 3600.0
        f = np.array(a.get("pcm_hist_f", []))
        Tpcm = np.array(a.get("pcm_hist_T_K", []))
        n = min(len(t), len(f))
        if n:
            ax[k].plot(t[:n], f[:n], color=NEU, lw=2.0)
            ax[k].set_ylim(-0.03, 1.03)
        ax[k].set_xlabel("time  [h]"); ax[k].set_ylabel("liquid fraction")
        a2 = ax[k].twinx()
        if n:
            a2.plot(t[:n], Tpcm[:n] - 273.15, color=WARN, lw=1.4, ls="--")
        # Three panels side by side means the right-hand axis of panels 1 and 2 sits right
        # against the next panel's own left axis, and the twin's label landed on its
        # neighbour's tick numbers. Only the last panel carries the label; the others keep
        # the ticks, which are enough because all three share the same scale.
        if k == 2:
            a2.set_ylabel("tray T  [$^\\circ$C]", color="#8a5a10")
        a2.tick_params(axis="y", colors="#8a5a10", labelsize=9.5); a2.grid(False)
        ttl = name
        if "stored_MJ_m2" in P["summary"][name]:
            ttl += "  —  %.2f MJ/m$^2$ stored" % P["summary"][name]["stored_MJ_m2"]
        ax[k].set_title(ttl, fontsize=11.4)
    fig.suptitle("Fig P3 — Tray state. Solid line: melted fraction. Dashed: tray temperature. "
                 "At stagnation the tray melts completely and then has nothing left to give.",
                 fontsize=12.0)
    fig.savefig(FIG + "/P3_pcm_state.png"); plt.close(fig)
    print("wrote P3")

# ------------------------------------------------------------------ P4 switching effect
if T and "cases" in T:
    cases = list(T["cases"].keys())
    fig, ax = plt.subplots(1, 2, figsize=(12.36, 5.36), layout="constrained")
    x = np.arange(len(cases))
    for j, (key, lab) in enumerate((("d_Tp_max_K", "change in peak plate temperature  [K]"),
                                    ("d_eta_pct", "change in efficiency  [%]"))):
        for drv, c, off in (("glass", CO, -0.19), ("plate", AL, +0.19)):
            v = [(T["cases"][k][drv][key] or 0.0) for k in cases]
            ax[j].bar(x + off, v, 0.38, color=c,
                      label="layer follows the %s" % ("glazing" if drv == "glass" else "absorber"))
            for i, vv in enumerate(v):
                if abs(vv) > 1e-9:
                    ax[j].text(i + off, vv, "%.0f" % vv if abs(vv) > 3 else "%.2f" % vv,
                               ha="center", va="top" if vv < 0 else "bottom", fontsize=9.4)
        ax[j].axhline(0, color="0.3", lw=0.9)
        ax[j].set_xticks(x)
        ax[j].set_xticklabels([c.replace("_", " ") for c in cases], rotation=12, fontsize=10.0)
        ax[j].set_ylabel(lab)
        ax[j].legend(frameon=True, framealpha=0.94, fontsize=9.6)
    ax[0].set_title("Overheating protection", fontsize=11.6)
    ax[1].set_title("Cost when collecting", fontsize=11.6)
    fig.suptitle("Fig P4 — Thermotropic switching effect. In the glazing it does nothing, "
                 "anywhere. On the absorber it costs nothing when collecting and removes "
                 "128 K at stagnation.", fontsize=11.9)
    fig.savefig(FIG + "/P4_thermotropic_effect.png"); plt.close(fig)
    print("wrote P4")
