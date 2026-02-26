size_x   = 100;
size_y   = 80;
size_z   = 40;
n_zubu_x = 6;
n_zubu_y = 5;
n_zubu_z = 3;
tloustka = 4;

module hrana_x(delka, n_zubu, posun_y) {
    if (n_zubu > 0) {
        krok = delka / (1 + 2 * n_zubu);
        for (i = [0 : n_zubu - 1])
            translate([krok + 2 * krok * i, posun_y, 0])
                cube([krok, tloustka, tloustka]);
    } else if (n_zubu < 0) {
        p = -n_zubu;
        krok = delka / (1 - 2 * n_zubu);
        for (i = [0 : p])
            translate([2 * krok * i, posun_y, 0])
                cube([krok, tloustka, tloustka]);
    }
}

module hrana_y(delka, n_zubu, posun_x) {
    if (n_zubu > 0) {
        krok = delka / (1 + 2 * n_zubu);
        for (i = [0 : n_zubu - 1])
            translate([posun_x, krok * (2 * i + 1), 0])
                cube([tloustka, krok, tloustka]);
    } else if (n_zubu < 0) {
        p = -n_zubu;
        krok = delka / (1 - 2 * n_zubu);
        for (i = [0 : p])
            translate([posun_x, krok * (2 * i), 0])
                cube([tloustka, krok, tloustka]);
    }
}

module strana(sx, sy, n_zubu_podel_x, n_zubu_podel_y) {
    union() {
        cube([sx, sy, tloustka]);
        hrana_x(sx, n_zubu_podel_x, -tloustka);
        hrana_x(sx, n_zubu_podel_x, sy);
        hrana_y(sy, n_zubu_podel_y, -tloustka);
        hrana_y(sy, n_zubu_podel_y, sx);
    }
}

module krabicka_slozena(
    size_x,
    size_y,
    size_z,
    n_zubu_x,
    n_zubu_y,
    n_zubu_z
) {
    size_z_vika = size_z + tloustka;

    // XY spodek
    strana(size_x, size_y,
           n_zubu_x, n_zubu_y);

    // XY vršek
    translate([0, 0, size_z_vika])
        strana(size_x, size_y,
               n_zubu_x, n_zubu_y);

    // XZ
    translate([0, -tloustka, size_z_vika])
        rotate([-90, 0, 0])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z);

    translate([0, size_y, size_z_vika])
        rotate([-90, 0, 0])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z);

    // ZY
    translate([0, 0, tloustka])
        rotate([0, -90, 0])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y);

    translate([size_x + tloustka, 0, tloustka])
        rotate([0, -90, 0])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y);
}

module krabicka_rozlozena(
    size_x,
    size_y,
    size_z,
    n_zubu_x,
    n_zubu_y,
    n_zubu_z,
    offset = 0
) {
    dx = size_x + tloustka + offset;
    dy = size_y + tloustka + offset;

    projection(cut = true)
    union() {
        // XY spodek
        translate([0, 0, -tloustka/2])
            strana(size_x, size_y,
                   n_zubu_x, n_zubu_y);

        // XY vršek
        translate([dx, 0, -tloustka/2])
            strana(size_x, size_y,
                   n_zubu_x, n_zubu_y);

        // XZ
        translate([0, size_y + tloustka + offset, -tloustka/2])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z);

        translate([dx, size_y + tloustka + offset, -tloustka/2])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z);

        // ZY
        translate([-size_z - tloustka - offset, 0, -tloustka/2])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y);

        translate([-size_z - tloustka - offset,
                   size_y + tloustka + offset,
                   -tloustka/2])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y);
    }
}

krabicka_slozena(
    size_x,
    size_y,
    size_z,
    n_zubu_x,
    n_zubu_y,
    n_zubu_z
);