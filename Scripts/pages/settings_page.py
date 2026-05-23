import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
)
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    ScrollArea, BodyLabel, PushButton, LineEdit, FluentIcon,
    SettingCardGroup, SwitchSettingCard, ComboBoxSettingCard,
    PushSettingCard, SpinBox,
    OptionsConfigItem, OptionsValidator, HyperlinkCard,
    StrongBodyLabel, CaptionLabel, SettingCard, SubtitleLabel,
    setTheme, Theme
)

from Scripts.custom_dialogs import show_confirmation
from Scripts.styles import COLORS, SPACING


class SettingsPage(ScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.settings = self.controller.backend.settings
        
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.enableTransparentBackground()
        
        self._init_ui()

    def _init_ui(self):
        self.expandLayout.setContentsMargins(SPACING["xxlarge"], SPACING["xlarge"], SPACING["xxlarge"], SPACING["xlarge"])
        self.expandLayout.setSpacing(SPACING["large"])

        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING["tiny"])

        title_label = SubtitleLabel("设置")
        header_layout.addWidget(title_label)

        subtitle_label = BodyLabel("配置 OpCore Simplify 首选项")
        subtitle_label.setStyleSheet("color: {};".format(COLORS["text_secondary"]))
        header_layout.addWidget(subtitle_label)

        self.expandLayout.addWidget(header_container)
        self.expandLayout.addSpacing(SPACING["medium"])

        self.build_output_group = self.create_build_output_group()
        self.expandLayout.addWidget(self.build_output_group)

        self.macos_group = self.create_macos_version_group()
        self.expandLayout.addWidget(self.macos_group)

        #self.appearance_group = self.create_appearance_group()
        #self.expandLayout.addWidget(self.appearance_group)

        self.update_group = self.create_update_settings_group()
        self.expandLayout.addWidget(self.update_group)

        self.advanced_group = self.create_advanced_group()
        self.expandLayout.addWidget(self.advanced_group)

        self.help_group = self.create_help_group()
        self.expandLayout.addWidget(self.help_group)
        
        self.bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(0, SPACING["large"], 0, SPACING["large"])
        bottom_layout.setSpacing(SPACING["medium"])
        bottom_layout.addStretch()

        reset_btn = PushButton("全部重置为默认值", self.bottom_widget)
        reset_btn.setIcon(FluentIcon.CANCEL)
        reset_btn.clicked.connect(self.reset_to_defaults)
        bottom_layout.addWidget(reset_btn)

        self.expandLayout.addWidget(self.bottom_widget)

        for card in self.findChildren(SettingCard):
            card.setIconSize(18, 18)

    def _update_widget_value(self, widget, value):
        if widget is None:
            return
            
        if isinstance(widget, SwitchSettingCard):
            widget.switchButton.setChecked(value)
        elif isinstance(widget, (ComboBoxSettingCard, OptionsConfigItem)):
            widget.setValue(value)
        elif isinstance(widget, SpinBox):
            widget.setValue(value)
        elif isinstance(widget, LineEdit):
            widget.setText(value)
        elif isinstance(widget, PushSettingCard):
            widget.setContent(value or "Use temporary directory (default)")

    def create_build_output_group(self):
        group = SettingCardGroup("构建输出", self.scrollWidget)

        self.output_dir_card = PushSettingCard(
            "浏览",
            FluentIcon.FOLDER,
            "输出目录",
            self.settings.get("build_output_directory") or "使用临时目录（默认）",
            group
        )
        self.output_dir_card.setObjectName("build_output_directory")
        self.output_dir_card.clicked.connect(self.browse_output_directory)
        group.addSettingCard(self.output_dir_card)

        return group

    def create_macos_version_group(self):
        group = SettingCardGroup("macOS 版本", self.scrollWidget)

        self.include_beta_card = SwitchSettingCard(
            FluentIcon.UPDATE,
            "包含测试版本",
            "在版本选择菜单中显示主要测试版 macOS 版本。启用以测试新 macOS 版本。",
            configItem=None,
            parent=group
        )
        self.include_beta_card.setObjectName("include_beta_versions")
        self.include_beta_card.switchButton.setChecked(self.settings.get_include_beta_versions())
        self.include_beta_card.switchButton.checkedChanged.connect(lambda checked: self.settings.set("include_beta_versions", checked))
        group.addSettingCard(self.include_beta_card)

        return group

    def create_appearance_group(self):
        group = SettingCardGroup("外观", self.scrollWidget)

        theme_values = [
            "Light",
            #"Dark",
        ]
        theme_value = self.settings.get_theme()
        if theme_value not in theme_values:
            theme_value = "Light"

        self.theme_config = OptionsConfigItem(
            "Appearance",
            "Theme",
            theme_value,
            OptionsValidator(theme_values)
        )

        def on_theme_changed(value):
            self.settings.set("theme", value)
            if value == "Dark":
                setTheme(Theme.DARK)
            else:
                setTheme(Theme.LIGHT)

        self.theme_config.valueChanged.connect(on_theme_changed)

        self.theme_card = ComboBoxSettingCard(
            self.theme_config,
            FluentIcon.BRUSH,
            "主题",
            "选择应用程序颜色主题。",
            theme_values,
            group
        )
        self.theme_card.setObjectName("theme")
        group.addSettingCard(self.theme_card)

        return group

    def create_update_settings_group(self):
        group = SettingCardGroup("更新与下载", self.scrollWidget)

        self.auto_update_card = SwitchSettingCard(
            FluentIcon.UPDATE,
            "启动时检查更新",
            "应用程序启动时自动检查 OpCore Simplify 的新更新，让您保持最新",
            configItem=None,
            parent=group
        )
        self.auto_update_card.setObjectName("auto_update_check")
        self.auto_update_card.switchButton.setChecked(self.settings.get_auto_update_check())
        self.auto_update_card.switchButton.checkedChanged.connect(lambda checked: self.settings.set("auto_update_check", checked))
        group.addSettingCard(self.auto_update_card)

        return group

    def create_advanced_group(self):
        group = SettingCardGroup("高级设置", self.scrollWidget)

        self.debug_logging_card = SwitchSettingCard(
            FluentIcon.DEVELOPER_TOOLS,
            "启用调试日志",
            "在整个应用程序中启用详细的调试日志，用于高级故障排除和诊断",
            configItem=None,
            parent=group
        )
        self.debug_logging_card.setObjectName("enable_debug_logging")
        self.debug_logging_card.switchButton.setChecked(self.settings.get_enable_debug_logging())
        self.debug_logging_card.switchButton.checkedChanged.connect(lambda checked: self.settings.set("enable_debug_logging", checked))
        group.addSettingCard(self.debug_logging_card)

        return group

    def create_help_group(self):
        group = SettingCardGroup("帮助与文档", self.scrollWidget)

        self.opencore_docs_card = HyperlinkCard(
            "https://dortania.github.io/OpenCore-Install-Guide/",
            "OpenCore 安装指南",
            FluentIcon.BOOK_SHELF,
            "OpenCore 文档",
            "使用 OpenCore 安装 macOS 的完整指南",
            group
        )
        group.addSettingCard(self.opencore_docs_card)

        self.troubleshoot_card = HyperlinkCard(
            "https://dortania.github.io/OpenCore-Install-Guide/troubleshooting/troubleshooting.html",
            "故障排除",
            FluentIcon.HELP,
            "故障排除指南",
            "常见 OpenCore 安装问题的解决方案",
            group
        )
        group.addSettingCard(self.troubleshoot_card)

        self.github_card = HyperlinkCard(
            "https://github.com/lzhoang2801/OpCore-Simplify",
            "在 GitHub 上查看",
            FluentIcon.GITHUB,
            "OpCore-Simplify 仓库",
            "报告问题、贡献或查看源代码",
            group
        )
        group.addSettingCard(self.github_card)

        return group

    def browse_output_directory(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择构建输出目录",
            os.path.expanduser("~")
        )

        if folder:
            self.settings.set("build_output_directory", folder)
            self.output_dir_card.setContent(folder)
            self.controller.update_status("输出目录已成功更新", "success")

    def reset_to_defaults(self):
        result = show_confirmation("重置设置", "确定要将所有设置重置为默认值吗？")

        if result:
            self.settings.settings = self.settings.defaults.copy()
            self.settings.save_settings()

            for widget in self.findChildren(QWidget):
                key = widget.objectName()
                if key and key in self.settings.defaults:
                    default_value = self.settings.defaults.get(key)
                    self._update_widget_value(widget, default_value)

            self.controller.update_status("所有设置已重置为默认值", "success")