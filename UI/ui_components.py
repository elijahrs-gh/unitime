from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy, QLineEdit, QComboBox, QFileDialog
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
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 80px;
                    min-height: 32px;
                    max-height: 40px;
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
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 80px;
                    min-height: 32px;
                    max-height: 40px;
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
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


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
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if self.icon_text:
            self.icon_label = QLabel(self.icon_text)
            self.icon_label.setFont(QFont("Arial", 20))
            self.icon_label.setStyleSheet("color: #3498db;")
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(self.title_text)
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Medium))
        self.title_label.setStyleSheet("color: #6c757d;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label)
        
        layout.addLayout(header_layout)
        
        self.value_label = QLabel(self.value_text)
        self.value_label.setFont(QFont("Arial", 30, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #2c3e50; margin: 8px 0px;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setWordWrap(True)
        layout.addWidget(self.value_label)
        layout.addStretch()
    
    def setup_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 16px;
                min-height: 120px;
                max-height: 160px;
                min-width: 200px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
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
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.indicator_dot = QLabel("●")
        self.indicator_dot.setFont(QFont("Arial", 16))
        self.indicator_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setFont(QFont("Arial", 14, QFont.Weight.Medium))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.indicator_dot)
        layout.addWidget(self.status_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 22px;
                padding: 4px 8px;
                min-width: 140px;
                max-width: 200px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
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
                    padding: 2px 6px;
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
                    padding: 2px 6px;
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
                    padding: 2px 6px;
                }
            """)


class ProjectCard(QFrame):
    remove_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str, dict)
    project_updated = pyqtSignal(str, dict)
    
    def __init__(self, project_path, project_data=None, remove_callback=None, edit_callback=None, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.project_data = project_data or {
            'name': '',
            'path': project_path,
            'application': '',
            'description': '',
            'status': 'active'
        }
        self.remove_callback = remove_callback
        self.edit_callback = edit_callback
        self.is_editing = False
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(12)
        self.display_widget = QWidget()
        self.setup_display_view()
        self.main_layout.addWidget(self.display_widget)
        self.edit_widget = QWidget()
        self.setup_edit_view()
        self.edit_widget.hide()
        self.main_layout.addWidget(self.edit_widget)
    
    def setup_display_view(self):
        layout = QHBoxLayout(self.display_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.name_label = QLabel(self.project_data['name'] or 'Untitled Project')
        self.name_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #2c3e50; margin-bottom: 4px;")
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.path_label = QLabel(self.project_data['path'])
        self.path_label.setFont(QFont("Arial", 12))
        self.path_label.setStyleSheet("color: #6c757d; font-style: italic; margin: 2px 0px;")
        self.path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.path_label.setWordWrap(True)
        
        if len(self.project_data['path']) > 60:
            display_path = "..." + self.project_data['path'][-57:]
            self.path_label.setText(display_path)
            self.path_label.setToolTip(self.project_data['path'])
        self.app_label = QLabel(f"App: {self.project_data.get('application', 'Not specified')}")
        self.app_label.setFont(QFont("Arial", 11))
        self.app_label.setStyleSheet("""
            color: #495057; 
            background-color: #e9ecef; 
            padding: 4px 8px; 
            border-radius: 6px; 
            margin-top: 4px;
            max-width: 200px;
        """)
        self.app_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.path_label)
        info_layout.addWidget(self.app_label)
        info_layout.addStretch()
        layout.addLayout(info_layout, 3)
        right_container = QHBoxLayout()
        right_container.setSpacing(12)
        right_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_container = QWidget()
        status_container.setFixedWidth(100)
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("● ACTIVE")
        self.status_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet("""
            color: #28a745; 
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 12px;
            padding: 6px 10px;
            min-width: 80px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_layout.addWidget(self.status_label)
        right_container.addWidget(status_container)
        button_container = QWidget()
        button_container.setFixedWidth(100)
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 4, 0, 4)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.edit_button = ModernButton("Edit")
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        self.edit_button.setFixedSize(90, 32)
        
        self.remove_button = ModernButton("Remove")
        self.remove_button.clicked.connect(self.on_remove_clicked)
        self.remove_button.setFixedSize(90, 32)
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 13px;
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
        
        right_container.addWidget(button_container)
        layout.addLayout(right_container, 1)
    
    def setup_edit_view(self):
        layout = QVBoxLayout(self.edit_widget)
        layout.setContentsMargins(0, 12, 0, 8)
        layout.setSpacing(16)
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 0, 0, 0)
        name_row = QHBoxLayout()
        name_row.setSpacing(12)
        name_label = QLabel("Project Name:")
        name_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        name_label.setFixedWidth(130)
        name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.name_edit = QLineEdit(self.project_data['name'])
        self.name_edit.setPlaceholderText("Enter project name...")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                min-height: 16px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """)
        name_row.addWidget(name_label)
        name_row.addWidget(self.name_edit, 1)
        path_row = QHBoxLayout()
        path_row.setSpacing(12)
        path_label = QLabel("Project Path:")
        path_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        path_label.setFixedWidth(130)
        path_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.path_edit = QLineEdit(self.project_data['path'])
        self.path_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                min-height: 16px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """)
        self.browse_button = ModernButton("Browse")
        self.browse_button.clicked.connect(self.browse_for_path)
        self.browse_button.setFixedSize(80, 36)
        path_row.addWidget(path_label)
        path_row.addWidget(self.path_edit, 2)
        path_row.addWidget(self.browse_button)
        app_row = QHBoxLayout()
        app_row.setSpacing(12)
        app_label = QLabel("Application:")
        app_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        app_label.setFixedWidth(130)
        app_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.app_combo = QComboBox()
        self.app_combo.setEditable(False)
        self.app_combo.addItems([
            "",
            "Zed",
            "VS Code"
        ])
        self.app_combo.setCurrentText(self.project_data.get('application', ''))
        self.app_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                min-width: 180px;
                min-height: 16px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 12px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6c757d;
            }
        """)
        app_row.addWidget(app_label)
        app_row.addWidget(self.app_combo, 1)
        app_row.addStretch()
        desc_row = QHBoxLayout()
        desc_row.setSpacing(12)
        desc_label = QLabel("Description:")
        desc_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        desc_label.setFixedWidth(130)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.desc_edit = QLineEdit(self.project_data.get('description', ''))
        self.desc_edit.setPlaceholderText("Optional project description...")
        self.desc_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                min-height: 16px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """)
        desc_row.addWidget(desc_label)
        desc_row.addWidget(self.desc_edit, 1)
        form_layout.addLayout(name_row)
        form_layout.addLayout(path_row)
        form_layout.addLayout(app_row)
        form_layout.addLayout(desc_row)
        layout.addWidget(form_container)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        self.save_button = ModernButton("Save", primary=True)
        self.save_button.clicked.connect(self.save_changes)
        self.save_button.setFixedSize(90, 36)
        self.cancel_button = ModernButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.cancel_button.setFixedSize(90, 36)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def setup_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                margin: 2px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.update_height()
    
    def update_height(self):
        if self.is_editing:
            self.setFixedHeight(260)
        else:
            self.setFixedHeight(130)
    
    def toggle_edit_mode(self):
        self.is_editing = not self.is_editing
        
        if self.is_editing:
            self.display_widget.hide()
            self.edit_widget.show()
            self.edit_button.setText("Cancel")
        else:
            self.edit_widget.hide()
            self.display_widget.show()
            self.edit_button.setText("Edit")
        
        self.update_height()
    
    def browse_for_path(self):
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Project Directory", 
            self.path_edit.text()
        )
        if directory:
            self.path_edit.setText(directory)
    
    def save_changes(self):
        old_path = self.project_data['path']
        project_name = self.name_edit.text().strip()
        if not project_name:
            project_name = self.path_edit.text().strip().split('/')[-1] or 'Untitled Project'
            
        self.project_data = {
            'name': project_name,
            'path': self.path_edit.text().strip(),
            'application': self.app_combo.currentText().strip(),
            'description': self.desc_edit.text().strip(),
            'status': self.project_data.get('status', 'active')
        }
        
        self.name_label.setText(self.project_data['name'])
        self.path_label.setText(self.project_data['path'])
        self.app_label.setText(f"App: {self.project_data['application'] or 'Not specified'}")
        
        if len(self.project_data['path']) > 50:
            display_path = "..." + self.project_data['path'][-47:]
            self.path_label.setText(display_path)
            self.path_label.setToolTip(self.project_data['path'])
        
        self.project_updated.emit(old_path, self.project_data)
        if self.edit_callback:
            self.edit_callback(old_path, self.project_data)
        
        self.toggle_edit_mode()
    
    def cancel_edit(self):
        self.name_edit.setText(self.project_data['name'])
        self.path_edit.setText(self.project_data['path'])
        self.app_combo.setCurrentText(self.project_data.get('application', ''))
        self.desc_edit.setText(self.project_data.get('description', ''))
        
        self.toggle_edit_mode()
    
    def on_remove_clicked(self):
        if self.remove_callback:
            self.remove_callback(self.project_path)
    
    def get_project_data(self):
        return self.project_data.copy()
    
    def update_project_data(self, new_data):
        self.project_data.update(new_data)
        self.name_label.setText(self.project_data['name'] or 'Untitled Project')
        self.path_label.setText(self.project_data['path'])
        self.app_label.setText(f"App: {self.project_data.get('application', 'Not specified')}")
