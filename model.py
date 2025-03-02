# %%

# The markers "# %%" separate code blocks for execution (cells)
# Press shift-enter to exectute a cell and move to next cell
# Press ctrl-enter to exectute a cell and keep cursor at the position
# For more details, see https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter

# %%

from dataclasses import dataclass
from typing import List

from build123d import *
from ocp_vscode import (
    show,
    show_object,
    reset_show,
    set_port,
    set_defaults,
    get_defaults,
)
set_defaults(helper_scale=1, transparent=True)
set_port(3939)


def location_symbol(self, l=1) -> Compound:
    return Compound.make_triad(axes_scale=l).locate(self)

# %%
# Builder mode

@dataclass(frozen=True)
class ClearanceGap:
    tight: float = 0.127
    standard: float = 0.254
    loose: float = 0.508

@dataclass(frozen=True)
class Pcb:
    width: float = 117
    length: float = 101
    thickness: float = 1.68


hole_diameter = 3.50
hole_radius = hole_diameter / 2
hole_distance = 3.75

hole_location_x = Pcb.width / 2 - hole_distance
hole_location_y = Pcb.length / 2 - hole_distance
holes = [
    (hole_location_x, hole_location_y),
    (hole_location_x, -hole_location_y),
    (-hole_location_x, hole_location_y),
    (-hole_location_x, -hole_location_y),
]
with BuildPart() as pcb_bp:
    with BuildSketch() as pcb_sketch:
        Rectangle(Pcb.width, Pcb.length)

        with Locations(holes):
            Circle(radius=hole_diameter / 2, mode=Mode.SUBTRACT)
    extrude(amount=Pcb.thickness)

    joint_locations: List[Location] = [Location((hole[0], hole[1], 0) ) for hole in holes]

    RigidJoint(label="PCB hole front left", joint_location=joint_locations[3])
    RigidJoint(label="PCB hole front right", joint_location=joint_locations[1])
    RigidJoint(label="PCB hole rear left", joint_location=joint_locations[2])
    RigidJoint(label="PCB hole rear right", joint_location=joint_locations[0])

show(pcb_bp, render_joints=True, axes=True, axes0=True, grid=(True, True, True), transparent=True)



@dataclass(frozen=True)
class Hdmi:
    holder_thickness: float = 8
    adapter_width: float = 31.56
    narrow_width: float = 13.1
    narrow_length: float = 9
    holder_wall_thickness: float = 4
    holder_width: float = adapter_width + holder_wall_thickness
    holder_length: float = 52

