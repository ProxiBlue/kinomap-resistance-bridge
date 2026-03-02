// Kinomap Resistance Bridge — 3D Printable Case
// Holds: Raspberry Pi (3B+/4 or Zero 2W) + 2-channel relay module
//
// Print settings:
//   Layer height: 0.2mm
//   Infill: 15-20%
//   Supports: No (designed to print without)
//   Material: PLA or PETG
//
// Usage:
//   1. Set rpi_model to "3" or "zero" below
//   2. Render and export STL
//   3. Print base and lid separately (set part = "base" or "lid")

/* [Configuration] */

// Which RPi model?
rpi_model = "3"; // ["3":RPi 3B+/4, "zero":RPi Zero 2W]

// Which part to render?
part = "base"; // ["base":Base, "lid":Lid, "both":Both (exploded)]

// Wall thickness (mm)
wall = 2.5;

// Floor/ceiling thickness (mm)
floor_t = 2.0;

// Standoff height for PCBs (mm)
standoff_h = 5.0;

// Standoff diameter (mm)
standoff_d = 5.5;

// Screw hole diameter — M2.5 (mm)
screw_d = 2.7;

// Cable hole diameter (mm)
cable_hole_d = 8.0;

// Vent slot width (mm)
vent_w = 2.0;

// Vent slot count per side
vent_count = 5;

// Lid snap-fit tolerance (mm)
tolerance = 0.3;

// Gap between RPi and relay module (mm)
component_gap = 5;

/* [Hidden] */
$fn = 30;

// ── Component Dimensions ──────────────────────────

// RPi 3B+/4
rpi3_pcb  = [85, 56];
rpi3_holes = [
    [3.5, 3.5],
    [3.5, 52.5],
    [61.5, 3.5],
    [61.5, 52.5],
];

// RPi Zero 2W
rpiz_pcb  = [65, 30];
rpiz_holes = [
    [3.5, 3.5],
    [3.5, 26.5],
    [61.5, 3.5],
    [61.5, 26.5],
];

// 2-channel relay module (typical)
relay_pcb = [50, 38];
relay_holes = [
    [3.5, 3.5],
    [3.5, 34.5],
    [46.5, 3.5],
    [46.5, 34.5],
];

// ── Derived Dimensions ────────────────────────────

rpi_pcb   = (rpi_model == "3") ? rpi3_pcb : rpiz_pcb;
rpi_holes = (rpi_model == "3") ? rpi3_holes : rpiz_holes;

// Interior dimensions
inner_w = rpi_pcb[0] + component_gap + relay_pcb[0];
inner_d = max(rpi_pcb[1], relay_pcb[1]);
inner_h = standoff_h + 25;  // PCB + tallest component clearance

// Outer dimensions
outer_w = inner_w + wall * 2;
outer_d = inner_d + wall * 2;
outer_h = inner_h + floor_t;

// Lid
lid_h = floor_t + 3;  // ceiling + snap lip

// RPi position (bottom-left of RPi PCB footprint inside case)
rpi_x = wall;
rpi_y = wall + (inner_d - rpi_pcb[1]) / 2;

// Relay position (to the right of RPi)
relay_x = wall + rpi_pcb[0] + component_gap;
relay_y = wall + (inner_d - relay_pcb[1]) / 2;

// ── Modules ───────────────────────────────────────

module standoff(pos, h=standoff_h, d=standoff_d, hole_d=screw_d) {
    translate([pos[0], pos[1], floor_t])
    difference() {
        cylinder(h=h, d=d);
        cylinder(h=h+1, d=hole_d);
    }
}

module vent_slots(length, count=vent_count, slot_w=vent_w) {
    spacing = length / (count + 1);
    for (i = [1:count]) {
        translate([0, i * spacing - slot_w/2, 0])
        cube([wall + 1, slot_w, inner_h * 0.5]);
    }
}

module cable_hole(pos, d=cable_hole_d) {
    translate(pos)
    rotate([0, 90, 0])
    cylinder(h=wall+2, d=d, center=true);
}

module base() {
    difference() {
        // Outer shell
        cube([outer_w, outer_d, outer_h]);

        // Hollow interior
        translate([wall, wall, floor_t])
        cube([inner_w, inner_d, inner_h + 1]);

        // Ventilation slots — left side
        translate([-0.5, wall, floor_t + inner_h * 0.3])
        vent_slots(inner_d);

        // Ventilation slots — right side
        translate([outer_w - wall - 0.5, wall, floor_t + inner_h * 0.3])
        vent_slots(inner_d);

        // Cable hole — back wall (for wires to bike buttons)
        cable_hole([outer_w - wall/2, outer_d * 0.3, floor_t + standoff_h + 8]);

        // Cable hole — back wall (for speed sensor wire)
        cable_hole([outer_w - wall/2, outer_d * 0.7, floor_t + standoff_h + 8]);

        // Cable hole — left wall (for RPi power USB)
        cable_hole([wall/2, outer_d * 0.5, floor_t + standoff_h + 5]);
    }

    // RPi standoffs
    for (hole = rpi_holes) {
        standoff([rpi_x + hole[0], rpi_y + hole[1]]);
    }

    // Relay module standoffs
    for (hole = relay_holes) {
        standoff([relay_x + hole[0], relay_y + hole[1]]);
    }

    // Lid snap-fit ledge (inner lip)
    translate([wall - 1, wall - 1, outer_h - 1.5])
    difference() {
        cube([inner_w + 2, inner_d + 2, 1.5]);
        translate([1.5, 1.5, -0.5])
        cube([inner_w - 1, inner_d - 1, 2.5]);
    }
}

module lid() {
    difference() {
        cube([outer_w, outer_d, lid_h]);

        // Snap-fit recess
        translate([wall - 1 + tolerance, wall - 1 + tolerance, -0.5])
        cube([inner_w + 2 - tolerance*2, inner_d + 2 - tolerance*2, 2]);
    }
}

// ── Render ────────────────────────────────────────

if (part == "base") {
    base();
} else if (part == "lid") {
    lid();
} else {
    // Exploded view
    base();
    translate([0, 0, outer_h + 15])
    lid();
}
