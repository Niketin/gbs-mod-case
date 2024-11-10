# %%

# The markers "# %%" separate code blocks for execution (cells)
# Press shift-enter to exectute a cell and move to next cell
# Press ctrl-enter to exectute a cell and keep cursor at the position
# For more details, see https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter

# %%

from build123d import *
from ocp_vscode import (
    show,
    show_object,
    reset_show,
    set_port,
    set_defaults,
    get_defaults,
)

set_port(3939)


# %%
# Builder mode

pcb_width = 117
pcb_height = 101
pcb_thickness = 1.68

hole_diameter = 3.50
hole_radius = hole_diameter / 2
hole_distance = 3.75

hole_location_x = pcb_width / 2 - hole_distance
hole_location_y = pcb_height / 2 - hole_distance
holes = [
    (hole_location_x, hole_location_y),
    (hole_location_x, -hole_location_y),
    (-hole_location_x, hole_location_y),
    (-hole_location_x, -hole_location_y),
]
with BuildPart() as pcb:
    with BuildSketch() as bs:
        Rectangle(pcb_width, pcb_height)

        with Locations(holes):
            Circle(radius=hole_diameter / 2, mode=Mode.SUBTRACT)
    extrude(amount=pcb_thickness)

show(pcb, axes=True, axes0=True, grid=(True, True, True), transparent=True)

# %%

case_inner_side_gap_to_pcb = 5
case_inner_width = pcb_width + case_inner_side_gap_to_pcb
case_inner_height = pcb_height + case_inner_side_gap_to_pcb
case_shell_thickness = 5
case_outer_width = case_inner_width + 2 * case_shell_thickness
case_outer_height = case_inner_height + 2 * case_shell_thickness

case_inner_bottom_gap_to_pcb = 5
case_inner_pcb_hole_pillar_height = case_inner_bottom_gap_to_pcb
case_inner_pcb_hole_pillar_radius = hole_radius + 2
case_inner_pcb_hole_pillar_hole_radius = hole_radius

case_height = 50

with BuildPart() as case:
    # Bottom of the case.
    case_bottom_top_face = (
        pcb.faces().sort_by(Axis.Z)[0].offset(case_inner_pcb_hole_pillar_height)
    )
    with BuildSketch(case_bottom_top_face):
        Rectangle(case_outer_width, case_outer_height)
    extrude(amount=case_shell_thickness)

    # Extrude pillars for PCB holes.
    with BuildSketch(case_bottom_top_face):
        with Locations(holes):
            Circle(radius=case_inner_pcb_hole_pillar_radius)
            Circle(radius=case_inner_pcb_hole_pillar_hole_radius, mode=Mode.SUBTRACT)
    extrude(amount=case_inner_pcb_hole_pillar_height)

    # Extrude Walls.
    with BuildSketch(case_bottom_top_face):
        Rectangle(case_outer_width, case_outer_height)
        Rectangle(case_inner_width, case_inner_height, mode=Mode.SUBTRACT)
    wall_height_to_extrude = case_height - case_shell_thickness
    extrude(amount=-wall_height_to_extrude)

    # Outer wall faces.
    case_front_wall_outer_face = case.faces().sort_by(Axis.Y)[0]
    case_back_wall_outer_face = case.faces().sort_by(Axis.Y)[-1]
    case_right_wall_outer_face = case.faces().sort_by(Axis.X)[-1]
    case_left_wall_outer_face = case.faces().sort_by(Axis.X)[0]

    # RCA connector holes
    rca_port_diameter = 8.3
    rca_port_hole_diameter = rca_port_diameter + 1
    rca_port_distance = 22.1 - rca_port_diameter  # From centers of the ports
    rca_right_from_pcb = Vector(
        pcb_width / 2 - (39.6 - rca_port_diameter / 2),
        12.2 - rca_port_diameter / 2 - pcb_thickness / 2,
    )
    rca_video_locations = [
        rca_right_from_pcb,
        rca_right_from_pcb - Vector(rca_port_distance, 0),
        rca_right_from_pcb - Vector(rca_port_distance, 0) * 2,
    ]
    rca_audio_locations = [
        rca_right_from_pcb + Vector(rca_port_distance, 0),
        rca_right_from_pcb + Vector(rca_port_distance, 0) * 2,
    ]
    pcb_front_face = pcb.faces().sort_by(Axis.Y)[0]
    with BuildSketch(pcb_front_face):
        with Locations(rca_video_locations + rca_audio_locations):
            Circle(radius=rca_port_hole_diameter / 2)
    extrude(until=case_front_wall_outer_face, mode=Mode.SUBTRACT)

    # VGA input connector hole
    vga_width = 31
    vga_height = 14.2 - pcb_thickness
    vga_from_pcb_front = Vector(
        44.5 - vga_width / 2 - pcb_width / 2, pcb_thickness / 2 + vga_height / 2
    )
    with BuildSketch(pcb_front_face):
        with Locations([vga_from_pcb_front]):
            Rectangle(vga_width, vga_height)
    extrude(until=case_front_wall_outer_face, mode=Mode.SUBTRACT)

    # Scart connector hole
    #
    scart_width = 47.2
    scart_height = 16.5
    scart_screw_hole_diam = 2.5
    scart_screw_hole_distance_from_scart_side = 7.2 - scart_screw_hole_diam / 2
    scart_from_pcb_left = Vector(pcb_height / 2 - 45, 45)
    pcb_left_face = pcb.faces().sort_by(Axis.X)[0]
    with BuildSketch(pcb_left_face):
        with Locations([Vector(0, -25)]):
            Rectangle(scart_width, scart_height)
    extrude(until=case_left_wall_outer_face, mode=Mode.SUBTRACT)


