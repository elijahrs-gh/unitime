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
        
        self.setWindowTitle("Unitime - Time Tracking Dashboard")
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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
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
        
        layout.addWidget(self.tab_widget, 1)
    
    def create_header(self):
        header = QFrame()
        header.setFixedHeight(90)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #667eea, stop: 1 #764ba2);
                border: none;
                border-radius: 16px;
                margin-bottom: 8px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)
        header_layout.setSpacing(20)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        title = QLabel("Unitime")
        title.setFont(QFont("Arial", 30, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin: 0; padding: 0;")
        title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        subtitle = QLabel("Advanced Time Tracking for Developers")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-weight: 500; margin: 0; padding: 0;")
        subtitle.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout, 1)
        
        stats_container = QWidget()
        stats_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 8px 16px;
            }
        """)
        stats_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(16, 8, 16, 8)
        stats_layout.setSpacing(16)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.quick_projects_count = QLabel("0")
        self.quick_projects_count.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.quick_projects_count.setStyleSheet("color: white;")
        self.quick_projects_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        projects_label = QLabel("Projects")
        projects_label.setFont(QFont("Arial", 11))
        projects_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        projects_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        projects_widget = QWidget()
        projects_widget_layout = QVBoxLayout(projects_widget)
        projects_widget_layout.setContentsMargins(0, 0, 0, 0)
        projects_widget_layout.setSpacing(2)
        projects_widget_layout.addWidget(self.quick_projects_count)
        projects_widget_layout.addWidget(projects_label)
        
        stats_layout.addWidget(projects_widget)
        header_layout.addWidget(stats_container)
        
        self.status_indicator = StatusIndicator()
        self.status_indicator.setFixedHeight(36)
        header_layout.addWidget(self.status_indicator)
        
        return header
    
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.tracked_files_card = ModernCard("Tracked Files", "0", "📁")
        self.active_projects_card = ModernCard("Active Projects", "0", "🚀")
        self.heartbeats_card = ModernCard("Pending Heartbeats", "0", "💓")
        self.time_active_card = ModernCard("Time Since Activity", "0s", "⏱️")
        
        for card in [self.tracked_files_card, self.active_projects_card, 
                    self.heartbeats_card, self.time_active_card]:
            card.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #ffffff, stop: 1 #f8f9fa);
                    border: 1px solid #e9ecef;
                    border-radius: 20px;
                    min-height: 120px;
                    max-height: 160px;
                }
                QFrame:hover {
                    border-color: #3498db;
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #f8f9fa, stop: 1 #ffffff);
                }
            """)
        
        stats_layout.addWidget(self.tracked_files_card, 1)
        stats_layout.addWidget(self.active_projects_card, 1)
        stats_layout.addWidget(self.heartbeats_card, 1)
        stats_layout.addWidget(self.time_active_card, 1)
        
        layout.addLayout(stats_layout)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        log_group = QGroupBox("Activity Log")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 18px;
                border: 2px solid #e9ecef;
                border-radius: 16px;
                margin-top: 16px;
                padding-top: 20px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 12px 0 12px;
                color: #2c3e50;
                background-color: white;
                border-radius: 8px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(16, 20, 16, 16)
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(250)
        self.activity_log.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #fafbfc, stop: 1 #f1f3f4);
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 16px;
                font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
                font-size: 13px;
                line-height: 1.6;
                color: #495057;
            }
            QTextEdit:focus {
                border-color: #3498db;
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
        content_layout.addWidget(log_group, 2)
        
        status_group = QGroupBox("⚡ Tracking Status")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 18px;
                border: 2px solid #e9ecef;
                border-radius: 16px;
                margin-top: 16px;
                padding-top: 20px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 12px 0 12px;
                color: #2c3e50;
                background-color: white;
                border-radius: 8px;
            }
        """)
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(16, 20, 16, 16)
        status_layout.setSpacing(16)
        
        self.api_status_label = QLabel("🔗 API Status: Checking...")
        self.api_key_status_label = QLabel("🔑 API Key: Not configured")
        self.tracking_status_label = QLabel("📡 Tracking: Inactive")
        
        for label in [self.api_status_label, self.api_key_status_label, self.tracking_status_label]:
            label.setFont(QFont("Arial", 14, QFont.Weight.Medium))
            label.setStyleSheet("""
                QLabel {
                    color: #495057;
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 12px;
                    padding: 12px 16px;
                    font-weight: 600;
                }
            """)
        
        status_layout.addWidget(self.api_status_label)
        status_layout.addWidget(self.api_key_status_label)
        status_layout.addWidget(self.tracking_status_label)
        status_layout.addStretch()
        
        content_layout.addWidget(status_group, 1)
        layout.addLayout(content_layout)
        
        return widget
    
    def create_projects_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        
        add_project_group = QGroupBox("➕ Add New Project")
        add_project_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 18px;
                border: 2px solid #e9ecef;
                border-radius: 16px;
                margin-top: 16px;
                padding-top: 20px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 12px 0 12px;
                color: #2c3e50;
                background-color: white;
                border-radius: 8px;
            }
        """)
        add_project_layout = QVBoxLayout(add_project_group)
        add_project_layout.setContentsMargins(20, 24, 20, 20)
        
        form_layout = QHBoxLayout()
        form_layout.setSpacing(12)
        
        path_label = QLabel("📁 Project Path:")
        path_label.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        path_label.setFixedWidth(120)
        path_label.setStyleSheet("color: #495057;")
        
        self.project_path_input = QLineEdit()
        self.project_path_input.setPlaceholderText("Click 'Browse' to select a project folder...")
        self.project_path_input.setReadOnly(True)
        self.project_path_input.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #fafbfc, stop: 1 #f1f3f4);
                color: #6c757d;
                border: 2px dashed #dee2e6;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit:hover {
                border-color: #3498db;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e7f3ff, stop: 1 #f0f8ff);
            }
        """)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        browse_button = ModernButton("📂 Browse", primary=True)
        browse_button.clicked.connect(self.browse_project_folder)
        browse_button.setFixedSize(120, 40)
        browse_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5a6fd8, stop: 1 #6a4190);
            }
            QPushButton:pressed {
            }
        """)
        
        add_button = ModernButton("✨ Add Project")
        add_button.clicked.connect(self.add_project)
        add_button.setFixedSize(120, 40)
        add_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4facfe, stop: 1 #00f2fe);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #429cec, stop: 1 #00e0ec);
            }
            QPushButton:pressed {
            }
        """)
        
        buttons_layout.addWidget(browse_button)
        buttons_layout.addWidget(add_button)
        
        form_layout.addWidget(path_label)
        form_layout.addWidget(self.project_path_input, 1)
        form_layout.addLayout(buttons_layout)
        
        add_project_layout.addLayout(form_layout)
        layout.addWidget(add_project_group)
        
        projects_group = QGroupBox("Tracked Projects")
        projects_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 18px;
                border: 2px solid #e9ecef;
                border-radius: 16px;
                margin-top: 16px;
                padding-top: 20px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 12px 0 12px;
                color: #2c3e50;
                background-color: white;
                border-radius: 8px;
            }
        """)
        projects_layout = QVBoxLayout(projects_group)
        projects_layout.setContentsMargins(20, 24, 20, 20)
        
        self.projects_scroll = QScrollArea()
        self.projects_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
                border-radius: 12px;
            }
            QScrollBar:vertical {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #ced4da, stop: 1 #adb5bd);
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #adb5bd, stop: 1 #868e96);
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
        self.projects_layout.setSpacing(12)
        self.projects_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.projects_scroll.setWidget(self.projects_widget)
        self.projects_scroll.setWidgetResizable(True)
        self.projects_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.projects_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        projects_layout.addWidget(self.projects_scroll)
        layout.addWidget(projects_group, 1)
        
        return widget
    
    def create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)
        
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout(api_group)
        api_layout.setContentsMargins(16, 20, 16, 16)
        api_layout.setSpacing(12)
        api_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your HackaTime API key...")
        self.api_key_input.setMinimumWidth(300)
        
        self.api_url_input = QLineEdit()
        self.api_url_input.setText("https://hackatime.hackclub.com/api/v1")
        self.api_url_input.setMinimumWidth(300)
        
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Default project name (optional)")
        self.project_name_input.setMinimumWidth(300)
        
        label_style = "QLabel { font-weight: 600; font-size: 14px; color: #495057; margin-bottom: 4px; }"
        
        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet(label_style)
        
        api_url_label = QLabel("API URL:")
        api_url_label.setStyleSheet(label_style)
        
        project_name_label = QLabel("Default Project:")
        project_name_label.setStyleSheet(label_style)
        
        api_layout.addRow(api_key_label, self.api_key_input)
        api_layout.addRow(api_url_label, self.api_url_input)
        api_layout.addRow(project_name_label, self.project_name_input)
        
        layout.addWidget(api_group)
        
        ide_group = QGroupBox("IDE Configuration")
        ide_layout = QFormLayout(ide_group)
        ide_layout.setContentsMargins(16, 20, 16, 16)
        ide_layout.setSpacing(12)
        ide_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.ide_selector = QComboBox()
        self.ide_selector.addItems(["Zed", "VSCode", "Other"])
        self.ide_selector.setMinimumWidth(200)
        
        self.heartbeat_interval_input = QSpinBox()
        self.heartbeat_interval_input.setMinimum(10)
        self.heartbeat_interval_input.setMaximum(300)
        self.heartbeat_interval_input.setValue(30)
        self.heartbeat_interval_input.setSuffix(" seconds")
        self.heartbeat_interval_input.setMinimumWidth(200)
        
        ide_label = QLabel("IDE:")
        ide_label.setStyleSheet(label_style)
        
        heartbeat_label = QLabel("Heartbeat Interval:")
        heartbeat_label.setStyleSheet(label_style)
        
        ide_layout.addRow(ide_label, self.ide_selector)
        ide_layout.addRow(heartbeat_label, self.heartbeat_interval_input)
        
        layout.addWidget(ide_group)
        
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        advanced_layout.setContentsMargins(16, 20, 16, 16)
        advanced_layout.setSpacing(12)
        
        self.auto_start_checkbox = QCheckBox("Start tracking automatically")
        self.auto_start_checkbox.setChecked(True)
        
        self.debug_mode_checkbox = QCheckBox("Enable debug mode")
        
        advanced_layout.addRow("", self.auto_start_checkbox)
        advanced_layout.addRow("", self.debug_mode_checkbox)
        
        layout.addWidget(advanced_group)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        save_button = ModernButton("Save Settings", primary=True)
        save_button.clicked.connect(self.save_settings)
        save_button.setFixedSize(140, 38)
        
        reset_button = ModernButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_settings)
        reset_button.setFixedSize(140, 38)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(reset_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return widget
    
    def apply_modern_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
            }
            
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                background-color: white;
                border-radius: 16px;
                margin-top: 8px;
            }
            
            QTabWidget::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                color: #6c757d;
                padding: 16px 24px;
                margin-right: 6px;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                font-weight: 700;
                font-size: 14px;
                min-width: 120px;
                border: 2px solid #e9ecef;
                border-bottom: none;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
                color: white;
                border-color: #667eea;
                margin-bottom: -2px;
                font-weight: 800;
            }
            
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f1f3f4, stop: 1 #e8eaed);
                color: #495057;
                border-color: #ced4da;
            }
            
            QGroupBox {
                font-weight: 700;
                font-size: 18px;
                border: 2px solid #e9ecef;
                border-radius: 16px;
                margin-top: 16px;
                padding-top: 20px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                color: #2c3e50;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 12px 0 12px;
                color: #2c3e50;
                background-color: white;
                border-radius: 8px;
                font-weight: 800;
            }
            
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                font-size: 14px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                color: #495057;
                min-height: 20px;
                font-weight: 500;
            }
            
            QLineEdit:focus {
                border-color: #667eea;
                outline: none;
                background: white;
            }
            
            QLineEdit:hover {
                border-color: #ced4da;
                background: white;
            }
            
            QComboBox {
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                font-size: 14px;
                color: #495057;
                min-width: 120px;
                min-height: 20px;
                font-weight: 500;
            }
            
            QComboBox:focus {
                border-color: #667eea;
                background: white;
            }
            
            QComboBox:hover {
                border-color: #ced4da;
                background: white;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 24px;
                padding-right: 8px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #6c757d;
            }
            
            QSpinBox {
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                font-size: 14px;
                color: #495057;
                min-height: 20px;
                font-weight: 500;
            }
            
            QSpinBox:focus {
                border-color: #667eea;
                background: white;
            }
            
            QSpinBox:hover {
                border-color: #ced4da;
                background: white;
            }
            
            QCheckBox {
                font-size: 14px;
                color: #495057;
                spacing: 10px;
                font-weight: 500;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
                border-color: #667eea;
                image: none;
            }
            
            QCheckBox::indicator:hover {
                border-color: #ced4da;
                background: white;
            }
            
            QLabel {
                color: #495057;
                font-weight: 500;
            }
            
            QFormLayout QLabel {
                font-weight: 600;
                margin-bottom: 6px;
                color: #2c3e50;
            }
            
            /* Enhanced scrollbar styling */
            QScrollBar:vertical {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #ced4da, stop: 1 #adb5bd);
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #adb5bd, stop: 1 #868e96);
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ced4da, stop: 1 #adb5bd);
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #adb5bd, stop: 1 #868e96);
            }
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
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
            item = self.projects_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.spacerItem():
                self.projects_layout.removeItem(item)
        
        try:
            status = self.api_client.get_status()
            if status and 'stats' in status:
                tracked_dirs = status['stats'].get('tracked_directories', [])
                
                if tracked_dirs:
                    for project_path in tracked_dirs:
                        project_card = ProjectCard(
                            project_path, 
                            remove_callback=self.remove_project, 
                            edit_callback=self.edit_project
                        )
                        self.projects_layout.addWidget(project_card)
                else:
                    empty_message = QLabel("No projects are currently being tracked. Add a project using the form above.")
                    empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    empty_message.setStyleSheet("""
                        color: #6c757d;
                        font-size: 14px;
                        padding: 20px;
                        font-style: italic;
                    """)
                    self.projects_layout.addWidget(empty_message)
                
                self.projects_layout.addStretch()
        except Exception as e:
            print(f"Error refreshing projects: {e}")
            
            error_message = QLabel(f"Error loading projects: {str(e)}")
            error_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_message.setStyleSheet("""
                color: #721c24;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 8px;
                font-size: 14px;
                padding: 16px;
            """)
            self.projects_layout.addWidget(error_message)
            self.projects_layout.addStretch()
    
    def remove_project(self, project_path):
        try:
            success = self.api_client.remove_project(project_path)
            if success:
                QMessageBox.information(
                    self, 
                    "Project Removed", 
                    f"Project has been removed from tracking:\n{project_path}",
                    QMessageBox.StandardButton.Ok
                )
                self.refresh_projects()
            else:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Failed to remove project from tracking:\n{project_path}\n\nPlease check if the API server is running."
                )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to remove project: {str(e)}\n\nProject: {project_path}"
            )
    
    def edit_project(self, project_path, project_data=None):
        if project_data:
            print(f"Project updated: {project_data}")
            self.refresh_projects()
        else:
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
                    'project': settings['default_project'],
                    'ide': settings['ide'],
                    'heartbeat_interval': settings['heartbeat_interval']
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
            
            project_count = len(stats.get('tracked_directories', []))
            self.active_projects_card.update_value(str(project_count))
            self.quick_projects_count.setText(str(project_count))
            
            self.heartbeats_card.update_value(str(stats.get('pending_heartbeats', 0)))
            
            time_since_activity = stats.get('time_since_last_activity', 0)
            if time_since_activity < 60:
                time_str = f"{time_since_activity:.0f}s"
            elif time_since_activity < 3600:
                time_str = f"{time_since_activity/60:.1f}m"
            else:
                time_str = f"{time_since_activity/3600:.1f}h"
            self.time_active_card.update_value(time_str)
            
            api_status = status.get('status', 'Unknown').title()
            if api_status == 'Running':
                self.api_status_label.setText(f"🟢 API Status: {api_status}")
                self.api_status_label.setStyleSheet("""
                    QLabel {
                        color: #155724;
                        background-color: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 12px;
                        padding: 12px 16px;
                        font-weight: 600;
                    }
                """)
            else:
                self.api_status_label.setText(f"🔴 API Status: {api_status}")
                self.api_status_label.setStyleSheet("""
                    QLabel {
                        color: #721c24;
                        background-color: #f8d7da;
                        border: 1px solid #f5c6cb;
                        border-radius: 12px;
                        padding: 12px 16px;
                        font-weight: 600;
                    }
                """)
            
            if status.get('api_key_configured'):
                self.api_key_status_label.setText("🔑 API Key: Configured")
                self.api_key_status_label.setStyleSheet("""
                    QLabel {
                        color: #155724;
                        background-color: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 12px;
                        padding: 12px 16px;
                        font-weight: 600;
                    }
                """)
            else:
                self.api_key_status_label.setText("🔑 API Key: Not configured")
                self.api_key_status_label.setStyleSheet("""
                    QLabel {
                        color: #856404;
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 12px;
                        padding: 12px 16px;
                        font-weight: 600;
                    }
                """)
            
            if stats.get('is_tracking_active'):
                self.tracking_status_label.setText("📡 Tracking: Active")
                self.tracking_status_label.setStyleSheet("""
                    QLabel {
                        color: #155724;
                        background-color: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 12px;
                        padding: 12px 16px;
                        font-weight: 600;
                    }
                """)
            else:
                self.tracking_status_label.setText("📡 Tracking: Inactive")
                self.tracking_status_label.setStyleSheet("""
                    QLabel {
                        color: #721c24;
                        background-color: #f8d7da;
                        border: 1px solid #f5c6cb;
                        border-radius: 12px;
                        padding: 12px 16px;
                        font-weight: 600;
                    }
                """)
            
            if stats.get('is_tracking_active'):
                log_entry = f"[{self.get_current_time()}] 🟢 Tracking active - {stats.get('tracked_files', 0)} files monitored"
                self.activity_log.append(log_entry)
                
                if self.activity_log.document().lineCount() > 100:
                    cursor = self.activity_log.textCursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    cursor.select(cursor.SelectionType.LineUnderCursor)
                    cursor.removeSelectedText()
                    cursor.removeSelectedText()
                
                self.activity_log.verticalScrollBar().setValue(
                    self.activity_log.verticalScrollBar().maximum()
                )
        
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
    
    app.setApplicationName("Unitime")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Unitime")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
