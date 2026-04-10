$fn=60;
wheel_height = 60;
thickness = 4;
kerf = 0.5;
connect_hole_d = 2.5;
connect_d = 10;
rod_d = 4.5;

module interconnect_screws(){
    for (i = [0 : 4]) {
        angle = 360 / 4 * i;
        rotate(angle)
        translate([connect_d, 0])
        circle(d = connect_hole_d);
    }
}

module wheel(
    outer_d = 50,
    hole_d = 3.5,
    count = 10,
    edge_offset = 5
) {
    R_outer = outer_d / 2;
    R_holes = R_outer - edge_offset;
    difference() {
        circle(d = outer_d);
        group(){
          for (i = [0 : count-1]) {
            angle = 360 / count * i;
            rotate(angle)
            translate([R_holes, 0])
            circle(d = hole_d);
          }
          interconnect_screws();
          circle(d=rod_d);
        }
    }
}

module wheel_connect(){
    difference(){
        cylinder(r=connect_d+connect_hole_d, h=3);
        linear_extrude(10) interconnect_screws();
    }
}

module wheel_inner(){
    difference(){
        group(){
            wheel_connect();
            translate([0,0,3]) cylinder(r=connect_d-connect_hole_d, h=wheel_height-(2*3));
            translate([0,0,wheel_height-3]) wheel_connect();
        }
        cylinder(d=rod_d, h=wheel_height);
    }
}

module card(){
    card_y = 1.75*(wheel_height/2);
    card_x = wheel_height+(thickness*1.5);
    difference(){
        square([card_x, card_y]);
        group(){
            translate([0,2,0]) square([4, 20]);
            translate([card_x-4,2,0]) square([4, 20]);
        }
    }
}

module whole_wheel(){
linear_extrude(thickness) wheel(outer_d = 50, hole_d = 3.5,count = 20,edge_offset = 5);
translate([0,0,thickness]) wheel_inner();
translate([0,0,wheel_height+thickness]) linear_extrude(thickness) wheel(outer_d = 50, hole_d = 3.5,count = 20,edge_offset = 5);
}

module all(){
whole_wheel();
translate([(wheel_height/2)-9, -1, thickness/4]) rotate([0, -90,0]) linear_extrude(2) card();
translate([(wheel_height/2)-9-3, -5, thickness/4]) rotate([180, -90,0]) linear_extrude(2) card();
}

module space_wheel(){
    difference(){
        circle(d=connect_d+connect_hole_d);
        circle(d=rod_d);
    }
}

module case(){
    plast = 2.5;
    difference(){
        cube([wheel_height+30, 2* wheel_height+20, wheel_height+(6*thickness)]);
        group(){
            translate([-20,plast,plast]) cube([wheel_height+50-(2*plast), 2* wheel_height+20-(2*plast), wheel_height+(6*thickness)-(2*plast)]);
            translate([45,70, 0]) cylinder(h=200, d=rod_d+1);
            translate([wheel_height+25,15,12]) cube([5, 2* wheel_height-15, wheel_height]);
        }
    }
}

//wheel_inner();
//wheel(outer_d = 50, hole_d = 3.5,count = 20,edge_offset = 5);
//space_wheel();
//card();
translate([45,70,thickness*2]) all();
case();