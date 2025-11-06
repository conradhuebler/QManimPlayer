# CLAUDE: QManimPlayer - Parameter Editor for manim-gl

## Overview

**QManimPlayer** is a PyQt6 GUI tool for dynamically editing parameters in manim-gl (Manim OpenGL) animation scripts. It automatically parses PARAMETERS dictionaries, generates UI controls (sliders, spinboxes), and provides preset management, undo/redo, and manimgl integration.

**Target users**: Animation creators who want intuitive parameter editing without touching code.

## General Instructions

- Each module has clear responsibilities (see Module Documentation)
- **Keep code modular**: Parser, Manager, UI, Rendering are separate concerns
- **Type-safe**: Use type hints throughout (required for IDE support)
- **AST-based parsing**: Never use regex for Python code - use `ast` module
- **File updates via AST**: When modifying .py files, use AST+regex hybrid (parse structure, replace values)
- **Change listeners**: Use callback system for loose coupling between modules
- **No hardcoded paths**: All paths are relative or configurable

## Development Guidelines

### Code Organization
- `parser.py` - Script parsing, parameter extraction, category recognition
- `param_manager.py` - Parameter state, undo/redo, file persistence
- `widgets.py` - Widget factory, dynamic control generation
- `param_editor.py` - Main editor UI with category groups
- `preset_manager.py` - JSON preset save/load
- `manim_runner.py` - Subprocess management for manimgl
- `main_window.py` - Application window, menu, toolbar
- `__main__.py` - CLI entry point

### Implementation Standards
- All parameter updates go through `ParameterManager` (single source of truth)
- Validation: Type check + bounds check before applying
- UI updates triggered by change listeners (not direct manipulation)
- Error handling: Always provide user feedback via dialogs or console
- Logging: Use print() for now, can upgrade to logging module later

### Workflow States
- **ADD**: Features to be added
- **WIP**: Currently being worked on
- **ADDED**: Basically implemented
- **TESTED**: Works (by operator feedback)
- **APPROVED**: Move to AICHANGELOG.md, remove from CLAUDE.md

