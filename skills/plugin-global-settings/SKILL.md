---
name: plugin-global-settings
description: 修改 TheHerta4 插件级设置及蓝图贴图节点预览开关；不用于工作空间或 Scene 专属选项。
---

先阅读 [全局设置说明](../../docs/plugin-global-settings.md)。复用根模块的
`HertaUpdatePreference`；侧栏和节点通过 `common/addon_preferences.py` 读取同一个偏好对象。
不要为同一个插件重复注册 AddonPreferences，也不要把全局开关放进 Scene。

新增预览工作前先检查全局开关；关闭路径必须避免文件探测、图片加载、重载和预览生成，
不能只隐藏最终图标。不要删除可能被材质共用的 `bpy.data.images`。
更新回调只通知节点编辑器重绘，draw 保持只读。

运行 `python tools/test_texture_node_previews.py`；涉及注册或持久化时，使用隔离用户配置
目录的 Blender 后台实例验证，避免改写用户日常偏好。交互布局和大型工程性能需要另行验收。
