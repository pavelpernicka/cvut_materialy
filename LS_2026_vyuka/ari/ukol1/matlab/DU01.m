%% 3a - analytická podmínka rovnovážného pracovního bodu systému
syms w0 F0 real

v0 = 0;

eq1 = -5*v0 + w0 + 0.1*abs(F0) == 0;
eq2 = v0 - w0 == 0;

sol = solve([eq1, eq2],[w0, F0])

%%% 3b - linearizace v P
%% i - se statickou nelinearitou
clear; clc;

syms v w F real

% nelinearni model
f1 = -5*v + w + 0.1*abs(F);
f2 = v - w;
f = [f1; f2];

% Jacobiany
A_sym = jacobian(f, [v w]);
B_sym = jacobian(f, F);

% pracovni bod
v0 = 0;
w0 = 0;
F0 = 0;

% dosazeni
A = double(subs(A_sym, {v,w,F}, {v0,w0,F0}));

% derivace abs(F) v nule neni definovana, tak berem nulu
B = [0; 0];

C = [1 0];
D = 0;

A
B
C
D

%% ii - bez staticke nelinearity
clear; clc;

syms v w F real

% bez abs
f1 = -5*v + w + 0.1*F;
f2 = v - w;
f = [f1; f2];

% Jacobiany
A_sym = jacobian(f, [v w]);
B_sym = jacobian(f, F);

% pracovni bod
v0 = 0;
w0 = 0;
F0 = 0;

% dosazeni
A = double(subs(A_sym, {v,w,F}, {v0,w0,F0}));
B = double(subs(B_sym, {v,w,F}, {v0,w0,F0}));
C = [1 0];
D = 0;

A
B
C
D

%% 3c - Porovnejte odezvu linearizovaného modelu s původním modelem. Diskutujte vhodný tvar signálu pro validaci linearizace systému
clear; clc; close all;

% Parametry simulace
Tend = 10;
tspan = [0 Tend];
F_amp = 5;

% nelinearni model
f_nl = @(t,x) [
    -5*x(1) + x(2) + 0.1*abs(F_amp);
     x(1) - x(2)
];

[t_nl, x_nl] = ode45(f_nl, tspan, [0;0]);
v_nl = x_nl(:,1);

% linearni model se statickou nelinearitou - B=0

A = [-5 1; 1 -1];
B_i = [0;0];
C = [1 0];
D = 0;

sys_i = ss(A,B_i,C,D);

t_lin = linspace(0,Tend,1000);
u = F_amp*ones(size(t_lin));

v_lin_i = lsim(sys_i,u,t_lin);

% linearni model bez staticke nelinearity B = 0.1

B_ii = [0.1;0];
sys_ii = ss(A,B_ii,C,D);

v_lin_ii = lsim(sys_ii,u,t_lin);

% i - graf
figure(1); clf;
plot(t_nl, v_nl,'LineWidth',1.6); hold on;
grid on;

xlabel('čas [s]');
ylabel('v(t)');
%legend('výstup','Location','best');

set(gcf, 'Units', 'centimeters', 'Position', [3 3 14 9]);
set(gcf,'Renderer','painters');
exportgraphics(gcf,'../tex/img/linearizace_i.pdf','ContentType','vector');

% ii - graf
figure(2); clf;
plot(t_nl, v_nl,'LineWidth',1.6); hold on;grid on;

xlabel('čas [s]');
ylabel('v(t)');
%legend('výstup','Location','best');

set(gcf, 'Units', 'centimeters', 'Position', [3 3 14 9]);
set(gcf,'Renderer','painters');
exportgraphics(gcf,'../tex/img/linearizace_ii.pdf','ContentType','vector');

%% 4a - analytická podmínka rovnovážného pracovního bodu systému pro v0 = 10 m/s
syms v0 w0 F0 real

v0 = 10;

eq1 = -5*v0 + w0 + 0.1*abs(F0) == 0;
eq2 = v0 - w0 == 0;

sol_10 = solve([eq1, eq2],[w0, F0],'Real',true)

