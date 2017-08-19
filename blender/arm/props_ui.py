import bpy
import subprocess
import webbrowser
from bpy.types import Menu, Panel, UIList
from bpy.props import *
import arm.utils
import arm.make_renderer as make_renderer
import arm.make as make
import arm.make_utils as make_utils
import arm.make_state as state
import arm.props_renderer as props_renderer
import arm.assets as assets
import arm.log as log

# Menu in object region
class ObjectPropsPanel(bpy.types.Panel):
    bl_label = "Armory Props"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
 
    def draw(self, context):
        layout = self.layout
        obj = bpy.context.object
        if obj == None:
            return
            
        wrd = bpy.data.worlds['Arm']

        row = layout.row()
        row.prop(obj, 'game_export')
        if not obj.game_export:
            return
        row.prop(obj, 'spawn')

        row = layout.row()
        row.prop(obj, 'mobile')
        if obj.type == 'ARMATURE':
            row.prop(obj, 'bone_animation_enabled')
        else:
            row.prop(obj, 'object_animation_enabled')

        if obj.type == 'MESH':
            layout.prop(obj, 'instanced_children')
            if obj.instanced_children:
                layout.label('Location')
                column = layout.column()
                column.prop(obj, 'instanced_children_loc_x')
                column.prop(obj, 'instanced_children_loc_y')
                column.prop(obj, 'instanced_children_loc_z')
                # layout.label('Rotation')
                # row = layout.row()
                # row.prop(obj, 'instanced_children_rot_x')
                # row.prop(obj, 'instanced_children_rot_y')
                # row.prop(obj, 'instanced_children_rot_z')
                # layout.label('Scale')
                # row = layout.row()
                # row.prop(obj, 'instanced_children_scale_x')
                # row.prop(obj, 'instanced_children_scale_y')
                # row.prop(obj, 'instanced_children_scale_z')
            # layout.prop(obj, 'override_material')
            # if obj.override_material:
                # layout.prop(obj, 'override_material_name')

class ModifiersPropsPanel(bpy.types.Panel):
    bl_label = "Armory Props"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "modifier"
 
    def draw(self, context):
        layout = self.layout
        obj = bpy.context.object
        if obj == None:
            return

        layout.operator("arm.invalidate_cache")

        # Assume as first modifier
        if len(obj.modifiers) > 0 and obj.modifiers[0].type == 'OCEAN':
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_base_color')
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_water_color')
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_fade')
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_amplitude')
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_height')
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_choppy')
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_speed')
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_freq')
            layout.prop(bpy.data.worlds['Arm'], 'generate_ocean_fade')

class PhysicsPropsPanel(bpy.types.Panel):
    bl_label = "Armory Props"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
 
    def draw(self, context):
        layout = self.layout
        obj = bpy.context.object
        if obj == None:
            return

        layout.prop(obj, 'soft_body_margin')

# Menu in data region
class DataPropsPanel(bpy.types.Panel):
    bl_label = "Armory Props"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
 
    def draw(self, context):
        layout = self.layout
        obj = bpy.context.object
        if obj == None:
            return

        wrd = bpy.data.worlds['Arm']
        if obj.type == 'CAMERA':
            layout.prop_search(obj.data, "renderpath_path", bpy.data, "node_groups")
            layout.prop(obj.data, 'frustum_culling')
            layout.prop(obj.data, 'is_mirror')
            col = layout.column()
            col.enabled = obj.data.is_mirror
            row = col.row(align=True)
            row.label('Resolution')
            row.prop(obj.data, 'mirror_resolution_x')
            row.prop(obj.data, 'mirror_resolution_y')
        elif obj.type == 'MESH' or obj.type == 'FONT' or obj.type == 'META':
            row = layout.row(align=True)
            row.prop(obj.data, 'dynamic_usage')
            row.prop(obj.data, 'data_compressed')
            if obj.type == 'MESH':
                layout.prop(obj.data, 'sdfgen')
            layout.operator("arm.invalidate_cache")
        elif obj.type == 'LAMP':
            row = layout.row(align=True)
            col = row.column()
            col.prop(obj.data, 'lamp_clip_start')
            col.prop(obj.data, 'lamp_clip_end')
            col = row.column()
            col.prop(obj.data, 'lamp_fov')
            col.prop(obj.data, 'lamp_shadows_bias')
            if obj.data.type == 'POINT':
                layout.prop(obj.data, 'lamp_omni_shadows')
                col = layout.column()
                col.enabled = obj.data.lamp_omni_shadows
                col.prop(wrd, 'lamp_omni_shadows_pcfsize')
            layout.prop(wrd, 'generate_lamp_texture')
            layout.prop(wrd, 'generate_lamp_ies_texture')
        elif obj.type == 'SPEAKER':
            layout.prop(obj.data, 'loop')
            layout.prop(obj.data, 'stream')
        elif obj.type == 'ARMATURE':
            layout.prop(obj.data, 'data_compressed')

