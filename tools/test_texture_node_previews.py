"""离线验证：关闭预览时不触碰文件/图片，设置跨 Scene 生效。"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]


def execute_without_imports(relative, namespace):
    tree = ast.parse((ROOT / relative).read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
    exec(compile(tree, str(ROOT / relative), 'exec'), namespace)


class TexturePreviewTests(unittest.TestCase):
    def setUp(self):
        self.preferences = SimpleNamespace(texture_node_previews=False)
        self.context = SimpleNamespace(preferences=SimpleNamespace(addons={
            'bl_ext.user_default.TheHerta4': SimpleNamespace(preferences=self.preferences),
        }))
        self.bpy = SimpleNamespace(
            context=self.context,
            props=SimpleNamespace(StringProperty=lambda **kwargs: kwargs, EnumProperty=lambda **kwargs: kwargs),
            data=SimpleNamespace(images=MagicMock()),
        )
        self.settings = {'bpy': self.bpy, '__package__': 'bl_ext.user_default.TheHerta4.common'}
        execute_without_imports('common/addon_preferences.py', self.settings)
        self.os = MagicMock()
        namespace = {
            'bpy': self.bpy, 'os': self.os, 'SSMTNodeBase': object, 'iface_': lambda text: text,
            'texture_node_previews_enabled': self.settings['texture_node_previews_enabled'],
        }
        execute_without_imports('blueprint/blueprint_node_texture.py', namespace)
        self.node = namespace['SSMTNode_Texture']()
        self.node.texture_format = 'AUTO'
        self.node.texture_hash = '12345678'
        self.node._resolve_preview_path = MagicMock(return_value='texture.dds')

    def test_disabled_preview_skips_file_image_and_icon_work(self):
        self.assertIsNone(self.node._get_preview_image())
        layout = MagicMock()
        self.node.draw_buttons(self.context, layout)
        self.node._resolve_preview_path.assert_not_called()
        self.os.path.getmtime.assert_not_called()
        self.bpy.data.images.load.assert_not_called()
        layout.template_icon.assert_not_called()
        # 常规节点字段仍可编辑。
        layout.column.return_value.prop.assert_any_call(self.node, 'texture_filepath', text='文件路径')

    def test_enabled_preview_loads_and_draws_then_stops_when_disabled(self):
        self.preferences.texture_node_previews = True
        self.os.path.getmtime.return_value = 123.0
        image = self.bpy.data.images.load.return_value
        image.preview.icon_id = 42
        layout = MagicMock()
        self.node.draw_buttons(self.context, layout)
        self.bpy.data.images.load.assert_called_once_with('texture.dds', check_existing=True)
        image.preview_ensure.assert_called_once()
        layout.template_icon.assert_called_once_with(icon_value=42, scale=6.0)
        self.preferences.texture_node_previews = False
        self.node.draw_buttons(self.context, layout)
        self.bpy.data.images.load.assert_called_once()
        image.preview_ensure.assert_called_once()
        self.bpy.data.images.remove.assert_not_called()

    def test_preferences_are_global_and_missing_preferences_disable_preview(self):
        other_scene = SimpleNamespace(preferences=self.context.preferences, scene=object())
        self.preferences.texture_node_previews = True
        enabled = self.settings['texture_node_previews_enabled']
        self.assertTrue(enabled(other_scene))
        self.assertFalse(enabled(SimpleNamespace()))
        self.context.preferences.addons.clear()
        self.assertIsNone(self.node._get_preview_image())

    def test_update_redraws_node_editors_in_all_windows(self):
        editors = [MagicMock(type='NODE_EDITOR'), MagicMock(type='NODE_EDITOR')]
        view = MagicMock(type='VIEW_3D')
        self.context.window_manager = SimpleNamespace(windows=[
            SimpleNamespace(screen=SimpleNamespace(areas=[editors[0], view])),
            SimpleNamespace(screen=SimpleNamespace(areas=[editors[1]])),
        ])
        self.settings['redraw_node_editors'](self.preferences, self.context)
        for editor in editors:
            editor.tag_redraw.assert_called_once()
        view.tag_redraw.assert_not_called()


if __name__ == '__main__':
    unittest.main()
