"""
Preset Manager - Save and load parameter presets in JSON format.

Handles:
- Saving current parameters as JSON presets
- Loading presets from JSON files
- Managing preset metadata
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class PresetManager:
    """Manage parameter presets (save/load from JSON)."""

    PRESET_SUFFIX = ".preset.json"

    def __init__(self, script_path: str):
        """
        Initialize preset manager for a script.

        Args:
            script_path: Path to the manim-gl .py script
        """
        self.script_path = Path(script_path)
        self.presets_dir = self.script_path.parent

    def save_preset(self, preset_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Save a parameter preset to JSON file.

        Filename format: {script_name}_{preset_name}.preset.json

        Args:
            preset_name: Name of the preset (e.g., "default", "low-energy")
            parameters: Dictionary of parameter_name -> value

        Returns:
            True if successful
        """
        try:
            # Sanitize preset name
            safe_name = preset_name.replace(" ", "_").replace("/", "_")

            script_stem = self.script_path.stem
            preset_filename = f"{script_stem}_{safe_name}{self.PRESET_SUFFIX}"
            preset_path = self.presets_dir / preset_filename

            # Create preset metadata
            preset_data = {
                "name": preset_name,
                "created": datetime.now().isoformat(),
                "script": self.script_path.name,
                "parameters": parameters
            }

            # Write JSON file
            preset_path.write_text(
                json.dumps(preset_data, indent=2),
                encoding="utf-8"
            )

            return True

        except Exception as e:
            print(f"Error saving preset: {e}")
            return False

    def load_preset(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a parameter preset from JSON file.

        Args:
            preset_name: Name of the preset

        Returns:
            Dictionary of parameters, or None if not found
        """
        try:
            safe_name = preset_name.replace(" ", "_").replace("/", "_")
            script_stem = self.script_path.stem
            preset_filename = f"{script_stem}_{safe_name}{self.PRESET_SUFFIX}"
            preset_path = self.presets_dir / preset_filename

            if not preset_path.exists():
                return None

            data = json.loads(preset_path.read_text(encoding="utf-8"))
            return data.get("parameters", {})

        except Exception as e:
            print(f"Error loading preset: {e}")
            return None

    def list_presets(self) -> List[str]:
        """
        List all available presets for this script.

        Returns:
            List of preset names
        """
        presets = []
        script_stem = self.script_path.stem

        try:
            for preset_file in self.presets_dir.glob(f"{script_stem}_*{self.PRESET_SUFFIX}"):
                # Extract preset name from filename
                # Format: {script_stem}_{preset_name}.preset.json
                filename = preset_file.stem  # Remove .json
                prefix = f"{script_stem}_"
                if filename.startswith(prefix):
                    preset_name = filename[len(prefix):]
                    # Remove .preset part
                    if preset_name.endswith(".preset"):
                        preset_name = preset_name[:-7]
                    presets.append(preset_name)
        except Exception as e:
            print(f"Error listing presets: {e}")

        return sorted(presets)

    def delete_preset(self, preset_name: str) -> bool:
        """
        Delete a preset file.

        Args:
            preset_name: Name of the preset to delete

        Returns:
            True if successful
        """
        try:
            safe_name = preset_name.replace(" ", "_").replace("/", "_")
            script_stem = self.script_path.stem
            preset_filename = f"{script_stem}_{safe_name}{self.PRESET_SUFFIX}"
            preset_path = self.presets_dir / preset_filename

            if preset_path.exists():
                preset_path.unlink()
                return True

            return False

        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False

    def export_to_json(self, file_path: str, parameters: Dict[str, Any]) -> bool:
        """
        Export parameters to a custom JSON file.

        Args:
            file_path: Path to export to
            parameters: Dictionary of parameters

        Returns:
            True if successful
        """
        try:
            export_data = {
                "script": self.script_path.name,
                "exported": datetime.now().isoformat(),
                "parameters": parameters
            }

            Path(file_path).write_text(
                json.dumps(export_data, indent=2),
                encoding="utf-8"
            )

            return True

        except Exception as e:
            print(f"Error exporting JSON: {e}")
            return False

    def import_from_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Import parameters from a JSON file.

        Args:
            file_path: Path to import from

        Returns:
            Dictionary of parameters, or None if error
        """
        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
            return data.get("parameters", {})

        except Exception as e:
            print(f"Error importing JSON: {e}")
            return None
