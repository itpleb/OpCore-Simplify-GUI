import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    ScrollArea, SubtitleLabel, BodyLabel, FluentIcon, 
    PushSettingCard, ExpandGroupSettingCard, 
    SettingCard, PushButton, PrimaryPushButton
)

from Scripts.custom_dialogs import show_macos_version_dialog
from Scripts.styles import SPACING, COLORS
from Scripts import ui_utils


class macOSCard(SettingCard):
    def __init__(self, controller, on_select_version, parent=None):
        super().__init__(
            FluentIcon.GLOBE,
            "macOS 版本",
            "目标操作系统版本",
            parent
        )
        self.controller = controller
        
        self.versionLabel = BodyLabel(self.controller.macos_state.selected_version_name)
        self.versionLabel.setStyleSheet("color: {}; margin-right: 10px;".format(COLORS["text_secondary"]))
        
        self.selectVersionBtn = PushButton("选择版本")
        self.selectVersionBtn.clicked.connect(on_select_version)
        self.selectVersionBtn.setFixedWidth(150)
        
        self.hBoxLayout.addWidget(self.versionLabel)
        self.hBoxLayout.addWidget(self.selectVersionBtn)
        self.hBoxLayout.addSpacing(16)

    def update_version(self):
        self.versionLabel.setText(self.controller.macos_state.selected_version_name)

class AudioLayoutCard(SettingCard):
    def __init__(self, controller, on_select_layout, parent=None):
        super().__init__(
            FluentIcon.MUSIC,
            "音频布局 ID",
            "为您的音频编解码器选择布局 ID",
            parent
        )
        self.controller = controller
        
        layout_text = str(self.controller.hardware_state.audio_layout_id) if self.controller.hardware_state.audio_layout_id is not None else "未配置"
        self.layoutLabel = BodyLabel(layout_text)
        self.layoutLabel.setStyleSheet("color: {}; margin-right: 10px;".format(COLORS["text_secondary"]))
        
        self.selectLayoutBtn = PushButton("配置布局")
        self.selectLayoutBtn.clicked.connect(on_select_layout)
        self.selectLayoutBtn.setFixedWidth(150)
        
        self.hBoxLayout.addWidget(self.layoutLabel)
        self.hBoxLayout.addWidget(self.selectLayoutBtn)
        self.hBoxLayout.addSpacing(16)

        self.setVisible(False)

    def update_layout(self):
        layout_text = str(self.controller.hardware_state.audio_layout_id) if self.controller.hardware_state.audio_layout_id is not None else "未配置"
        self.layoutLabel.setText(layout_text)

class SMBIOSModelCard(SettingCard):
    def __init__(self, controller, on_select_model, parent=None):
        super().__init__(
            FluentIcon.TAG,
            "SMBIOS 型号",
            "为您的系统选择 Mac 型号标识符",
            parent
        )
        self.controller = controller
        
        model_text = self.controller.smbios_state.model_name if self.controller.smbios_state.model_name != "Not selected" else "未配置"
        self.modelLabel = BodyLabel(model_text)
        self.modelLabel.setStyleSheet("color: {}; margin-right: 10px;".format(COLORS["text_secondary"]))
        
        self.selectModelBtn = PushButton("配置型号")
        self.selectModelBtn.clicked.connect(on_select_model)
        self.selectModelBtn.setFixedWidth(150)
        
        self.hBoxLayout.addWidget(self.modelLabel)
        self.hBoxLayout.addWidget(self.selectModelBtn)
        self.hBoxLayout.addSpacing(16)

    def update_model(self):
        model_text = self.controller.smbios_state.model_name if self.controller.smbios_state.model_name != "Not selected" else "未配置"
        self.modelLabel.setText(model_text)

