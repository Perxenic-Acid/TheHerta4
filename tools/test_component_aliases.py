"""CPU 回归：直接执行工作空间解析类，隔离 Blender 注册和绘图依赖。"""
import ast
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Union


def workspace_types():
    source = Path(__file__).resolve().parents[1] / "workspace" / "ssmt_workspace.py"
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    module = types.ModuleType("ssmt_workspace_alias_fixture")
    module.__dict__.update({key: value for key, value in globals().items() if not key.startswith("__")})
    module.bpy = types.SimpleNamespace(types=types.SimpleNamespace(Collection=object))
    module.JsonUtils = types.SimpleNamespace(LoadFromFile=lambda path: json.loads(Path(path).read_text(encoding="utf-8-sig")))
    sys.modules[module.__name__] = module
    exec(compile(tree, str(source), "exec"), module.__dict__)
    return module.WorkSpaceModel, module.SSMTWorkSpace


WorkSpaceModel, SSMTWorkSpace = workspace_types()


class ComponentAliasTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def test_legacy_workspace_without_lod_or_alias_map(self):
        (self.root / "848c5980-3-0").mkdir()
        self.write("Config.json", [{"DrawIB": "848c5980", "Alias": "旧 IB 别名"}])
        model = WorkSpaceModel(str(self.root))
        self.assertEqual(model.get_display_name("", "848c5980", 0), "848c5980-0.旧 IB 别名")
        for name in ["848c5980-0", "848c5980-0.旧 IB 别名", "848c5980-3-0"]:
            self.assertEqual(model.parse_any_format_name(name)["old_folder_name"], "848c5980-3-0")

    def test_aliases_are_per_component_and_lod_and_ignore_old_name_suffixes(self):
        for lod in ["LOD0", "LOD1"]:
            for name in ["848c5980-3-0", "848c5980-6-3"]:
                (self.root / lod / name).mkdir(parents=True)
        # 故意与扫描顺序相反，确认沿用 SSMT 已持久化的编号。
        self.write("LOD0/DrawIB-Component.json", {"848c5980": {"0": "848c5980-6-3", "1": "848c5980-3-0"}})
        self.write("LOD0/ComponentAliases.json", {"848c5980-3-0": "脸.高光", "848c5980-6-3": "衣服"})
        self.write("LOD1/ComponentAliases.json", {"848c5980-3-0": "低模脸"})
        model = WorkSpaceModel(str(self.root))
        self.assertEqual(model.get_display_name("LOD0", "848c5980", 1), "LOD0.848c5980-1.脸.高光")
        self.assertEqual(model.get_display_name("LOD0", "848c5980", 0), "LOD0.848c5980-0.衣服")
        self.assertEqual(model.get_display_name("LOD1", "848c5980", 0), "LOD1.848c5980-0.低模脸")
        self.assertIn("LOD0.848c5980-1.脸.高光", model.get_all_display_names())
        for name in ["LOD0.848c5980-1", "LOD0.848c5980-1.旧别名", "LOD0.848c5980-1.脸.高光", "LOD0.848c5980-3-0"]:
            parsed = model.parse_any_format_name(name)
            self.assertEqual(parsed["old_folder_name"], "848c5980-3-0")
            self.assertEqual(model.get_index_count_first_index(parsed["lod"], parsed["draw_ib"], parsed["component"]), (3, 0))
        self.assertTrue(model.get_submesh_folder_path_for_name("LOD0.848c5980-1.新别名").endswith("848c5980-3-0"))

    def test_corrupt_alias_metadata_preserves_legacy_import(self):
        (self.root / "LOD0/848c5980-3-0").mkdir(parents=True)
        (self.root / "LOD0/ComponentAliases.json").write_text("broken", encoding="utf-8")
        self.assertEqual(WorkSpaceModel(str(self.root)).get_display_name("LOD0", "848c5980", 0), "LOD0.848c5980-0")

    def test_blueprint_explicit_submesh_accepts_lod_prefix(self):
        path = Path(__file__).resolve().parents[1] / "blueprint/blueprint_node_obj.py"
        node = next(node for node in ast.parse(path.read_text(encoding="utf-8-sig")).body if isinstance(node, ast.ClassDef) and node.name == "SSMTNode_Object_Info")
        method = next(method for method in node.body if isinstance(method, ast.FunctionDef) and method.name == "_get_effective_parse_name")
        scope = {"SSMTWorkSpace": SSMTWorkSpace}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), "exec"), scope)
        obj = types.SimpleNamespace(submesh_name="LOD0.848c5980-0.新别名", object_name="旧物体")
        self.assertEqual(scope[method.name](obj), obj.submesh_name)


if __name__ == "__main__":
    unittest.main()
