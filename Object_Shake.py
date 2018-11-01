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

shakeObjects = []

#Update Functions
def updateHandler(scn):
    """ Updates properties every frame on all objects """
    
    global shakeObjects
    if not shakeObjects:
        return

    for eachObj in shakeObjects:
        ob = scn.objects[eachObj]
        settings = ob.objSettings[0]

        updateNoiseFreq(ob, settings.noiseFreq)

        axis_vect = [settings.useX, settings.useY, settings.useZ]
        updateNoiseAmp(ob, axis_vect, settings.noiseAmp, settings.ratio)


def updateNoiseFreq(obj, amount):
    """ Applies a given noise frequency to all channels of object """

    action = obj.animation_data.action
    scaleVal = 5 / amount
    
    for i in ['location', 'rotation_euler']:
        for j in range(3):
            action.fcurves.find(i, index=j).modifiers[0].scale = scaleVal

def updateNoiseAmp(obj, axis_vect, amount, ratio):
    """ Applies a given noise amplitude to all active channels based on ratio """

    action = obj.animation_data.action
    
    for name, portion in [('location', 1 - ratio), ('rotation_euler', ratio)]:
        for i in range(3):
            curve = action.fcurves.find(name, index=i)
            curve.modifiers[0].strength = amount * int(axis_vect[i]) * portion

def freqMessenger(self, context):
    """ Passes values to noise update function """

    updateNoiseFreq(context.object, self.noiseFreq)

def ampMessenger(self, context):
    """ Passes values to noise update function """

    updateNoiseAmp(
        context.object, 
        [self.useX, self.useY, self.useZ],
        self.noiseAmp,
        self.ratio
        )

class ObjSettings(bpy.types.PropertyGroup):
    """ Data Structure Holding Custom Variables """
    
    #Hidden Preferences
    insertFrame = bpy.props.IntProperty()

    #UI Properties
    useX = bpy.props.BoolProperty(
        name="X",
        description = "Use X Axis",
        default = True,
        update = ampMessenger,
    )
    useY = bpy.props.BoolProperty(
        name="Y",
        description = "Use Y Axis",
        default = True,
        update = ampMessenger,
    )
    useZ = bpy.props.BoolProperty(
        name="Z",
        description = "Use Z Axis",
        default = True,
        update = ampMessenger,
    )
    ratio = bpy.props.FloatProperty(
        name = "Loc/Rot Ratio",
        description = "Ratio between Location Movement and Rotation Movement",
        default = 0.5,
        min = 0,
        max = 1,
        update = ampMessenger,
    )
    noiseFreq = bpy.props.FloatProperty(
        name = "Speed",
        default = 0.5,
        min = 0.001,
        precision = 3,
        update = freqMessenger,
    )
    noiseAmp = bpy.props.FloatProperty(
        name = "Amount",
        default = 0.5,
        precision = 3,
        update = ampMessenger,
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
                mod.strength = ob.objSettings[0].noiseAmp
                mod.phase = random.random() * 10

        ob.objSettings[0].insertFrame = context.scene.frame_current

        global shakeObjects
        shakeObjects.append(ob.name)
        
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
        scn.frame_set(ob.objSettings[0].insertFrame)

        ob.keyframe_delete("location")
        ob.keyframe_delete("rotation_euler")

        ob.objSettings.remove(0)

        global shakeObjects
        shakeObjects.remove(ob.name)

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
        if ob == None:
            layout.label("Select an Object")

        elif len(ob.objSettings) == 0:
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
            col2.prop(current, "noiseAmp")

            row3 = layout.row()
            row3.scale_y = 1.5
            row3.operator("update.phase", icon="FILE_REFRESH")

            row4 = layout.row()
            
            row5 = layout.row()
            row5.operator("remove.shake", icon="CANCEL")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.objSettings = bpy.props.CollectionProperty(type=ObjSettings)
    bpy.app.handlers.frame_change_pre.append(updateHandler)


def unregister():
    bpy.utils.unregister_module(__name__)
    if updateHandler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(updateHandler)
