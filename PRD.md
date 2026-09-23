# `niri-layout` - Multi-Monitor Workspace Layout Manager for Niri

---

## 1. Problem Statement

Niri is a scrollable-tiling Wayland window manager where windows are organized in horizontal column ribbons across workspaces and monitors. Currently, setting up complex multi-monitor workflow sessions (e.g., development environments with specific terminals, browser windows, and documentation tiles grouped into columns with specific widths) must be performed manually every time a session restarts or context shifts.

There is no native mechanism in Niri to snapshot, serialize, and reliably restore multi-monitor, column-aware workspace layouts on demand.

---

## 2. Proposed Solution

`niri-layout` is a zero-dependency Python CLI tool that interfaces with Niri via its CLI IPC (`niri msg`). It captures live workspace configurations into declarative JSON schema definitions, manages layout restoration by appending fresh workspaces onto physical monitors, and provides an export option to generate standalone executable shell scripts.

### 2.1 Core Architectural Decisions

* **Hybrid Snapshot/Declarative Model**: Snapshots live workspace topologies into clean, editable `.json` layout templates.
* **Display Identification**: Matches displays using monitor hardware metadata (`make`, `model`, `serial`) with connector name fallback.
* **Hierarchical Column Topology**: Stores layouts as `output -> workspace -> column -> window`, retaining column width ratios and grouping modes (`tabbed` vs. `split`).
* **Workspace Isolation**: Appends new isolated workspaces to target monitors without overwriting or disrupting existing sessions.
* **Event-Stream IPC Placement**: Launches applications and correlates new windows using Niri's `event-stream` IPC, matching windows via a sequential FIFO queue per `app_id`.
* **Display Fallback**: Collapses layouts destined for disconnected displays onto available active displays.
* **Focus Preservation**: Captures the focused window during snapshot and refocuses it upon restoration completion.

---

## 3. Concrete Examples

### 3.1 Layout Schema Definition (`~/.config/niri/layouts/dev-dual.json`)

```json
{
  "name": "dev-dual",
  "version": 1,
  "focus": {
    "output_match": "Dell Inc. DELL U2720Q 123456",
    "column_index": 0,
    "window_index": 0
  },
  "outputs": [
    {
      "identifier": {
        "make": "Dell Inc.",
        "model": "DELL U2720Q",
        "serial": "123456",
        "fallback_connector": "DP-1"
      },
      "workspaces": [
        {
          "name": "dev-main",
          "columns": [
            {
              "mode": "split",
              "width": { "proportion": 0.5 },
              "windows": [
                {
                  "app_id": "Alacritty",
                  "desktop_id": "Alacritty.desktop"
                }
              ]
            },
            {
              "mode": "tabbed",
              "width": { "proportion": 0.5 },
              "windows": [
                {
                  "app_id": "firefox",
                  "desktop_id": "firefox.desktop"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "identifier": {
        "make": "LG Electronics",
        "model": "LG Ultra HD",
        "serial": "789012",
        "fallback_connector": "HDMI-A-1"
      },
      "workspaces": [
        {
          "name": "dev-side",
          "columns": [
            {
              "mode": "split",
              "width": { "proportion": 1.0 },
              "windows": [
                {
                  "app_id": "org.gnome.Nautilus",
                  "desktop_id": "org.gnome.Nautilus.desktop"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}

```

### 3.2 CLI Interface Usage

```bash
# Capture currently active workspaces on all connected monitors
niri-layout save dev-dual

# Restore layout into newly appended workspaces
niri-layout restore dev-dual

# Export layout into an autonomous standalone launcher script
niri-layout export dev-dual ~/.config/niri/scripts/launch-dev.sh
chmod +x ~/.config/niri/scripts/launch-dev.sh

```

---

## 4. Constraints

1. **Zero External Dependencies**: Must run on Python 3.10+ using only standard library modules (`subprocess`, `json`, `pathlib`, `argparse`, `time`, `shutil`).
2. **IPC Communication Mechanism**: Must interact with Niri strictly via standard subprocesses invoking `niri msg --json ...` and streaming `niri msg --json event-stream` (no external socket or C-bindings).
3. **Execution Runtime Safety**: Per-window timeout (e.g., 5 seconds) must ensure non-blocking recovery: if a window fails to spawn or register on the event stream, log a warning and proceed without hanging.
4. **Desktop Resolution**: Window execution commands must be resolved from standard system and user desktop entries (`/usr/share/applications/` and `~/.local/share/applications/`).

---

## 5. Acceptance Criteria

* [ ] **Capture & Serialization**:
* `niri-layout save <name>` queries `niri msg --json outputs` and `niri msg --json workspaces`.
* Captures the active workspace per connected monitor by default (or all workspaces if `--all-workspaces` is passed).
* Resolves each window's `app_id` to its corresponding `.desktop` file `Exec` key.
* Successfully writes standard formatted JSON to `~/.config/niri/layouts/<name>.json`.


* [ ] **Display Resolution & Matching**:
* `niri-layout restore <name>` matches physical displays using EDID/metadata (`make`, `model`, `serial`).
* Successfully falls back to connector names (eDP-1, DP-X, etc.) if metadata is incomplete.
* If a saved output is completely missing/unplugged, collapses its workspaces onto the primary connected display.


* [ ] **Workspace Creation & Window Placement**:
* Appends a new workspace to the target monitor before window creation.
* Starts background event listener on `niri msg --json event-stream`.
* Launches each application's `.desktop` command and correlates incoming `WindowOpenedOrChanged` events via FIFO queue on `app_id`.
* Issues Niri actions to set column widths and configure column grouping modes (`tabbed` or `split`).


* [ ] **Resilience & Focus**:
* Continues restoring subsequent columns/windows if an application fails to emit a window event within 5 seconds.
* Refocuses the captured target window upon completion using `niri msg action focus-window --id <id>`.


* [ ] **Script Export**:
* `niri-layout export <name> <output_path>` produces a self-contained executable shell script that invokes the restoration routine for binding into `niri.kdl` or application menus.



---

## 6. Out of Scope

The following items were identified and explicitly deferred for future iterations:

* **Process Inspection via `/proc**`: Restoring exact terminal working directories (`cwd`) and transient CLI flags (`/proc/<pid>/cmdline`).
* **Single-Instance Application Flag Injection**: Hardcoded overrides (such as auto-injecting `--new-window` for Firefox, Chrome, or Electron apps).
* **Floating Window State Persistence**: Capturing, repositioning, or restoring floating geometries.
* **Session Teardown / Workspace Killing**: Automated tracking and terminating of spawned processes or batch closing of layout workspaces.
* **YAML Storage Format**: Direct `.yaml` layout definitions (deferred until external dependency packaging like `PyYAML` or `uv` is adopted).
* **Native Direct Socket IPC Protocol**: Connecting directly to `$NIRI_SOCKET` without spawning the `niri msg` CLI binary.