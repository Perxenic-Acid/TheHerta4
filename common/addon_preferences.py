"""插件级偏好设置入口，不随 Scene 或工作空间变化。"""
import bpy


def get_addon_preferences(context=None):
    context = context if context is not None else bpy.context
    preferences = getattr(context, "preferences", None)
    addons = getattr(preferences, "addons", None)
    addon = addons.get(__package__.rsplit('.', 1)[0]) if addons is not None else None
    return getattr(addon, "preferences", None)


def texture_node_previews_enabled(context=None):
    preferences = get_addon_preferences(context)
    return bool(getattr(preferences, "texture_node_previews", False))


def redraw_node_editors(self, context):
    window_manager = getattr(context, "window_manager", None)
    if window_manager is None:
        return
    for window in window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()
