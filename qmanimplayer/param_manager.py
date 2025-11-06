"""
Parameter Manager - Handles parameter state, undo/redo, and file updates.

Manages:
- Current parameter values
- Undo/Redo stack
- In-place .py file updates
- Change tracking and notifications
"""

import ast
import re
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ParameterChange:
    """Represents a single parameter change for undo/redo."""
    param_name: str
    old_value: Any
    new_value: Any
    timestamp: float = field(default_factory=lambda: __import__("time").time())


@dataclass
class UndoRedoCommand:
    """Represents a complete undo/redo command (may contain multiple changes)."""
    changes: List[ParameterChange]
    description: str = ""

    def execute(self):
        """Execute this command (for redo)."""
        pass

    def undo(self):
        """Undo this command."""
        pass


class ParameterManager:
    """
    Manages parameter state, persistence, and undo/redo operations.
    """

    def __init__(self, script_path: str, parameters: Dict[str, Any]):
        """
        Initialize parameter manager.

        Args:
            script_path: Path to the manim-gl .py script
            parameters: Dictionary of parameters (from parser)
        """
        self.script_path = Path(script_path)
        self.parameters = parameters.copy()
        self.current_values = {}
        self._initialize_current_values()

        # Undo/Redo stack
        self.undo_stack: List[List[ParameterChange]] = []
        self.redo_stack: List[List[ParameterChange]] = []

        # Change callbacks
        self.on_change_callbacks: List[Callable[[str, Any, Any], None]] = []
        self.on_file_modified_callbacks: List[Callable[[], None]] = []

        self.is_modified = False

    def _initialize_current_values(self):
        """Initialize current values from parameters dictionary."""
        for param_name, param_data in self.parameters.items():
            if isinstance(param_data, dict) and "value" in param_data:
                self.current_values[param_name] = param_data["value"]

    def set_parameter(self, param_name: str, new_value: Any) -> bool:
        """
        Set a parameter value and update the file.

        Args:
            param_name: Name of the parameter
            new_value: New value to set

        Returns:
            True if successful, False otherwise
        """
        if param_name not in self.current_values:
            return False

        old_value = self.current_values[param_name]

        # Skip if value hasn't actually changed
        if old_value == new_value:
            return False

        # Type validation
        if not self._validate_type(param_name, new_value):
            return False

        # Min/max validation
        if not self._validate_bounds(param_name, new_value):
            return False

        # Update in-memory state
        self.current_values[param_name] = new_value
        self.parameters[param_name]["value"] = new_value

        # Create undo/redo record
        change = ParameterChange(param_name, old_value, new_value)
        self.undo_stack.append([change])
        self.redo_stack.clear()

        # Update file
        self._update_file(param_name, new_value)

        # Notify observers
        self._notify_change(param_name, old_value, new_value)

        self.is_modified = True
        self._notify_file_modified()

        return True

    def set_parameters_batch(self, updates: Dict[str, Any]) -> Dict[str, bool]:
        """
        Set multiple parameters at once (single undo/redo entry).

        Args:
            updates: Dictionary of parameter_name -> new_value

        Returns:
            Dictionary of parameter_name -> success status
        """
        results = {}
        changes = []

        # Validate all changes first
        for param_name, new_value in updates.items():
            if param_name not in self.current_values:
                results[param_name] = False
                continue

            if not self._validate_type(param_name, new_value):
                results[param_name] = False
                continue

            if not self._validate_bounds(param_name, new_value):
                results[param_name] = False
                continue

            results[param_name] = True

        # Apply all valid changes
        for param_name, new_value in updates.items():
            if results[param_name]:
                old_value = self.current_values[param_name]
                self.current_values[param_name] = new_value
                self.parameters[param_name]["value"] = new_value
                changes.append(ParameterChange(param_name, old_value, new_value))
                self._update_file(param_name, new_value)
                self._notify_change(param_name, old_value, new_value)

        # Add as single undo/redo entry
        if changes:
            self.undo_stack.append(changes)
            self.redo_stack.clear()
            self.is_modified = True
            self._notify_file_modified()

        return results

    def undo(self) -> bool:
        """
        Undo the last parameter change(s).

        Returns:
            True if undo was successful
        """
        if not self.undo_stack:
            return False

        changes = self.undo_stack.pop()

        for change in changes:
            self.current_values[change.param_name] = change.old_value
            self.parameters[change.param_name]["value"] = change.old_value
            self._update_file(change.param_name, change.old_value)
            self._notify_change(change.param_name, change.new_value, change.old_value)

        self.redo_stack.append(changes)
        self.is_modified = True
        self._notify_file_modified()

        return True

    def redo(self) -> bool:
        """
        Redo the last undone change(s).

        Returns:
            True if redo was successful
        """
        if not self.redo_stack:
            return False

        changes = self.redo_stack.pop()

        for change in changes:
            self.current_values[change.param_name] = change.new_value
            self.parameters[change.param_name]["value"] = change.new_value
            self._update_file(change.param_name, change.new_value)
            self._notify_change(change.param_name, change.old_value, change.new_value)

        self.undo_stack.append(changes)
        self.is_modified = True
        self._notify_file_modified()

        return True

    def reset_parameter(self, param_name: str, default_value: Any) -> bool:
        """
        Reset a parameter to its default value.

        Args:
            param_name: Name of the parameter
            default_value: The default value to reset to

        Returns:
            True if successful
        """
        return self.set_parameter(param_name, default_value)

    def get_parameter(self, param_name: str) -> Optional[Any]:
        """
        Get current parameter value.

        Args:
            param_name: Name of the parameter

        Returns:
            Current value or None if parameter not found
        """
        return self.current_values.get(param_name)

    def get_all_parameters(self) -> Dict[str, Any]:
        """
        Get all current parameter values.

        Returns:
            Dictionary of parameter_name -> current_value
        """
        return self.current_values.copy()

    def _validate_type(self, param_name: str, value: Any) -> bool:
        """Validate that value matches expected type."""
        if param_name not in self.parameters:
            return False

        param_data = self.parameters[param_name]
        if "type" not in param_data:
            return True

        expected_type = param_data["type"]
        if expected_type == float:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == int:
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == bool:
            return isinstance(value, bool)
        elif expected_type == str:
            return isinstance(value, str)

        return True

    def _validate_bounds(self, param_name: str, value: Any) -> bool:
        """Validate that value is within min/max bounds."""
        param_data = self.parameters.get(param_name, {})

        if "min" in param_data and value < param_data["min"]:
            return False

        if "max" in param_data and value > param_data["max"]:
            return False

        return True

    def _update_file(self, param_name: str, new_value: Any):
        """
        Update the PARAMETERS dictionary in the .py file.

        Args:
            param_name: Name of the parameter to update
            new_value: New value
        """
        try:
            source = self.script_path.read_text(encoding="utf-8")

            # Parse the file to find PARAMETERS dictionary
            tree = ast.parse(source)

            # Find PARAMETERS dictionary line range
            params_start = None
            params_end = None

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "PARAMETERS":
                            params_start = node.lineno - 1
                            params_end = node.end_lineno or node.lineno
                            break

            if params_start is None:
                return

            lines = source.split('\n')

            # Find the specific parameter line within PARAMETERS
            for i in range(params_start, params_end):
                if f'"{param_name}"' in lines[i] or f"'{param_name}'" in lines[i]:
                    # Found the parameter line, now find and update its "value" field
                    # Search for the next "value":" occurrence after this line
                    for j in range(i, min(i + 20, params_end)):
                        if '"value"' in lines[j] or "'value'" in lines[j]:
                            # Replace the value
                            lines[j] = self._replace_parameter_value(lines[j], new_value)
                            break
                    break

            # Write back
            self.script_path.write_text('\n'.join(lines), encoding="utf-8")

        except Exception as e:
            print(f"Error updating file: {e}")

    def _replace_parameter_value(self, line: str, new_value: Any) -> str:
        """
        Replace the value in a parameter value line.

        Handles: "value": 123.45 or 'value': "string" etc.

        Args:
            line: The line containing the value field
            new_value: New value to insert

        Returns:
            Modified line
        """
        # Format new value
        if isinstance(new_value, str):
            formatted = f'"{new_value}"'
        elif isinstance(new_value, float):
            formatted = str(new_value)
        elif isinstance(new_value, int):
            formatted = str(new_value)
        elif isinstance(new_value, bool):
            formatted = "True" if new_value else "False"
        else:
            formatted = str(new_value)

        # Replace pattern: "value": ... with "value": <new_value>
        pattern = r'(["\']value["\'])\s*:\s*[^,}]+'
        replacement = rf'\1: {formatted}'

        return re.sub(pattern, replacement, line)

    def add_change_listener(self, callback: Callable[[str, Any, Any], None]):
        """
        Add a listener for parameter changes.

        Callback signature: callback(param_name, old_value, new_value)

        Args:
            callback: Function to call when parameter changes
        """
        self.on_change_callbacks.append(callback)

    def remove_change_listener(self, callback: Callable):
        """Remove a change listener."""
        if callback in self.on_change_callbacks:
            self.on_change_callbacks.remove(callback)

    def add_file_modified_listener(self, callback: Callable[[], None]):
        """
        Add a listener for file modifications.

        Args:
            callback: Function to call when file is modified
        """
        self.on_file_modified_callbacks.append(callback)

    def _notify_change(self, param_name: str, old_value: Any, new_value: Any):
        """Notify all change listeners."""
        for callback in self.on_change_callbacks:
            try:
                callback(param_name, old_value, new_value)
            except Exception as e:
                print(f"Error in change callback: {e}")

    def _notify_file_modified(self):
        """Notify all file modified listeners."""
        for callback in self.on_file_modified_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in file modified callback: {e}")

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def clear_history(self):
        """Clear undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
