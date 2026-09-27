function X = grail_sim_expressions(p)
% GRAIL_SIM_EXPRESSIONS  The equations of every Fcn block in the GRAIL Simulink model.
%
% This is the ONLY place the model equations are written. build_grail_simulink.m puts these
% strings into Simulink Fcn blocks, and test_expressions_octave.m evaluates the very same strings
% in GNU Octave to check them against the Xcos and Octave results.
%
% Fcn-block syntax is used: the block input is the vector u, its elements are u(1), u(2), ...
% Only operators and functions that the Simulink Fcn block accepts are used: + - * / , relational
% operators and abs(). min and max are therefore written with abs():
%     min(a,b) = (a+b-abs(a-b))/2        max(a,b) = (a+b+abs(a-b))/2
% Parameter values are written into the strings as numbers (17 significant digits), so the model
% does not depend on workspace variables. SI units, temperatures in kelvin.
%
% p fields: A (m2), C (J/K), g2 (W/K, = 2*mdot*cp), cp (J/kgK), e0, a1 (W/m2K), a2 (W/m2K2),
%           M (kg), UA (W/K), Tset (K), Tmax (K)

n = @(v) sprintf('%.17g', v);
mn = @(a, b) ['(((' a ')+(' b ')-abs((' a ')-(' b ')))/2)'];   % min(a,b), fully bracketed
mx = @(a, b) ['(((' a ')+(' b ')+abs((' a ')-(' b ')))/2)'];   % max(a,b), fully bracketed

% mixing valve: fraction of the draw taken from the tank, min(1, (Tset-Tmains)/max(Tt-Tmains,1e-9))
frac = @(Tt, Tmn) mn('1', ['(' n(p.Tset) '-' Tmn ')/' mx([Tt '-' Tmn], '1e-9')]);

% ---- pump control chain -------------------------------------------------------------------
X.dT      = 'u(1)-u(2)';                                    % u = [Tc; Tt]      -> Relay
X.pump    = ['u(1)*(u(2)<=' n(p.Tmax) ')'];                 % u = [demand; Tt]  -> pump 0/1

% ---- state derivatives ----------------------------------------------------------------------
% collector node: C dTc/dt = A[e0 G - a1 (Tc-Ta) - a2 (Tc-Ta)^2] - g2 (Tc-Tt) pump
% u = [G_eff; T_amb; Tc; Tt; pump]
X.dTc = ['(' n(p.A) '*(' n(p.e0) '*u(1)-' n(p.a1) '*(u(3)-u(2))-' n(p.a2) ...
         '*(u(3)-u(2))*(u(3)-u(2)))-' n(p.g2) '*(u(3)-u(4))*u(5))/' n(p.C)];
% tank: M cp dTt/dt = g2 (Tc-Tt) pump - UA (Tt-Ta) - m_t cp (Tt-Tmains)
% u = [Tc; Tt; pump; T_amb; T_mains; m_draw]
X.dTt = ['(' n(p.g2) '*(u(1)-u(2))*u(3)-' n(p.UA) '*(u(2)-u(4))-u(6)*' frac('u(2)', 'u(5)') ...
         '*' n(p.cp) '*(u(2)-u(5)))/' n(p.M * p.cp)];

% ---- heat rates (W) that are integrated into annual energies ---------------------------------
X.Q_coll  = [n(p.g2) '*(u(1)-u(2))*u(3)'];                                   % u = [Tc; Tt; pump]
X.Q_loss  = [n(p.UA) '*(u(1)-u(2))'];                                        % u = [Tt; T_amb]
X.Q_draw  = ['u(3)*' frac('u(1)', 'u(2)') '*' n(p.cp) '*(u(1)-u(2))'];       % u = [Tt; T_mains; m_draw]
X.Q_solar = mn(['u(3)*' frac('u(1)', 'u(2)') '*' n(p.cp) '*' mx('u(1)-u(2)', '0')], ...
               ['u(3)*' n(p.cp) '*(' n(p.Tset) '-u(2))']);                    % u = [Tt; T_mains; m_draw]
X.Q_load  = ['u(2)*' n(p.cp) '*(' n(p.Tset) '-u(1))'];                       % u = [T_mains; m_draw]
X.pump_on = 'u(1)';                                                          % u = pump (seconds)
end
