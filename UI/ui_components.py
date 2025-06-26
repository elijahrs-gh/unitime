from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QColor


class ModernButton(QPushButton):
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setup_style()
    
    def setup_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 600;
                    min-width: 70px;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
                    color: #7f8c8d;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #495057;
                    border: 1px solid #dee2e6;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 600;
                    min-width: 70px;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #adb5bd;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
                QPushButton:disabled {
                    background-color: #f8f9fa;
                    color: #6c757d;
                    border-color: #dee2e6;
                }
            """)


class ModernCard(QFrame):
    def __init__(self, title, value, icon="", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.value_text = value
        self.icon_text = icon
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        if self.icon_text:
            self.icon_label = QLabel(self.icon_text)
            self.icon_label.setFont(QFont("Arial", 18))
            self.icon_label.setStyleSheet("color: #3498db;")
            header_layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(self.title_text)
        self.title_label.setFont(QFont("Arial", 13, QFont.Weight.Medium))
        self.title_label.setStyleSheet("color: #6c757d;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        self.value_label = QLabel(self.value_text)
        self.value_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #2c3e50; margin: 8px 0px;")
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def setup_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 16px;
                min-height: 120px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        self.setFrameStyle(QFrame.Shape.Box)
    
    def update_value(self, new_value):
        self.value_label.setText(new_value)
        self.value_text = new_value


class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "disconnected"
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        
        self.indicator_dot = QLabel("●")
        self.indicator_dot.setFont(QFont("Arial", 14))
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setFont(QFont("Arial", 13, QFont.Weight.Medium))
        
        layout.addWidget(self.indicator_dot)
        layout.addWidget(self.status_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 20px;
                padding: 4px 8px;
            }
        """)
        
        self.set_status("disconnected")
    
    def set_status(self, status):
        self.status = status
        
        if status == "connected":
            self.indicator_dot.setStyleSheet("color: #28a745;")
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: #28a745; font-weight: 600;")
            self.setStyleSheet("""
                QWidget {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 20px;
                    padding: 4px 8px;
                }
            """)
        elif status == "connecting":
            self.indicator_dot.setStyleSheet("color: #ffc107;")
            self.status_label.setText("Connecting...")
            self.status_label.setStyleSheet("color: #856404; font-weight: 600;")
            self.setStyleSheet("""
                QWidget {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 20px;
                    padding: 4px 8px;
                }
            """)
        else:
            self.indicator_dot.setStyleSheet("color: #dc3545;")
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: #721c24; font-weight: 600;")
            self.setStyleSheet("""
                QWidget {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 20px;
                    padding: 4px 8px;
                }
            """)


class ProjectCard(QFrame):
    remove_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str)
    
    def __init__(self, project_path, remove_callback=None, edit_callback=None, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.remove_callback = remove_callback
        self.edit_callback = edit_callback
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        project_name = self.project_path.split('/')[-1] or self.project_path
        self.name_label = QLabel(project_name)
        self.name_label.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #2c3e50;")
        
        self.path_label = QLabel(self.project_path)
        self.path_label.setFont(QFont("Arial", 11))
        self.path_label.setStyleSheet("color: #6c757d; font-style: italic;")
        
        if len(self.project_path) > 50:
            display_path = "..." + self.project_path[-47:]
            self.path_label.setText(display_path)
            self.path_label.setToolTip(self.project_path)
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.path_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout, 1)
        
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("● ACTIVE")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("""
            color: #28a745; 
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 10px;
            padding: 4px 8px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMaximumWidth(80)
        
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_container)
        
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(6)
        button_layout.setContentsMargins(0, 4, 0, 4)
        
        self.edit_button = ModernButton("Edit")
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.edit_button.setFixedSize(80, 32)
        
        self.remove_button = ModernButton("Remove")
        self.remove_button.clicked.connect(self.on_remove_clicked)
        self.remove_button.setFixedSize(80, 32)
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        
        layout.addWidget(button_container)
    
    def setup_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                margin: 4px 2px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedHeight(100)
    
    def on_remove_clicked(self):
        if self.remove_callback:
            self.remove_callback(self.project_path)
    
    def on_edit_clicked(self):
        if self.edit_callback:
            self.edit_callback(self.project_path)
