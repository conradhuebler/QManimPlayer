"""
Main Window - Main application window for QManimPlayer.

Features:
- File browser and script loading
- Menu bar with File/Edit/Presets
- Toolbar with quick actions
- Parameter editor panel
- Output console
- Status bar
"""

import sys
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QTextEdit,
    QSplitter, QComboBox, QLabel, QStatusBar, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QIcon

from .parser import parse_script
from .param_manager import ParameterManager
from .param_editor import ParameterEditor
from .preset_manager import PresetManager
from .manim_runner import ManimRunner, ManimProcessStatus, ManimRenderMode


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QManimPlayer - Parameter Editor for manim-gl")
        self.setGeometry(100, 100, 1200, 800)

        # Current state
        self.current_script: Optional[Path] = None
        self.param_manager: Optional[ParameterManager] = None
        self.preset_manager: Optional[PresetManager] = None
        self.manim_runner: Optional[ManimRunner] = None
        self.param_editor: Optional[ParameterEditor] = None

        # Setup UI
        self._setup_ui()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()

    def _setup_ui(self):
        """Set up the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # File selection area
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Script:"))

        self.script_path_label = QLabel("(No script loaded)")
        file_layout.addWidget(self.script_path_label, 1)

        open_btn = QPushButton("Open Script...")
        open_btn.clicked.connect(self._on_open_script)
        file_layout.addWidget(open_btn)

        layout.addLayout(file_layout)

        # Main content: file browser | editor | console
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # File browser (left)
        file_browser_widget = self._create_file_browser()
        splitter.addWidget(file_browser_widget)

        # Parameter editor (middle)
        self.editor_placeholder = QWidget()
        self.editor_placeholder.setLayout(QVBoxLayout())
        self.editor_placeholder.layout().addWidget(
            QLabel("Load a script to edit parameters")
        )

        splitter.addWidget(self.editor_placeholder)

        # Output console (right)
        console_layout = QVBoxLayout()
        console_layout.addWidget(QLabel("Output:"))

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(200)
        console_layout.addWidget(self.console)

        console_widget = QWidget()
        console_widget.setLayout(console_layout)
        splitter.addWidget(console_widget)

        # Layout proportions: 1 (browser) : 3 (editor) : 1 (console)
        splitter.setStretchFactor(0, 1)  # File browser
        splitter.setStretchFactor(1, 3)  # Editor
        splitter.setStretchFactor(2, 1)  # Console

        layout.addWidget(splitter, 1)

        # Control buttons
        control_layout = QHBoxLayout()

        self.run_btn = QPushButton("Run (manimgl)")
        self.run_btn.clicked.connect(self._on_run_manim)
        self.run_btn.setEnabled(False)
        control_layout.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop_manim)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        control_layout.addStretch()

        layout.addLayout(control_layout)

        central_widget.setLayout(layout)

    def _create_file_browser(self) -> QWidget:
        """Create file browser widget."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.addWidget(QLabel("Scripts"))

        refresh_btn = QPushButton("↻")
        refresh_btn.setMaximumWidth(30)
        refresh_btn.clicked.connect(self._refresh_file_list)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        # File list
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self._on_file_selected)
        layout.addWidget(self.file_list)

        widget.setLayout(layout)
        return widget

    def _refresh_file_list(self):
        """Refresh list of .py files with error handling."""
        self.file_list.clear()

        try:
            # Determine directory
            if self.current_script:
                directory = self.current_script.parent
            else:
                directory = Path.cwd()

            # Validate directory
            if not directory.exists() or not directory.is_dir():
                self._log(f"⚠ Directory not accessible: {directory}")
                return

            # Find all .py files
            try:
                py_files = list(directory.glob("*.py"))

                # Limit to prevent UI freeze
                if len(py_files) > 100:
                    self._log(f"⚠ {len(py_files)} scripts found, showing only first 100")
                    py_files = py_files[:100]

                for py_file in sorted(py_files):
                    try:
                        item = QListWidgetItem(py_file.name)
                        item.setData(Qt.ItemDataRole.UserRole, str(py_file))
                        self.file_list.addItem(item)

                        # Highlight current file
                        if self.current_script and py_file == self.current_script:
                            item.setSelected(True)
                            self.file_list.scrollToItem(item)
                    except Exception as e:
                        self._log(f"⚠ Error adding {py_file.name}: {e}")
                        continue

            except PermissionError:
                self._log(f"⚠ Permission denied reading directory: {directory}")
            except Exception as e:
                self._log(f"⚠ Error listing scripts: {e}")

        except Exception as e:
            self._log(f"⚠ Error in file list refresh: {e}")

    @pyqtSlot(QListWidgetItem)
    def _on_file_selected(self, item: QListWidgetItem):
        """Handle file selection from browser."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self._load_script(file_path)

    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Script...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_script)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self._on_undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self._on_redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        self.reset_action = QAction("Reset All Parameters", self)
        self.reset_action.triggered.connect(self._on_reset_all)
        self.reset_action.setEnabled(False)
        edit_menu.addAction(self.reset_action)

        # Presets menu
        presets_menu = menubar.addMenu("&Presets")

        self.save_preset_action = QAction("Save Current as Preset...", self)
        self.save_preset_action.triggered.connect(self._on_save_preset)
        self.save_preset_action.setEnabled(False)
        presets_menu.addAction(self.save_preset_action)

        self.load_preset_menu = presets_menu.addMenu("Load Preset")
        self.load_preset_menu.setEnabled(False)

        presets_menu.addSeparator()

        export_action = QAction("Export Parameters (JSON)...", self)
        export_action.triggered.connect(self._on_export_json)
        presets_menu.addAction(export_action)

        import_action = QAction("Import Parameters (JSON)...", self)
        import_action.triggered.connect(self._on_import_json)
        presets_menu.addAction(import_action)

    def _create_tool_bar(self):
        """Create toolbar."""
        toolbar = self.addToolBar("Main Toolbar")

        open_action = QAction("Open", self)
        open_action.triggered.connect(self._on_open_script)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        self.undo_toolbar = QAction("Undo", self)
        self.undo_toolbar.triggered.connect(self._on_undo)
        self.undo_toolbar.setEnabled(False)
        toolbar.addAction(self.undo_toolbar)

        self.redo_toolbar = QAction("Redo", self)
        self.redo_toolbar.triggered.connect(self._on_redo)
        self.redo_toolbar.setEnabled(False)
        toolbar.addAction(self.redo_toolbar)

        toolbar.addSeparator()

        self.run_toolbar = QAction("Run (manimgl)", self)
        self.run_toolbar.triggered.connect(self._on_run_manim)
        self.run_toolbar.setEnabled(False)
        toolbar.addAction(self.run_toolbar)

        self.stop_toolbar = QAction("Stop", self)
        self.stop_toolbar.triggered.connect(self._on_stop_manim)
        self.stop_toolbar.setEnabled(False)
        toolbar.addAction(self.stop_toolbar)

        toolbar.addSeparator()

        # Render mode dropdown
        toolbar.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            ManimRenderMode.AUTO_PLAY.value,
            ManimRenderMode.PREVIEW_LOOP.value,
            ManimRenderMode.SAVE_ONLY.value,
        ])
        self.mode_combo.setCurrentIndex(1)  # Default: Preview Loop (interactive)
        self.mode_combo.setEnabled(False)
        toolbar.addWidget(self.mode_combo)

    def _create_status_bar(self):
        """Create status bar."""
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Ready")

    def _show_error(self, title: str, message: str):
        """Show error dialog and log to console."""
        QMessageBox.warning(self, title, message)
        self._log(f"❌ {title}: {message}")

    def _cleanup_on_error(self):
        """Reset UI after script loading error."""
        try:
            layout = self.editor_placeholder.layout()
            while layout.count():
                layout.takeAt(0)
            layout.addWidget(QLabel("⚠ Load a valid script to edit parameters"))

            self.run_btn.setEnabled(False)
            self.run_toolbar.setEnabled(False)
            self.mode_combo.setEnabled(False)
            self.statusbar.showMessage("⚠ Ready (no valid script loaded)")
        except Exception:
            pass

    @pyqtSlot()
    def _on_open_script(self):
        """Handle open script action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open manim-gl Script",
            "",
            "Python Files (*.py);;All Files (*)"
        )

        if not file_path:
            return

        self._load_script(file_path)

    def _load_script(self, file_path: str):
        """Load a manim-gl script with comprehensive error handling."""
        try:
            # Validate file exists
            self.current_script = Path(file_path)
            if not self.current_script.exists():
                self._show_error("File Not Found", f"Script nicht gefunden:\n{file_path}")
                self.current_script = None
                return

            if not self.current_script.is_file():
                self._show_error("Invalid Path", "Das ist kein File, sondern ein Verzeichnis")
                self.current_script = None
                return

            # Try to parse script
            try:
                parameters, categories, scenes = parse_script(file_path)
            except SyntaxError as e:
                self._show_error("Syntax Error", f"Syntax-Fehler im Script:\n\n{str(e)[:200]}")
                self.current_script = None
                self._cleanup_on_error()
                return
            except Exception as e:
                self._show_error("Parse Error", f"Script konnte nicht gelesen werden:\n\n{str(e)[:200]}")
                self.current_script = None
                self._cleanup_on_error()
                return

            # Validate parameters found
            if not parameters:
                self._show_error("No Parameters", "PARAMETERS Dictionary nicht gefunden im Script")
                self.current_script = None
                self._cleanup_on_error()
                return

            try:
                # Create managers
                self.param_manager = ParameterManager(file_path, parameters)
                self.param_manager.add_file_modified_listener(self._on_params_modified)

                self.preset_manager = PresetManager(file_path)

                self.manim_runner = ManimRunner(file_path)
                self.manim_runner.on_status_changed = self._on_manim_status_changed
                self.manim_runner.on_output = self._on_manim_output
                self.manim_runner.on_error = self._on_manim_error

                # Start queue processing timer (thread-safe output handling)
                self.manim_runner.queue_timer = QTimer()
                self.manim_runner.queue_timer.timeout.connect(self.manim_runner._process_queues)
                self.manim_runner.queue_timer.start(50)  # Process queues every 50ms

                # Create parameter editor
                self.param_editor = ParameterEditor(self.param_manager, categories)
                self.param_editor.parameter_changed.connect(self._on_param_changed)

                # Replace placeholder with actual editor
                layout = self.editor_placeholder.layout()
                while layout.count():
                    layout.takeAt(0)
                layout.addWidget(self.param_editor)

                # Update UI
                self.script_path_label.setText(self.current_script.name)
                self.run_btn.setEnabled(True)
                self.run_toolbar.setEnabled(True)
                self.mode_combo.setEnabled(True)
                self.save_preset_action.setEnabled(True)
                self.load_preset_menu.setEnabled(True)
                self.reset_action.setEnabled(True)

                # Update lists
                self._update_presets_menu()
                self._refresh_file_list()

                # Log success
                self.console.clear()
                self._log(f"✓ Loaded: {self.current_script.name}")
                self._log(f"  Scenes: {', '.join(scenes) if scenes else 'None found'}")
                self._log(f"  Parameters: {len(parameters)}")
                self.statusbar.showMessage(f"✓ Loaded: {self.current_script.name}")

            except Exception as e:
                self._show_error("Setup Error", f"Fehler beim Einrichten:\n\n{str(e)[:200]}")
                self.current_script = None
                self._cleanup_on_error()
                import traceback
                self._log(f"Setup Traceback: {traceback.format_exc()[:500]}")

        except Exception as e:
            # Catch-all for unexpected errors
            self._show_error("Unexpected Error", f"Unerwarteter Fehler:\n\n{str(e)[:200]}")
            self.current_script = None
            self._cleanup_on_error()
            import traceback
            self._log(f"Full Traceback: {traceback.format_exc()[:500]}")

    def _update_presets_menu(self):
        """Update the presets menu with available presets."""
        self.load_preset_menu.clear()

        if not self.preset_manager:
            return

        presets = self.preset_manager.list_presets()

        if not presets:
            action = self.load_preset_menu.addAction("(No presets)")
            action.setEnabled(False)
            return

        for preset_name in presets:
            action = self.load_preset_menu.addAction(preset_name)
            action.triggered.connect(
                lambda checked, name=preset_name: self._load_preset(name)
            )

    @pyqtSlot(str, object)
    def _on_param_changed(self, param_name: str, new_value):
        """Handle parameter change."""
        self._update_undo_redo_state()

    @pyqtSlot()
    def _on_undo(self):
        """Handle undo action."""
        if self.param_manager and self.param_manager.undo():
            self._update_undo_redo_state()
            self._log("Undo")

    @pyqtSlot()
    def _on_redo(self):
        """Handle redo action."""
        if self.param_manager and self.param_manager.redo():
            self._update_undo_redo_state()
            self._log("Redo")

    @pyqtSlot()
    def _on_reset_all(self):
        """Handle reset all parameters."""
        reply = QMessageBox.question(
            self,
            "Reset All Parameters",
            "Reset all parameters to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.param_editor:
                self.param_editor._on_reset_all()
            self._log("Reset all parameters")

    @pyqtSlot()
    def _on_save_preset(self):
        """Handle save preset action."""
        if not self.param_manager or not self.preset_manager:
            return

        # Simple input dialog
        preset_name, ok = self._input_dialog("Save Preset", "Preset name:")
        if not ok or not preset_name:
            return

        params = self.param_manager.get_all_parameters()
        if self.preset_manager.save_preset(preset_name, params):
            self._log(f"Saved preset: {preset_name}")
            self._update_presets_menu()
        else:
            QMessageBox.warning(self, "Error", "Failed to save preset")

    def _load_preset(self, preset_name: str):
        """Load a preset."""
        if not self.param_manager or not self.preset_manager:
            return

        params = self.preset_manager.load_preset(preset_name)
        if params:
            self.param_manager.set_parameters_batch(params)
            self._log(f"Loaded preset: {preset_name}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load preset")

    @pyqtSlot()
    def _on_export_json(self):
        """Handle export to JSON."""
        if not self.param_manager or not self.preset_manager:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Parameters",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        params = self.param_manager.get_all_parameters()
        if self.preset_manager.export_to_json(file_path, params):
            self._log(f"Exported to: {file_path}")
        else:
            QMessageBox.warning(self, "Error", "Failed to export")

    @pyqtSlot()
    def _on_import_json(self):
        """Handle import from JSON."""
        if not self.param_manager or not self.preset_manager:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Parameters",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        params = self.preset_manager.import_from_json(file_path)
        if params:
            self.param_manager.set_parameters_batch(params)
            self._log(f"Imported from: {file_path}")
        else:
            QMessageBox.warning(self, "Error", "Failed to import")

    @pyqtSlot()
    def _on_run_manim(self):
        """Handle run manim action."""
        if not self.manim_runner:
            return

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.run_toolbar.setEnabled(False)
        self.stop_toolbar.setEnabled(True)
        self.mode_combo.setEnabled(False)

        self.console.clear()
        self._log("Starting manim-gl...")

        # Get selected render mode from dropdown
        mode_text = self.mode_combo.currentText()
        render_mode = None

        if mode_text == ManimRenderMode.AUTO_PLAY.value:
            render_mode = ManimRenderMode.AUTO_PLAY
        elif mode_text == ManimRenderMode.PREVIEW_LOOP.value:
            render_mode = ManimRenderMode.PREVIEW_LOOP
        elif mode_text == ManimRenderMode.SAVE_ONLY.value:
            render_mode = ManimRenderMode.SAVE_ONLY

        self._log(f"Mode: {mode_text}")

        success = self.manim_runner.run(mode=render_mode)
        if not success:
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.run_toolbar.setEnabled(True)
            self.stop_toolbar.setEnabled(False)
            self.mode_combo.setEnabled(True)

    @pyqtSlot()
    def _on_stop_manim(self):
        """Handle stop manim action."""
        if self.manim_runner:
            self.manim_runner.stop()
            self._log("Manim process stopped")

    def _on_manim_status_changed(self, status: ManimProcessStatus):
        """Handle manim process status change."""
        self.statusbar.showMessage(f"Manim: {status.value}")

        if status == ManimProcessStatus.STOPPING:
            # During stopping: disable all controls
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.run_toolbar.setEnabled(False)
            self.stop_toolbar.setEnabled(False)
            self.mode_combo.setEnabled(False)
            self._log("Stopping process...")

        elif status == ManimProcessStatus.FINISHED:
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.run_toolbar.setEnabled(True)
            self.stop_toolbar.setEnabled(False)
            self.mode_combo.setEnabled(True)
            self._log("Rendering completed!")

        elif status == ManimProcessStatus.ERROR or status == ManimProcessStatus.STOPPED:
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.run_toolbar.setEnabled(True)
            self.stop_toolbar.setEnabled(False)
            self.mode_combo.setEnabled(True)

    def _on_manim_output(self, message: str):
        """Handle manim output."""
        self._log(message)

    def _on_manim_error(self, message: str):
        """Handle manim error."""
        self._log(f"ERROR: {message}")

    def _on_params_modified(self):
        """Handle parameter file modification."""
        self._update_undo_redo_state()

    def _update_undo_redo_state(self):
        """Update undo/redo button states."""
        if not self.param_manager:
            return

        can_undo = self.param_manager.can_undo()
        can_redo = self.param_manager.can_redo()

        self.undo_action.setEnabled(can_undo)
        self.undo_toolbar.setEnabled(can_undo)
        self.redo_action.setEnabled(can_redo)
        self.redo_toolbar.setEnabled(can_redo)

    def _log(self, message: str):
        """Add message to console."""
        self.console.append(message)

    def _input_dialog(self, title: str, label: str) -> tuple:
        """Simple input dialog."""
        from PyQt6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, title, label)
        return text, ok
