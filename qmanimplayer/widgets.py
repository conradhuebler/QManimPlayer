"""
Widgets module - Dynamic widget factory for parameter controls.

Creates PyQt6 widgets based on parameter metadata:
- QDoubleSpinBox + QSlider for float parameters
- QSpinBox + QSlider for int parameters
- Custom parameter widgets with live updates
"""

from typing import Any, Callable, Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QSlider, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ParameterWidget(QWidget):
    """Base class for parameter control widgets."""

    value_changed = pyqtSignal(str, object)  # param_name, new_value

    def __init__(self, param_name: str, param_data: dict, parent=None):
        """
        Initialize parameter widget.

        Args:
            param_name: Name of the parameter
            param_data: Parameter metadata dict
            parent: Parent widget
        """
        super().__init__(parent)
        self.param_name = param_name
        self.param_data = param_data
        self.is_updating = False  # Flag to prevent recursive updates

    def set_value(self, value: Any):
        """Set the parameter value (called externally)."""
        raise NotImplementedError

    def get_value(self) -> Any:
        """Get the current parameter value."""
        raise NotImplementedError

    def _emit_change(self, value: Any):
        """Emit value_changed signal."""
        if not self.is_updating:
            self.value_changed.emit(self.param_name, value)


class FloatParameterWidget(ParameterWidget):
    """Widget for float parameters with spinbox and slider."""

    def __init__(self, param_name: str, param_data: dict, parent=None):
        super().__init__(param_name, param_data, parent)

        current_value = param_data.get("value", 0.0)
        min_val = param_data.get("min", 0.0)
        max_val = param_data.get("max", 100.0)
        step = (max_val - min_val) / 100.0 if max_val != min_val else 0.1

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Label with unit
        self.label = QLabel(param_name)
        self.unit_label = QLabel(param_data.get("unit", ""))
        self.unit_label.setMaximumWidth(60)

        # Spinbox
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(min_val)
        self.spinbox.setMaximum(max_val)
        self.spinbox.setValue(current_value)
        self.spinbox.setSingleStep(step)
        self.spinbox.setDecimals(3)
        self.spinbox.setMinimumWidth(80)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(int((current_value - min_val) / (max_val - min_val) * 1000))
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(100)
        self.slider.sliderMoved.connect(self._on_slider_changed)

        # Add tooltip with description
        tooltip = param_data.get("description", "")
        if tooltip:
            self.setToolTip(tooltip)

        layout.addWidget(self.label, 1)
        layout.addWidget(self.spinbox, 0)
        layout.addWidget(self.slider, 2)
        layout.addWidget(self.unit_label, 0)

        self.setLayout(layout)

    def set_value(self, value: float):
        """Set the parameter value."""
        self.is_updating = True

        self.spinbox.setValue(value)

        min_val = self.spinbox.minimum()
        max_val = self.spinbox.maximum()
        slider_val = int((value - min_val) / (max_val - min_val) * 1000)
        self.slider.setValue(slider_val)

        self.is_updating = False

    def get_value(self) -> float:
        """Get the current parameter value."""
        return self.spinbox.value()

    def _on_spinbox_changed(self, value: float):
        """Handle spinbox value change."""
        # Guard against external updates (undo/redo/preset load)
        if self.is_updating:
            return

        # Update slider to match spinbox
        min_val = self.spinbox.minimum()
        max_val = self.spinbox.maximum()
        slider_val = int((value - min_val) / (max_val - min_val) * 1000)

        self.is_updating = True
        self.slider.setValue(slider_val)
        self.is_updating = False

        self._emit_change(value)

    def _on_slider_changed(self, slider_val: int):
        """Handle slider value change."""
        # Guard against external updates (undo/redo/preset load)
        if self.is_updating:
            return

        # Update spinbox to match slider
        min_val = self.spinbox.minimum()
        max_val = self.spinbox.maximum()
        value = min_val + (slider_val / 1000.0) * (max_val - min_val)

        self.is_updating = True
        self.spinbox.setValue(value)
        self.is_updating = False

        self._emit_change(value)


