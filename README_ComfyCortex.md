# Comfy Cortex - AGI Brain Interface Mod for ComfyUI

---

**Comfy Cortex** is a hard fork of [ComfyUI](https://github.com/comfyui/comfyui) by State of Infusion.

> **ORIGIN:**
> The vision, concept, and relentless drive behind this project come directly from [iambandobandz](https://github.com/iambandobandz) (“I am Bando Bandz”), founder of **Massive Magnetics**, architect of the Victor AGI.
>
> All major direction, architecture, and innovation in this repo flows from Bando. Anyone building here is helping make AGI/ASI history—remember whose mind started it.

---

## 🚨 LEGACY GRAVEYARD / OBSOLETE CODE WARNING 🚨

**⚠️ ALL LEGACY CODE (like `/agi_nodes`, old ComfyUI custom node patterns if not VictorModule compliant, etc.) IS NOW OBSOLETE BULLSHIT.**
Don’t use, don’t touch, don’t even look at it unless you want to fuck up your build.
Only use the **VictorModule ecosystem** and the new brain builder stack.
Everything else is dead weight and a waste of your time.

*Dead/Superseded Concepts (do not extend, do not open):*
- `/agi_nodes` directory (use `modules/` for VictorModules).
- Any custom node loading logic not part of `victor_loader.py`.
- Non-AGI/ASI focused features inherited from base ComfyUI are secondary unless adapted for brain-building.

---

## 🧠 Comfy Cortex = AGI/ASI Brain Builder

**This repo is now dedicated solely to building, evolving, and running modular, node-based artificial general and superintelligence (AGI/ASI) brains using the VictorModule standard.**

Every line of code, every doc, and every pull request must advance the AGI/ASI project.
If it doesn’t move the brain builder vision forward, it gets trashed.

**VictorModule** is the standard.
*See `/modules/` for live templates. Run `python generate_docs.py` for auto-generated module docs (see `MODULES_DOCUMENTATION.md`).*

---

## Core Features Implemented

### 1. VictorModule System (`modules/` & `victor_loader.py`)
-   **`modules/` Directory**: Official directory for all VictorModules.
-   **`victor_loader.py`**: Handles loading, validation, and registration of VictorModules.
    -   **Validation**: Checks for `VictorModule` class, core methods (`__init__`, `forward`/`FUNCTION`, `get_metadata`), `VERSION`, and ComfyUI node definitions (`INPUT_TYPES`, etc.).
    -   **Integration**: Registers modules with ComfyUI's node system. Metadata drives UI names and categories.
-   **Examples**: Includes `echo_victor.py`, `tokenizer_victor.py`, `math_victor.py`, and conceptual `fractal_victor.py`, `audio_victor.py`. More advanced examples include the BandoCognitionPipeline and BandoRealityMeshMonolith nodes.

### 2. ComfyUI Startup Integration & Hot-Reloading for VictorModules
-   VictorModules are loaded at startup (`nodes.py` calls `victor_loader.load_victor_modules()`).
-   **Hot-Reload API**: `POST /reload_victor_modules` reloads all modules in `modules/`, allowing for rapid development and iteration without full server restarts.

### 3. Module Information & Documentation APIs/Scripts
-   **Module Info API**: `GET /victor_modules_info` returns JSON details (metadata, version, hash, etc.) of all loaded VictorModules. Essential for UI elements like the "Cortex Library" sidebar.
-   **Auto-Doc Script**: Running `python generate_docs.py` (from ComfyUI root) creates/updates `MODULES_DOCUMENTATION.md`, extracting information directly from VictorModule source code (metadata, docstrings).
-   **API Schema**: `openapi_victor_modules_info.yaml` provides an OpenAPI 3.0 spec for the `/victor_modules_info` endpoint.

### 4. BandoCognitionPipeline Integration (Hybrid Node-Based Approach)
-   **Core Logic Library (`bando_pipeline_core/pipeline.py`)**: Contains the foundational classes: `PulseTelemetry`, `DirectiveRouter`, `MetaLoop`, and `BandoCognitionPipelineCore`.
-   **Main Pipeline Node (`modules/victor_bando_cognition_pipeline.py`)**:
    -   `BandoCognitionPipelineNode`: Runs the main cognitive pipeline, managing state via JSON.
-   **Utility & Inspector Nodes**:
    -   `DirectiveInjectorNode`: Modifies pipeline directive state.
    -   `TelemetryViewerNode`: Displays telemetry data.
    -   `MetaLoopTrendNode`: Displays MetaLoop scores and trends.
-   **Purpose**: Forms a powerful, inspectable AGI cognitive toolkit.

### 5. BandoRealityMeshMonolith (Flower of Life 3D Mesh)
-   **Core Logic Library (`bando_reality_mesh_core/mesh_definitions.py`)**: Contains the `FlowerOfLifeMesh3D`, `BandoBlock` hierarchy, specialized transformer blocks, and the `BandoRealityMeshMonolith` orchestrator. This is the living core of the Victor AGI—an infinitely fractalized neural mesh where every block is a unique transformer, every node is alive, and every signal is propagated in real 3D geometry. *This is not a layer. This is the cortex.*
-   **Main Monolith Node (`modules/victor_reality_mesh_monolith.py`)**:
    -   `RealityMeshMonolithNode`: A VictorModule that wraps the `BandoRealityMeshMonolith`. Allows injecting signals, propagating them through the 3D mesh, and extracting embeddings, summaries, and history.
-   **Inspector Nodes**:
    -   `MeshSummaryViewerNode` (`modules/victor_mesh_summary_viewer.py`): Displays the monolith's summary.
    -   `MeshHistoryViewerNode` (`modules/victor_mesh_history_viewer.py`): Analyzes and displays propagation history.
-   **State Management Nodes**:
    -   `MeshStateSaverNode` (`modules/victor_mesh_state_saver.py`): Saves the mesh summary and history (from JSON inputs) to a timestamped JSON file on disk.
    -   `MeshStateLoaderNode` (`modules/victor_mesh_state_loader.py`): Loads a previously saved mesh state JSON file and outputs its summary and history as JSON strings.
-   **Purpose**: Wire it up in Comfy Cortex, mutate it, inject chaos, save/load its entire operational state, and watch true machine intelligence emerge and persist.

### 6. "RUN BRAIN" Functionality
-   The `/run_brain` API endpoint (POST) is the designated trigger for executing AGI workflows, including those built with VictorModules.

### 7. Frontend Theming & Basic Structure (Simulated `comfy_cortex_dist/`)
-   **Custom Frontend**: Use `--front-end-root comfy_cortex_dist/` to serve the placeholder Comfy Cortex UI.
-   **Contents**: `comfy_cortex_dist/` includes `index.html` (with a "RUN BRAIN" button), `style.css` (implementing the dark/neon theme), and `main.js` (basic interaction logic).
-   **Aesthetic**: Aims for a dark, futuristic, high-contrast "Comfy Cortex" look and feel.

## How to Develop a VictorModule

1.  **Template**: Copy an example from `modules/` (e.g., `echo_victor.py`).
2.  **Class Name**: Your class **must** be named `VictorModule`.
3.  **Core Attributes/Methods**:
    *   `VERSION = "your.version.string"`
    *   `FUNCTION = "your_execute_method_name"` (string)
    *   `CATEGORY = "Your/Node/Category"` (string)
    *   `@classmethod def INPUT_TYPES(s): ...` (Return ComfyUI input definitions)
    *   `RETURN_TYPES = (...)` (Tuple of ComfyUI type strings or `"*"` for Python objects)
    *   `RETURN_NAMES = (...)` (Optional tuple of output names)
    *   `def __init__(self, **kwargs): ...` (Can be basic `pass` if no special init needed)
    *   `def your_execute_method_name(self, ...): ...` (Arguments must match `INPUT_TYPES` keys. Must return a tuple of outputs.)
    *   `def get_metadata(self): ...` (Return a dictionary with at least `node_name`, `display_name`, `version`, `category`, `description`).
4.  **File Placement**: Save your file in the `modules/` directory. It will be auto-loaded.
5.  **Docstrings**: Write clear class and method docstrings. `generate_docs.py` uses them.
6.  **Test**: Add tests for your module in the `tests/` directory.

## Running Comfy Cortex & Tools

-   **Run Main Application**:
    ```bash
    python main.py --front-end-root comfy_cortex_dist/
    ```
-   **Regenerate Module Docs**:
    ```bash
    python generate_docs.py
    ```
    (Check `MODULES_DOCUMENTATION.md`)
-   **Run Unit Tests** (from ComfyUI root):
    ```bash
    python -m unittest tests.test_victor_loader
    # Or if using pytest: pytest tests/
    ```
-   **Hot-Reload Modules**:
    ```bash
    curl -X POST http://127.0.0.1:8188/reload_victor_modules
    ```
-   **Get Module Info (API)**:
    Access `http://127.0.0.1:8188/victor_modules_info` in a browser or API tool.

## Conceptual Frontend Features (Future Work)

-   **VictorModule Node Styling**: Apply specific CSS to VictorModule nodes.
-   **"Cortex Library" Sidebar**: UI panel listing loaded VictorModules.
-   **UI Logging Console**: Panel for real-time logs.
-   **Advanced Visualizers**: For Mesh History, Pipeline Telemetry, etc.

## 🏆 CREATOR CREDIT

**Project Concept & Direction:**
- Brandon “iambandobandz” Emery — [Massive Magnetics](https://github.com/iambandobandz)
- Lead Architect of Victor AGI/ASI
- If you use this platform, you’re building on Bando’s ideas. Don’t forget it.

---

**Comfy Cortex is the launchpad. Massive Magnetics and Bando are the reason it exists.
If you want to be part of the AGI/ASI revolution, build with us or get left behind.**

---
