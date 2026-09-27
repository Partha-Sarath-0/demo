// RUN_GRAIL_XCOS  Build the GRAIL Xcos diagram, save GRAIL_system.zcos, simulate one year at
// Berhampur for each case, and write xcos_results.csv. Run from this folder:
//   scilab -nw -f run_grail_xcos.sce        (or open in the Scilab console and press Execute)
here = get_absolute_file_path("run_grail_xcos.sce");
exec(here + "grail_xcos_build.sce", -1);
xcosDiagramToScilab(here + "GRAIL_system.zcos", scs_m);
mprintf("saved %s\n", here + "GRAIL_system.zcos");

D = csvRead(here + "xcos_inputs.csv", ",", ".", "double", [], [], [], 1);
t = D(:, 1) * 3600;
Vg = struct("time", t, "values", D(:, 2));
Va = struct("time", t, "values", D(:, 3));
Vm = struct("time", t, "values", D(:, 4));
Vd = struct("time", t, "values", D(:, 5));

cases = list( ..
  list("alternating", 0.5966, 2.004, 0.00038, 2), ..
  list("parallel",    0.6368, 2.104, 0.0,     2), ..
  list("alternating", 0.5966, 2.004, 0.00038, 4), ..
  list("parallel",    0.6368, 2.104, 0.0,     4));
// efficiency coefficients are re-read exactly from the JSON (the literals above are labels only)
J = mgetl(here + "efficiency_correlations.json"); J = strcat(J, " ");
function v = jget(J, arr, key)
    k = strindex(J, """" + arr + """"); k = k(1);
    kk = strindex(part(J, k:length(J)), """" + key + """"); kk = kk(1) + k - 1;
    s = part(J, kk + length(key) + 3:kk + length(key) + 40);
    s = tokens(s, [",", "}", " "]); v = evstr(s(1));
endfunction
fd = mopen(here + "xcos_results.csv", "w");
mfprintf(fd, "arrangement,n_modules,Q_coll_kWh,Q_loss_kWh,Q_draw_kWh,Q_solar_kWh,Q_load_kWh,pump_h,solar_fraction,Tt_end_K,Tc_max_K,closure_kWh,run_s\n");
for i = 1:size(cases)
    cs = cases(i); arr = cs(1); n = cs(5);
    e0 = jget(J, arr, "eta0"); a1 = jget(J, arr, "a1_W_m2K"); a2 = jget(J, arr, "a2_W_m2K2");
    A = n * 0.528;
    upd = struct("A", A, "C", 33500 * A, "g2", 2 * (n * 0.00275) * 4180, "e0", e0, "a1", a1, "a2", a2, "Tc0", D(1, 3));
    tic(); Info = scicos_simulate(scs_m, list(), upd, "nw"); rs = toc();
    Ef = E.values($, :) / 3.6e6;           // cumulative energies at t = 8760 h, kWh
    Ef(6) = E.values($, 6) / 3600;         // pump running time, h
    // tank first law at the time of the last energy sample (both recorders use the same clock grid)
    tE = E.time($); kT = find(abs(T.time - tE) < 1e-6);
    if kT == [] then [dmin, kT] = min(abs(T.time - tE)); end
    Tt_end = T.values(kT(1), 2);
    closure = Ef(1) - Ef(2) - Ef(3) - 100 * 4180 * (Tt_end - 298.15) / 3.6e6;
    mfprintf(fd, "%s,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f,%.6f,%.4f,%.3f,%.3e,%.0f\n", arr, n, Ef(1), Ef(2), Ef(3), Ef(4), Ef(5), Ef(6), Ef(4) / Ef(5), Tt_end, max(T.values(:, 1)), closure, rs);
    mprintf("%-11s %d modules: solar %.1f kWh, load %.1f kWh, SF %.2f %%, max Tc %.1f K, closure %.2e kWh (%.0f s)\n", arr, n, Ef(4), Ef(5), 100 * Ef(4) / Ef(5), max(T.values(:, 1)), closure, rs);
end
mclose(fd);
mprintf("done\n");
exit(0);