class ScenePropsPanel(bpy.types.Panel):
    bl_label = "Armory Props"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
 
    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        if scene == None:
            return
        row = layout.row()
        column = row.column()
        column.prop(scene, 'game_export')
        column.prop(scene, 'data_compressed')
        column = row.column()
        column.prop(scene, 'gp_export')
        columnb = column.column()
        columnb.enabled = scene.gp_export
        columnb.operator('arm.invalidate_gp_cache')

class InvalidateCacheButton(bpy.types.Operator):
    '''Delete cached mesh data'''
    bl_idname = "arm.invalidate_cache"
    bl_label = "Invalidate Cache"
 
    def execute(self, context):
        context.object.data.mesh_cached = False
        return{'FINISHED'}

class InvalidateMaterialCacheButton(bpy.types.Operator):
    '''Delete cached material data'''
    bl_idname = "arm.invalidate_material_cache"
    bl_label = "Invalidate Cache"
 
    def execute(self, context):
        context.material.is_cached = False
        return{'FINISHED'}

class InvalidateGPCacheButton(bpy.types.Operator):
    '''Delete cached grease pencil data'''
    bl_idname = "arm.invalidate_gp_cache"
    bl_label = "Invalidate GP Cache"
 
    def execute(self, context):
        if context.scene.grease_pencil != None:
            context.scene.grease_pencil.data_cached = False
        return{'FINISHED'}

class MaterialPropsPanel(bpy.types.Panel):
    bl_label = "Armory Props"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        mat = bpy.context.material
        if mat == None:
            return

        row = layout.row()
        column = row.column()
        column.prop(mat, 'cast_shadow')
        column.prop(mat, 'receive_shadow')
        column.separator()
        column.prop(mat, 'two_sided_shading')
        columnb = column.column()
        columnb.enabled = not mat.two_sided_shading
        columnb.prop(mat, 'override_cull_mode')
        
        column = row.column()
        column.prop(mat, 'overlay')
        column.prop(mat, 'decal')

        column.separator()
        column.prop(mat, 'discard_transparent')
        columnb = column.column()
        columnb.enabled = mat.discard_transparent
        columnb.prop(mat, 'discard_transparent_opacity')
        columnb.prop(mat, 'discard_transparent_opacity_shadows')

        # row = layout.row()
        # column = row.column()
        # column.prop(mat, 'override_shader')
        # columnb = column.column()
        # columnb.enabled = mat.override_shader
        # columnb.prop(mat, 'override_shader_name')
        # column = row.column()
        # column.prop(mat, 'override_shader_context')
        # columnb = column.column()
        # columnb.enabled = mat.override_shader_context
        # columnb.prop(mat, 'override_shader_context_name')

        # row = layout.row()
        # row.prop(mat, 'stencil_mask')
        # row.prop(mat, 'skip_context')

        layout.separator()
        row = layout.row()
        column = row.column()
        column.prop(mat, 'height_tess')
        columnb = column.column()
        columnb.enabled = mat.height_tess
        columnb.prop(mat, 'height_tess_inner')
        columnb.prop(mat, 'height_tess_outer')

        column = row.column()
        column.prop(mat, 'height_tess_shadows')
        columnb = column.column()
        columnb.enabled = mat.height_tess_shadows
        columnb.prop(mat, 'height_tess_shadows_inner')
        columnb.prop(mat, 'height_tess_shadows_outer')

        layout.prop(mat, 'transluc_shadows')

        layout.operator("arm.invalidate_material_cache")