with BuildPart() as hdmi_holder_bp:
    dir_down = Vector(0, 0, -1)

    # Base block
    with BuildSketch() as hdmi_holder_face:
        Rectangle(Hdmi.holder_width, Hdmi.holder_length)
    extrude(amount=Hdmi.holder_thickness)

    top = hdmi_holder_bp.faces().sort_by(Axis.Z)[-1]
    bottom = hdmi_holder_bp.faces().sort_by(Axis.Z)[0]
    front = hdmi_holder_bp.faces().sort_by(Axis.Y)[0]

    # Hollow
    hollow_extrude = 6
    with BuildSketch(top):
        Rectangle(Hdmi.adapter_width, Hdmi.holder_length)
    extrude(amount=-hollow_extrude, mode=Mode.SUBTRACT)

    # Narrowing the holder at the adapter's neck
    neck_pos = (0, 36.9 - Hdmi.holder_length / 2)
    neck_extrude = 3.4 + 2
    with BuildSketch(bottom.__neg__()):
        with Locations([neck_pos]):
            Rectangle(Hdmi.holder_width, Hdmi.narrow_length)
            Rectangle(Hdmi.narrow_width, Hdmi.narrow_length, mode=Mode.SUBTRACT)
    extrude(amount=neck_extrude)

    # Audio jack screw place
    @dataclass(frozen=True)
    class AudioJack:
        hole_width: float = 6.6
        hole_height: float = 26#13 # TODO confirm this, is it 13 or more?
        near_pcb_width: float = 2.76
    audiojack_offset_x = Hdmi.adapter_width / 2 - AudioJack.near_pcb_width - AudioJack.hole_width / 2
    audiojack_hdmi_distance_x = (Hdmi.adapter_width - AudioJack.near_pcb_width) / 2
    with BuildSketch(top):
        with Locations(
            [
                (
                    audiojack_offset_x,
                    - Hdmi.holder_length / 2,
                )
            ]
        ):
            Rectangle(AudioJack.hole_width, AudioJack.hole_height)
    extrude(until=bottom, dir=dir_down)


    @dataclass(frozen=True)
    class ScrewHolder:
        width: float = AudioJack.hole_width
        length: float = 20

    with BuildSketch() as hdmi_holder_screw_hole_block:
        with Locations(
            (
                -(Hdmi.adapter_width + ScrewHolder.width)/2,
                -(Hdmi.holder_length - ScrewHolder.length)/2
            )):
            Rectangle(ScrewHolder.width, ScrewHolder.length)
    extrude(amount=Hdmi.holder_thickness)

    @dataclass(frozen=True)
    class HdmiHolderScrewHole:
        radius: float = 1
        depth: float = 10

    with BuildSketch(front) as hdmi_holder_screw_holes:
        left_hole_location = Vector(-Hdmi.adapter_width/2 - ScrewHolder.width/2, 0)
        right_hole_location = Vector(Hdmi.adapter_width/2 - AudioJack.hole_width/2 - AudioJack.near_pcb_width, 0)
        with Locations([left_hole_location, right_hole_location]):
            Circle(radius=HdmiHolderScrewHole.radius)
    extrude(amount=-HdmiHolderScrewHole.depth, mode=Mode.SUBTRACT)

    RigidJoint(label="HDMI left hole", joint_location=Location((
        left_hole_location.X,
        -Hdmi.holder_length/2,
        Hdmi.holder_thickness/2
    )))

    RigidJoint(label="HDMI right hole", joint_location=Location((
        right_hole_location.X,
        -Hdmi.holder_length/2,
        Hdmi.holder_thickness/2
    )))

    hdmi_connector_offset_x = -(AudioJack.hole_width + AudioJack.near_pcb_width)/2
    RigidJoint(label="HDMI female connector", joint_location=Location((
        hdmi_connector_offset_x,
        -Hdmi.holder_length/2,
        Hdmi.holder_thickness/2
    )))



show(hdmi_holder_bp, render_joints=True)

# %%

case_inner_side_gap_to_pcb = 5
case_inner_width = Pcb.width + case_inner_side_gap_to_pcb
case_inner_length = Pcb.length + case_inner_side_gap_to_pcb
case_shell_thickness = 4
case_outer_width = case_inner_width + 2 * case_shell_thickness
case_outer_length = case_inner_length + 2 * case_shell_thickness

case_inner_bottom_gap_to_pcb = 5
case_inner_pcb_hole_pillar_height = case_inner_bottom_gap_to_pcb
case_inner_pcb_hole_pillar_radius = hole_radius + 2
case_inner_pcb_hole_pillar_hole_radius = hole_radius

case_outer_height = 50