with BuildPart() as case_lid:
    with BuildSketch(
        case.faces().sort_by(Axis.Z)[0].__neg__().offset(case_height)
    ):
        Rectangle(case_outer_width, case_outer_height)
    extrude(amount=case_shell_thickness)

hdmi_holder_thickness = 8
with BuildPart() as hdmi_holder:
    hdmi_width = 31.56
    hdmi_narrow_width = 13.1
    hdmi_narrow_height = 9
    dir_down = Vector(0, 0, -1)

    # Base block
    with BuildSketch():
        hdmi_holder_width = 36
        hdmi_holder_height = 52
        Rectangle(hdmi_holder_width, hdmi_holder_height)
    extrude(amount=hdmi_holder_thickness)

    top = hdmi_holder.faces().sort_by(Axis.Z)[-1]
    bottom = hdmi_holder.faces().sort_by(Axis.Z)[0]

    # Hollow
    hdmi_holder_hollow_extrude = 6
    with BuildSketch(top):
        Rectangle(hdmi_width, hdmi_holder_height)
    extrude(amount=-hdmi_holder_hollow_extrude, mode=Mode.SUBTRACT)

    # Narrowing the holder at the adapter's neck
    neck_pos = (0, 36.9 - hdmi_holder_height / 2)
    neck_extrude = 3.4 + 2
    with BuildSketch(bottom.__neg__()):
        with Locations([neck_pos]):
            Rectangle(hdmi_holder_width, hdmi_narrow_height)
            Rectangle(hdmi_narrow_width, hdmi_narrow_height, mode=Mode.SUBTRACT)
    extrude(amount=neck_extrude)

    # Audio jack screw place
    audio_jack_hole_width = 6.6
    audio_jack_hole_height = 13
    audio_jack_near_pcb_width = 2.76
    with BuildSketch(top):
        with Locations(
            [
                (
                    hdmi_holder_width / 2
                    - audio_jack_near_pcb_width
                    - audio_jack_hole_width / 2
                    - (hdmi_holder_width - hdmi_width) / 2,
                    -hdmi_holder_height / 2,
                )
            ]
        ):
            Rectangle(audio_jack_hole_width, audio_jack_hole_height)
    extrude(until=bottom, dir=dir_down)

with BuildPart() as hdmi_holder_plank:
    with BuildSketch():
        Rectangle(hdmi_width - 5, hdmi_narrow_height)
    extrude(amount=hdmi_holder_thickness - neck_extrude)


show(
    # [hdmi_holder, hdmi_holder_plank],
    [case, pcb]
    # axes=True,
    # axes0=True,
    # grid=(True, True, True),
    # transparent=True,
)

# %%
