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

module tvar(velikost, typ) {
    if (typ == "ctverec") {
        square([velikost, velikost], center = true);
    }

    if (typ == "trojuhelnik") {
        polovina = velikost / 2;
        vyska = sqrt(3) / 2 * velikost;
        polygon(points = [
            [ 0,        vyska / 2 ],
            [ -polovina, -vyska / 2],
            [  polovina, -vyska / 2]
        ]);
    }

    if (typ == "kruh") {
        circle(r = velikost / 2, $fn = 50);
    }

    if (typ == "hvezda") {
        r1 = velikost / 2;
        r2 = velikost / 4;
        polygon(
            points = [
                for (i = [0 : 9])
                    let(uhel = i * 36,r = (i % 2 == 0) ? r1 : r2)
                    [ r * cos(uhel), r * sin(uhel) ]
            ]
        );
    }

    if (typ == "srdce") {
        r = velikost / 4;
        posun = r;
        union() {
            translate([-posun, 0]) circle(r = r, $fn = 40);
            translate([ posun, 0]) circle(r = r, $fn = 40);
            polygon(points = [
                [-2 * r, 0],
                [ 2 * r, 0],
                [ 0, -2.8 * r]
            ]);
        }
    }

    if (typ == "kosoctverec") {
        sirka  = velikost * 0.6;
        vyska  = velikost * 1.3;
        sirka_pul = sirka / 2;
        vyska_pul = vyska / 2;
        sirka_carky = velikost / 8;
        vyska_carky = velikost * 0.7;

        difference() {
            polygon(points = [
                [ 0,         vyska_pul],
                [ sirka_pul, 0        ],
                [ 0,        -vyska_pul],
                [-sirka_pul, 0        ]
            ]);
            square([sirka_carky, vyska_carky], center = true);
        }
    }
}


module tvar_3d(sx, sy, typ) {
    velikost = min(sx, sy) / 3;
    translate([sx / 2, sy / 2, 0])
        linear_extrude(height = tloustka + 0.2)
            tvar(velikost, typ);
}

module strana(sx, sy, n_zubu_podel_x, n_zubu_podel_y, typ_tvaru = "none") {
    union() {
        if (typ_tvaru == "none") {
            cube([sx, sy, tloustka]);
        } else {
            difference() {
                cube([sx, sy, tloustka]);
                tvar_3d(sx, sy, typ_tvaru);
            }
        }

        hrana_x(sx, n_zubu_podel_x, -tloustka);
        hrana_x(sx, n_zubu_podel_x, sy);

        hrana_y(sy, n_zubu_podel_y, -tloustka);
        hrana_y(sy, n_zubu_podel_y, sx);
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
    n_zubu_z
) {
    size_z_vika = size_z + tloustka;

    // XY spodek
    color(random_color())
    strana(size_x, size_y,
           n_zubu_x, n_zubu_y,
           "ctverec");

    // XY vršek
    color(random_color())
    translate([0, 0, size_z_vika])
        strana(size_x, size_y,
               n_zubu_x, n_zubu_y,
               "kruh");

    // XZ předek
    color(random_color())
    translate([0, -tloustka, size_z_vika])
        rotate([-90, 0, 0])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z,
                   "trojuhelnik");

    // XZ zadek
    color(random_color())
    translate([0, size_y, size_z_vika])
        rotate([-90, 0, 0])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z,
                   "hvezda");

    // ZY levý
    color(random_color())
    translate([0, 0, tloustka])
        rotate([0, -90, 0])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y,
                   "srdce");

    // ZY pravý
    color(random_color())
    translate([size_x + tloustka, 0, tloustka])
        rotate([0, -90, 0])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y,
                   "kosoctverec");
}

module krabicka_rozlozena(
    size_x,
    size_y,
    size_z,
    n_zubu_x,
    n_zubu_y,
    n_zubu_z,
    offset = 10
) {
    dx = size_x + tloustka + offset;
    dy = size_y + tloustka + offset;

    projection(cut = true)
    union() {
        // XY spodek
        translate([0, 0, -tloustka/2])
            strana(size_x, size_y,
                   n_zubu_x, n_zubu_y,
                   "ctverec");

        // XY vršek
        translate([dx, 0, -tloustka/2])
            strana(size_x, size_y,
                   n_zubu_x, n_zubu_y,
                   "kruh");

        // XZ předek
        translate([0, size_y + tloustka + offset, -tloustka/2])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z,
                   "trojuhelnik");

        // XZ zadek
        translate([dx, size_y + tloustka + offset, -tloustka/2])
            strana(size_x, size_z,
                   -n_zubu_x, n_zubu_z,
                   "hvezda");

        // ZY levý
        translate([-size_z - tloustka - offset, 0, -tloustka/2])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y,
                   "srdce");

        // ZY pravý
        translate([-size_z - tloustka - offset,
                   size_y + tloustka + offset,
                   -tloustka/2])
            strana(size_z, size_y,
                   -n_zubu_z, -n_zubu_y,
                   "kosoctverec");
    }
}

size_x   = 100;
size_y   = 100;
size_z   = 100;
n_zubu_x = 4;
n_zubu_y = 4;
n_zubu_z = 4;
tloustka = 4;

krabicka_rozlozena(
    size_x,
    size_y,
    size_z,
    n_zubu_x,
    n_zubu_y,
    n_zubu_z,
    4.001
);