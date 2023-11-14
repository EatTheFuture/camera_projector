#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

bl_info = {
    "name": "Camera Projector",
    "version": (0, 1, 0),
    "author": "Nathan Vegdahl, Ian Hubert",
    "blender": (3, 0, 0),
    "description": "Project textures from perspective cameras accurately.",
    "location": "Camera properties",
    # "doc_url": "",
    "category": "Shading / Texturing",
}

import math

import bpy


#========================================================


# Takes a camera object, and ensures there is a node group for
# projecting textures from that camera.
#
# It will create it if it doesn't exist, and returns the group.
def ensure_camera_project_group(camera, default_aspect=1.0):
    name = "Camera Project | " + camera.name

    # Fetch or create group.
    group = None
    if name in bpy.data.node_groups:
        group = bpy.data.node_groups[name]
    else:
        group = bpy.data.node_groups.new(name, type='ShaderNodeTree')

    # Clear all nodes, to start from a clean slate.
            
    for node in group.nodes:
        group.remove(node)

    # Create the group inputs and outputs.
    if not "Aspect Ratio" in group.interface.items_tree:
        group.interface.new_socket(name="Aspect Ratio", socket_type="NodeSocketFloat", in_out='INPUT')
        group.interface.items_tree['Aspect Ratio'].default_value = default_aspect
    if not "Rotation" in group.interface.items_tree:
        group.interface.new_socket(name="Rotation", socket_type="NodeSocketFloat", in_out='INPUT')
    if not "Loc X" in group.interface.items_tree:
        group.interface.new_socket(name="Loc X", socket_type="NodeSocketFloat", in_out='INPUT')
    if not "Loc Y" in group.interface.items_tree:
        group.interface.new_socket(name="Loc Y", socket_type="NodeSocketFloat", in_out='INPUT')
    if not "Vector" in group.interface.items_tree:
        group.interface.new_socket(name="Vector", socket_type="NodeSocketVector", in_out='OUTPUT')

    #-------------------
    # Create the nodes.

    camera_transform = group.nodes.new(type='ShaderNodeTexCoord')
    lens = group.nodes.new(type='ShaderNodeValue')
    sensor_width = group.nodes.new(type='ShaderNodeValue')
    lens_shift_x = group.nodes.new(type='ShaderNodeValue')
    lens_shift_y = group.nodes.new(type='ShaderNodeValue')

    zoom_1 = group.nodes.new(type='ShaderNodeMath')
    zoom_2 = group.nodes.new(type='ShaderNodeMath')
    lens_shift_1 = group.nodes.new(type='ShaderNodeCombineXYZ')
    to_radians = group.nodes.new(type='ShaderNodeMath')
    user_location = group.nodes.new(type='ShaderNodeCombineXYZ')

    perspective_1 = group.nodes.new(type='ShaderNodeSeparateXYZ')
    perspective_2 = group.nodes.new(type='ShaderNodeMath')
    perspective_3 = group.nodes.new(type='ShaderNodeMath')
    perspective_4 = group.nodes.new(type='ShaderNodeCombineXYZ')
    zoom_3 = group.nodes.new(type='ShaderNodeVectorMath')
    lens_shift_2 = group.nodes.new(type='ShaderNodeVectorMath')

    user_translate = group.nodes.new(type='ShaderNodeVectorMath')
    user_rotate = group.nodes.new(type='ShaderNodeVectorRotate')
    aspect_ratio_1 = group.nodes.new(type='ShaderNodeCombineXYZ')
    aspect_ratio_2 = group.nodes.new(type='ShaderNodeCombineXYZ')
    aspect_ratio_div = group.nodes.new(type='ShaderNodeMath')
    aspect_ratio_lt = group.nodes.new(type='ShaderNodeMath')
    aspect_ratio_switch = group.nodes.new(type='ShaderNodeMixRGB')
    user_transforms = group.nodes.new(type='ShaderNodeVectorMath')

    recenter = group.nodes.new(type='ShaderNodeVectorMath')
    
    #--------------------
    # Label the nodes.
    camera_transform.label = "Camera Transform"
    lens.label = "Lens"
    sensor_width.label = "Sensor Width"
    lens_shift_x.label = "Lens Shift X"
    lens_shift_y.label = "Lens Shift Y"

    zoom_1.label = "Zoom 1"
    zoom_2.label = "Zoom 2"
    lens_shift_1.label = "Lens Shift 1"
    to_radians.label = "Degrees to Radians"
    user_location.label = "User Location"

    perspective_1.label = "Perspective 1"
    perspective_2.label = "Perspective 2"
    perspective_3.label = "Perspective 3"
    perspective_4.label = "Perspective 4"
    zoom_3.label = "Zoom 3"
    lens_shift_2.label = "Lens Shift 2"

    user_translate.label = "User Translate"
    user_rotate.label = "User Rotate"

    aspect_ratio_1.label = "Aspect Ratio 1"
    aspect_ratio_2.label = "Aspect Ratio 2"
    aspect_ratio_div.label = "Divide"
    aspect_ratio_lt.label = "Less Than"
    aspect_ratio_switch.label = "Aspect Ratio Switch"

    user_transforms.label = "User Transforms"

    recenter.label = "Recenter"

    #---------------------
    # Position the nodes.
    hs = 250.0
    x = 0.0

    camera_transform.location = (x, 0.0)
    lens.location = (x, -700.0)
    sensor_width.location = (x, -900.0)
    lens_shift_x.location = (x, -1100.0)
    lens_shift_y.location = (x, -1300.0)
    input.location = (x, -1500.0)

    x += hs
    zoom_1.location = (x, -700.0)
    lens_shift_1.location = (x, -1100.0)
    to_radians.location = (x, -1500.0)
    user_location.location = (x, -1700.0)

    x += hs
    zoom_2.location = (x, -700.0)

    x += hs
    perspective_1.location = (x, 0.0)

    x += hs
    perspective_2.location = (x, 0.0)
    perspective_3.location = (x, -200.0)

    x += hs
    perspective_4.location = (x, 0.0)

    x += hs
    zoom_3.location = (x, 0.0)

    x += hs
    lens_shift_2.location = (x, 0.0)
    aspect_ratio_div.location = (x, -850.0)

    x += hs
    user_translate.location = (x, 0.0)
    aspect_ratio_lt.location = (x, -500.0)
    aspect_ratio_1.location = (x, -700.0)
    aspect_ratio_2.location = (x, -850.0)

    x += hs
    user_rotate.location = (x, 0.0)
    aspect_ratio_switch.location = (x, -600.0)

    x += hs
    user_transforms.location = (x, 0.0)

    x += hs
    recenter.location = (x, 0.0)

    x += hs
    output.location = (x, 0.0)

    #---------------------
    # Set up the drivers.

    drv_lens = lens.outputs['Value'].driver_add("default_value").driver
    drv_lens.type = 'SUM'
    var = drv_lens.variables.new()
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'CAMERA'
    var.targets[0].id = camera.data
    var.targets[0].data_path = 'lens'

    drv_width = sensor_width.outputs['Value'].driver_add("default_value").driver
    drv_width.type = 'SUM'
    var = drv_width.variables.new()
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'CAMERA'
    var.targets[0].id = camera.data
    var.targets[0].data_path = 'sensor_width'

    drv_shift_x = lens_shift_x.outputs['Value'].driver_add("default_value").driver
    drv_shift_x.type = 'SUM'
    var = drv_shift_x.variables.new()
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'CAMERA'
    var.targets[0].id = camera.data
    var.targets[0].data_path = 'shift_x'

    drv_shift_y = lens_shift_y.outputs['Value'].driver_add("default_value").driver
    drv_shift_y.type = 'SUM'
    var = drv_shift_y.variables.new()
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'CAMERA'
    var.targets[0].id = camera.data
    var.targets[0].data_path = 'shift_y'

    #----------------------
    # Configure the nodes.
    camera_transform.object = camera

    zoom_1.operation = 'DIVIDE'
    zoom_1.use_clamp = False
    zoom_2.operation = 'MULTIPLY'
    zoom_2.use_clamp = False
    zoom_2.inputs[1].default_value = -1.0
    lens_shift_1.inputs[2].default_value = 0.0
    to_radians.operation = 'MULTIPLY'
    to_radians.use_clamp = False
    to_radians.inputs[1].default_value = math.pi / 180.0
    user_location.inputs[2].default_value = 0.0

    perspective_2.operation = 'DIVIDE'
    perspective_2.use_clamp = False
    perspective_3.operation = 'DIVIDE'
    perspective_3.use_clamp = False
    zoom_3.operation = 'MULTIPLY'
    lens_shift_2.operation = 'SUBTRACT'

    user_translate.operation = 'SUBTRACT'
    user_rotate.rotation_type = 'Z_AXIS'
    user_rotate.invert = False
    user_rotate.inputs['Center'].default_value = (0.0, 0.0, 0.0)
    aspect_ratio_1.inputs['X'].default_value = 1.0
    aspect_ratio_1.inputs['Z'].default_value = 0.0
    aspect_ratio_2.inputs['Y'].default_value = 1.0
    aspect_ratio_2.inputs['Z'].default_value = 0.0
    aspect_ratio_div.operation = 'DIVIDE'
    aspect_ratio_div.inputs[0].default_value = 1.0
    aspect_ratio_lt.operation = 'LESS_THAN'
    aspect_ratio_lt.inputs[1].default_value = 1.0
    aspect_ratio_switch.blend_type = 'MIX'
    aspect_ratio_switch.use_clamp = False

    user_transforms.operation = 'MULTIPLY'

    recenter.operation = 'ADD'
    recenter.inputs[1].default_value = (0.5, 0.5, 0.0)

    #--------------------
    # Hook up the nodes.
    group.links.new(camera_transform.outputs['Object'], perspective_1.inputs['Vector'])
    group.links.new(lens.outputs['Value'], zoom_1.inputs[0])
    group.links.new(sensor_width.outputs['Value'], zoom_1.inputs[1])
    group.links.new(zoom_1.outputs['Value'], zoom_2.inputs[0])
    group.links.new(zoom_2.outputs['Value'], zoom_3.inputs[1])
    group.links.new(lens_shift_x.outputs['Value'], lens_shift_1.inputs['X'])
    group.links.new(lens_shift_y.outputs['Value'], lens_shift_1.inputs['Y'])
    group.links.new(lens_shift_1.outputs['Vector'], lens_shift_2.inputs[1])

    group.links.new(input.outputs['Aspect Ratio'], aspect_ratio_1.inputs['Y'])
    group.links.new(input.outputs['Aspect Ratio'], aspect_ratio_div.inputs[1])
    group.links.new(input.outputs['Aspect Ratio'], aspect_ratio_lt.inputs[0])
    group.links.new(input.outputs['Rotation'], to_radians.inputs[0])
    group.links.new(to_radians.outputs['Value'], user_rotate.inputs['Angle'])
    group.links.new(input.outputs['Loc X'], user_location.inputs['X'])
    group.links.new(input.outputs['Loc Y'], user_location.inputs['Y'])
    group.links.new(user_location.outputs['Vector'], user_translate.inputs[1])

    group.links.new(perspective_1.outputs['X'], perspective_2.inputs[0])
    group.links.new(perspective_1.outputs['Y'], perspective_3.inputs[0])
    group.links.new(perspective_1.outputs['Z'], perspective_2.inputs[1])
    group.links.new(perspective_1.outputs['Z'], perspective_3.inputs[1])
    group.links.new(perspective_1.outputs['Z'], perspective_4.inputs['Z'])
    group.links.new(perspective_2.outputs['Value'], perspective_4.inputs['X'])
    group.links.new(perspective_3.outputs['Value'], perspective_4.inputs['Y'])
    group.links.new(perspective_4.outputs['Vector'], zoom_3.inputs[0])
    group.links.new(zoom_3.outputs['Vector'], lens_shift_2.inputs[0])
    group.links.new(lens_shift_2.outputs['Vector'], user_translate.inputs[0])

    group.links.new(aspect_ratio_div.outputs[0], aspect_ratio_2.inputs['X'])
    group.links.new(aspect_ratio_1.outputs[0], aspect_ratio_switch.inputs[1])
    group.links.new(aspect_ratio_2.outputs[0], aspect_ratio_switch.inputs[2])
    group.links.new(aspect_ratio_lt.outputs[0], aspect_ratio_switch.inputs[0])

    group.links.new(user_translate.outputs['Vector'], user_rotate.inputs['Vector'])
    group.links.new(user_rotate.outputs['Vector'], user_transforms.inputs[0])
    group.links.new(aspect_ratio_switch.outputs[0], user_transforms.inputs[1])
    group.links.new(user_transforms.outputs['Vector'], recenter.inputs[0])

    group.links.new(recenter.outputs['Vector'], output.inputs['Vector'])

    return group


#========================================================


class CameraProjectorPanel(bpy.types.Panel):
    """Project textures from perspective cameras accurately."""
    bl_label = "Camera Projector"
    bl_idname = "DATA_PT_camera_projector"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'CAMERA'

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout

        col = layout.column()
        col.operator("material.camera_project_new")


#========================================================


class CameraProjectGroupNew(bpy.types.Operator):
    """Creates a new camera projection node group from the current selected camera"""
    bl_idname = "material.camera_project_new"
    bl_label = "New Camera Project Node Group"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None and context.active_object.type == 'CAMERA'

    def execute(self, context):
        x_res = context.scene.render.resolution_x
        y_res = context.scene.render.resolution_y
        x_asp = context.scene.render.pixel_aspect_x
        y_asp = context.scene.render.pixel_aspect_y

        ensure_camera_project_group(context.active_object, (x_res * x_asp) / (y_res * y_asp))
        return {'FINISHED'}


#========================================================


def register():
    bpy.utils.register_class(CameraProjectorPanel)
    bpy.utils.register_class(CameraProjectGroupNew)

def unregister():
    bpy.utils.unregister_class(CameraProjectorPanel)
    bpy.utils.unregister_class(CameraProjectGroupNew)


if __name__ == "__main__":
    register()
