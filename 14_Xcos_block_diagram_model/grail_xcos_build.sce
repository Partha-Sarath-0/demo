// GRAIL Collector - system model as an Xcos block diagram (Scilab 2024.0.0).
// Roadmap Section 11 (MATLAB/Simulink) implemented in Scilab Xcos, the open-source equivalent.
//
// This script BUILDS the diagram block by block, saves it as GRAIL_system.zcos (open it with
// xcos("GRAIL_system.zcos") to see and edit the block diagram), and returns scs_m.
//
// Physics (identical to the Python / Octave system model except the draw, see below):
//   collector node  C dTc/dt = A[eta0 Geff - a1 (Tc-Ta) - a2 (Tc-Ta)^2] - 2 mdot cp (Tc-Tt) pump
//   tank            M cp dTt/dt = 2 mdot cp (Tc-Tt) pump - UA (Tt-Ta) - m_t cp (Tt-Tmn)
//   pump            hysteresis on Tc-Tt: on at +7 K, off at +2 K, and only while Tt <= Tmax
//   draw            continuous flow m_d(t) during the draw hours (kg/s); a mixing valve takes
//                   m_t = m_d min(1, (Tset-Tmn)/(Tt-Tmn)) from the tank; electric top-up to Tset
// Units: SI, temperatures in kelvin.
//
// Block map (index in scs_m.objs):
//   1 FROMWS_c  Vg  effective plane-of-array irradiance G_eff (W/m2, hourly, zero-order hold)
//   2 FROMWS_c  Va  ambient temperature (K)
//   3 FROMWS_c  Vm  mains water temperature (K)
//   4 FROMWS_c  Vd  draw flow (kg/s)
//   5 INTEGRAL_m  Tc   collector node temperature
//   6 INTEGRAL_m  Tt   tank temperature
//   7 EXPRESSION  Tc - Tt
//   8 HYSTHERESIS pump demand (on 7 K, off 2 K)
//   9 EXPRESSION  pump = demand * (Tt <= Tmax)
//  10 EXPRESSION  dTc/dt
//  11 EXPRESSION  dTt/dt
//  12-17 EXPRESSION  heat rates: collector->tank, tank loss, tank draw, solar delivered, load, pump on
//  18 MUX(6)      19 INTEGRAL_m (6 energy accumulators)
//  20 SampleCLK 3600 s   21 TOWS_c "E" (hourly cumulative energies)
//  22 MUX(2) Tc,Tt       23 SampleCLK 60 s   24 TOWS_c "T" (temperatures every 60 s)

loadXcosLibs(); loadScicos();

function b = blk(name, exprs, x, y)
    execstr("b = " + name + "(""define"");");
    if exprs <> [] then b.graphics.exprs = exprs; end
    b.graphics.orig = [x y]; b.graphics.sz = [4 2];
    if name == "EXPRESSION" then nin = evstr(exprs(1)); b.graphics.sz = [5 max(2, 1.6 * nin)]; end
endfunction
function l = sig(f, fp, t, tp)
    l = scicos_link(xx=[0;0], yy=[0;0], ct=[1 1], from=[f fp 0], to=[t tp 1]);
endfunction
function l = evt(f, fp, t, tp)
    l = scicos_link(xx=[0;0], yy=[0;0], ct=[5 -1], from=[f fp 0], to=[t tp 1]);
endfunction

// port coordinates (diagram units; block size is in 20-unit grid cells, y upwards)
function xy = portxy(b, kind, k)
    w = b.graphics.sz(1) * 20; h = b.graphics.sz(2) * 20; o = b.graphics.orig;
    if b.gui == "SPLIT_f" then xy = o + [3.5 3.5]; return; end
    if kind == "out" then n = size(b.model.out, "*"); xy = [o(1) + w, o(2) + h - h * k / (n + 1)];
    elseif kind == "in" then n = size(b.model.in, "*"); xy = [o(1), o(2) + h - h * k / (n + 1)];
    elseif kind == "eout" then xy = [o(1) + w / 2, o(2)];
    else xy = [o(1) + w / 2, o(2) + h]; end