class WorldPropsPanel(bpy.types.Panel):
    bl_label = "Armory Props"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
 
    def draw(self, context):
        layout = self.layout
        # wrd = bpy.context.world
        wrd = bpy.data.worlds['Arm']
        
        layout.prop(wrd, 'generate_irradiance')
        row = layout.row()
        row.enabled = wrd.generate_irradiance
        column = row.column()
        column.prop(wrd, 'generate_radiance')
        column.prop(wrd, 'generate_radiance_size')
        column = row.column()
        column.prop(wrd, 'generate_radiance_sky')
        column.prop(wrd, 'generate_radiance_sky_type')

class ArmoryPlayerPanel(bpy.types.Panel):
    bl_label = "Armory Player"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
 
    def draw(self, context):
        layout = self.layout
        wrd = bpy.data.worlds['Arm']

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if state.playproc == None and state.compileproc == None:
            row.operator("arm.play", icon="PLAY")
        else:
            row.operator("arm.stop", icon="MESH_PLANE")
        if state.playproc == None and state.krom_running == False:
            row.operator("arm.build")
        else:
            row.operator("arm.patch")
        row.operator("arm.clean_menu")
        
        layout.prop(wrd, 'arm_play_runtime')
        layout.prop(wrd, 'arm_play_camera')

class ArmoryRenderPanel(bpy.types.Panel):
    bl_label = "Armory Render"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout
        wrd = bpy.data.worlds['Arm']
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("arm.render", icon="RENDER_STILL")
        row.operator("arm.render_anim", icon="RENDER_ANIMATION")
        layout.prop(wrd, "rp_rendercapture_format")

class ArmoryExporterPanel(bpy.types.Panel):
    bl_label = "Armory Exporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout
        wrd = bpy.data.worlds['Arm']
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("arm.build_project")
        row.operator("arm.publish_project")
        layout.prop(wrd, 'arm_project_target')
        layout.prop(wrd, make_utils.target_to_gapi())