class ConfigurationPage(ScrollArea):
    def __init__(self, parent, ui_utils_instance=None):
        super().__init__(parent)
        self.setObjectName("configurationPage")
        self.controller = parent
        self.settings = self.controller.backend.settings
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.ui_utils = ui_utils_instance if ui_utils_instance else ui_utils.UIUtils()
        
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.enableTransparentBackground()
        
        self.status_card = None
        
        self._init_ui()

    def _init_ui(self):
        # 紧凑布局
        self.expandLayout.setContentsMargins(SPACING["large"], SPACING["medium"], SPACING["large"], SPACING["medium"])
        self.expandLayout.setSpacing(SPACING["medium"])

        self.expandLayout.addWidget(self.ui_utils.create_step_indicator(3))

        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING["tiny"])

        title_label = SubtitleLabel("配置")
        header_layout.addWidget(title_label)

        subtitle_label = BodyLabel("配置您的 OpenCore EFI 设置")
        subtitle_label.setStyleSheet("color: {};".format(COLORS["text_secondary"]))
        header_layout.addWidget(subtitle_label)

        self.expandLayout.addWidget(header_container)
        self.expandLayout.addSpacing(SPACING["medium"])

        self.status_start_index = self.expandLayout.count()
        self._update_status_card()

        self.macos_card = macOSCard(self.controller, self.select_macos_version, self.scrollWidget)
        self.expandLayout.addWidget(self.macos_card)

        self.acpi_card = PushSettingCard(
            "配置补丁",
            FluentIcon.DEVELOPER_TOOLS,
            "ACPI 补丁",
            "自定义系统 ACPI 表修改以实现硬件兼容性",
            self.scrollWidget
        )
        self.acpi_card.clicked.connect(self.customize_acpi_patches)
        self.expandLayout.addWidget(self.acpi_card)

        self.kexts_card = PushSettingCard(
            "管理驱动",
            FluentIcon.CODE,
            "内核扩展",
            "配置您的硬件所需的 kext 驱动",
            self.scrollWidget
        )
        self.kexts_card.clicked.connect(self.customize_kexts)
        self.expandLayout.addWidget(self.kexts_card)

        self.audio_layout_card = None
        self.audio_layout_card_index = None
        self.audio_layout_card = AudioLayoutCard(self.controller, self.customize_audio_layout, self.scrollWidget)
        self.expandLayout.addWidget(self.audio_layout_card)

        self.smbios_card = SMBIOSModelCard(self.controller, self.customize_smbios_model, self.scrollWidget)
        self.expandLayout.addWidget(self.smbios_card)

        # 创建下一步按钮
        self._create_next_button()
        
        self.expandLayout.addStretch()

    def _create_next_button(self):
        # 创建右下角的下一步按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.next_btn = PrimaryPushButton(FluentIcon.RIGHT_ARROW, "下一步")
        self.next_btn.clicked.connect(self.go_to_next_page)
        self.next_btn.setEnabled(False)  # 默认禁用
        self.next_btn.setFixedWidth(150)
        self.next_btn.setFixedHeight(40)
        
        button_layout.addWidget(self.next_btn)
        self.expandLayout.addLayout(button_layout)

    def go_to_next_page(self):
        """切换到下一页（构建与审查页面）"""
        # 使用 FluentWindow 的 switchTo 方法
        try:
            self.controller.switchTo(self.controller.buildPage)
        except Exception as e:
            print(f"导航失败: {e}")

    def _update_status_card(self):
        if self.status_card is not None:
            self.expandLayout.removeWidget(self.status_card)
            self.status_card.deleteLater()
            self.status_card = None

        disabled_devices = self.controller.hardware_state.disabled_devices or {}
        
        status_text = ""
        status_color = COLORS["text_secondary"]
        bg_color = COLORS["bg_card"]
        icon = FluentIcon.INFO
        
        if disabled_devices:
            status_text = "部分硬件组件已从配置中排除"
            status_color = COLORS["text_secondary"]
            bg_color = COLORS["warning_bg"]
        elif not self.controller.hardware_state.hardware_report:
            status_text = "请先选择硬件报告"
        elif not self.controller.macos_state.darwin_version:
            status_text = "请先选择目标 macOS 版本"
        else:
            status_text = "所有硬件组件兼容且已启用"
            status_color = COLORS["success"]
            bg_color = COLORS["success_bg"]
            icon = FluentIcon.ACCEPT

        self.status_card = ExpandGroupSettingCard(
            icon,
            "兼容性状态",
            status_text,
            self.scrollWidget
        )
        
        if disabled_devices:
            for device_name, device_info in disabled_devices.items():
                self.ui_utils.add_group_with_indent(
                    self.status_card,
                    FluentIcon.CLOSE,
                    device_name,
                    "不兼容" if device_info.get("Compatibility") == (None, None) else "已禁用",
                )
        else:
            pass

        self.expandLayout.insertWidget(self.status_start_index, self.status_card)
        
        # 控制下一步按钮的启用状态
        if hasattr(self, "next_btn"):
            # 当配置完成（选择了 macOS 版本）时启用按钮
            if self.controller.macos_state.darwin_version and self.controller.hardware_state.hardware_report:
                self.next_btn.setEnabled(True)
            else:
                self.next_btn.setEnabled(False)

    def select_macos_version(self):
        if not self.controller.validate_prerequisites(require_darwin_version=False, require_customized_hardware=False):
            return

        selected_version = show_macos_version_dialog(
            self.controller.macos_state.native_version,
            self.controller.macos_state.ocl_patched_version,
            self.controller.macos_state.suggested_version
        )

        if selected_version:
            self.controller.apply_macos_version(selected_version)
            self.controller.update_status("macOS 版本已更新为 {}".format(self.controller.macos_state.selected_version_name), "success")
            if hasattr(self, "macos_card"):
                self.macos_card.update_version()

    def customize_acpi_patches(self):
        if not self.controller.validate_prerequisites():
            return

        self.controller.backend.ac.customize_patch_selection()
        self.controller.update_status("ACPI 补丁配置已成功更新", "success")

    def customize_kexts(self):
        if not self.controller.validate_prerequisites():
            return

        self.controller.backend.k.kext_configuration_menu(self.controller.macos_state.darwin_version)
        self.controller.update_status("驱动配置已成功更新", "success")

    def customize_audio_layout(self):
        if not self.controller.validate_prerequisites():
            return

        audio_layout_id, audio_controller_properties = self.controller.backend.k._select_audio_codec_layout(
            self.controller.hardware_state.hardware_report,
            default_layout_id=self.controller.hardware_state.audio_layout_id
        )

        if audio_layout_id is not None:
            self.controller.hardware_state.audio_layout_id = audio_layout_id
            self.controller.hardware_state.audio_controller_properties = audio_controller_properties
            self._update_audio_layout_card_visibility()
            self.controller.update_status("音频布局已更新为 {}".format(audio_layout_id), "success")

    def customize_smbios_model(self):
        if not self.controller.validate_prerequisites():
            return

        current_model = self.controller.smbios_state.model_name
        selected_model = self.controller.backend.s.customize_smbios_model(self.controller.hardware_state.customized_hardware, current_model, self.controller.macos_state.darwin_version, self.controller.window())

        if selected_model and selected_model != current_model:
            self.controller.smbios_state.model_name = selected_model
            self.controller.backend.s.smbios_specific_options(self.controller.hardware_state.customized_hardware, selected_model, self.controller.macos_state.darwin_version, self.controller.backend.ac.patches, self.controller.backend.k)

            if hasattr(self, "smbios_card"):
                self.smbios_card.update_model()
            self.controller.update_status("SMBIOS 型号已更新为 {}".format(selected_model), "success")

    def _update_audio_layout_card_visibility(self):
        if self.controller.hardware_state.audio_layout_id is not None:
            self.audio_layout_card.setVisible(True)
            self.audio_layout_card.update_layout()
        else:
            self.audio_layout_card.setVisible(False)

    def update_display(self):
        self._update_status_card()
        if hasattr(self, "macos_card"):
            self.macos_card.update_version()
        self._update_audio_layout_card_visibility()
        if hasattr(self, "smbios_card"):
            self.smbios_card.update_model()

    def refresh(self):
        self.update_display()