# Comfy Cortex - AGI Brain Interface Mod for ComfyUI

This project modifies the standard ComfyUI to transform it into "Comfy Cortex," an interface designed for visual AGI brain construction. It implements the **VictorModule** system for custom Python-based components, a dedicated "RUN BRAIN" execution pathway, hot-reloading for VictorModules, new APIs for module information, and initial frontend theming for a dark, neon aesthetic.

## Core Features Implemented

### 1. VictorModule System (`modules/` & `victor_loader.py`)
-   **`modules/` Directory**: This is the official directory for all custom AGI components, now called VictorModules.
-   **`victor_loader.py`**: This new backend script handles all loading, validation, and registration of VictorModules.
    -   **Discovery & Validation**: Scans `modules/` for `.py` files. Each file should define a class named `VictorModule`. The loader validates that this class has `__init__`, `forward`, and `get_metadata` methods. It also expects a `VERSION` class attribute (or in metadata) and ComfyUI-standard `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, and `CATEGORY` attributes/methods.
    -   **Integration**: Valid VictorModules are registered with ComfyUI's `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`. Display names and categories are derived from the module's `get_metadata()` method.
    -   **Internal Registry**: `victor_loader.py` maintains its own `loaded_modules` dictionary containing detailed information about each loaded module (path, hash, version, metadata, etc.).
-   **Example**: See `modules/echo_victor.py` for a template.

### 2. ComfyUI Startup Integration
-   `nodes.py` has been updated to call `victor_loader.load_victor_modules()` during startup, ensuring all VictorModules are loaded and available.
-   Previous custom loading logic for `agi_nodes/` has been removed.

### 3. Hot-Reloading for VictorModules
-   **API Endpoint**: A new backend API endpoint `@routes.post('/reload_victor_modules')` is available.
-   **Functionality**: Calling this endpoint triggers `victor_loader.reload_victor_modules_command()`. This command re-scans the `modules/` directory, unregisters all existing VictorModules, clears them from `sys.modules`, and then performs a fresh load and registration of all found VictorModules.
-   **Usage**: Allows developers to update VictorModule code and see changes without a full server restart. (e.g., `curl -X POST http://127.0.0.1:8188/reload_victor_modules`)

### 4. Backend API for Module Information
-   **API Endpoint**: A new backend API endpoint `@routes.get('/victor_modules_info')` is available.
-   **Functionality**: This endpoint calls `victor_loader.get_loaded_modules_info()` and returns a JSON list of all loaded VictorModules, including their filename, version, hash, display name, category, and other metadata.
-   **Purpose**: To provide data for the conceptual "Cortex Library" UI sidebar.

### 5. "RUN BRAIN" Functionality
-   **API Endpoint**: The `/run_brain` (POST) endpoint remains for triggering AGI workflows.
-   **Execution**: Workflows containing VictorModules will be executed by ComfyUI's standard engine, as VictorModules are registered like any other custom node.

### 6. Frontend Theming & Basic Structure (Simulated)
-   **Custom Frontend Root**: The system is set up to serve a custom frontend from `comfy_cortex_dist/` using the `--front-end-root comfy_cortex_dist/` argument.
-   **`comfy_cortex_dist/`**: Contains:
    -   `index.html`: Basic page structure with a "RUN BRAIN" button.
    -   `style.css`: Implements a dark theme with neon green, cyan, and magenta accents. Includes styles for UI elements and conceptual VictorModule nodes.
    -   `main.js`: Handles the "RUN BRAIN" button click and is the placeholder for Vue app init.
-   **Aesthetic**: Aims for a dark, futuristic, "Comfy Cortex" look.

## How to Use

1.  **Create VictorModules**: Develop your Python AGI components as classes named `VictorModule` in `.py` files within the `modules/` directory. Ensure they have `VERSION`, `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, `CATEGORY`, `__init__`, `forward`, and `get_metadata` (see `modules/echo_victor.py`).
2.  **Run Comfy Cortex**:
    ```bash
    python main.py --front-end-root comfy_cortex_dist/
    ```
3.  **Access UI**: Open ComfyUI in your browser. You'll see the dark theme and "RUN BRAIN" button. VictorModules should appear in the "Add Node" menu under their specified category.
4.  **"Run Brain"**: Clicking the "RUN BRAIN" button sends a (dummy) workflow to `/run_brain`.
5.  **Hot-Reload**: After modifying files in `modules/`, POST to `/reload_victor_modules` to update.
6.  **Module Info**: GET `/victor_modules_info` to retrieve data about loaded modules.

## Conceptual Frontend Features (Future Work)

-   **VictorModule Node Styling**: Apply specific CSS to VictorModule nodes in the graph (CSS is defined; JS hook in frontend needed).
-   **"Cortex Library" Sidebar**: A UI panel listing all loaded VictorModules, using data from `/victor_modules_info`.
-   **UI Logging Console**: A panel to display real-time logs from module execution (requires WebSocket integration).

This version establishes the VictorModule system as the core for custom components in Comfy Cortex.Tool output for `overwrite_file_with_block`:
