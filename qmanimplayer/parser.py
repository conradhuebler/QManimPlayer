"""
Parser module for extracting PARAMETERS dictionary from manim-gl scripts.

Uses AST (Abstract Syntax Tree) parsing to robustly extract:
- PARAMETERS dictionary with all metadata
- Comment-based categories (# Physical Parameters, etc.)
- Scene class information
"""

import ast
import re
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path


class ParameterParser:
    """Parse manim-gl scripts for PARAMETERS dictionary and metadata."""

    def __init__(self, file_path: str):
        """
        Initialize parser with a Python file.

        Args:
            file_path: Path to the .py script to parse
        """
        self.file_path = Path(file_path)
        self.source_code = self.file_path.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source_code)
        self.lines = self.source_code.split('\n')

    def extract_parameters(self) -> Dict[str, Any]:
        """
        Extract PARAMETERS dictionary from the script.

        Returns:
            Dictionary with parameter name as key and metadata (value, type, unit, etc.) as value.
            Empty dict if PARAMETERS not found.
        """
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "PARAMETERS":
                        # Found PARAMETERS assignment
                        return self._extract_dict_value(node.value)
        return {}

    def _extract_dict_value(self, node: ast.expr) -> Dict[str, Any]:
        """
        Convert AST dict node to Python dictionary.

        Args:
            node: AST node representing a dictionary

        Returns:
            Extracted dictionary
        """
        if not isinstance(node, ast.Dict):
            return {}

        result = {}
        for key_node, value_node in zip(node.keys, node.values):
            if isinstance(key_node, ast.Constant):
                key = key_node.value
                value = self._extract_value(value_node)
                result[key] = value

        return result

    def _extract_value(self, node: ast.expr) -> Any:
        """
        Extract Python value from AST node.

        Supports: dicts, lists, strings, numbers, booleans, type objects.

        Args:
            node: AST node to extract value from

        Returns:
            Extracted Python value
        """
        if isinstance(node, ast.Dict):
            return self._extract_dict_value(node)
        elif isinstance(node, ast.List):
            return [self._extract_value(elem) for elem in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._extract_value(elem) for elem in node.elts)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            # Handle True, False, None
            if node.id == "True":
                return True
            elif node.id == "False":
                return False
            elif node.id == "None":
                return None
            # Handle type objects (float, int, bool, str)
            elif node.id == "float":
                return float
            elif node.id == "int":
                return int
            elif node.id == "bool":
                return bool
            elif node.id == "str":
                return str
        elif isinstance(node, ast.UnaryOp):
            # Handle unary operations (negative numbers: -x, positive: +x)
            operand = self._extract_value(node.operand)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand
        return None

    def get_categories(self) -> Dict[str, List[str]]:
        """
        Extract parameter categories from comments.

        Looks for patterns like:
        # Physical Parameters
        # Animation Settings
        etc.

        Returns:
            Dictionary mapping category names to lists of parameter keys.
        """
        parameters = self.extract_parameters()
        if not parameters:
            return {}

        # Find PARAMETERS dictionary position
        params_line_num = self._find_parameters_line()
        if params_line_num is None:
            return {"Default": list(parameters.keys())}

        categories = {}
        current_category = "Default"
        current_params = []

        # Regex to match category comments
        category_pattern = re.compile(r"#\s*([A-Z][^#\n]+?)\s*$")

        # Search backwards and forwards from PARAMETERS line
        # to find category comments
        for i, line in enumerate(self.lines[params_line_num:], start=params_line_num):
            match = category_pattern.search(line)
            if match:
                category_text = match.group(1).strip()
                # Check if it looks like a category header
                if any(keyword in category_text.lower() for keyword in
                       ["parameter", "setting", "config", "option", "property"]):
                    if current_params:
                        categories[current_category] = current_params
                    current_category = category_text
                    current_params = []

        # Add remaining parameters
        if current_params:
            categories[current_category] = current_params
        elif current_category not in categories:
            categories[current_category] = []

        # Now match parameters to categories based on order
        # This is a simple heuristic: parameters appearing after a comment
        # belong to that category
        param_keys = list(parameters.keys())
        param_line_numbers = self._find_parameter_lines(param_keys, params_line_num)

        categories_by_line = self._extract_category_lines(params_line_num)

        # Map parameters to categories
        result = {cat: [] for cat in categories.keys()}
        result["Default"] = param_keys  # Default fallback

        for param_key, param_line in param_line_numbers.items():
            assigned_category = "Default"
            # Find closest preceding category comment
            for cat_line, cat_name in sorted(categories_by_line.items(), reverse=True):
                if cat_line < param_line:
                    assigned_category = cat_name
                    break

            if assigned_category not in result:
                result[assigned_category] = []
            if param_key not in result[assigned_category]:
                result[assigned_category].append(param_key)
            # Remove from Default if assigned elsewhere
            if assigned_category != "Default" and param_key in result["Default"]:
                result["Default"].remove(param_key)

        # Remove empty categories
        result = {k: v for k, v in result.items() if v}

        return result

    def _find_parameters_line(self) -> Optional[int]:
        """Find the line number where PARAMETERS is defined."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "PARAMETERS":
                        return node.lineno - 1  # Convert to 0-indexed
        return None

    def _extract_category_lines(self, start_line: int) -> Dict[int, str]:
        """Extract category comment lines and their content."""
        categories = {}
        category_pattern = re.compile(r"#\s*([A-Z][^#\n]+?Parameters?|[A-Z][^#\n]+?Settings?|[A-Z][^#\n]+?[Cc]onfig[^#\n]*)\s*$")

        for i in range(start_line, len(self.lines)):
            match = category_pattern.search(self.lines[i])
            if match:
                categories[i] = match.group(1).strip()

        return categories

    def _find_parameter_lines(self, param_keys: List[str],
                              start_line: int) -> Dict[str, int]:
        """Find line numbers for each parameter in the PARAMETERS dict."""
        param_lines = {}

        # Simple approach: search for each parameter key after start_line
        for key in param_keys:
            for i in range(start_line, len(self.lines)):
                if f'"{key}"' in self.lines[i] or f"'{key}'" in self.lines[i]:
                    param_lines[key] = i
                    break

        return param_lines

    def get_scene_classes(self) -> List[str]:
        """
        Extract Scene class names from the script.

        Returns:
            List of class names that inherit from Scene
        """
        scene_classes = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # Check if it inherits from Scene
                for base in node.bases:
                    base_name = None
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        # Handle manimlib.scene.Scene etc.
                        base_name = base.attr

                    if base_name and "Scene" in base_name:
                        scene_classes.append(node.name)
                        break

        return scene_classes

    def validate_parameters(self) -> Tuple[bool, List[str]]:
        """
        Validate PARAMETERS dictionary structure.

        Required fields per parameter: value, type, unit, description, min, max

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        parameters = self.extract_parameters()
        if not parameters:
            return False, ["PARAMETERS dictionary not found"]

        errors = []
        required_fields = {"value", "type", "unit", "description", "min", "max"}

        for param_name, param_data in parameters.items():
            if not isinstance(param_data, dict):
                errors.append(f"Parameter '{param_name}': value must be a dictionary")
                continue

            missing_fields = required_fields - set(param_data.keys())
            if missing_fields:
                errors.append(
                    f"Parameter '{param_name}': missing fields {missing_fields}"
                )

            # Type validation
            if "type" in param_data:
                param_type = param_data["type"]
                if param_type not in (int, float, bool, str):
                    errors.append(
                        f"Parameter '{param_name}': invalid type {param_type}"
                    )

        return len(errors) == 0, errors


def parse_script(file_path: str) -> Tuple[Dict[str, Any], Dict[str, List[str]], List[str]]:
    """
    Convenience function to parse a manim-gl script completely.

    Args:
        file_path: Path to the .py script

    Returns:
        Tuple of (parameters_dict, categories_dict, scene_classes)
    """
    parser = ParameterParser(file_path)
    parameters = parser.extract_parameters()
    categories = parser.get_categories()
    scenes = parser.get_scene_classes()

    return parameters, categories, scenes
