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
            "version":(1,2)}

shakeObjects = set()

#Update Functions
def updateHandler(scn):
    """ Updates properties every frame on all objects """
    global shakeObjects
    if len(shakeObjects) == 0:
        return

    for o in shakeObjects:
        ob = scn.objects[o]
        settings = ob.objSettings[0]

        updateNoiseFreq(ob, settings.noiseFreq)

        axis_vect = [settings.useX, settings.useY, settings.useZ]
        updateNoiseAmp(ob, axis_vect, settings.noiseAmp, settings.ratioLoc, settings.ratioRot)


def updateNoiseFreq(obj, amount):
    """ Applies a given noise frequency to all channels of object """

    action = obj.animation_data.action
    scaleVal = 5 / amount
    
    for i in ['location', 'rotation_euler']:
        for j in range(3):
            action.fcurves.find(i, index=j).modifiers[0].scale = scaleVal

def updateNoiseAmp(obj, axis_vect, amount, ratioLoc, ratioRot):
    """ Applies a given noise amplitude to all active channels based on ratio """

    action = obj.animation_data.action
    
    for name, portion in [('location', ratioLoc / 100), ('rotation_euler', ratioRot / 100)]:
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
        self.ratioLoc,
        self.ratioRot
    )
        

def getAllSelected(context):
    """ returns a list of selected objects from the current scene """
    
    return [ob for ob in context.selected_objects]


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
    ratioLoc = bpy.props.IntProperty(
        name = "Location",
        description = "Amount of Location Movement",
        subtype="PERCENTAGE",
        default = 100,
        min = 0,
        max = 100,
        update = ampMessenger,
    )
    ratioRot = bpy.props.IntProperty(
        name = "Rotation", 
        description = "Amount of Rotational Movement",
        subtype = "PERCENTAGE",
        default = 100,
        min = 0,
        max = 100,
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

        if updateHandler not in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.append(updateHandler)

        selectedObjects = getAllSelected(context)
        
        for s in selectedObjects:
            s.objSettings.add()
            s.keyframe_insert("location")
            s.keyframe_insert("rotation_euler")

            action = s.animation_data.action

            for i in ['location', 'rotation_euler']:
                for j in range(3):
                    mod = action.fcurves.find(i, index=j).modifiers.new("NOISE")
                    mod.scale = 5 / s.objSettings[0].noiseFreq
                    mod.strength = s.objSettings[0].noiseAmp
                    mod.phase = random.random() * 10

            s.objSettings[0].insertFrame = context.scene.frame_current

            global shakeObjects
            shakeObjects.add(s.name)
        
        return {"FINISHED"}


class REMOVE_OT_shake(bpy.types.Operator):
    """ Removes animation curves from object and animation settings """

    bl_idname = 'remove.shake'
    bl_label = "Remove Shake"

    def execute(self, context):
        
        selectedObjects = getAllSelected(context)
        scn = context.scene

        for s in selectedObjects:
            action = s.animation_data.action

            #reset to starting position
            for i in ['location', 'rotation_euler']:
                for j in range(3):
                    action.fcurves.find(i, index=j).modifiers[0].strength = 0

            #remove property animation curves
            for f in action.fcurves:
                if f.data_path.startswith("objSettings"):
                    action.fcurves.remove(f)

            #go to keyframe
            scn.frame_set(s.objSettings[0].insertFrame)
            scn.update()

            s.keyframe_delete("location")
            s.keyframe_delete("rotation_euler")

            del s['objSettings']

            global shakeObjects
            shakeObjects.remove(s.name)

        return {"FINISHED"}


class RANDOMIZE_OT_phase(bpy.types.Operator):
    """Randomizes the animation phase"""

    bl_idname = 'update.phase'
    bl_label = "Randomize"
    
    def execute(self, context):
        selectedObjects = getAllSelected(context)

        for s in selectedObjects:
            action = s.animation_data.action

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

            col = layout.column(align = True)
            col.prop(current, "ratioLoc", slider=True)
            col.prop(current, "ratioRot", slider=True)

            col2 = layout.column(align = True)
            row2 = col2.row(align = True)
            row2.prop(current, "useX")
            row2.prop(current, "useY")
            row2.prop(current, "useZ")
            
            col3 = layout.column(align = True)
            col3.prop(current, "noiseFreq")
            col3.prop(current, "noiseAmp")

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