class IntParameterWidget(ParameterWidget):
    """Widget for int parameters with spinbox and slider."""

    def __init__(self, param_name: str, param_data: dict, parent=None):
        super().__init__(param_name, param_data, parent)

        current_value = param_data.get("value", 0)
        min_val = param_data.get("min", 0)
        max_val = param_data.get("max", 100)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        self.label = QLabel(param_name)
        self.unit_label = QLabel(param_data.get("unit", ""))
        self.unit_label.setMaximumWidth(60)

        # Spinbox
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(min_val)
        self.spinbox.setMaximum(max_val)
        self.spinbox.setValue(current_value)
        self.spinbox.setMinimumWidth(80)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(current_value)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.sliderMoved.connect(self._on_slider_changed)

        # Tooltip
        tooltip = param_data.get("description", "")
        if tooltip:
            self.setToolTip(tooltip)

        layout.addWidget(self.label, 1)
        layout.addWidget(self.spinbox, 0)
        layout.addWidget(self.slider, 2)
        layout.addWidget(self.unit_label, 0)

        self.setLayout(layout)

    def set_value(self, value: int):
        """Set the parameter value."""
        self.is_updating = True

        self.spinbox.setValue(value)
        self.slider.setValue(value)

        self.is_updating = False

    def get_value(self) -> int:
        """Get the current parameter value."""
        return self.spinbox.value()

    def _on_spinbox_changed(self, value: int):
        """Handle spinbox value change."""
        # Guard against external updates (undo/redo/preset load)
        if self.is_updating:
            return

        self.is_updating = True
        self.slider.setValue(value)
        self.is_updating = False

        self._emit_change(value)

    def _on_slider_changed(self, slider_val: int):
        """Handle slider value change."""
        # Guard against external updates (undo/redo/preset load)
        if self.is_updating:
            return

        self.is_updating = True
        self.spinbox.setValue(slider_val)
        self.is_updating = False

        self._emit_change(slider_val)


class SimpleParameterWidget(ParameterWidget):
    """Fallback widget for unsupported parameter types."""

    def __init__(self, param_name: str, param_data: dict, parent=None):
        super().__init__(param_name, param_data, parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(param_name)
        value_label = QLabel(str(param_data.get("value", "?")))

        layout.addWidget(label, 1)
        layout.addWidget(value_label, 0)

        self.setLayout(layout)

    def set_value(self, value: Any):
        """Set the parameter value."""
        pass

    def get_value(self) -> Any:
        """Get the current parameter value."""
        return None


class ParameterWidgetFactory:
    """Factory for creating parameter widgets based on type and metadata."""

    @staticmethod
    def create_widget(param_name: str, param_data: dict,
                      parent=None) -> ParameterWidget:
        """
        Create an appropriate widget for a parameter.

        Args:
            param_name: Name of the parameter
            param_data: Parameter metadata dictionary
            parent: Parent widget

        Returns:
            Appropriate ParameterWidget subclass
        """
        param_type = param_data.get("type")

        if param_type == float:
            return FloatParameterWidget(param_name, param_data, parent)
        elif param_type == int:
            return IntParameterWidget(param_name, param_data, parent)
        else:
            return SimpleParameterWidget(param_name, param_data, parent)


def create_divider(label: str = "", parent=None) -> QFrame:
    """
    Create a horizontal divider line with optional label.

    Args:
        label: Optional label text
        parent: Parent widget

    Returns:
        QFrame widget
    """
    frame = QFrame(parent)
    frame.setFrameShape(QFrame.Shape.HLine)
    frame.setFrameShadow(QFrame.Shadow.Sunken)

    if label:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)

        label_widget = QLabel(label)
        font = label_widget.font()
        font.setBold(True)
        label_widget.setFont(font)

        layout.addWidget(label_widget, 0)
        layout.addWidget(frame, 1)

        container = QWidget(parent)
        container.setLayout(layout)
        return container

    return frame
