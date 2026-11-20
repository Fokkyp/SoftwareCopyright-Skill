from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from generate_manual_draft import build_manual_text, plain_manual_text, technical_term_hits  # noqa: E402


def business_fixture() -> dict:
    return {
        "industry": "计算流体力学网格前处理",
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
                "title": "模型列表",
                "purpose": "以列表方式列出网格模型中的全部块、面、边、点",
                "usage": "块数较多时按名称查找对象",
                "entry": "左侧面板“模型”页签",
                "visible_elements": ["顶部搜索框", "块、面、边、点四个分类节点"],
                "operation_steps": ["在搜索框中输入块名", "勾选复选框显示或隐藏对象"],
                "validation_rules": [],
                "feedback": ["视图中对应对象立即显示或隐藏"],
                "screenshot": "模型页",
            }
        ],
    }


class PlainManualTextTests(unittest.TestCase):
    def test_domain_words_are_not_rewritten(self) -> None:
        for text in ("按住左键拖动旋转模型", "通过 USB 接口连接设备", "装配组件列表", "点击 Next 按钮"):
            self.assertEqual(plain_manual_text(text), text)

    def test_only_surrounding_whitespace_is_trimmed(self) -> None:
        self.assertEqual(plain_manual_text("  模型列表 \n"), "模型列表")


class TechnicalTermCheckTests(unittest.TestCase):
    def test_reports_build_level_terms_with_context(self) -> None:
        hits = technical_term_hits("页面通过状态管理保存结果，界面基于 React 构建")
        self.assertEqual(len(hits), 2)
        self.assertTrue(any("状态管理" in hit for hit in hits))
        self.assertTrue(any("React" in hit and "界面基于" in hit for hit in hits))

    def test_domain_words_are_not_reported(self) -> None:
        self.assertEqual(technical_term_hits("旋转模型、USB 接口、装配组件、集成框架、Reactor 设备"), [])


class ManualDraftTests(unittest.TestCase):
    def test_model_wording_survives_into_manual(self) -> None:
        text, records, _ = build_manual_text({}, "网格查看软件", "V1.0", business_fixture())
        self.assertIn("模型列表", text)
        self.assertIn("网格模型", text)
        self.assertNotIn("智能服务", text)
        self.assertTrue(all("偏技术表达" not in issue for record in records for issue in record["issues"]))

    def test_technical_wording_is_reported_not_replaced(self) -> None:
        business = business_fixture()
        business["manual_modules"][0]["purpose"] = "通过状态管理列出网格模型中的全部块"
        text, records, _ = build_manual_text({}, "网格查看软件", "V1.0", business)
        self.assertIn("通过状态管理列出", text)
        self.assertTrue(any("状态管理" in issue for issue in records[-1]["issues"]))


if __name__ == "__main__":
    unittest.main()
