module hrana_x(delka, n_zubu, posun_y, kerf = 0) {
    if (n_zubu > 0) {
        krok = delka / (1 + 2 * n_zubu);
        tooth_len = krok + kerf;

        for (i = [0 : n_zubu - 1])
            translate([krok + 2 * krok * i - kerf / 2, posun_y, 0])
                cube([tooth_len, tloustka, tloustka]);

    } else if (n_zubu < 0) {
        p = -n_zubu;
        krok = delka / (1 - 2 * n_zubu); 

        tooth_len = krok;

        for (i = [0 : p])
            translate([2 * krok * i, posun_y, 0])
                cube([tooth_len, tloustka, tloustka]);
    }
}

module hrana_y(delka, n_zubu, posun_x, kerf = 0) {
    if (n_zubu > 0) {
        krok = delka / (1 + 2 * n_zubu);
        tooth_len = krok + kerf;

        for (i = [0 : n_zubu - 1])
            translate([posun_x, krok * (2 * i + 1) - kerf / 2, 0])
                cube([tloustka, tooth_len, tloustka]);

    } else if (n_zubu < 0) {
        p = -n_zubu;
        krok = delka / (1 - 2 * n_zubu);

        tooth_len = krok;

        for (i = [0 : p])
            translate([posun_x, krok * (2 * i), 0])
                cube([tloustka, tooth_len, tloustka]);
    }
}

module strana(
    sx,
    sy,
    n_zubu_podel_x,
    n_zubu_podel_y,
    kerf = 0
) {
    union() {
        cube([sx, sy, tloustka]);

        hrana_x(sx, n_zubu_podel_x, -tloustka, kerf);
        hrana_x(sx, n_zubu_podel_x, sy,        kerf);

        hrana_y(sy, n_zubu_podel_y, -tloustka, kerf);
        hrana_y(sy, n_zubu_podel_y, sx,        kerf);
    }
}

function random_color() =
    concat(
        rands(0,1,3, floor(rands(0,1000000,1)[0])),
        [0.8]
    );

module krabicka_slozena(
    size_x,
    size_y,
    size_z,
    n_zubu_x,
    n_zubu_y,
    n_zubu_z,
    kerf = 0
) {
    size_z_vika = size_z + tloustka;

    // XY spodek
    color(random_color())
        strana(size_x, size_y,
               n_zubu_x, n_zubu_y,
               kerf);

    // XY vršek
    color(random_color())
    translate([0, 0, size_z_vika])
        strana(size_x, size_y,
               n_zubu_x, n_zubu_y,
               kerf);

    // XZ předek
    color(random_color())
    translate([0, -tloustka, size_z_vika])
        rotate([-90, 0, 0])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z,
                   kerf);

    // XZ zadek
    color(random_color())
    translate([0, size_y, size_z_vika])
        rotate([-90, 0, 0])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z,
                   kerf);

    // ZY levý
    color(random_color())
    translate([0, 0, tloustka])
        rotate([0, -90, 0])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y,
                   kerf);

    // ZY pravý
    color(random_color())
    translate([size_x + tloustka, 0, tloustka])
        rotate([0, -90, 0])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y,
                   kerf);
}

module krabicka_rozlozena(
    size_x,
    size_y,
    size_z,
    n_zubu_x,
    n_zubu_y,
    n_zubu_z,
    offset = 10,
    kerf = 0
) {
    dx = size_x + tloustka + offset;
    dy = size_y + tloustka + offset;

    projection(cut = true)
    union() {
        // XY spodek
        translate([0, 0, -tloustka/2])
            strana(size_x, size_y,
                   n_zubu_x, n_zubu_y,
                   kerf);

        // XY vršek
        translate([dx, 0, -tloustka/2])
            strana(size_x, size_y,
                   n_zubu_x, n_zubu_y,
                   kerf);

        // XZ předek
        translate([0, size_y + tloustka + offset, -tloustka/2])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z,
                   kerf);

        // XZ zadek
        translate([dx, size_y + tloustka + offset, -tloustka/2])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z,
                   kerf);

        // ZY levý
        translate([-size_z - tloustka - offset, 0, -tloustka/2])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y,
                   kerf);

        // ZY pravý
        translate([-size_z - tloustka - offset,
                   size_y + tloustka + offset,
                   -tloustka/2])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y,
                   kerf);
    }
}

size_x   = 100;
size_y   = 100;
size_z   = 100;
n_zubu_x = 4;
n_zubu_y = 4;
n_zubu_z = 4;
tloustka = 4;
kerf = 0.5;

krabicka_slozena(
    size_x,
    size_y,
    size_z,
    n_zubu_x,
    n_zubu_y,
    n_zubu_z,
    4,
    kerf
);