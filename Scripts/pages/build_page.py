import platform
import os
import shutil
import threading

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, CardWidget, TextEdit,
    StrongBodyLabel, ProgressBar, PrimaryPushButton, FluentIcon,
    ScrollArea
)

from Scripts.datasets import chipset_data
from Scripts.datasets import kext_data
from Scripts.custom_dialogs import show_confirmation
from Scripts.styles import SPACING, COLORS, RADIUS
from Scripts import ui_utils
from Scripts.widgets.config_editor import ConfigEditor


class BuildPage(ScrollArea):
    build_progress_signal = pyqtSignal(str, list, int, int, bool)
    build_complete_signal = pyqtSignal(bool, object)
    
    def __init__(self, parent, ui_utils_instance=None):
        super().__init__(parent)
        self.setObjectName("buildPage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.build_in_progress = False
        self.build_successful = False
        self.ui_utils = ui_utils_instance if ui_utils_instance else ui_utils.UIUtils()
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.expandLayout.setContentsMargins(SPACING["xxlarge"], SPACING["xlarge"], SPACING["xxlarge"], SPACING["xlarge"])
        self.expandLayout.setSpacing(SPACING["large"])

        self.expandLayout.addWidget(self.ui_utils.create_step_indicator(4))
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(SPACING["small"])
        title = SubtitleLabel("构建 OpenCore EFI")
        subtitle = BodyLabel("构建您的自定义 OpenCore EFI，准备安装")
        subtitle.setStyleSheet("color: {};".format(COLORS["text_secondary"]))
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        self.expandLayout.addLayout(header_layout)

        self.expandLayout.addSpacing(SPACING["medium"])

        self.instructions_after_content = QWidget()
        self.instructions_after_content_layout = QVBoxLayout(self.instructions_after_content)
        self.instructions_after_content_layout.setContentsMargins(0, 0, 0, 0)
        self.instructions_after_content_layout.setSpacing(SPACING["medium"])
        
        self.instructions_after_build_card = self.ui_utils.custom_card(
            card_type="warning",
            title="使用 EFI 前",
            body="在使用构建的 EFI 之前，请完成以下重要步骤：",
            custom_widget=self.instructions_after_content,
            parent=self.scrollWidget
        )
        
        self.instructions_after_build_card.setVisible(False)
        self.expandLayout.addWidget(self.instructions_after_build_card)

        build_control_card = CardWidget(self.scrollWidget)
        build_control_card.setBorderRadius(RADIUS["card"])
        build_control_layout = QVBoxLayout(build_control_card)
        build_control_layout.setContentsMargins(SPACING["large"], SPACING["large"], SPACING["large"], SPACING["large"])
        build_control_layout.setSpacing(SPACING["medium"])

        title = StrongBodyLabel("构建控制")
        build_control_layout.addWidget(title)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACING["medium"])

        self.build_btn = PrimaryPushButton(FluentIcon.DEVELOPER_TOOLS, "构建 OpenCore EFI")
        self.build_btn.clicked.connect(self.start_build)
        btn_layout.addWidget(self.build_btn)
        self.controller.build_btn = self.build_btn

        self.open_result_btn = PrimaryPushButton(FluentIcon.FOLDER, "打开结果文件夹")
        self.open_result_btn.clicked.connect(self.open_result)
        self.open_result_btn.setEnabled(False)
        btn_layout.addWidget(self.open_result_btn)
        self.controller.open_result_btn = self.open_result_btn

        build_control_layout.addLayout(btn_layout)

        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, SPACING["small"], 0, 0)
        progress_layout.setSpacing(SPACING["medium"])

        status_row = QHBoxLayout()
        status_row.setSpacing(SPACING["medium"])
        
        self.status_icon_label = QLabel()
        self.status_icon_label.setFixedSize(28, 28)
        status_row.addWidget(self.status_icon_label)
        
        self.progress_label = StrongBodyLabel("准备构建")
        self.progress_label.setStyleSheet("color: {}; font-size: 15px; font-weight: 600;".format(COLORS["text_secondary"]))
        status_row.addWidget(self.progress_label)
        status_row.addStretch()
        
        progress_layout.addLayout(status_row)

        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(True)
        self.controller.progress_bar = self.progress_bar
        progress_layout.addWidget(self.progress_bar)
        
        self.controller.progress_label = self.progress_label
        self.progress_container.setVisible(False)
        
        self.progress_helper = ui_utils.ProgressStatusHelper(
            self.status_icon_label,
            self.progress_label,
            self.progress_bar,
            self.progress_container
        )
        
        build_control_layout.addWidget(self.progress_container)
        self.expandLayout.addWidget(build_control_card)

        log_card = CardWidget(self.scrollWidget)
        log_card.setBorderRadius(RADIUS["card"])
        log_card_layout = QVBoxLayout(log_card)
        log_card_layout.setContentsMargins(SPACING["large"], SPACING["large"], SPACING["large"], SPACING["large"])
        log_card_layout.setSpacing(SPACING["medium"])

        log_title = StrongBodyLabel("构建日志")
        log_card_layout.addWidget(log_title)
        
        log_description = BodyLabel("详细的构建过程信息和状态更新")
        log_description.setStyleSheet("color: {}; font-size: 13px;".format(COLORS["text_secondary"]))
        log_card_layout.addWidget(log_description)

        self.build_log = TextEdit()
        self.build_log.setReadOnly(True)
        self.build_log.setMinimumHeight(400)
        self.build_log.setStyleSheet(f"""
            TextEdit {{
                background-color: rgba(0, 0, 0, 0.03);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: {RADIUS["small"]}px;
                padding: {SPACING["large"]}px;
                font-family: "Consolas", "Monaco", "Courier New", monospace;
                font-size: 13px;
                line-height: 1.7;
            }}
        """)
        self.controller.build_log = self.build_log
        log_card_layout.addWidget(self.build_log)
        
        self.log_card = log_card
        self.log_card.setVisible(False)
        self.expandLayout.addWidget(log_card)

        self.config_editor = ConfigEditor(self.scrollWidget)
        self.config_editor.setVisible(False)
        self.expandLayout.addWidget(self.config_editor)

        self.expandLayout.addStretch()

    def _connect_signals(self):
        self.build_progress_signal.connect(self._handle_build_progress)
        self.build_complete_signal.connect(self._handle_build_complete)

    def _handle_build_progress(self, title, steps, current_step_index, progress, done):
        status = "success" if done else "loading"
        
        if done:
            message = "{} 完成！".format(title)
        else:
            step_text = steps[current_step_index] if current_step_index < len(steps) else "处理中"
            step_counter = "步骤 {}/{}".format(current_step_index + 1, len(steps))
            message = "{}：{}...".format(step_counter, step_text)
        
        if done:
            final_progress = 100
        else:
            if "构建" in title:
                final_progress = 40 + int(progress * 0.6)
            else:
                final_progress = progress
        
        if hasattr(self, "progress_helper"):
            self.progress_helper.update(status, message, final_progress)
        
        if done:
            self.controller.backend.u.log_message("[BUILD] {} 完成！".format(title), "SUCCESS", to_build_log=True)
        else:
            step_text = steps[current_step_index] if current_step_index < len(steps) else "处理中"
            self.controller.backend.u.log_message("[BUILD] 步骤 {}/{}：{}...".format(current_step_index + 1, len(steps), step_text), "INFO", to_build_log=True)

    def start_build(self):
        if not self.controller.validate_prerequisites():
            return

        if self.controller.macos_state.needs_oclp:
            content = (
                "1. OpenCore Legacy Patcher 允许在新版 macOS 上恢复对已弃用 GPU 和 Broadcom WiFi 的支持，并可在 macOS Tahoe 26 上启用 AppleHDA。<br>"
                "2. OpenCore Legacy Patcher 需要禁用 SIP 才能应用自定义内核补丁，这可能导致不稳定、安全风险和更新问题。<br>"
                "3. OpenCore Legacy Patcher 不正式支持 Hackintosh 社区。<br><br>"
                "<b><font color=\"{info_color}\">macOS Tahoe 26 支持：</font></b><br>"
                "要修补 macOS Tahoe 26，您必须从我的仓库下载 OpenCore-Patcher 3.0.0 或更新版本：<a href=\"https://github.com/lzhoang2801/OpenCore-Legacy-Patcher/releases/tag/3.0.0\">lzhoang2801/OpenCore-Legacy-Patcher</a>。<br>"
                "官方 Dortania 版本或旧版补丁无法在 macOS Tahoe 26 上工作。"
            ).format(error_color=COLORS["error"], info_color="#00BCD4")
            if not show_confirmation("OpenCore Legacy Patcher 警告", content):
                return

        self.build_in_progress = True
        self.build_successful = False
        self.build_btn.setEnabled(False)
        self.build_btn.setText("构建中...")
        self.open_result_btn.setEnabled(False)
        
        self.progress_helper.update("loading", "准备构建...", 0)
        
        self.instructions_after_build_card.setVisible(False)
        self.build_log.clear()
        self.log_card.setVisible(True)
        
        thread = threading.Thread(target=self._start_build_thread, daemon=True)
        thread.start()

    def _start_build_thread(self):
        try:
            backend = self.controller.backend
            backend.o.gather_bootloader_kexts(backend.k.kexts, self.controller.macos_state.darwin_version)

            self._build_opencore_efi(
                self.controller.hardware_state.customized_hardware,
                self.controller.hardware_state.disabled_devices,
                self.controller.smbios_state.model_name,
                self.controller.macos_state.darwin_version,
                self.controller.macos_state.needs_oclp
            )
            
            bios_requirements = self._check_bios_requirements(
                self.controller.hardware_state.customized_hardware,
                self.controller.hardware_state.customized_hardware
            )
            
            self.build_complete_signal.emit(True, bios_requirements)
        except Exception as e:
            self.build_complete_signal.emit(False, None)

    def _check_bios_requirements(self, org_hardware_report, hardware_report):
        requirements = []
        
        org_firmware_type = org_hardware_report.get("BIOS", {}).get("Firmware Type", "未知")
        firmware_type = hardware_report.get("BIOS", {}).get("Firmware Type", "未知")
        if org_firmware_type == "Legacy" and firmware_type == "UEFI":
            requirements.append("启用 UEFI 模式（禁用 Legacy/CSM（兼容性支持模块））")

        secure_boot = hardware_report.get("BIOS", {}).get("Secure Boot", "未知")
        if secure_boot != "Disabled":
            requirements.append("禁用安全启动（Secure Boot）")
        
        if hardware_report.get("Motherboard", {}).get("Platform") == "Desktop" and hardware_report.get("Motherboard", {}).get("Chipset") in chipset_data.IntelChipsets[112:]:
            resizable_bar_enabled = any(gpu_props.get("Resizable BAR", "Disabled") == "Enabled" for gpu_props in hardware_report.get("GPU", {}).values())
            if not resizable_bar_enabled:
                requirements.append("启用 Above 4G Decoding")
                requirements.append("禁用 Resizable BAR/Smart Access Memory")
                
        return requirements

    def _build_opencore_efi(self, hardware_report, disabled_devices, smbios_model, macos_version, needs_oclp):
        steps = [
            "复制 EFI 基础文件到结果文件夹",
            "应用 ACPI 补丁",
            "复制驱动并快照到 config.plist",
            "生成 config.plist",
            "清理未使用的驱动、资源和工具"
        ]
        
        title = "构建 OpenCore EFI"
        current_step = 0

        progress = int((current_step / len(steps)) * 100)
        self.build_progress_signal.emit(title, steps, current_step, progress, False)
        current_step += 1
        
        backend = self.controller.backend
        backend.u.create_folder(backend.result_dir, remove_content=True)

        if not os.path.exists(backend.k.ock_files_dir):
            raise Exception("Directory \"{}\" does not exist.".format(backend.k.ock_files_dir))
        
        source_efi_dir = os.path.join(backend.k.ock_files_dir, "OpenCorePkg")
        shutil.copytree(source_efi_dir, backend.result_dir, dirs_exist_ok=True)

        config_file = os.path.join(backend.result_dir, "EFI", "OC", "config.plist")
        config_data = backend.u.read_file(config_file)
        
        if not config_data:
            raise Exception("Error: The file {} does not exist.".format(config_file))
        
        progress = int((current_step / len(steps)) * 100)
        self.build_progress_signal.emit(title, steps, current_step, progress, False)
        current_step += 1
        
        config_data["ACPI"]["Add"] = []
        config_data["ACPI"]["Delete"] = []
        config_data["ACPI"]["Patch"] = []
        
        acpi_directory = os.path.join(backend.result_dir, "EFI", "OC", "ACPI")
        
        if backend.ac.ensure_dsdt():
            backend.ac.hardware_report = hardware_report
            backend.ac.disabled_devices = disabled_devices
            backend.ac.acpi_directory = acpi_directory
            backend.ac.smbios_model = smbios_model
            backend.ac.lpc_bus_device = backend.ac.get_lpc_name()
            
            for patch in backend.ac.patches:
                if patch.checked:
                    if patch.name == "BATP":
                        patch.checked = getattr(backend.ac, patch.function_name)()
                        backend.k.kexts[kext_data.kext_index_by_name.get("ECEnabler")].checked = patch.checked
                        continue
                    
                    acpi_load = getattr(backend.ac, patch.function_name)()
                    if not isinstance(acpi_load, dict):
                        continue
                    
                    config_data["ACPI"]["Add"].extend(acpi_load.get("Add", []))
                    config_data["ACPI"]["Delete"].extend(acpi_load.get("Delete", []))
                    config_data["ACPI"]["Patch"].extend(acpi_load.get("Patch", []))
        
        config_data["ACPI"]["Patch"].extend(backend.ac.dsdt_patches)
        config_data["ACPI"]["Patch"] = backend.ac.apply_acpi_patches(config_data["ACPI"]["Patch"])

        progress = int((current_step / len(steps)) * 100)
        self.build_progress_signal.emit(title, steps, current_step, progress, False)
        current_step += 1
        
        kexts_directory = os.path.join(backend.result_dir, "EFI", "OC", "Kexts")
        backend.k.install_kexts_to_efi(macos_version, kexts_directory)
        config_data["Kernel"]["Add"] = backend.k.load_kexts(hardware_report, macos_version, kexts_directory)

        progress = int((current_step / len(steps)) * 100)
        self.build_progress_signal.emit(title, steps, current_step, progress, False)
        current_step += 1
        
        audio_layout_id = self.controller.hardware_state.audio_layout_id
        audio_controller_properties = self.controller.hardware_state.audio_controller_properties
        
        backend.co.genarate(
            hardware_report,
            disabled_devices,
            smbios_model,
            macos_version,
            needs_oclp,
            backend.k.kexts,
            config_data,
            audio_layout_id,
            audio_controller_properties
        )
        
        backend.u.write_file(config_file, config_data)

        progress = int((current_step / len(steps)) * 100)
        self.build_progress_signal.emit(title, steps, current_step, progress, False)
        files_to_remove = []

        drivers_directory = os.path.join(backend.result_dir, "EFI", "OC", "Drivers")
        driver_list = backend.u.find_matching_paths(drivers_directory, extension_filter=".efi")
        driver_loaded = [kext.get("Path") for kext in config_data.get("UEFI").get("Drivers")]
        for driver_path, type in driver_list:
            if not driver_path in driver_loaded:
                files_to_remove.append(os.path.join(drivers_directory, driver_path))

        resources_audio_dir = os.path.join(backend.result_dir, "EFI", "OC", "Resources", "Audio")
        if os.path.exists(resources_audio_dir):
            files_to_remove.append(resources_audio_dir)

        picker_variant = config_data.get("Misc", {}).get("Boot", {}).get("PickerVariant")
        if picker_variant in (None, "Auto"):
            picker_variant = "Acidanthera/GoldenGate" 
        if os.name == "nt":
            picker_variant = picker_variant.replace("/", "\\")

        resources_image_dir = os.path.join(backend.result_dir, "EFI", "OC", "Resources", "Image")
        available_picker_variants = backend.u.find_matching_paths(resources_image_dir, type_filter="dir")

        for variant_name, variant_type in available_picker_variants:
            variant_path = os.path.join(resources_image_dir, variant_name)
            if ".icns" in ", ".join(os.listdir(variant_path)):
                if picker_variant not in variant_name:
                    files_to_remove.append(variant_path)

        tools_directory = os.path.join(backend.result_dir, "EFI", "OC", "Tools")
        tool_list = backend.u.find_matching_paths(tools_directory, extension_filter=".efi")
        tool_loaded = [tool.get("Path") for tool in config_data.get("Misc").get("Tools")]
        for tool_path, type in tool_list:
            if not tool_path in tool_loaded:
                files_to_remove.append(os.path.join(tools_directory, tool_path))

        if "manifest.json" in os.listdir(backend.result_dir):
            files_to_remove.append(os.path.join(backend.result_dir, "manifest.json"))

        for file_path in files_to_remove:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            except Exception as e:
                backend.u.log_message("[BUILD] Failed to remove file {}: {}".format(os.path.basename(file_path), e), level="WARNING", to_build_log=True)
        
        self.build_progress_signal.emit(title, steps, len(steps) - 1, 100, True)

    def show_post_build_instructions(self, bios_requirements):
        while self.instructions_after_content_layout.count():
            item = self.instructions_after_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if bios_requirements:
            bios_header = StrongBodyLabel("1. BIOS/UEFI 设置要求：")
            bios_header.setStyleSheet("color: {}; font-size: 14px;".format(COLORS["warning_text"]))
            self.instructions_after_content_layout.addWidget(bios_header)
            
            bios_text = "\n".join(["  • {}".format(req) for req in bios_requirements])
            bios_label = BodyLabel(bios_text)
            bios_label.setWordWrap(True)
            bios_label.setStyleSheet("color: #424242; line-height: 1.6;")
            self.instructions_after_content_layout.addWidget(bios_label)
            
            self.instructions_after_content_layout.addSpacing(SPACING["medium"])
        
        usb_header = StrongBodyLabel("{}. USB 端口映射：".format(2 if bios_requirements else 1))
        usb_header.setStyleSheet("color: {}; font-size: 14px;".format(COLORS["warning_text"]))
        self.instructions_after_content_layout.addWidget(usb_header)
        
        path_sep = "\\" if platform.system() == "Windows" else "/"
        
        usb_mapping_instructions = (
            "1. 使用 USBToolBox 工具映射 USB 端口<br>"
            "2. 将创建的 UTBMap.kext 添加到 EFI{path_sep}OC{path_sep}Kexts 文件夹<br>"
            "3. 从 EFI{path_sep}OC{path_sep}Kexts 文件夹中删除 UTBDefault.kext<br>"
            "4. 使用 ProperTree 编辑 config.plist：<br>"
            "   a. 运行 OC Snapshot（Command/Ctrl + R）<br>"
            "   b. 如果每个控制器有超过 15 个端口，启用 XhciPortLimit quirk<br>"
            "   c. 完成后保存文件。"
        ).format(path_sep=path_sep)
        
        usb_label = BodyLabel(usb_mapping_instructions)
        usb_label.setWordWrap(True)
        usb_label.setStyleSheet("color: #424242; line-height: 1.6;")
        self.instructions_after_content_layout.addWidget(usb_label)
        
        self.instructions_after_build_card.setVisible(True)

    def _handle_build_complete(self, success, bios_requirements):
        self.build_in_progress = False
        self.build_successful = success
        
        if success:
            self.log_card.setVisible(False)
            self.progress_helper.update("success", "构建成功完成！", 100)
            
            self.show_post_build_instructions(bios_requirements)
            self._load_configs_after_build()
            
            self.build_btn.setText("构建 OpenCore EFI")
            self.build_btn.setEnabled(True)
            self.open_result_btn.setEnabled(True)
            
            success_message = "您的 OpenCore EFI 已成功构建！"
            if bios_requirements is not None:
                success_message += " 请查看下方的重要说明。"
            
            self.controller.update_status(success_message, "success")
        else:
            self.progress_helper.update("error", "构建 OpenCore EFI 失败", None)
            
            self.config_editor.setVisible(False)
            
            self.build_btn.setText("重试构建 OpenCore EFI")
            self.build_btn.setEnabled(True)
            self.open_result_btn.setEnabled(False)
            
            self.controller.update_status("构建过程中发生错误。请查看日志了解详情。", "error")

    def open_result(self):
        result_dir = self.controller.backend.result_dir
        try:
            self.controller.backend.u.open_folder(result_dir)
        except Exception as e:
            self.controller.update_status("无法打开结果文件夹：{}".format(e), "warning")

    def _load_configs_after_build(self):
        backend = self.controller.backend
        
        source_efi_dir = os.path.join(backend.k.ock_files_dir, "OpenCorePkg")
        original_config_file = os.path.join(source_efi_dir, "EFI", "OC", "config.plist")
        
        if not os.path.exists(original_config_file):
            return
        
        original_config = backend.u.read_file(original_config_file)
        if not original_config:
            return
        
        modified_config_file = os.path.join(backend.result_dir, "EFI", "OC", "config.plist")
        
        if not os.path.exists(modified_config_file):
            return
        
        modified_config = backend.u.read_file(modified_config_file)
        if not modified_config:
            return
        
        context = {
            "hardware_report": self.controller.hardware_state.hardware_report,
            "macos_version": self.controller.macos_state.darwin_version,
            "smbios_model": self.controller.smbios_state.model_name,
        }
        
        self.config_editor.load_configs(original_config, modified_config, context)
        self.config_editor.setVisible(True)

    def refresh(self):
        if not self.build_in_progress:
            if self.build_successful:
                self.progress_container.setVisible(True)
                self.open_result_btn.setEnabled(True)
            else:
                log_text = self.build_log.toPlainText()
                if not log_text or log_text == DEFAULT_LOG_TEXT:
                    self.progress_container.setVisible(False)
                    self.log_card.setVisible(False)
                self.open_result_btn.setEnabled(False)