with BuildPart() as case_bp:
    Box(case_outer_width, case_outer_length, case_outer_height)
    top_face = case_bp.faces().sort_by(Axis.Z)[-1]
    offset(amount=-case_shell_thickness, openings=top_face)


    # Bottom of the case.
    case_bottom_top_face = case_bp.faces().sort_by(Axis.Z)[1]

    # Extrude pillars for PCB holes.
    with BuildSketch(case_bottom_top_face):
        with Locations(holes):
            Circle(radius=case_inner_pcb_hole_pillar_radius)
            Circle(radius=case_inner_pcb_hole_pillar_hole_radius, mode=Mode.SUBTRACT)
    extrude(amount=case_inner_pcb_hole_pillar_height)

    asd = case_bp.faces(Select.LAST)
    case_bottom_top_face.center_location
    joint_locations: List[Location] = [Location(Vector(hole[0], hole[1], case_inner_pcb_hole_pillar_height) + case_bottom_top_face.center_location.position) for hole in holes]

    RigidJoint(label="PCB pillar front left", joint_location=joint_locations[3])
    RigidJoint(label="PCB pillar front right", joint_location=joint_locations[1])
    RigidJoint(label="PCB pillar rear left", joint_location=joint_locations[2])
    RigidJoint(label="PCB pillar rear right", joint_location=joint_locations[0])

    # Outer wall faces.
    case_front_wall_outer_face: Face = case_bp.faces().sort_by(Axis.Y)[0]
    case_back_wall_outer_face: Face = case_bp.faces().sort_by(Axis.Y)[-1]
    case_right_wall_outer_face: Face = case_bp.faces().sort_by(Axis.X)[-1]
    case_left_wall_outer_face: Face = case_bp.faces().sort_by(Axis.X)[0]

    case_front_wall_inner_face: Face = case_bp.faces().filter_by(Axis.Y).sort_by(Axis.Y)[1]
    case_back_wall_inner_face: Face = case_bp.faces().filter_by(Axis.Y).sort_by(-Axis.Y)[1]
    case_left_wall_inner_face: Face = case_bp.faces().filter_by(Axis.X).sort_by(Axis.X)[1]

    front_inner_face_plane: Plane = Plane(case_front_wall_inner_face).rotated((0,-90,0))
    back_inner_face_plane: Plane = Plane(case_back_wall_inner_face).rotated((0,90,0))
    left_inner_face_plane: Plane = Plane(case_left_wall_inner_face).rotated((-90,0,0))

    # RCA connector holes
    rca_port_diameter = 8.3
    rca_port_hole_diameter = rca_port_diameter + 1
    rca_port_distance = 22.1 - rca_port_diameter  # From centers of the ports
    rca_right_from_pcb = Vector(
        Pcb.width / 2 - (39.6 - rca_port_diameter / 2),
        -(12.2 - rca_port_diameter / 2 - Pcb.thickness / 2),
    )
    pcb_location_from_case_front_wall_inner_face = Vector(
        0,
        -case_outer_height/2 + case_shell_thickness + case_inner_pcb_hole_pillar_height + Pcb.thickness/2,
    )
    rca_right_location = -rca_right_from_pcb + pcb_location_from_case_front_wall_inner_face
    rca_video_locations = [
        rca_right_location,
        rca_right_location + Vector(rca_port_distance, 0),
        rca_right_location + Vector(rca_port_distance, 0) * 2,
    ]
    rca_audio_locations = [
        rca_right_location - Vector(rca_port_distance, 0),
        rca_right_location - Vector(rca_port_distance, 0) * 2,
    ]
    rca_audio_screw_hole_locations = [
        ShapeList(rca_audio_locations).center().add((0, 7, 0))
    ]
    rca_audio_screw_hole_radius = 1.5
    with BuildSketch(front_inner_face_plane):
        with Locations(rca_video_locations + rca_audio_locations):
            Circle(radius=rca_port_hole_diameter / 2)
        with Locations(rca_audio_screw_hole_locations):
            Circle(radius=rca_audio_screw_hole_radius)
    extrude(amount=-case_shell_thickness, mode=Mode.SUBTRACT)

    # VGA input connector hole
    vga_width = 31
    vga_height = 14.2 - Pcb.thickness
    vga_from_pcb_front = Vector(
        -(vga_width / 2 - 44.5),
        vga_height / 2 + Pcb.thickness / 2
    )
    vga_location = vga_from_pcb_front + pcb_location_from_case_front_wall_inner_face
    with BuildSketch(front_inner_face_plane) as la:
        with Locations([vga_location]):
            Rectangle(vga_width, vga_height)
    extrude(amount=-case_shell_thickness, mode=Mode.SUBTRACT)

    # Scart connector hole
    scart_width = 47.2
    scart_height = 16.4
    scart_ideal_distance_from_pcb_z = 20
    scart_screw_hole_diam = 2.4
    scart_screw_hole_distance_from_scart_side = 5.7
    scart_from_pcb_left = Vector(
        0,
        scart_ideal_distance_from_pcb_z
    )
    pcb_location_from_case_left_wall_inner_face = Vector(
        0,
        -case_outer_height/2 + case_shell_thickness + case_inner_pcb_hole_pillar_height + Pcb.thickness/2,
    )
    scart_location = scart_from_pcb_left + pcb_location_from_case_left_wall_inner_face

    scart_screw_hole_locations = [
        scart_location + Vector(6.0 +  scart_width / 2, 0, 0),
        scart_location - Vector(5.7 +  scart_width / 2, 0, 0),
    ]
    scart_screw_hole_radius=1.1

    with BuildSketch(left_inner_face_plane) as ll:
        with Locations([scart_location]):
            Rectangle(scart_width, scart_height)
        with Locations([scart_screw_hole_locations]):
            Circle(radius=scart_screw_hole_radius)
    extrude(amount=-case_shell_thickness, mode=Mode.SUBTRACT)

    # HDMI connector hole and screw holes
    @dataclass(frozen=True)
    class HdmiFemaleConnector:
        width = 14.0
        height = 4.55
        hole_width = width + 1
        hole_height = height + 1
        hole_distance_from_top = 4
        screw_hole_radius = HdmiHolderScrewHole.radius
        screw_hole_distance = audiojack_hdmi_distance_x
        offset_y_from_pcb = 28.1

    with BuildSketch(back_inner_face_plane) as hdmi_hole:
        # HDMI connector hole
        hdmi_connector_hole_from_pcb_back = Vector(
            0,
            HdmiFemaleConnector.offset_y_from_pcb
        )
        pcb_location_from_case_back_wall_inner_face = Vector(
            0,
            -case_outer_height/2 + case_shell_thickness + case_inner_pcb_hole_pillar_height + Pcb.thickness/2,
        )
        hdmi_connector_hole_location = hdmi_connector_hole_from_pcb_back + pcb_location_from_case_back_wall_inner_face
        with Locations([hdmi_connector_hole_location]):
            Rectangle(HdmiFemaleConnector.hole_width, HdmiFemaleConnector.hole_height)

        # HDMI connector screw holes
        hole_0_location = hdmi_connector_hole_location + Vector(-HdmiFemaleConnector.screw_hole_distance, 0)
        hole_1_location = hdmi_connector_hole_location + Vector(HdmiFemaleConnector.screw_hole_distance, 0)
        with Locations([hole_0_location, hole_1_location]):
            Circle(HdmiFemaleConnector.screw_hole_radius)
    extrude(amount=-case_shell_thickness, mode=Mode.SUBTRACT)

    hdmi_female_hole_location = Location(back_inner_face_plane.from_local_coords(hdmi_connector_hole_location))
    # Rotate hdmi hole by 180 degrees
    hdmi_female_hole_location.orientation = (0, 0, 180)
    RigidJoint(label="HDMI female hole", joint_location=hdmi_female_hole_location)
    # RigidJoint(label="HDMI screw hole 0", joint_location=Location(back_inner_face_plane.from_local_coords(hole_0_location)))
    # RigidJoint(label="HDMI screw hole 1", joint_location=Location(back_inner_face_plane.from_local_coords(hole_1_location)))

