# Changelog

All notable changes to QManimPlayer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-06

### Added

#### Core Functionality
- **Parser Module** (`parser.py`)
  - AST-based parameter extraction from manim-gl scripts
  - Automatic category recognition from comments
  - Support for float, int, bool, and str parameter types
  - Metadata extraction (value, type, unit, description, min/max bounds)

- **Parameter Manager** (`param_manager.py`)
  - Centralized parameter state management
  - Undo/redo system with stack-based implementation
  - In-place Python file updates (hybrid AST+regex approach)
  - Change listener pattern for UI synchronization
  - Batch parameter updates support

- **Widget Factory** (`widgets.py`)
  - Dynamic control generation based on parameter types
  - FloatParameterWidget with linked spinbox and slider
  - IntParameterWidget with linked spinbox and slider
  - Automatic bounds validation
  - Real-time value synchronization

- **Parameter Editor** (`param_editor.py`)
  - Collapsible category groups
  - Automatic UI generation from PARAMETERS dictionary
  - Real-time parameter updates
  - Category-based organization

- **Preset Manager** (`preset_manager.py`)
  - JSON-based preset persistence
  - Save/load parameter combinations
  - Preset listing and selection
  - Script-specific preset isolation

- **Manim Runner** (`manim_runner.py`)
  - Thread-safe subprocess management
  - Live output capture (stdout/stderr)
  - Process control (start/stop/kill)
  - Error handling and reporting

- **Main Window** (`main_window.py`)
  - Full GUI with menu bar and toolbar
  - File browser for script navigation
  - Integrated console for manim output
  - Keyboard shortcuts (Ctrl+Z/Y for undo/redo)
  - Status bar with operation feedback

- **CLI Entry Point** (`__main__.py`)
  - Command-line interface with argparse
  - Optional script path argument
  - `python -m qmanimplayer [script.py]` support

#### Documentation
- README.md with comprehensive usage guide (German)
- CLAUDE.md with architecture and development guidelines
- setup.py for package installation
- requirements.txt with dependencies

### Features

- ✅ Dynamic parameter editing with real-time file updates
- ✅ Undo/redo system for parameter changes
- ✅ Preset save/load functionality
- ✅ Live manim-gl integration with output capture
- ✅ Category-based parameter organization
- ✅ Type-safe parameter validation
- ✅ Keyboard shortcuts for common operations
- ✅ Extensible widget system

### Technical Details

- Python 3.8+ support
- PyQt6-based GUI
- AST-based Python code analysis
- Thread-safe process management
- Change listener pattern for loose coupling
- Modular architecture with clear separation of concerns

### Known Limitations

- Only float/int parameters have slider+spinbox (bool/str use fallback)
- No parameter dependency validation (e.g., min < max)
- File updates use regex (sensitive to formatting changes)
- Single script per session (no multi-script support)

### Credits

- **Author:** Conrad Hübler (Conrad.Huebler@gmx.net)
- **AI Contributor:** Claude (Anthropic) - Code generation and architecture assistance

---

[0.1.0]: https://github.com/yourusername/qmanimplayer/releases/tag/v0.1.0
