from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from generate_manual_draft import build_manual_text, manual_section_body  # noqa: E402


def business_fixture() -> dict:
    return {
        "industry": "网格前处理",
        "target_users": ["网格生成人员，需要在计算前检查网格", "流体分析人员"],
        "product_positioning": "一款查看和检查多块结构化网格的桌面软件。",
        "core_value": "在提交计算前发现网格问题。",
        "operation_flow": [
            "导入网格文件",
            "查看属性页中的块数和单元数",
            "旋转视图检查外形",
            "查看拓扑检查结果",
            "计算质量指标并定位最差单元",
            "保存工程",
        ],
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


BOILERPLATE = (
    "账号进入、业务创建",
    "本手册用于",
    "日常使用时，",
    "再选择或创建业务对象",
    "请确保实际运行环境满足以上要求",
)


class BoilerplateTests(unittest.TestCase):
    def test_fixed_sentences_are_not_emitted(self) -> None:
        text, records, _ = build_manual_text({}, "网格查看软件", "V1.0", business_fixture())
        for phrase in BOILERPLATE:
            self.assertNotIn(phrase, text)
        self.assertFalse([issue for issue in records[-1]["issues"] if "模板化表达" in issue])

    def test_overview_uses_model_paragraphs_in_full(self) -> None:
        business = business_fixture()
        business["manual_sections"] = [
            {"title": "说明", "paragraphs": ["第一段说明。", "第二段说明。", "第三段说明。"]},
            {"title": "系统要求", "paragraphs": ["安装包已包含运行所需组件。"]},
        ]
        text, _, _ = build_manual_text({}, "网格查看软件", "V1.0", business)
        overview = manual_section_body(text, "说明")
        for paragraph in ("第一段说明。", "第二段说明。", "第三段说明。"):
            self.assertIn(paragraph, overview)
        self.assertNotIn("安装包已包含运行所需组件。", overview)
        self.assertIn("安装包已包含运行所需组件。", manual_section_body(text, "系统要求"))
        self.assertNotIn("主要供以下人员使用", overview)

    def test_target_users_fill_overview_when_no_paragraphs(self) -> None:
        text, _, _ = build_manual_text({}, "网格查看软件", "V1.0", business_fixture())
        overview = manual_section_body(text, "说明")
        self.assertIn("主要供以下人员使用：网格生成人员，需要在计算前检查网格；流体分析人员。", overview)

    def test_typical_flow_keeps_every_step(self) -> None:
        text, _, _ = build_manual_text({}, "网格查看软件", "V1.0", business_fixture())
        flow = manual_section_body(text, "典型使用流程")
        for step in business_fixture()["operation_flow"]:
            self.assertIn(step, flow)

    def test_meta_text_from_model_is_reported(self) -> None:
        business = business_fixture()
        business["manual_sections"] = [{"title": "说明", "paragraphs": ["本手册用于说明软件的操作方法。"]}]
        _, records, _ = build_manual_text({}, "网格查看软件", "V1.0", business)
        self.assertTrue(any("手册用于" in issue for issue in records[-1]["issues"]))


if __name__ == "__main__":
    unittest.main()
