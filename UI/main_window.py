import sys
import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QFrame,
    QGridLayout, QScrollArea, QProgressBar, QCheckBox, QSpacerItem,
    QSizePolicy, QGroupBox, QFormLayout, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap

from ui_components import ModernButton, ModernCard, StatusIndicator, ProjectCard
from api_client import APIClient
from settings_manager import SettingsManager


class StatusUpdateThread(QThread):
    status_updated = pyqtSignal(dict)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.running = True
    
    def run(self):
        while self.running:
            try:
                status = self.api_client.get_status()
                if status:
                    self.status_updated.emit(status)
            except Exception as e:
                print(f"Error fetching status: {e}")
            self.msleep(5000)
    
    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.settings_manager = SettingsManager()
        self.status_thread = None
        
        self.setWindowTitle("UniTime - Time Tracking Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)
        
        self.setup_ui()
        self.apply_modern_style()
        self.setup_status_updates()
        self.load_initial_data()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header = self.create_header()
        layout.addWidget(header)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        self.dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        self.projects_tab = self.create_projects_tab()
        self.tab_widget.addTab(self.projects_tab, "Projects")
        
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        layout.addWidget(self.tab_widget)
    
    def create_header(self):
        header = QFrame()
        header.setFixedHeight(90)
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                margin-bottom: 8px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)
        header_layout.setSpacing(20)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel("UniTime")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 0; padding: 0;")
        
        subtitle = QLabel("Advanced Time Tracking for Developers")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet("color: #6c757d; font-weight: 500; margin: 0; padding: 0;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        self.status_indicator = StatusIndicator()
        header_layout.addWidget(self.status_indicator)
        
        return header
    
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.tracked_files_card = ModernCard("Tracked Files", "0", "")
        self.active_projects_card = ModernCard("Active Projects", "0", "")
        self.heartbeats_card = ModernCard("Pending Heartbeats", "0", "")
        self.time_active_card = ModernCard("Time Since Activity", "0s", "")
        
        stats_layout.addWidget(self.tracked_files_card)
        stats_layout.addWidget(self.active_projects_card)
        stats_layout.addWidget(self.heartbeats_card)
        stats_layout.addWidget(self.time_active_card)
        
        layout.addLayout(stats_layout)
        
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(200)
        self.activity_log.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 16px;
                font-family: 'Courier New', 'Monaco', monospace;
                font-size: 13px;
                line-height: 1.4;
                color: #495057;
            }
            QScrollBar:vertical {
                background: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #ced4da;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #adb5bd;
            }
        """)
        
        log_layout.addWidget(self.activity_log)
        layout.addWidget(log_group)
        
        status_group = QGroupBox("Tracking Status")
        status_layout = QGridLayout(status_group)
        
        self.api_status_label = QLabel("API Status: Checking...")
        self.api_key_status_label = QLabel("API Key: Not configured")
        self.tracking_status_label = QLabel("Tracking: Inactive")
        
        status_layout.addWidget(self.api_status_label, 0, 0)
        status_layout.addWidget(self.api_key_status_label, 0, 1)
        status_layout.addWidget(self.tracking_status_label, 1, 0)
        
        layout.addWidget(status_group)
        
        return widget
    
    def create_projects_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        add_project_group = QGroupBox("Add New Project")
        add_project_layout = QVBoxLayout(add_project_group)
        
        form_layout = QHBoxLayout()
        form_layout.setSpacing(12)
        
        path_label = QLabel("Project Path:")
        path_label.setFont(QFont("Arial", 14, QFont.Weight.Medium))
        path_label.setMinimumWidth(100)
        
        self.project_path_input = QLineEdit()
        self.project_path_input.setPlaceholderText("Click 'Browse' to select a project folder...")
        self.project_path_input.setReadOnly(True)
        self.project_path_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px dashed #dee2e6;
            }
            QLineEdit:hover {
                border-color: #3498db;
                background-color: #e7f3ff;
            }
        """)
        
        browse_button = ModernButton("Browse Folder", primary=True)
        browse_button.clicked.connect(self.browse_project_folder)
        browse_button.setFixedSize(140, 42)
        
        add_button = ModernButton("Add Project")
        add_button.clicked.connect(self.add_project)
        add_button.setFixedSize(120, 42)
        
        form_layout.addWidget(path_label)
        form_layout.addWidget(self.project_path_input, 1)
        form_layout.addWidget(browse_button)
        form_layout.addWidget(add_button)
        
        add_project_layout.addLayout(form_layout)
        layout.addWidget(add_project_group)
        
        projects_group = QGroupBox("Tracked Projects")
        projects_layout = QVBoxLayout(projects_group)
        
        self.projects_scroll = QScrollArea()
        self.projects_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #f8f9fa;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #ced4da;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #adb5bd;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        self.projects_widget = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_widget)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(8)
        
        self.projects_scroll.setWidget(self.projects_widget)
        self.projects_scroll.setWidgetResizable(True)
        self.projects_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.projects_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        projects_layout.addWidget(self.projects_scroll)
        layout.addWidget(projects_group)
        
        return widget
    
    def create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout(api_group)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your HackaTime API key...")
        
        self.api_url_input = QLineEdit()
        self.api_url_input.setText("https://hackatime.hackclub.com/api/v1")
        
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Default project name (optional)")
        
        api_layout.addRow("API Key:", self.api_key_input)
        api_layout.addRow("API URL:", self.api_url_input)
        api_layout.addRow("Default Project:", self.project_name_input)
        
        layout.addWidget(api_group)
        
        ide_group = QGroupBox("IDE Configuration")
        ide_layout = QFormLayout(ide_group)
        
        self.ide_selector = QComboBox()
        self.ide_selector.addItems(["Zed", "VSCode", "Other"])
        
        self.heartbeat_interval_input = QSpinBox()
        self.heartbeat_interval_input.setMinimum(10)
        self.heartbeat_interval_input.setMaximum(300)
        self.heartbeat_interval_input.setValue(30)
        self.heartbeat_interval_input.setSuffix(" seconds")
        
        ide_layout.addRow("IDE:", self.ide_selector)
        ide_layout.addRow("Heartbeat Interval:", self.heartbeat_interval_input)
        
        layout.addWidget(ide_group)
        
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        self.auto_start_checkbox = QCheckBox("Start tracking automatically")
        self.auto_start_checkbox.setChecked(True)
        
        self.debug_mode_checkbox = QCheckBox("Enable debug mode")
        
        advanced_layout.addRow(self.auto_start_checkbox)
        advanced_layout.addRow(self.debug_mode_checkbox)
        
        layout.addWidget(advanced_group)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = ModernButton("Save Settings", primary=True)
        save_button.clicked.connect(self.save_settings)
        
        reset_button = ModernButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_settings)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(reset_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return widget
    
    def apply_modern_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 12px;
                margin-top: 4px;
            }
            
            QTabWidget::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #6c757d;
                padding: 14px 24px;
                margin-right: 4px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-weight: 600;
                font-size: 14px;
                min-width: 100px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #3498db;
                border-bottom: 3px solid #3498db;
                margin-bottom: -1px;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
                color: #495057;
            }
            
            QGroupBox {
                font-weight: 600;
                font-size: 16px;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: white;
                color: #2c3e50;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                background-color: white;
            }
            
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #495057;
            }
            
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            
            QLineEdit:hover {
                border-color: #ced4da;
            }
            
            QComboBox {
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                color: #495057;
                min-width: 120px;
            }
            
            QComboBox:focus {
                border-color: #3498db;
            }
            
            QComboBox:hover {
                border-color: #ced4da;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6c757d;
            }
            
            QSpinBox {
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                color: #495057;
            }
            
            QSpinBox:focus {
                border-color: #3498db;
            }
            
            QSpinBox:hover {
                border-color: #ced4da;
            }
            
            QCheckBox {
                font-size: 14px;
                color: #495057;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #e9ecef;
                border-radius: 4px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                image: none;
            }
            
            QCheckBox::indicator:hover {
                border-color: #ced4da;
            }
            
            QLabel {
                color: #495057;
            }
            
            QFormLayout QLabel {
                font-weight: 600;
                margin-bottom: 4px;
            }
        """)
    
    def setup_status_updates(self):
        self.status_thread = StatusUpdateThread(self.api_client)
        self.status_thread.status_updated.connect(self.update_dashboard)
        self.status_thread.start()
    
    def load_initial_data(self):
        settings = self.settings_manager.load_settings()
        
        if settings:
            self.api_key_input.setText(settings.get('api_key', ''))
            self.api_url_input.setText(settings.get('api_url', 'https://hackatime.hackclub.com/api/v1'))
            self.project_name_input.setText(settings.get('default_project', ''))
            
            ide = settings.get('ide', 'Zed')
            idx = self.ide_selector.findText(ide)
            if idx >= 0:
                self.ide_selector.setCurrentIndex(idx)
            
            self.heartbeat_interval_input.setValue(settings.get('heartbeat_interval', 30))
            self.auto_start_checkbox.setChecked(settings.get('auto_start', True))
            self.debug_mode_checkbox.setChecked(settings.get('debug_mode', False))
        
        self.refresh_projects()
    
    def browse_project_folder(self):
        last_dir = self.settings_manager.get_setting('last_browse_dir', str(Path.home()))
        
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Project Folder to Track",
            last_dir,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if folder:
            self.settings_manager.set_setting('last_browse_dir', str(Path(folder).parent))
            
            self.project_path_input.setText(folder)
            self.project_path_input.setStyleSheet("""
                QLineEdit {
                    background-color: #d4edda;
                    color: #155724;
                    border: 2px solid #c3e6cb;
                }
            """)
            
            folder_info = f"Selected: {Path(folder).name}"
            self.project_path_input.setToolTip(f"Full path: {folder}")
            
            print(f"Selected project folder: {folder}")
    
    def add_project(self):
        path = self.project_path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "Warning", "Please select a project folder using the 'Browse Folder' button.")
            return
        
        if not os.path.exists(path):
            QMessageBox.warning(self, "Warning", "The selected folder does not exist.")
            return
        
        try:
            success = self.api_client.add_project(path)
            if success:
                QMessageBox.information(self, "Success", f"Project added successfully!\nPath: {path}")
                self.project_path_input.clear()
                self.project_path_input.setStyleSheet("""
                    QLineEdit {
                        background-color: #f8f9fa;
                        color: #6c757d;
                        border: 2px dashed #dee2e6;
                    }
                    QLineEdit:hover {
                        border-color: #3498db;
                        background-color: #e7f3ff;
                    }
                """)
                self.refresh_projects()
            else:
                QMessageBox.warning(self, "Error", "Failed to add project. Check if the API server is running.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add project: {str(e)}")
    
    def refresh_projects(self):
        for i in reversed(range(self.projects_layout.count())):
            child = self.projects_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        try:
            status = self.api_client.get_status()
            if status and 'stats' in status:
                tracked_dirs = status['stats'].get('tracked_directories', [])
                
                for project_path in tracked_dirs:
                    project_card = ProjectCard(project_path, self.remove_project, self.edit_project)
                    self.projects_layout.addWidget(project_card)
                
                self.projects_layout.addStretch()
        except Exception as e:
            print(f"Error refreshing projects: {e}")
    
    def remove_project(self, project_path):
        reply = QMessageBox.question(
            self,
            "Remove Project",
            f"Are you sure you want to stop tracking this project?\n\n{project_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.api_client.remove_project(project_path)
                if success:
                    QMessageBox.information(self, "Success", "Project removed successfully!")
                    self.refresh_projects()
                else:
                    QMessageBox.warning(self, "Error", "Failed to remove project.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove project: {str(e)}")
    
    def edit_project(self, project_path):
        reply = QMessageBox.question(
            self,
            "Edit Project",
            f"Do you want to change the path for this project?\n\nCurrent path: {project_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            new_folder = QFileDialog.getExistingDirectory(
                self, 
                "Select New Project Folder",
                project_path
            )
            
            if new_folder and new_folder != project_path:
                try:
                    remove_success = self.api_client.remove_project(project_path)
                    if remove_success:
                        add_success = self.api_client.add_project(new_folder)
                        if add_success:
                            QMessageBox.information(
                                self, 
                                "Success", 
                                f"Project updated successfully!\nOld: {project_path}\nNew: {new_folder}"
                            )
                            self.refresh_projects()
                        else:
                            self.api_client.add_project(project_path)
                            QMessageBox.warning(
                                self, 
                                "Error", 
                                "Failed to add new project path. Restored original project."
                            )
                    else:
                        QMessageBox.warning(self, "Error", "Failed to remove original project.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to edit project: {str(e)}")
    
    def save_settings(self):
        settings = {
            'api_key': self.api_key_input.text().strip(),
            'api_url': self.api_url_input.text().strip(),
            'default_project': self.project_name_input.text().strip(),
            'ide': self.ide_selector.currentText(),
            'heartbeat_interval': self.heartbeat_interval_input.value(),
            'auto_start': self.auto_start_checkbox.isChecked(),
            'debug_mode': self.debug_mode_checkbox.isChecked()
        }
        
        try:
            self.settings_manager.save_settings(settings)
            
            if settings['api_key']:
                self.api_client.update_config({
                    'api_key': settings['api_key'],
                    'api_url': settings['api_url'],
                    'project': settings['default_project']
                })
            
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def reset_settings(self):
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.api_key_input.clear()
            self.api_url_input.setText("https://hackatime.hackclub.com/api/v1")
            self.project_name_input.clear()
            self.ide_selector.setCurrentIndex(0)
            self.heartbeat_interval_input.setValue(30)
            self.auto_start_checkbox.setChecked(True)
            self.debug_mode_checkbox.setChecked(False)
    
    def update_dashboard(self, status):
        try:
            if status.get('status') == 'running':
                self.status_indicator.set_status('connected')
            else:
                self.status_indicator.set_status('disconnected')
            
            stats = status.get('stats', {})
            self.tracked_files_card.update_value(str(stats.get('tracked_files', 0)))
            self.active_projects_card.update_value(str(len(stats.get('tracked_directories', []))))
            self.heartbeats_card.update_value(str(stats.get('pending_heartbeats', 0)))
            
            time_since_activity = stats.get('time_since_last_activity', 0)
            if time_since_activity < 60:
                time_str = f"{time_since_activity:.0f}s"
            elif time_since_activity < 3600:
                time_str = f"{time_since_activity/60:.1f}m"
            else:
                time_str = f"{time_since_activity/3600:.1f}h"
            self.time_active_card.update_value(time_str)
            
            self.api_status_label.setText(f"API Status: {status.get('status', 'Unknown').title()}")
            self.api_key_status_label.setText(f"API Key: {'Configured' if status.get('api_key_configured') else 'Not configured'}")
            self.tracking_status_label.setText(f"Tracking: {'Active' if stats.get('is_tracking_active') else 'Inactive'}")
            
            if stats.get('is_tracking_active'):
                log_entry = f"[{self.get_current_time()}] Tracking active - {stats.get('tracked_files', 0)} files monitored"
                self.activity_log.append(log_entry)
                
                if self.activity_log.document().lineCount() > 100:
                    cursor = self.activity_log.textCursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    cursor.select(cursor.SelectionType.LineUnderCursor)
                    cursor.removeSelectedText()
        
        except Exception as e:
            print(f"Error updating dashboard: {e}")
    
    def get_current_time(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def closeEvent(self, event):
        if self.status_thread:
            self.status_thread.stop()
            self.status_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    app.setApplicationName("UniTime")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("UniTime")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
