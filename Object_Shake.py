import bpy
import math
import random

bl_info = {"name": "Object Shake", 
            "category": "Animation", 
            "author": "Tim Crellin (Thatimster)", 
            "blender": (2,79,0), 
            "location": "3D Toolbar", 
            "description":"Adds randomly generated shaking to any object",
            "warning": "",
            "wiki_url":"", 
            "tracker_url": "https://github.com/thatimster/object-shake", 
            "version":(1,0)}

#Update Functions

def noiseFreqUpdate(self, context):
    """ Applies a given noise frequency to all channels """

    ob = context.object
    action = ob.animation_data.action
    scaleVal = 5 / self.noiseFreq
    
    for i in ['location', 'rotation_euler']:
        for j in range(3):
            action.fcurves.find(i, index=j).modifiers[0].scale = scaleVal


def noiseAmpliUpdate(self, context):
    """ Applies a given noise amplitude to all active channels based on ratio """

    ob = context.object
    action = ob.animation_data.action

    axis_vect = [self.useX, self.useY, self.useZ]
    
    for name, amount in [('location', 1 - self.ratio), ('rotation_euler', self.ratio)]:
        for i in range(3):
            curve = action.fcurves.find(name, index=i)
            curve.modifiers[0].strength = self.noiseAmpli * int(axis_vect[i]) * amount


class ObjSettings(bpy.types.PropertyGroup):
    """ Data Structure Holding Custom Variables """
    
    #Hidden Preferences
    insertFrame = bpy.props.IntProperty()

    #UI Properties
    useX = bpy.props.BoolProperty(
        name="X",
        description = "Use X Axis",
        default = True,
        update = noiseAmpliUpdate,
    )
    useY = bpy.props.BoolProperty(
        name="Y",
        description = "Use Y Axis",
        default = True,
        update = noiseAmpliUpdate,
    )
    useZ = bpy.props.BoolProperty(
        name="Z",
        description = "Use Z Axis",
        default = True,
        update = noiseAmpliUpdate,
    )
    ratio = bpy.props.FloatProperty(
        name = "Loc/Rot Ratio",
        description = "Ratio between Location Movement and Rotation Movement",
        default = 0.5,
        min = 0,
        max = 1,
        update = noiseAmpliUpdate,
    )
    noiseFreq = bpy.props.FloatProperty(
        name = "Speed",
        default = 0.5,
        min = 0.001,
        precision = 3,
        update = noiseFreqUpdate,
    )
    noiseAmpli = bpy.props.FloatProperty(
        name = "Amount",
        default = 0.5,
        min = 0.001,
        update = noiseAmpliUpdate,
    )


class INIT_OT_properties(bpy.types.Operator):
    """Initiates properties on the selected object and adds animation curves"""

    bl_idname = 'init.prop'
    bl_label = "Add Shake"
    
    def execute(self, context):
        context.object.objSettings.add()
        ob = context.object

        ob.keyframe_insert("location")
        ob.keyframe_insert("rotation_euler")

        action = ob.animation_data.action

        for i in ['location', 'rotation_euler']:
            for j in range(3):
                mod = action.fcurves.find(i, index=j).modifiers.new("NOISE")
                mod.scale = 5 / ob.objSettings[0].noiseFreq
                mod.strength = ob.objSettings[0].noiseAmpli
                mod.phase = random.random() * 10

        ob.objSettings[0].insertFrame = context.scene.frame_current
        
        return {"FINISHED"}


class REMOVE_OT_shake(bpy.types.Operator):
    """ Removes animation curves from object and animation settings """

    bl_idname = 'remove.shake'
    bl_label = "Remove Shake"

    def execute(self, context):
        ob = context.object
        scn = context.scene
        action = ob.animation_data.action

        #reset to starting position
        for i in ['location', 'rotation_euler']:
            for j in range(3):
                action.fcurves.find(i, index=j).modifiers[0].strength = 0

        scn.update()

        #go to keyframe
        scn.frame_current = ob.objSettings[0].insertFrame

        ob.keyframe_delete("location")
        ob.keyframe_delete("rotation_euler")

        ob.objSettings.remove(0)

        return {"FINISHED"}


class RANDOMIZE_OT_phase(bpy.types.Operator):
    """Randomizes the animation phase"""

    bl_idname = 'update.phase'
    bl_label = "Randomize"
    
    def execute(self, context):
        ob = context.object
        action = ob.animation_data.action

        for i in ['location', 'rotation_euler']:
            for j in range(3):
                action.fcurves.find(i, index=j).modifiers[0].phase = random.random() * 10

        return {"FINISHED"}

class OBJECT_PR_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        col = layout.column(align = True)
        row = col.row(align = True)
        row.scale_y = 1.5
        row.label(text=" ")
        row.operator(
                "wm.url_open", 
                text="YouTube Channel", 
                icon='TRIA_RIGHT',
        ).url = "https://youtube.com/thatimst3r"
        
        row.operator(
                "wm.url_open", 
                text="Support Me", 
                icon='SOLO_ON',
        ).url = "https://blendermarket.com/creators/thatimst3r"
        row.label(text=" ")
        row = layout.row()


class OBJECTSHAKE_PT_panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    
    bl_label = "Object Shake"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        ob = context.object

        #shown if scene hasn't been setup
        if ob != None and len(ob.objSettings) == 0:
            row = layout.row()
            row.scale_y = 1.5
            row.operator('init.prop', icon='FILE_TICK')
        else:
            current = ob.objSettings[0]

            row = layout.row()
            row.prop(current, "ratio", slider=True)

            col = layout.column(align = True)
            row2 = col.row(align = True)
            row2.prop(current, "useX")
            row2.prop(current, "useY")
            row2.prop(current, "useZ")
            
            col2 = layout.column(align = True)
            col2.prop(current, "noiseFreq")
            col2.prop(current, "noiseAmpli")

            row3 = layout.row()
            row3.scale_y = 1.5
            row3.operator("update.phase", icon="FILE_REFRESH")

            row4 = layout.row()
            
            row5 = layout.row()
            row5.operator("remove.shake", icon="CANCEL")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.objSettings = bpy.props.CollectionProperty(type=ObjSettings)


def unregister():
    bpy.utils.unregister_module(__name__)
