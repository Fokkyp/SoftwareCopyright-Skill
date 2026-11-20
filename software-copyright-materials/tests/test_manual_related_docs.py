from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from generate_manual_draft import build_manual_text  # noqa: E402


def business_fixture() -> dict:
    return {
        "industry": "网格前处理",
        "target_users": ["网格生成人员"],
        "product_positioning": "一款查看和检查多块结构化网格的桌面软件。",
        "core_value": "在提交计算前发现网格问题。",
        "operation_flow": [],
        "manual_sections": [],
        "system_requirements": [{"item": "操作系统", "minimum": "Windows 10 64 位", "recommended": "Windows 11 64 位"}],
        "faq": [{"question": "导入失败怎么办？", "answer": "确认文件格式后重新导出。"}],
        "glossary": [{"term": "块", "definition": "多块结构化网格中的一个网格区域。"}],
        "manual_modules": [
            {
                "title": "块列表",
                "purpose": "以列表方式列出网格中的全部块、面、边、点",
                "usage": "块数较多时按名称查找对象",
                "entry": "左侧面板“块列表”页签",
                "visible_elements": ["顶部搜索框", "块、面、边、点四个分类节点"],
                "operation_steps": ["在搜索框中输入块名", "勾选复选框显示或隐藏对象"],
                "validation_rules": [],
                "feedback": ["视图中对应对象立即显示或隐藏"],
                "screenshot": "块列表页",
            }
        ],
    }


class RelatedDocumentsTests(unittest.TestCase):
    def test_chapter_is_omitted_without_real_documents(self) -> None:
        text, _, _ = build_manual_text({}, "网格查看软件", "V1.0", business_fixture())
        self.assertNotIn("相关文档", text)
        for fabricated in ("《总体设计》", "《详细设计》", "《测试案例》"):
            self.assertNotIn(fabricated, text)
        self.assertIn("## 一、说明", text)
        self.assertIn("## 二、功能特点", text)
        self.assertIn("## 三、系统要求", text)
        self.assertIn("## 四、块列表", text)

    def test_chapter_lists_only_supplied_documents(self) -> None:
        business = business_fixture()
        business["related_documents"] = [{"name": "用户使用手册", "target": "《网格查看软件用户使用手册》"}]
        text, _, _ = build_manual_text({}, "网格查看软件", "V1.0", business)
        self.assertIn("## 一、相关文档", text)
        self.assertIn("《网格查看软件用户使用手册》", text)
        self.assertNotIn("《详细设计》", text)
        self.assertIn("## 二、说明", text)
        self.assertIn("## 五、块列表", text)

    def test_missing_chapter_is_not_a_self_review_issue(self) -> None:
        _, records, _ = build_manual_text({}, "网格查看软件", "V1.0", business_fixture())
        self.assertTrue(all("相关文档" not in issue for record in records for issue in record["issues"]))


if __name__ == "__main__":
    unittest.main()
