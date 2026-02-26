%% Ukol 2.3
t = linspace(0,5,2000);

x1 = exp(-3*t) .* (2*cos(2*t) - 3*sin(2*t));
x2 = -0.5 * exp(-3*t) .* sin(2*t);

figure(1); clf;

plot(t, x1, 'LineWidth', 1.3); hold on;
plot(t, x2, '--', 'LineWidth', 1.3);

grid on;

xlabel('$t$ [s]', 'Interpreter', 'latex');
ylabel('Amplituda $x_1(t),\,x_2(t)$', 'Interpreter', 'latex');
legend({'$x_1(t)$', '$x_2(t)$'}, ...
       'Interpreter', 'latex', ...
       'Location', 'best');

set(gcf, 'Units', 'centimeters', 'Position', [3 3 14 9]);

set(gcf, 'Renderer', 'painters');

exportgraphics(gcf, '../tex/img/ukol2_x1x2.pdf', 'ContentType', 'vector');

%% Ukol 7 – Diskretizace

clc; clear; close all;

% spojity system
s = tf('s');
G = (s - 3) / ((s + 1)*(s + 7));

% periody vzorkovani
T1 = 0.05;      % dobra
T2 = 1.0;       % opravdu spatna

% diskretizace
Gd1 = c2d(G, T1, 'zoh');
Gd2 = c2d(G, T2, 'zoh');

T_end = 30;
f_in  = 0.2;

t_cont = linspace(0, T_end, 8000);
u_cont = sin(2*pi*f_in*t_cont);
y_cont = lsim(G, u_cont, t_cont);

idx = t_cont >= 10;
t_plot = t_cont(idx);
y_plot = y_cont(idx);

% dobra perioda

t1 = 0:T1:T_end;
u1 = sin(2*pi*f_in*t1);
y1 = lsim(Gd1, u1, t1);

figure(1); clf;
plot(t_plot, y_plot, 'LineWidth', 1.5); hold on;
stairs(t1(t1>=10), y1(t1>=10), 'LineWidth', 1.2);
grid on;

xlabel('čas [s]');
ylabel('amplituda');
legend('Spojitý systém', ...
       sprintf('Diskrétní systém (T = %.2f s)', T1), ...
       'Location','northeast');

xlim([10 30]);

set(gcf,'Units','centimeters','Position',[3 3 14 8]);
set(gcf,'Renderer','painters');
exportgraphics(gcf,'../tex/img/ukol7_vhodna.pdf','ContentType','vector');

% spatna perioda

t2 = 0:T2:T_end;
u2 = sin(2*pi*f_in*t2);
y2 = lsim(Gd2, u2, t2);

figure(2); clf;
plot(t_plot, y_plot, 'LineWidth', 1.5); hold on;
stairs(t2(t2>=10), y2(t2>=10), 'LineWidth', 1.2);
grid on;

xlabel('čas [s]');
ylabel('amplituda');
legend('Spojitý systém', ...
       sprintf('Diskrétní systém (T = %.1f s)', T2), ...
       'Location','northeast');

xlim([10 30]);

set(gcf,'Units','centimeters','Position',[3 3 14 8]);
set(gcf,'Renderer','painters');
exportgraphics(gcf,'../tex/img/ukol7_nevhodna.pdf','ContentType','vector');