endfunction
function l = placed(l, objs)
    if l.ct(2) == -1 then a = portxy(objs(l.from(1)), "eout", l.from(2)); b = portxy(objs(l.to(1)), "ein", l.to(2));
    else a = portxy(objs(l.from(1)), "out", l.from(2)); b = portxy(objs(l.to(1)), "in", l.to(2)); end
    l.xx = [a(1); b(1)]; l.yy = [a(2); b(2)];
endfunction

scs_m = scicos_diagram();
scs_m.props.title = "GRAIL_system";
scs_m.props.tf = 8760 * 3600;
// [atol rtol ttol deltat scale solver hmax]; solver 0 = LSodar, hmax 60 s
scs_m.props.tol = [1e-6; 1e-6; 1e-10; 8760*3600 + 1; 0; 0; 60];
scs_m.props.context = [
  "// GRAIL parameters (SI, K) - values are overwritten per run by run_grail_xcos.sce"
  "A = 2*0.528; C = 33500*A; g2 = 2*(2*0.00275)*4180; cp = 4180;"
  "e0 = 0.6368; a1 = 2.104; a2 = 0;"
  "M = 100; UA = 1.5; Tset = 318.15; Tmax = 358.15;"
  "Tc0 = 293.15; Tt0 = 298.15;"
];

o = list();
o(1)  = blk("FROMWS_c", ["Vg"; "0"; "1"; "0"], 0, 640);
o(2)  = blk("FROMWS_c", ["Va"; "0"; "1"; "0"], 0, 500);
o(3)  = blk("FROMWS_c", ["Vm"; "0"; "1"; "0"], 0, 360);
o(4)  = blk("FROMWS_c", ["Vd"; "0"; "1"; "0"], 0, 220);
o(5)  = blk("INTEGRAL_m", ["Tc0"; "0"; "0"; "1e9"; "-1e9"], 560, 660);
o(6)  = blk("INTEGRAL_m", ["Tt0"; "0"; "0"; "1e9"; "-1e9"], 560, 300);
o(7)  = blk("EXPRESSION", ["2"; "u1-u2"; "0"], 760, 470);
o(8)  = blk("HYSTHERESIS", ["7"; "2"; "1"; "0"; "1"], 920, 470);
o(9)  = blk("EXPRESSION", ["2"; "u1*(u2<=Tmax)"; "1"], 1080, 470);
o(10) = blk("EXPRESSION", ["5"; "(A*(e0*u1-a1*(u3-u2)-a2*(u3-u2)^2)-g2*(u3-u4)*u5)/C"; "0"], 300, 620);
o(11) = blk("EXPRESSION", ["6"; "(g2*(u1-u2)*u3-UA*(u2-u4)-u6*min(1,(Tset-u5)/max(u2-u5,1e-9))*cp*(u2-u5))/(M*cp)"; "0"], 300, 260);
o(12) = blk("EXPRESSION", ["3"; "g2*(u1-u2)*u3"; "0"], 1320, 960);
o(13) = blk("EXPRESSION", ["2"; "UA*(u1-u2)"; "0"], 1320, 820);
o(14) = blk("EXPRESSION", ["3"; "u3*min(1,(Tset-u2)/max(u1-u2,1e-9))*cp*(u1-u2)"; "0"], 1320, 680);
o(15) = blk("EXPRESSION", ["3"; "min(u3*min(1,(Tset-u2)/max(u1-u2,1e-9))*cp*max(u1-u2,0),u3*cp*(Tset-u2))"; "0"], 1320, 540);
o(16) = blk("EXPRESSION", ["2"; "u2*cp*(Tset-u1)"; "0"], 1320, 400);
o(17) = blk("EXPRESSION", ["2"; "u1+0*u2"; "0"], 1320, 280);
o(18) = blk("MUX", "6", 1560, 560);
o(19) = blk("INTEGRAL_m", ["zeros(6,1)"; "0"; "0"; "1e18*ones(6,1)"; "-1e18*ones(6,1)"], 1680, 560);
o(20) = blk("SampleCLK", ["3600"; "0"], 1820, 700);
o(21) = blk("TOWS_c", ["8761"; "E"; "0"], 1820, 560);
o(22) = blk("MUX", "2", 1560, 120);
o(23) = blk("SampleCLK", ["60"; "0"], 1820, 260);
o(24) = blk("TOWS_c", ["525601"; "T"; "0"], 1820, 120);
lab = ["G_eff (W/m2)", "T_amb (K)", "T_mains (K)", "draw (kg/s)", "Tc collector", "Tt tank", "Tc-Tt", ..
       "pump hysteresis 7/2 K", "pump enable Tt<=Tmax", "dTc/dt", "dTt/dt", "Q collector->tank", "Q tank loss", ..
       "Q drawn from tank", "Q solar delivered", "Q hot-water load", "pump on", "mux", "energy integrals", ..
       "clock 3600 s", "to workspace E", "mux", "clock 60 s", "to workspace T"];