show(case_bp, hdmi_hole, back_inner_face_plane,
    # location_symbol(Location(front_inner_face_plane.from_local_coords(hdmi_connector_hole_location)), l=10),
    render_joints=True
     )
# %%

with BuildPart() as case_lid_bp:
    with BuildSketch(
        case_bp.faces().sort_by(Axis.Z)[0].__neg__().offset(case_outer_height)
    ):
        Rectangle(case_outer_width, case_outer_length)
    extrude(amount=case_shell_thickness)




# %%


case = case_bp.part
pcb = pcb_bp.part
hdmi_holder = hdmi_holder_bp.part

case.label="case"
pcb.color=Color(0x046307)
pcb.label="pcb"
hdmi_holder.label="hdmi_holder"
hdmi_holder.color=Color("orange")
case.joints["HDMI female hole"].connect_to(hdmi_holder.joints["HDMI female connector"])
# case.joints["HDMI screw hole 0"].connect_to(hdmi_holder.joints["HDMI right hole"])
# case.joints["HDMI screw hole 1"].connect_to(hdmi_holder.joints["HDMI right hole"])
case.joints["PCB pillar front left"].connect_to(pcb.joints["PCB hole front left"])

case_assembly = Compound(label="assembly", children=[
    case,
    hdmi_holder,
    pcb,
])
print(case_assembly.show_topology())




show(case_assembly, back_inner_face_plane, front_inner_face_plane, left_inner_face_plane, render_joints=True)
# %%
# show(pp)

for part_builder in [case_bp, hdmi_holder_bp]:
    export_stl(part_builder.part, f"{part_builder.part.label}.stl")


# %%
