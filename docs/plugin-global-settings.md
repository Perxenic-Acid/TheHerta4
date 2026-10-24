# 插件全局设置与贴图节点预览

TheHerta4 侧栏的“插件全局设置”提供“贴图节点启用预览功能”，默认关闭。
设置复用插件现有的 `HertaUpdatePreference`，不存入 Scene、工作空间或蓝图节点。
保存遵循 Blender 偏好设置机制；关闭自动保存偏好时，需在 Blender 偏好设置中手动保存。
参见 [Blender AddonPreferences](https://docs.blender.org/api/5.0/bpy.types.AddonPreferences.html)。

入口是 `ui/ui_panel_settings.py`，公共读取函数在 `common/addon_preferences.py`。
插件 ID 根据包名解析，兼容普通安装和 `bl_ext.<仓库>.<插件>` 扩展命名。
设置变化会通知所有窗口的节点编辑器重绘。

关闭开关后，贴图节点跳过路径探测、文件时间读取、图像加载/重载、`preview_ensure`
以及预览图标绘制。预览读取函数自身也检查开关，避免其它调用点绕过。
节点属性、贴图导出和材质图像不受影响；不删除已加载的共享图像。
此开关不控制材质节点预览、三维视图渲染或贴图合并工具的图片展示。

离线回归：

```powershell
python tools/test_texture_node_previews.py
```

本次已在隔离用户配置目录的 Blender 5.2 后台实例验证插件注册/注销、面板注册、默认值、
跨 Scene 读取和偏好保存。仍需在交互界面核对侧栏布局及大型工程的实际流畅度。