for i = 1:size(o)
    o(i).graphics.id = lab(i);
    scs_m.objs(i) = o(i);
end
// text annotations (TEXT_f) so the diagram reads without the script
notes = list( ..
  list("INPUTS (hourly): G_eff, T_amb, T_mains, m_draw", 0, 740), ..
  list("COLLECTOR node: C dTc/dt = A[eta0 G - a1(Tc-Ta) - a2(Tc-Ta)^2] - 2 mdot cp (Tc-Tt) pump", 280, 820), ..
  list("TANK: M cp dTt/dt = 2 mdot cp (Tc-Tt) pump - UA(Tt-Ta) - m_t cp (Tt-Tmains)", 280, 200), ..
  list("PUMP CONTROL: on at Tc-Tt > 7 K, off below 2 K, disabled above Tmax", 740, 560), ..
  list("HEAT RATES -> energy integrals -> workspace E (hourly)", 1320, 1080), ..
  list("Tc, Tt every 60 s -> workspace T", 1560, 200));
for k = 1:size(notes)
    tx = TEXT_f("define"); tx.graphics.exprs = [notes(k)(1); "2"; "1"]; tx.model.rpar = notes(k)(1);
    tx.graphics.orig = [notes(k)(2) notes(k)(3)]; tx.graphics.sz = [20 1];
    o($+1) = tx;
