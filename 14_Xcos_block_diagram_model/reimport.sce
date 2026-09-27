here = pwd() + "/";
loadXcosLibs(); loadScicos();
ok = importXcosDiagram(here + "GRAIL_system.zcos"); if ~ok then error("import failed"); end
D = csvRead(here + "xcos_inputs.csv", ",", ".", "double", [], [], [], 1);
t = D(:, 1) * 3600;
Vg = struct("time", t, "values", D(:, 2)); Va = struct("time", t, "values", D(:, 3));
Vm = struct("time", t, "values", D(:, 4)); Vd = struct("time", t, "values", D(:, 5));
n = 0; for i = 1:size(scs_m.objs), if typeof(scs_m.objs(i)) == "Block" then n = n + 1; end, end
mprintf("re-imported GRAIL_system.zcos: %d blocks, %d objects\n", n, size(scs_m.objs));
Info = scicos_simulate(scs_m, list(), struct("Tc0", D(1,3)), "nw");   // context default = parallel, 2 modules
mprintf("re-imported file, parallel 2 modules: solar %.2f kWh, load %.2f kWh\n", E.values($, 4) / 3.6e6, E.values($, 5) / 3.6e6);
exit(0);
