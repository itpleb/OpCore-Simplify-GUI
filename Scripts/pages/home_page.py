from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from qfluentwidgets import SubtitleLabel, BodyLabel, CardWidget, StrongBodyLabel, FluentIcon, ScrollArea

from Scripts.styles import COLORS, SPACING
from Scripts import ui_utils


class HomePage(ScrollArea):
    def __init__(self, parent, ui_utils_instance=None):
        super().__init__(parent)
        self.setObjectName("homePage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.ui_utils = ui_utils_instance if ui_utils_instance else ui_utils.UIUtils()
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()
        
        self.scrollWidget.setStyleSheet("QWidget { background: transparent; }")
        
        self._init_ui()

    def _init_ui(self):
        self.expandLayout.setContentsMargins(SPACING["xxlarge"], SPACING["xlarge"], SPACING["xxlarge"], SPACING["xlarge"])
        self.expandLayout.setSpacing(SPACING["large"])

        self.expandLayout.addWidget(self._create_title_label())
        
        self.expandLayout.addWidget(self._create_hero_section())
        
        self.expandLayout.addWidget(self._create_note_card())
        
        self.expandLayout.addWidget(self._create_warning_card())
        
        self.expandLayout.addWidget(self._create_guide_card())

        self.expandLayout.addStretch()

    def _create_title_label(self):
        title_label = SubtitleLabel("欢迎使用 OpCore Simplify")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        return title_label

    def _create_hero_section(self):
        hero_card = CardWidget()
        
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(SPACING["large"], SPACING["large"], SPACING["large"], SPACING["large"])
        hero_layout.setSpacing(SPACING["large"])

        hero_text = QVBoxLayout()
        hero_text.setSpacing(SPACING["medium"])

        hero_title = StrongBodyLabel("简介")
        hero_title.setStyleSheet("font-size: 18px; color: {};".format(COLORS["primary"]))
        hero_text.addWidget(hero_title)

        hero_body = BodyLabel(
            "一款专业的 OpenCore EFI 配置工具，通过自动化关键设置流程和提供标准化配置来简化 Hackintosh 构建。<br>"
            "旨在减少手动操作，同时确保您的 Hackintosh 之旅准确无误。"
        )
        hero_body.setWordWrap(True)
        hero_body.setStyleSheet("line-height: 1.6; font-size: 14px;")
        hero_text.addWidget(hero_body)

        hero_layout.addLayout(hero_text, 2)

        robot_icon = self.ui_utils.build_icon_label(FluentIcon.ROBOT, COLORS["primary"], size=64)
        hero_layout.addWidget(robot_icon, 1, Qt.AlignmentFlag.AlignVCenter)

        return hero_card

    def _create_note_card(self):
        return self.ui_utils.custom_card(
            card_type="note",
            title="OpenCore Legacy Patcher 3.0.0 - 现已支持 macOS Tahoe 26！",
            body=(
                "期待已久的 OpenCore Legacy Patcher 3.0.0 版本终于发布，为社区带来了<b>macOS Tahoe 26 的初步支持</b>！<br><br>"
                "<b>请注意：</b><br>"
                "- 只有来自 <a href=\"https://github.com/lzhoang2801/OpenCore-Legacy-Patcher/releases/tag/3.0.0\" style=\"color: #0078D4; text-decoration: none;\">lzhoang2801/OpenCore-Legacy-Patcher</a> 仓库的 OpenCore-Patcher 3.0.0 才提供对 macOS Tahoe 26 的支持。<br>"
                "- 官方 Dortania 版本或旧版补丁<b>无法</b>在 macOS Tahoe 26 上工作。"
            )
        )

    def _create_warning_card(self):
        return self.ui_utils.custom_card(
            card_type="warning",
            title="警告",
            body=(
                "虽然 OpCore Simplify 大大减少了设置时间，但 Hackintosh 之旅仍需要：<br><br>"
                "- 了解 <a href=\"https://dortania.github.io/OpenCore-Install-Guide/\" style=\"color: #F57C00; text-decoration: none;\">Dortania 指南</a>中的基本概念<br>"
                "- 在安装过程中进行测试和故障排除<br>"
                "- 耐心和毅力来解决遇到的任何问题<br><br>"
                "我们的工具不保证一次安装成功，但它可以帮助您入门。"
            )
        )

    def _create_guide_card(self):
        guide_card = CardWidget()
        guide_layout = QVBoxLayout(guide_card)
        guide_layout.setContentsMargins(SPACING["large"], SPACING["large"], SPACING["large"], SPACING["large"])
        guide_layout.setSpacing(SPACING["medium"])

        guide_title = StrongBodyLabel("开始使用")
        guide_title.setStyleSheet("font-size: 18px;")
        guide_layout.addWidget(guide_title)

        step_items = [
            (FluentIcon.FOLDER_ADD, "1. 选择硬件报告", "选择要为其构建 EFI 的目标系统的硬件报告。"),
            (FluentIcon.CHECKBOX, "2. 检查兼容性", "查看硬件与 macOS 的兼容性。"),
            (FluentIcon.EDIT, "3. 配置设置", "自定义 ACPI 补丁、驱动和 OpenCore EFI 配置。"),
            (FluentIcon.DEVELOPER_TOOLS, "4. 构建 EFI", "生成您的 OpenCore EFI。"),
        ]

        for idx, (icon, title, desc) in enumerate(step_items):
            guide_layout.addWidget(self._create_guide_row(icon, title, desc))

            if idx < len(step_items) - 1:
                guide_layout.addWidget(self._create_divider())

        return guide_card

    def _create_guide_row(self, icon, title, desc):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(SPACING["medium"])

        icon_container = QWidget()
        icon_container.setFixedWidth(40)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        row_icon = self.ui_utils.build_icon_label(icon, COLORS["primary"], size=24)
        icon_layout.addWidget(row_icon)
        
        row_layout.addWidget(icon_container)

        text_col = QVBoxLayout()
        text_col.setSpacing(SPACING["tiny"])
        
        title_label = StrongBodyLabel(title)
        title_label.setStyleSheet("font-size: 14px;")
        
        desc_label = BodyLabel(desc)
        desc_label.setWordWrap(True)
        
        desc_label.setStyleSheet("color: {}; line-height: 1.4;".format(COLORS["text_secondary"]))
        
        text_col.addWidget(title_label)
        text_col.addWidget(desc_label)
        row_layout.addLayout(text_col)

        return row

    def _create_divider(self):
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: {};".format(COLORS["border_light"]))
        return divider

    def refresh(self):
        pass