end
for i = 25:size(o), scs_m.objs(i) = o(i); end
// evaluate every block from its parameter strings and the context, so each block gets its real
// number of ports BEFORE the links are attached
needcompile = 4; %scicos_prob = %f; full_uids = [];
[%scicos_context, ierr] = script2var(scs_m.props.context, struct());
[scs_m, %cpr0, needcompile, ok] = do_eval(scs_m, list(), %scicos_context);
if ~ok then error("do_eval failed"); end
L = list();
// FROMWS_c: own event output feeds its event input (as in the library FROMWSB superblock)
for i = 1:4, L($+1) = evt(i, 1, i, 1); end
// state feedback
L($+1) = sig(10, 1, 5, 1);                    // dTc/dt -> Tc integrator
L($+1) = sig(11, 1, 6, 1);                    // dTt/dt -> Tt integrator
// pump logic
L($+1) = sig(5, 1, 7, 1); L($+1) = sig(6, 1, 7, 2);
L($+1) = sig(7, 1, 8, 1);
L($+1) = sig(8, 1, 9, 1); L($+1) = sig(6, 1, 9, 2);
// collector derivative: G, Ta, Tc, Tt, pump
L($+1) = sig(1, 1, 10, 1); L($+1) = sig(2, 1, 10, 2); L($+1) = sig(5, 1, 10, 3);
L($+1) = sig(6, 1, 10, 4); L($+1) = sig(9, 1, 10, 5);
// tank derivative: Tc, Tt, pump, Ta, Tmn, md
L($+1) = sig(5, 1, 11, 1); L($+1) = sig(6, 1, 11, 2); L($+1) = sig(9, 1, 11, 3);
L($+1) = sig(2, 1, 11, 4); L($+1) = sig(3, 1, 11, 5); L($+1) = sig(4, 1, 11, 6);
// heat rates
L($+1) = sig(5, 1, 12, 1); L($+1) = sig(6, 1, 12, 2); L($+1) = sig(9, 1, 12, 3);   // collector -> tank
L($+1) = sig(6, 1, 13, 1); L($+1) = sig(2, 1, 13, 2);                               // tank loss
L($+1) = sig(6, 1, 14, 1); L($+1) = sig(3, 1, 14, 2); L($+1) = sig(4, 1, 14, 3);   // energy drawn from tank
L($+1) = sig(6, 1, 15, 1); L($+1) = sig(3, 1, 15, 2); L($+1) = sig(4, 1, 15, 3);   // solar delivered
L($+1) = sig(3, 1, 16, 1); L($+1) = sig(4, 1, 16, 2);                               // hot-water load
L($+1) = sig(9, 1, 17, 1); L($+1) = sig(6, 1, 17, 2);                               // pump running
for k = 1:6, L($+1) = sig(11 + k, 1, 18, k); end
L($+1) = sig(18, 1, 19, 1); L($+1) = sig(19, 1, 21, 1); L($+1) = evt(20, 1, 21, 1);
L($+1) = sig(5, 1, 22, 1); L($+1) = sig(6, 1, 22, 2);
L($+1) = sig(22, 1, 24, 1); L($+1) = evt(23, 1, 24, 1);
// ---- attach links. A block output that feeds several inputs is sent through GOTO/FROM tags. ----
n0 = size(o); nobj = n0;
src = []; for k = 1:size(L), src = [src; L(k).from(1:2), L(k).ct(2)]; end
done = zeros(size(L), 1);
for k = 1:size(L)
    if done(k) then continue; end
    same = find(src(:, 1) == src(k, 1) & src(:, 2) == src(k, 2) & src(:, 3) == src(k, 3));
    lk = L(k);
    if size(same, "*") == 1 | lk.ct(2) == -1 then
        nobj = nobj + 1; scs_m.objs(nobj) = placed(lk, scs_m.objs); done(k) = 1;
        f = lk.from; t = lk.to;
        if lk.ct(2) == -1 then
            g = scs_m.objs(f(1)).graphics; g.peout(f(2)) = nobj; scs_m.objs(f(1)).graphics = g;
            g = scs_m.objs(t(1)).graphics; g.pein(t(2)) = nobj; scs_m.objs(t(1)).graphics = g;
        else
            g = scs_m.objs(f(1)).graphics; g.pout(f(2)) = nobj; scs_m.objs(f(1)).graphics = g;
            g = scs_m.objs(t(1)).graphics; g.pin(t(2)) = nobj; scs_m.objs(t(1)).graphics = g;
        end
    else
        // fan-out: source -> GOTO(tag); every destination <- its own FROM(tag) placed beside it
        // (standard Simulink/Xcos practice; the compiler turns the tags back into direct links)
        tagnames = ["G_eff", "T_amb", "T_mains", "m_draw", "Tc", "Tt", "", "", "pump"]; tag = tagnames(lk.from(1));
        f = lk.from; po = portxy(scs_m.objs(f(1)), "out", f(2));
        gt = GOTO("define"); gt.graphics.exprs = [tag; "1"]; gt.graphics.orig = po + [20 -10]; gt.graphics.sz = [2 1];
        gt.model.opar = list(tag); gt.model.ipar = 1; gt.graphics.id = tag;
        nobj = nobj + 1; ig = nobj; scs_m.objs(ig) = gt;
        nobj = nobj + 1; scs_m.objs(nobj) = placed(sig(f(1), f(2), ig, 1), scs_m.objs);
        g = scs_m.objs(f(1)).graphics; g.pout(f(2)) = nobj; scs_m.objs(f(1)).graphics = g;
        g = scs_m.objs(ig).graphics; g.pin(1) = nobj; scs_m.objs(ig).graphics = g;
        for j = 1:size(same, "*")
            t = L(same(j)).to; pi = portxy(scs_m.objs(t(1)), "in", t(2));
            fr = FROM("define"); fr.graphics.exprs = tag; fr.graphics.orig = pi + [-60 -10]; fr.graphics.sz = [2 1];
            fr.model.opar = list(tag); fr.graphics.id = tag;
            nobj = nobj + 1; ifr = nobj; scs_m.objs(ifr) = fr;
            nobj = nobj + 1; scs_m.objs(nobj) = placed(sig(ifr, 1, t(1), t(2)), scs_m.objs);
            g = scs_m.objs(ifr).graphics; g.pout(1) = nobj; scs_m.objs(ifr).graphics = g;
            g = scs_m.objs(t(1)).graphics; g.pin(t(2)) = nobj; scs_m.objs(t(1)).graphics = g;
            done(same(j)) = 1;
        end
    end
end
