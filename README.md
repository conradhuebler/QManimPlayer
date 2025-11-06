# QManimPlayer - PyQt6 Parameter Editor for manim-gl

[English](#english) | [Deutsch](#deutsch)

---

## English

A dynamic GUI tool for editing parameters in manim-gl (Manim OpenGL) animation scripts.

### Features

✅ **Automatic Parameter Detection** - Reads PARAMETERS dictionary from any manim-gl script
✅ **Dynamic UI Generation** - Automatically creates sliders and spinboxes based on type/min/max
✅ **Categorization** - Organizes parameters by comments (# Physical Parameters, etc.)
✅ **Undo/Redo** - Unlimited change history
✅ **Presets** - Save and load parameter combinations (JSON)
✅ **In-Place File Updates** - Modifies parameters directly in .py files
✅ **manimgl Integration** - Start rendering with current parameters
✅ **Export/Import** - JSON-based data exchange
✅ **Live Updates** - Real-time synchronization between sliders and input fields

### Installation

#### Prerequisites
- Python 3.8+
- PyQt6 (`pip install PyQt6`)
- manim-gl (for rendering: `pip install manimgl`)

#### Step 1: Install
```bash
cd /path/to/qmanimplayer
pip install -e .
```

#### Step 2: Usage

**Via CLI:**
```bash
# GUI without pre-loaded script
python -m qmanimplayer

# GUI with automatically loaded script
python -m qmanimplayer path/to/script.py
```

**Or directly:**
```bash
qmanimplayer script.py
```

### How to Make Scripts Compatible

Your manim-gl script must have a `PARAMETERS` dictionary with this structure:

```python
class MyScene(Scene):
    PARAMETERS = {
        "parameter_name": {
            "value": 100.0,           # Default/current value
            "type": float,            # float or int
            "unit": "kcal/mol",       # Unit (optional, for labels)
            "description": "...",     # Description (tooltip)
            "min": 0.0,               # Minimum
            "max": 1000.0,            # Maximum
        },
        # More parameters...
    }

    def construct(self):
        # Extract values from dictionary
        k = self.PARAMETERS["k"]["value"]
        r0 = self.PARAMETERS["r0"]["value"]
        # ...
```

#### Categorization (Optional)

Comments before parameter blocks are recognized as categories:

```python
PARAMETERS = {
    # Physical Parameters
    "k": { "value": 300.0, ... },
    "r0": { "value": 1.54, ... },

    # Animation Settings
    "duration": { "value": 5.0, ... },
    "fps": { "value": 60, ... },
}
```

This automatically creates collapsible groups in the GUI.

### Project Structure

```
qmanimplayer/
├── __init__.py              # Package init
├── __main__.py              # CLI entry point
├── parser.py                # AST-based PARAMETERS parser
├── param_manager.py         # Parameter state & undo/redo
├── param_editor.py          # Main editor panel
├── widgets.py               # Widget factory (slider, spinbox)
├── preset_manager.py        # Preset save/load (JSON)
├── manim_runner.py          # Subprocess management for manimgl
└── main_window.py           # Main GUI window
```

### Usage Examples

#### 1. Simple Script Opening
```bash
python -m qmanimplayer bond_stretching.py
```

The GUI opens with all detected parameters as editable widgets.

#### 2. Adjust Parameters
- **Slider:** Drag for quick adjustment
- **SpinBox:** Precise numeric input
- **Reset:** Reset all parameters to defaults

#### 3. Save Preset
1. **Menu → Presets → Save Current as Preset...**
2. Enter name (e.g., "high-energy")
3. Preset is saved as `script_high-energy.preset.json`

#### 4. Load Preset
1. **Menu → Presets → Load Preset → [Preset Name]**
2. All parameters are updated

#### 5. Render with Manim
1. Adjust all parameters as desired
2. Click **Run (manimgl)** button
3. Rendering starts in manimgl (shows preview window)
4. Output is displayed in the console

#### 6. Export/Import
```bash
# Export to JSON
Menu → Presets → Export Parameters (JSON)...

# Import from JSON
Menu → Presets → Import Parameters (JSON)...
```

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Script | Ctrl+O |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Quit | Ctrl+Q |

### Known Limitations & TODOs

#### Current Limitations
- Only `float` and `int` parameters are displayed as slider/spinbox
- Other types (bool, str) have only basic widgets
- manimgl must be installed separately
- Parameter dependencies not supported

#### Planned Features
- 🔄 Parameter dependencies (e.g., max ≥ min)
- 🎨 Dark mode support
- 📊 Parameter history visualization
- 🔗 Batch processing of multiple scripts
- 💾 Auto-save session

### Technical Details

#### Parser (AST-based)
- Extracts PARAMETERS dictionary using Abstract Syntax Tree
- Automatically detects Scene classes
- Validates parameter structure

#### ParameterManager
- Undo/Redo stack (unlimited)
- Type validation (float/int)
- Min/Max bounds checking
- In-place .py file updates via regex
- Change listener system

#### Widget Factory
- FloatParameterWidget: SpinBox + Slider for float
- IntParameterWidget: SpinBox + Slider for int
- SimpleParameterWidget: Fallback for other types
- Live synchronization between slider and spinbox

#### PresetManager
- JSON-based (structured, human-readable)
- Stores parameters + metadata (timestamp, script name)
- Naming convention: `{script}_{preset}.preset.json`

### Troubleshooting

**Problem: "manimgl command not found"**
```bash
pip install manimgl
```

**Problem: "PARAMETERS dictionary not found"**
- Ensure your script has a `PARAMETERS` dictionary at the top level
- The name must be exactly `PARAMETERS` (case-sensitive)

**Problem: Parameters are not updating**
- Verify that parameter names in the PARAMETERS dictionary are correct
- Check that the type (float/int) is correct

**Problem: Categories are not recognized**
- Comments must be directly **before** the parameters
- Pattern: `# Word Parameters` (case-insensitive "Parameters" or "Settings")

### Architecture Highlights

```
┌─────────────────────────────────────────┐
│       MainWindow (PyQt6)                 │
│  File Menu | Edit Menu | Presets Menu   │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
   ┌───▼──────┐   ┌────▼────────┐
   │ Param     │   │ Manim       │
   │ Editor    │   │ Runner      │
   │           │   │ (subprocess)│
   └───┬──────┘   └────┬────────┘
       │                │
   ┌───▼──────────────┐ │
   │ ParameterManager │ │
   │ (State + Undo)   │ │
   └───┬──────────────┘ │
       │                │
   ┌───▼──────────────┐ │
   │ .py Script File  │◄┘
   │ (in-place update)│
   └──────────────────┘
```

### License

MIT License - See [LICENSE](LICENSE) file for details.

### Credits

**Author:** Conrad Hübler (Conrad.Huebler@gmx.net)
**AI Contributor:** Claude (Anthropic) - Code generation and architecture assistance

Developed for manim-gl animations with PyQt6 parameter UI automation.

---

## Deutsch

Ein dynamisches GUI-Tool zum Bearbeiten von Parametern in manim-gl (Manim OpenGL) Animationsskripten.

### Features

✅ **Automatische Parameter-Erkennung** - Liest PARAMETERS Dictionary aus beliebigen manim-gl Skripten
✅ **Dynamische UI-Generierung** - Erstellt automatisch Slider, SpinBoxes basierend auf Typ/Min/Max
✅ **Kategorisierung** - Organisiert Parameter nach Kommentaren (# Physical Parameters, etc.)
✅ **Undo/Redo** - Unbegrenzte Änderungshistorie
✅ **Presets** - Speichern und Laden von Parameterkombinationen (JSON)
✅ **In-Place File Updates** - Modifiziert Parameter direkt in der .py Datei
✅ **manimgl Integration** - Startet Rendering mit aktuellen Parametern
✅ **Export/Import** - JSON-basierter Datenaustausch
✅ **Live-Updates** - Echtzeit-Synchronisation zwischen Slidern und Eingabefeldern

### Installation

#### Voraussetzungen
- Python 3.8+
- PyQt6 (`pip install PyQt6`)
- manim-gl (für Rendering: `pip install manimgl`)

#### Schritt 1: Installation
```bash
cd /path/to/qmanimplayer
pip install -e .
```

#### Schritt 2: Verwendung

**Über CLI:**
```bash
# GUI ohne vorgeladenes Skript
python -m qmanimplayer

# GUI mit automatisch geladenem Skript
python -m qmanimplayer path/to/script.py
```

**Oder direkt:**
```bash
qmanimplayer script.py
```

### Wie man Skripte kompatibel macht

Dein manim-gl Skript muss ein `PARAMETERS` Dictionary mit dieser Struktur haben:

```python
class MyScene(Scene):
    PARAMETERS = {
        "parameter_name": {
            "value": 100.0,           # Standard-/aktueller Wert
            "type": float,            # float oder int
            "unit": "kcal/mol",       # Einheit (optional, für Labels)
            "description": "...",     # Beschreibung (Tooltip)
            "min": 0.0,               # Minimum
            "max": 1000.0,            # Maximum
        },
        # Weitere Parameter...
    }

    def construct(self):
        # Werte aus Dictionary extrahieren
        k = self.PARAMETERS["k"]["value"]
        r0 = self.PARAMETERS["r0"]["value"]
        # ...
```

#### Kategorisierung (Optional)

Kommentare vor Parameterblöcken werden als Kategorien erkannt:

```python
PARAMETERS = {
    # Physical Parameters
    "k": { "value": 300.0, ... },
    "r0": { "value": 1.54, ... },

    # Animation Settings
    "duration": { "value": 5.0, ... },
    "fps": { "value": 60, ... },
}
```

Dies erzeugt automatisch kollapsible Gruppen in der GUI.

### Projektstruktur

```
qmanimplayer/
├── __init__.py              # Package init
├── __main__.py              # CLI Entry Point
├── parser.py                # AST-basierter PARAMETERS Parser
├── param_manager.py         # Parameter-State & Undo/Redo
├── param_editor.py          # Haupt-Editor Panel
├── widgets.py               # Widget Factory (Slider, SpinBox)
├── preset_manager.py        # Preset Save/Load (JSON)
├── manim_runner.py          # Subprocess-Management für manimgl
└── main_window.py           # Haupt-GUI Window
```

### Verwendungsbeispiele

#### 1. Einfaches Öffnen eines Skripts
```bash
python -m qmanimplayer bond_stretching.py
```

Die GUI öffnet sich mit allen erkannten Parametern als bearbeitbare Widgets.

#### 2. Parameter anpassen
- **Slider:** Drag für schnelle Anpassung
- **SpinBox:** Präzise numerische Eingabe
- **Reset:** Alle Parameter auf Standard zurücksetzen

#### 3. Preset speichern
1. **Menu → Presets → Save Current as Preset...**
2. Name eingeben (z.B. "high-energy")
3. Preset wird als `script_high-energy.preset.json` gespeichert

#### 4. Preset laden
1. **Menu → Presets → Load Preset → [Preset-Name]**
2. Alle Parameter werden aktualisiert

#### 5. Manim rendern
1. Alle Parameter nach Wunsch anpassen
2. **Run (manimgl)** Button klicken
3. Rendering startet in manimgl (zeigt Preview-Fenster)
4. Output wird in der Konsole angezeigt

#### 6. Export/Import
```bash
# Export zu JSON
Menu → Presets → Export Parameters (JSON)...

# Import von JSON
Menu → Presets → Import Parameters (JSON)...
```

### Keyboard-Shortcuts

| Aktion | Shortcut |
|--------|----------|
| Open Script | Ctrl+O |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Quit | Ctrl+Q |

### Known Limitations & TODOs

#### Aktuelle Einschränkungen
- Nur `float` und `int` Parameter werden als Slider/SpinBox angezeigt
- Andere Typen (bool, str) haben nur Basic-Widgets
- manimgl muss separat installiert sein
- Parameter-Abhängigkeiten nicht unterstützt

#### Geplante Features
- 🔄 Parameter-Abhängigkeiten (z.B. max ≥ min)
- 🎨 Dark Mode Support
- 📊 Parameter-History Visualisierung
- 🔗 Batch-Processing mehrerer Skripte
- 💾 Auto-Save Session

### Technische Details

#### Parser (AST-basiert)
- Extrahiert PARAMETERS Dictionary mittels Abstract Syntax Tree
- Erkennt Scene-Klassen automatisch
- Validiert Parameter-Struktur

#### ParameterManager
- Undo/Redo Stack (unbegrenzt)
- Type-Validierung (float/int)
- Min/Max Bounds-Checking
- In-Place .py Datei-Updates via Regex
- Change-Listener System

#### Widget Factory
- FloatParameterWidget: SpinBox + Slider für float
- IntParameterWidget: SpinBox + Slider für int
- SimpleParameterWidget: Fallback für andere Typen
- Live-Synchronisation zwischen Slider und SpinBox

#### PresetManager
- JSON-basiert (strukturiert, menschlich-lesbar)
- Speichert Parameter + Metadaten (Zeitstempel, Script-Name)
- Namenkonvention: `{script}_{preset}.preset.json`

### Troubleshooting

**Problem: "manimgl command not found"**
```bash
pip install manimgl
```

**Problem: "PARAMETERS dictionary not found"**
- Stelle sicher, dass dein Skript ein `PARAMETERS` Dictionary auf Top-Level hat
- Der Name muss exakt `PARAMETERS` sein (Case-sensitive)

**Problem: Parameter werden nicht aktualisiert**
- Verifiziere, dass die Parameter-Namen im PARAMETERS Dictionary korrekt sind
- Überprüfe, dass Typ (float/int) korrekt ist

**Problem: Kategorien werden nicht erkannt**
- Kommentare müssen direkt **vor** den Parametern sein
- Pattern: `# Wort Parameters` (case-insensitive "Parameters" oder "Settings")

### Architektur-Highlights

```
┌─────────────────────────────────────────┐
│       MainWindow (PyQt6)                 │
│  File Menu | Edit Menu | Presets Menu   │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
   ┌───▼──────┐   ┌────▼────────┐
   │ Param     │   │ Manim       │
   │ Editor    │   │ Runner      │
   │           │   │ (subprocess)│
   └───┬──────┘   └────┬────────┘
       │                │
   ┌───▼──────────────┐ │
   │ ParameterManager │ │
   │ (State + Undo)   │ │
   └───┬──────────────┘ │
       │                │
   ┌───▼──────────────┐ │
   │ .py Script File  │◄┘
   │ (in-place update)│
   └──────────────────┘
```

### Lizenz

MIT License - Siehe [LICENSE](LICENSE) Datei für Details.

### Credits

**Autor:** Conrad Hübler (Conrad.Huebler@gmx.net)
**AI Contributor:** Claude (Anthropic) - Code-Generierung und Architektur-Unterstützung

Entwickelt für manim-gl Animationen mit PyQt6 Parameter-UI Automation.