w0_10 = double(sol_10.w0)   % vyjde 10
F0_10 = double(sol_10.F0)   % vyjdou dve hodnoty ±400, zvolime F0 = 400

% budeme pracovat s kladnym momentem:
F0_10 = 400;

% 4b - linearizace v pracovním bodě v0 = 10 m/s

%% 4b-i) Uvažujte statickou nelinearitu na vstupu systému
clear; clc;

syms v w F real

% nelineární model s abs(F)
f1 = -5*v + w + 0.1*abs(F);
f2 = v - w;
f  = [f1; f2];

A_sym = jacobian(f, [v w]);
B_sym = jacobian(f, F);

v0 = 10;
w0 = 10;
F0 = 400;    % z 4a (kladný moment)

A_i_10  = double(subs(A_sym, {v,w,F}, {v0,w0,F0}));
B_i_10  = double(subs(B_sym, {v,w,F}, {v0,w0,F0}));   % = [0.1; 0]
C_i_10  = [1 0];
D_i_10  = 0;

A_i_10
B_i_10
C_i_10
D_i_10

%% 4b-ii) Neuvažujte statickou nelinearitu na vstupu systému
clear; clc;

syms v w F real

% dynamická část bez abs(F)
f1 = -5*v + w + 0.1*F;
f2 = v - w;
f  = [f1; f2];

A_sym = jacobian(f, [v w]);
B_sym = jacobian(f, F);

v0 = 10;
w0 = 10;
F0 = 400;

A_ii_10 = double(subs(A_sym, {v,w,F}, {v0,w0,F0}));
B_ii_10 = double(subs(B_sym, {v,w,F}, {v0,w0,F0}));   % opět [0.1; 0]
C_ii_10 = [1 0];
D_ii_10 = 0;

A_ii_10
B_ii_10
C_ii_10
D_ii_10

%% 4c - Porovnání odezvy v pracovním bodě v0 = 10 m/s
% (lineární vs nelineární model)

clear; clc; close all;

% pracovní bod
v0 = 10;
w0 = 10;
F0 = 400;

% parametry simulace
Tend   = 10;
tspan  = [0 Tend];
dF     = 5;               % malý skok kolem pracovního bodu
F_fun  = @(t) F0 + dF;     % jednoduchý skok F(t) = F0 + dF

% nelineární model
f_nl_10 = @(t,x) [
    -5*x(1) + x(2) + 0.1*abs(F_fun(t));
     x(1) - x(2)
];

% simulace nelineárního systému z pracovního bodu
[t_nl_10, x_nl_10] = ode45(f_nl_10, tspan, [v0; w0]);
v_nl_10 = x_nl_10(:,1);

% lineární model – v tomto pracovním bodě jsou varianty i) a ii) stejné
A = [-5 1; 1 -1];
B = [0.1; 0];
C = [1 0];
D = 0;

sys_10 = ss(A,B,C,D);

t_lin_10 = linspace(0,Tend,1000);
F_vec    = F0 + dF*ones(size(t_lin_10));   % skutečný vstup
u_tilde  = F_vec - F0;                     % odchylka vstupu delta F

% simulace lineárního modelu v odchylkách
v_tilde_10 = lsim(sys_10, u_tilde, t_lin_10);
v_lin_10   = v0 + v_tilde_10;             % zpátky do absolutních hodnot

figure(3); clf;
plot(t_nl_10, v_nl_10,'LineWidth',1.6);
grid on;

xlabel('čas [s]');
ylabel('v(t)');
set(gcf,'Units','centimeters','Position',[3 3 14 9]);
set(gcf,'Renderer','painters');
exportgraphics(gcf,'../tex/img/linearizace2_i.pdf','ContentType','vector');
figure(4); clf;
plot(t_lin_10, v_lin_10,'LineWidth',1.6);
grid on;

xlabel('čas [s]');
ylabel('v(t)');
set(gcf,'Units','centimeters','Position',[3 3 14 9]);
set(gcf,'Renderer','painters');
exportgraphics(gcf,'../tex/img/linearizace2_ii.pdf','ContentType','vector');