class ArmoryProjectPanel(bpy.types.Panel):
    bl_label = "Armory Project"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout
        wrd = bpy.data.worlds['Arm']

        row = layout.row(align=True)
        row.operator("arm.kode_studio")
        row.operator("arm.open_project_folder")

        layout.label('Build:')
        row = layout.row()
        col = row.column()

        col.prop(wrd, 'arm_play_console')
        col.prop(wrd, 'arm_stream_scene')
        
        if arm.utils.with_krom():
            col.prop(wrd, 'arm_play_live_patch')
            colb = col.column()
            colb.enabled = wrd.arm_play_live_patch
            colb.prop(wrd, 'arm_play_auto_build')

        col = row.column()
        col.prop(wrd, 'arm_cache_shaders')
        col.prop(wrd, 'arm_cache_compiler')
        col.prop(wrd, 'arm_gpu_processing')

        layout.label('Flags:')
        row = layout.row()
        col = row.column()
        col.prop(wrd, 'arm_batch_meshes')
        col.prop(wrd, 'arm_batch_materials')
        col.prop(wrd, 'arm_sampled_animation')
        col.prop(wrd, 'arm_dce')
        col.prop(wrd, 'arm_play_active_scene')
        if not wrd.arm_play_active_scene:
            col.prop_search(wrd, 'arm_project_scene', bpy.data, 'scenes', '')

        col = row.column()
        col.prop(wrd, 'arm_minimize')
        col.prop(wrd, 'arm_optimize_mesh')
        col.prop(wrd, 'arm_deinterleaved_buffers')
        col.prop(wrd, 'arm_export_tangents')
        col.prop(wrd, 'arm_asset_compression')

        layout.label('Window:')
        row = layout.row()
        col = row.column()
        col.prop(wrd, 'arm_vsync')
        col.prop(wrd, 'arm_loadbar')
        col.prop(wrd, 'arm_winmode')

        col = row.column()
        col.prop(wrd, 'arm_winresize')
        col.prop(wrd, 'arm_winmaximize')
        col.prop(wrd, 'arm_winminimize')

        layout.separator()
        layout.label('Modules:')
        layout.prop(wrd, 'arm_physics')
        layout.prop(wrd, 'arm_navigation')
        layout.prop(wrd, 'arm_ui')
        layout.prop(wrd, 'arm_hscript')

        layout.separator()
        layout.label('Project:')
        layout.prop(wrd, 'arm_project_name')
        layout.prop(wrd, 'arm_project_package')
        layout.prop_search(wrd, 'arm_khafile', bpy.data, 'texts', 'Khafile')
        layout.prop_search(wrd, 'arm_khamake', bpy.data, 'texts', 'Khamake')

        layout.separator()
        layout.label("Libraries:")
        rows = 2
        if len(wrd.my_librarytraitlist) > 1:
            rows = 4
        
        row = layout.row()
        row.template_list("MY_UL_LibraryTraitList", "The_List", wrd, "my_librarytraitlist", wrd, "librarytraitlist_index", rows=rows)

        col = row.column(align=True)
        col.operator("my_librarytraitlist.new_item", icon='ZOOMIN', text="")
        col.operator("my_librarytraitlist.delete_item", icon='ZOOMOUT', text="")

        if len(wrd.my_librarytraitlist) > 1:
            col.separator()
            col.operator("my_librarytraitlist.move_item", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("my_librarytraitlist.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'

        # if wrd.librarytraitlist_index >= 0 and len(wrd.my_librarytraitlist) > 0:
            # libitem = wrd.my_librarytraitlist[wrd.librarytraitlist_index]         

        layout.label('Armory v' + wrd.arm_version)

class ArmVirtualInputPanel(bpy.types.Panel):
    bl_label = "Armory Virtual Input"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout

class ArmGlobalVarsPanel(bpy.types.Panel):
    bl_label = "Armory Global Variables"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout

class ArmNavigationPanel(bpy.types.Panel):
    bl_label = "Armory Navigation"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
 
    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        if scene == None:
            return

        layout.operator("arm.generate_navmesh")

class ArmoryGenerateNavmeshButton(bpy.types.Operator):
    '''Generate navmesh from selected meshes'''
    bl_idname = 'arm.generate_navmesh'
    bl_label = 'Generate Navmesh'
 
    def execute(self, context):
        obj = context.active_object
        if obj == None or obj.type != 'MESH':
            return{'CANCELLED'}

        # TODO: build tilecache here

        # Navmesh trait
        obj.my_traitlist.add()
        obj.my_traitlist[-1].type_prop = 'Bundled Script'
        obj.my_traitlist[-1].class_name_prop = 'NavMesh'

        # For visualization
        bpy.ops.mesh.navmesh_make('EXEC_DEFAULT')
        obj = context.active_object
        obj.hide_render = True
        obj.game_export = False

        return{'FINISHED'}

class ArmoryPlayButton(bpy.types.Operator):
    '''Launch player in new window'''
    bl_idname = 'arm.play'
    bl_label = 'Play'
 
    def execute(self, context):
        if state.compileproc != None:
            return {"CANCELLED"}
        
        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        if not arm.utils.check_camera(self):
            return {"CANCELLED"}

        if not arm.utils.check_sdkpath(self):
            return {"CANCELLED"}

        if not arm.utils.check_engine(self):
            return {"CANCELLED"}
            
        make_renderer.check_default()

        if bpy.data.cameras[0].rp_rendercapture == True:
            self.report({"ERROR"}, "Disable Camera - Armory Render Path - Render Capture first")
            return {"CANCELLED"}

        assets.invalidate_enabled = False
        make.play_project(False)
        assets.invalidate_enabled = True
        return{'FINISHED'}

class ArmoryPlayInViewportButton(bpy.types.Operator):
    '''Launch player in 3D viewport'''
    bl_idname = 'arm.play_in_viewport'
    bl_label = 'Play in Viewport'
 
    def execute(self, context):
        if state.compileproc != None:
            return {"CANCELLED"}

        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        if not arm.utils.check_camera(self):
            return {"CANCELLED"}

        if not arm.utils.check_sdkpath(self):
            return {"CANCELLED"}

        if not arm.utils.check_engine(self):
            return {"CANCELLED"}

        if context.area == None:
            return {"CANCELLED"}

        make_renderer.check_default()

        if bpy.data.cameras[0].rp_rendercapture == True:
            self.report({"ERROR"}, "Disable Camera - Armory Render Path - Render Capture first")
            return {"CANCELLED"}

        assets.invalidate_enabled = False
        if state.playproc == None and state.krom_running == False:
            if context.area.type != 'VIEW_3D':
                return {"CANCELLED"}
            # Cancel viewport render
            for space in context.area.spaces:
                if space.type == 'VIEW_3D':
                    if space.viewport_shade == 'RENDERED':
                        space.viewport_shade = 'SOLID'
                    break
            make.play_project(True)
        else:
            make.play_project(True)
        assets.invalidate_enabled = True
        return{'FINISHED'}

class ArmoryStopButton(bpy.types.Operator):
    '''Stop currently running player'''
    bl_idname = 'arm.stop'
    bl_label = 'Stop'
 
    def execute(self, context):
        make.stop_project()
        return{'FINISHED'}

class ArmoryBuildButton(bpy.types.Operator):
    '''Build and compile project'''
    bl_idname = 'arm.build'
    bl_label = 'Build'
 
    def execute(self, context):
        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        if not arm.utils.check_camera(self):
            return {"CANCELLED"}

        if not arm.utils.check_sdkpath(self):
            return {"CANCELLED"}

        if not arm.utils.check_engine(self):
            return {"CANCELLED"}

        state.target = make.runtime_to_target(in_viewport=False)
        assets.invalidate_enabled = False
        make.build_project(target=state.target)
        make.compile_project(target_name=state.target, watch=True)
        assets.invalidate_enabled = True
        return{'FINISHED'}

class ArmoryBuildProjectButton(bpy.types.Operator):
    '''Build and compile project'''
    bl_idname = 'arm.build_project'
    bl_label = 'Build'
 
    def execute(self, context):
        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        if not arm.utils.check_camera(self):
            return {"CANCELLED"}

        if not arm.utils.check_sdkpath(self):
            return {"CANCELLED"}

        if not arm.utils.check_engine(self):
            return {"CANCELLED"}

        state.target = bpy.data.worlds['Arm'].arm_project_target
        assets.invalidate_enabled = False
        make.build_project(target=state.target)
        make.compile_project(target_name=state.target, watch=True)
        assets.invalidate_enabled = True
        return{'FINISHED'}

class ArmoryPatchButton(bpy.types.Operator):
    '''Update currently running player instance'''
    bl_idname = 'arm.patch'
    bl_label = 'Patch'
 
    def execute(self, context):
        assets.invalidate_enabled = False
        make.play_project(True)
        assets.invalidate_enabled = True
        return{'FINISHED'}

class ArmoryOpenProjectFolderButton(bpy.types.Operator):
    '''Open project folder'''
    bl_idname = 'arm.open_project_folder'
    bl_label = 'Project Folder'
 
    def execute(self, context):
        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        webbrowser.open('file://' + arm.utils.get_fp())
        return{'FINISHED'}

class ArmoryKodeStudioButton(bpy.types.Operator):
    '''Launch this project in Kode Studio'''
    bl_idname = 'arm.kode_studio'
    bl_label = 'Kode Studio'
    bl_description = 'Open Project in Kode Studio'
 
    def execute(self, context):
        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        make_utils.kode_studio()
        return{'FINISHED'}

class CleanMenu(bpy.types.Menu):
    bl_label = "Ok?"
    bl_idname = "OBJECT_MT_clean_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("arm.clean_cache")
        layout.operator("arm.clean_project")

class CleanButtonMenu(bpy.types.Operator):
    '''Clean cached data'''
    bl_label = "Clean"
    bl_idname = "arm.clean_menu"
 
    def execute(self, context):
        bpy.ops.wm.call_menu(name=CleanMenu.bl_idname)
        return {"FINISHED"}

class ArmoryCleanCacheButton(bpy.types.Operator):
    '''Delete all compiled data'''
    bl_idname = 'arm.clean_cache'
    bl_label = 'Clean Cache'
 
    def execute(self, context):
        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        make.clean_cache()
        return{'FINISHED'}

class ArmoryCleanProjectButton(bpy.types.Operator):
    '''Delete all cached project data'''
    bl_idname = 'arm.clean_project'
    bl_label = 'Clean Project'
 
    def execute(self, context):
        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        make.clean_project()
        return{'FINISHED'}

class ArmoryPublishButton(bpy.types.Operator):
    '''Build project ready for publishing'''
    bl_idname = 'arm.publish_project'
    bl_label = 'Publish'
 
    def execute(self, context):
        if not arm.utils.check_saved(self):
            return {"CANCELLED"}

        if not arm.utils.check_camera(self):
            return {"CANCELLED"}

        if not arm.utils.check_sdkpath(self):
            return {"CANCELLED"}

        if not arm.utils.check_engine(self):
            return {"CANCELLED"}

        make.publish_project()
        self.report({'INFO'}, 'Publishing project, check console for details.')
        return{'FINISHED'}

class ArmoryRenderButton(bpy.types.Operator):
    '''Capture Armory output as render result'''
    bl_idname = 'arm.render'
    bl_label = 'Render'
 
    def execute(self, context):
        if state.playproc != None:
            make.stop_project()
        if bpy.data.worlds['Arm'].arm_play_runtime != 'Krom':
            bpy.data.worlds['Arm'].arm_play_runtime = 'Krom'
        if bpy.data.cameras[0].rp_rendercapture == False:
            self.report({"ERROR"}, "Set Camera - Armory Render Path - Preset to Render Capture first")
            return {"CANCELLED"}
        assets.invalidate_enabled = False
        make.get_render_result()
        assets.invalidate_enabled = True
        return{'FINISHED'}

class ArmoryRenderAnimButton(bpy.types.Operator):
    '''Capture Armory output as render result'''
    bl_idname = 'arm.render_anim'
    bl_label = 'Animation'
 
    def execute(self, context):
        if state.playproc != None:
            make.stop_project()
        if bpy.data.worlds['Arm'].arm_play_runtime != 'Krom':
            bpy.data.worlds['Arm'].arm_play_runtime = 'Krom'
        self.report({"ERROR"}, "Animation capture not yet supported")
        return {"CANCELLED"}
        # return{'FINISHED'}

# Play button in 3D View panel
def draw_view3d_header(self, context):
    layout = self.layout
    if state.playproc == None and state.compileproc == None:
        if arm.utils.with_krom():
            layout.operator("arm.play_in_viewport", icon="PLAY")
        else:
            layout.operator("arm.play", icon="PLAY")
    else:
        layout.operator("arm.stop", icon="MESH_PLANE")

# Info panel in header
def draw_info_header(self, context):
    layout = self.layout
    if 'Arm' not in bpy.data.worlds:
        return
    wrd = bpy.data.worlds['Arm']
    if wrd.arm_progress < 100:
        layout.prop(wrd, 'arm_progress')
    if log.info_text != '':
        layout.label(log.info_text)

def register():
    bpy.utils.register_class(ObjectPropsPanel)
    bpy.utils.register_class(ModifiersPropsPanel)
    bpy.utils.register_class(PhysicsPropsPanel)
    bpy.utils.register_class(DataPropsPanel)
    bpy.utils.register_class(ScenePropsPanel)
    bpy.utils.register_class(InvalidateCacheButton)
    bpy.utils.register_class(InvalidateMaterialCacheButton)
    bpy.utils.register_class(InvalidateGPCacheButton)
    bpy.utils.register_class(MaterialPropsPanel)
    bpy.utils.register_class(WorldPropsPanel)
    bpy.utils.register_class(ArmoryPlayerPanel)
    bpy.utils.register_class(ArmoryRenderPanel)
    bpy.utils.register_class(ArmoryExporterPanel)
    bpy.utils.register_class(ArmoryProjectPanel)
    # bpy.utils.register_class(ArmVirtualInputPanel)
    # bpy.utils.register_class(ArmGlobalVarsPanel)
    bpy.utils.register_class(ArmoryPlayButton)
    bpy.utils.register_class(ArmoryPlayInViewportButton)
    bpy.utils.register_class(ArmoryStopButton)
    bpy.utils.register_class(ArmoryBuildButton)
    bpy.utils.register_class(ArmoryBuildProjectButton)
    bpy.utils.register_class(ArmoryPatchButton)
    bpy.utils.register_class(ArmoryOpenProjectFolderButton)
    bpy.utils.register_class(ArmoryKodeStudioButton)
    bpy.utils.register_class(CleanMenu)
    bpy.utils.register_class(CleanButtonMenu)
    bpy.utils.register_class(ArmoryCleanCacheButton)
    bpy.utils.register_class(ArmoryCleanProjectButton)
    bpy.utils.register_class(ArmoryPublishButton)
    bpy.utils.register_class(ArmoryRenderButton)
    bpy.utils.register_class(ArmoryRenderAnimButton)
    bpy.utils.register_class(ArmoryGenerateNavmeshButton)
    bpy.utils.register_class(ArmNavigationPanel)

    bpy.types.VIEW3D_HT_header.append(draw_view3d_header)
    bpy.types.INFO_HT_header.prepend(draw_info_header)

def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_view3d_header)
    bpy.types.INFO_HT_header.remove(draw_info_header)

    bpy.utils.unregister_class(ObjectPropsPanel)
    bpy.utils.unregister_class(ModifiersPropsPanel)
    bpy.utils.unregister_class(PhysicsPropsPanel)
    bpy.utils.unregister_class(DataPropsPanel)
    bpy.utils.unregister_class(ScenePropsPanel)
    bpy.utils.unregister_class(InvalidateCacheButton)
    bpy.utils.unregister_class(InvalidateMaterialCacheButton)
    bpy.utils.unregister_class(InvalidateGPCacheButton)
    bpy.utils.unregister_class(MaterialPropsPanel)
    bpy.utils.unregister_class(WorldPropsPanel)
    bpy.utils.unregister_class(ArmoryPlayerPanel)
    bpy.utils.unregister_class(ArmoryRenderPanel)
    bpy.utils.unregister_class(ArmoryExporterPanel)
    bpy.utils.unregister_class(ArmoryProjectPanel)
    # bpy.utils.unregister_class(ArmVirtualInputPanel)
    # bpy.utils.unregister_class(ArmGlobalVarsPanel)
    bpy.utils.unregister_class(ArmoryPlayButton)
    bpy.utils.unregister_class(ArmoryPlayInViewportButton)
    bpy.utils.unregister_class(ArmoryStopButton)
    bpy.utils.unregister_class(ArmoryBuildButton)
    bpy.utils.unregister_class(ArmoryBuildProjectButton)
    bpy.utils.unregister_class(ArmoryPatchButton)
    bpy.utils.unregister_class(ArmoryOpenProjectFolderButton)
    bpy.utils.unregister_class(ArmoryKodeStudioButton)
    bpy.utils.unregister_class(CleanMenu)
    bpy.utils.unregister_class(CleanButtonMenu)
    bpy.utils.unregister_class(ArmoryCleanCacheButton)
    bpy.utils.unregister_class(ArmoryCleanProjectButton)
    bpy.utils.unregister_class(ArmoryPublishButton)
    bpy.utils.unregister_class(ArmoryRenderButton)
    bpy.utils.unregister_class(ArmoryRenderAnimButton)
    bpy.utils.unregister_class(ArmoryGenerateNavmeshButton)
    bpy.utils.unregister_class(ArmNavigationPanel)