### File Update Strategy
- **In-Place Updates**: Modify PARAMETERS values directly in .py scripts
- **Hybrid Approach**: Use AST to find PARAMETERS block, then regex to replace values
- **Safety**: Always create backups or version control (user's responsibility)

### Git Best Practices
- **Only commit source code**: Don't commit preset files or rendered media
- **Meaningful commits**: "Add parameter export", "Fix slider bounds validation"
- **Include context**: If fixing a bug, reference what went wrong

## [Preserved Section - Permanent Documentation]
**Change only if explicitly wanted by operator**

### Architecture v1.0.0

**Core Design:**
- **Single Responsibility**: Each module handles one concern
- **Change Listener Pattern**: Loose coupling between components
- **AST-based Parsing**: Robust Python code analysis
- **Type-Safe Operations**: Full type hints, validation at boundaries

**Parameter Metadata Structure:**
```python
PARAMETERS = {
    "param_name": {
        "value": 100.0,           # Current/default value
        "type": float,            # Type: float, int, bool, str
        "unit": "kcal/mol",       # Display unit
        "description": "...",     # Tooltip
        "min": 0.0,               # Minimum
        "max": 1000.0,            # Maximum
    }
}
```

**Module Responsibilities:**
- `ParameterParser`: Extract metadata from scripts (AST)
- `ParameterManager`: Manage state, undo/redo, file updates
- `ParameterWidgetFactory`: Create appropriate UI controls
- `ParameterEditor`: Organize widgets with categories
- `PresetManager`: Save/load parameter combinations (JSON)
- `ManimRunner`: Subprocess control + output capture
- `MainWindow`: Orchestrate all components

**Widget Strategy:**
- `FloatParameterWidget`: QDoubleSpinBox + QSlider (linked)
- `IntParameterWidget`: QSpinBox + QSlider (linked)
- Live sync between slider and spinbox value
- Bounds validation before commit

**Undo/Redo Implementation:**
- Stack-based: `undo_stack` and `redo_stack` (lists of changes)
- Change unit: List of `ParameterChange` objects (can batch multiple params)
- Bidirectional: `set_parameter()` pushes to undo, `undo()` pops and pushes to redo
- File sync: Each undo/redo triggers file update

**Preset Format (JSON):**
```json
{
  "name": "preset_name",
  "created": "2025-11-05T...",
  "script": "bond_stretching.py",
  "parameters": {
    "k": 350.0,
    "r0": 1.6,
    ...
  }
}
```

**Category Recognition:**
- Regex pattern: `# \w+\s+Parameters?|Settings?`
- Categories are comments before parameter blocks
- Automatic detection: No manual configuration needed

### Known Limitations
- Only float/int have slider+spinbox (bool/str use fallback)
- No parameter dependencies (max must be > min is user's responsibility)
- File updates use regex (fragile if code formatting changes)
- Single script per session (no multi-script support yet)

## [Variable Section - Current Tasks]

### ✅ COMPLETED (v1.0.0)
- ✅ **Parser Module** - AST-based parameter extraction + category recognition
- ✅ **ParameterManager** - State mgmt, undo/redo, in-place .py updates
- ✅ **Widget Factory** - Dynamic spinbox/slider generation
- ✅ **ParameterEditor** - Collapsible category groups
- ✅ **PresetManager** - JSON save/load
- ✅ **ManimRunner** - Subprocess + output capture
- ✅ **MainWindow** - Full UI with menu/toolbar/console
- ✅ **CLI Entry Point** - `python -m qmanimplayer [script.py]`
- ✅ **Documentation** - README.md with usage examples

### TESTED
- Parser: Correctly extracts 7 parameters from bond_stretching.py
- ParameterManager: Undo/redo stack working, file updates functional
- PresetManager: Save/load/list presets via JSON
- All imports: No circular dependencies

## [Instructions Block - Operator-Defined Tasks]

### Vision
- Keep parameter editing simple and intuitive (no complex UI)
- Support arbitrary manim scripts (extensible via PARAMETERS pattern)
- Enable power users via presets, undo/redo, export/import

### Future Features (Priority Order)
1. **Parameter Dependencies** - Add validation rules (e.g., min < max)
2. **Dark Mode** - PyQt6 stylesheet support
3. **Video Preview** - Embed MP4 player for rendered output
4. **Batch Mode** - Edit parameters for multiple scripts
5. **Parameter History** - Show before/after values in UI
6. **Custom Validators** - Per-parameter validation functions
7. **Macro Recording** - Record/replay parameter change sequences

### Known Improvements Needed
- File update regex is fragile (consider full AST rewrite)
- Error messages could be more user-friendly
- Category detection could handle nested structures
- Console output should be syntax-highlighted

### Testing TODOs
- Test with different manim script structures
- Test parameter bounds edge cases
- Test undo/redo with batch operations
- Test manimgl integration on different systems

## Module Documentation

- **parser.py** - AST-based script parsing, parameter extraction
- **param_manager.py** - Parameter state, undo/redo, file updates
- **widgets.py** - Widget factory for control generation
- **param_editor.py** - Main editor panel with categories
- **preset_manager.py** - Preset persistence (JSON)
- **manim_runner.py** - Subprocess management for manimgl
- **main_window.py** - Application window, menus, toolbar
- **__main__.py** - CLI entry point

## Standards

### Parameter Metadata (Required Fields)
- `value`: Current/default value (any type)
- `type`: Python type (float, int, bool, str)
- `unit`: Display unit string (e.g., "kcal/mol")
- `description`: User-friendly tooltip
- `min`: Minimum bound (numeric only)
- `max`: Maximum bound (numeric only)

### File Update Pattern
1. Parse .py with AST to find PARAMETERS block line range
2. Use regex to find specific parameter's "value" field
3. Replace old value with new value
4. Write back to file (atomic, no intermediate states)

### Error Handling Standards
- **Parser errors**: Show dialog with file path + line number
- **Manager errors**: Log to console, allow retry
- **UI errors**: Display in status bar + tooltip
- **Runner errors**: Show in output console with [ERROR] prefix

### Testing Strategy
- Unit test each module independently
- Test with bond_stretching.py as reference
- Test edge cases: empty PARAMETERS, malformed dict, invalid values
- Manual UI testing: slider drag, preset save/load, undo/redo chain
