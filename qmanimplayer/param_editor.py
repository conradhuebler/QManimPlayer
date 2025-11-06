"""
Parameter Editor - Main UI panel for editing parameters.

Features:
- Categorized parameter display
- Collapsible groups
- Live parameter updates
- Reset all functionality
"""

from typing import Dict, List, Any, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QGroupBox, QPushButton, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .widgets import ParameterWidgetFactory, ParameterWidget
from .param_manager import ParameterManager


class CategoryGroup(QGroupBox):
    """Collapsible group for a parameter category."""

    def __init__(self, category_name: str, parent=None):
        super().__init__(category_name, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.setFlat(False)

        # Make category name bold
        font = self.font()
        font.setBold(True)
        self.setFont(font)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def add_widget(self, widget: QWidget):
        """Add a parameter widget to this category."""
        self.layout.addWidget(widget)

    def add_stretch(self):
        """Add stretch at the end."""
        self.layout.addStretch()


class ParameterEditor(QWidget):
    """Main parameter editor widget with categories and live updates."""

    parameter_changed = pyqtSignal(str, object)  # param_name, new_value
    reset_requested = pyqtSignal()

    def __init__(self, param_manager: ParameterManager, categories: Dict[str, List[str]],
                 parent=None):
        """
        Initialize parameter editor.

        Args:
            param_manager: ParameterManager instance
            categories: Dictionary mapping category names to parameter lists
            parent: Parent widget
        """
        super().__init__(parent)
        self.param_manager = param_manager
        self.categories = categories
        self.param_widgets: Dict[str, ParameterWidget] = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout()

        # Title
        title = QLabel("Parameter Editor")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Create category groups
        for category_name, param_names in self.categories.items():
            group = CategoryGroup(category_name)

            for param_name in param_names:
                param_data = self.param_manager.parameters.get(param_name)
                if param_data is None:
                    continue

                # Create parameter widget
                widget = ParameterWidgetFactory.create_widget(param_name, param_data)
                self.param_widgets[param_name] = widget

                # Connect value changes
                widget.value_changed.connect(self._on_param_changed)

                group.add_widget(widget)

            container_layout.addWidget(group)

        # Stretch at the end
        container_layout.addStretch()

        container.setLayout(container_layout)
        scroll.setWidget(container)

        main_layout.addWidget(scroll, 1)

        # Control buttons
        button_layout = QHBoxLayout()

        reset_all_btn = QPushButton("Reset All")
        reset_all_btn.clicked.connect(self._on_reset_all)

        button_layout.addStretch()
        button_layout.addWidget(reset_all_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _connect_signals(self):
        """Connect parameter manager signals."""
        self.param_manager.add_change_listener(self._on_external_change)

    def _on_param_changed(self, param_name: str, new_value: Any):
        """Handle parameter change from widget."""
        self.param_manager.set_parameter(param_name, new_value)
        self.parameter_changed.emit(param_name, new_value)

    def _on_external_change(self, param_name: str, old_value: Any, new_value: Any):
        """Handle parameter change from external source (undo/redo)."""
        if param_name in self.param_widgets:
            widget = self.param_widgets[param_name]
            widget.set_value(new_value)

    def _on_reset_all(self):
        """Reset all parameters to default values."""
        # Collect default values
        defaults = {}
        for param_name, param_data in self.param_manager.parameters.items():
            # For now, use the original value field as default
            # In a real app, you might track original values separately
            defaults[param_name] = param_data.get("value")

        # Apply all defaults
        self.param_manager.set_parameters_batch(defaults)
        # Note: Signal emission removed to prevent circular dialog loop
        # MainWindow already handles reset via direct method call

    def get_all_values(self) -> Dict[str, Any]:
        """Get all current parameter values from widgets."""
        return {
            param_name: widget.get_value()
            for param_name, widget in self.param_widgets.items()
        }

    def set_all_values(self, values: Dict[str, Any]):
        """Set all parameter values from dictionary."""
        for param_name, value in values.items():
            if param_name in self.param_widgets:
                self.param_widgets[param_name].set_value(value)
