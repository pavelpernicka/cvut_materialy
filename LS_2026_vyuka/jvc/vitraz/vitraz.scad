PETAL_COUNT = 7;
HEIGHT = 90;
WIDTH = 28;
BASE_WIDTH = 12;
TILT = 65;          // 0 = svisle nahoru, větší = víc ven
THICKNESS = 1;
BOTTOM_GAP = 2;

MODE = "layout";   // "preview" nebo "layout"

$fn = 80;

// -------------------------------------------------
// pomocné funkce
// -------------------------------------------------
function ring_radius(n, chord) = chord / (2 * sin(180 / n));
function pitch(base_w, gap) = base_w + gap;

// -------------------------------------------------
// 2D tvar lístku
// spodní střed je v [0,0], lístek roste do +Y
// -------------------------------------------------
module petal_2d(h, w, base_w) {
    polygon([
        [-base_w/2, 0],
        [ base_w/2, 0],
        [ w/2, h*0.42],
        [ 0, h],
        [-w/2, h*0.42]
    ]);
}

module smooth_petal(h, w, base_w) {
    offset(r=2)
        offset(delta=-2)
            petal_2d(h, w, base_w);
}

module petal_3d() {
    linear_extrude(height = THICKNESS)
        smooth_petal(HEIGHT, WIDTH, BASE_WIDTH);
}

// -------------------------------------------------
// jeden lístek
// -------------------------------------------------
// Lokální soustava před umístěním:
// - spodní střed je v [0,0,0]
// - šířka je v ose X
// - výška je v ose Y
//
// Postup:
// 1) naklopit kolem X => lístek se otevře ven
// 2) posunout na kružnici ve směru +Y
// 3) otočit kolem Z do správného azimutu
module placed_petal(a, R) {
    rotate([0,0,a])
        translate([0,R,0])
            rotate([-TILT,0,0])
                petal_3d();
}

module flower_preview() {
    R = ring_radius(PETAL_COUNT, pitch(BASE_WIDTH, BOTTOM_GAP));

    for (i = [0:PETAL_COUNT-1]) {
        placed_petal(i * 360 / PETAL_COUNT, R);
    }
}

module layout() {
    cols = 5;
    step_x = WIDTH + 15;
    step_y = HEIGHT + 15;

    for (i = [0:PETAL_COUNT-1]) {
        x = (i % cols) * step_x;
        y = -floor(i / cols) * step_y;
        translate([x, y])
            smooth_petal(HEIGHT, WIDTH, BASE_WIDTH);
    }
}

if (MODE == "preview") {
    flower_preview();
} else {
    layout();
}