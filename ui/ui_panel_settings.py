import bpy

from ..common.addon_preferences import get_addon_preferences
from ..utils.translate_utils import iface_


class HERTA_PT_GlobalSettings(bpy.types.Panel):
    bl_label = "插件全局设置"
    bl_idname = "HERTA_PT_GlobalSettings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TheHerta4'
    bl_order = 98
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        preferences = get_addon_preferences(context)
        if preferences is None:
            self.layout.label(text=iface_("插件偏好设置不可用"), icon='ERROR')
            return
        self.layout.prop(preferences, "texture_node_previews", text=iface_("贴图节点启用预览功能"))


def register():
    bpy.utils.register_class(HERTA_PT_GlobalSettings)


def unregister():
    bpy.utils.unregister_class(HERTA_PT_GlobalSettings)
