# Comfy Cortex - AGI Brain Interface Mod for ComfyUI

This project modifies the standard ComfyUI to begin transforming it into "Comfy Cortex," an interface designed for visual AGI brain construction. It introduces backend modularity for custom Python-based AGI components, a dedicated "RUN BRAIN" execution pathway, hot-reloading for AGI components, and initial frontend theming for a dark, neon aesthetic.

## Core Features Implemented

### 1. Backend Modularity for AGI Components
-   **`agi_nodes/` Directory**: A new top-level directory `agi_nodes/` has been created. Users can place their custom Python modules (`.py` files) here to define new AGI components.
-   **Discovery**: ComfyUI will automatically discover and load nodes defined in these modules.
-   **Convention**:
    -   Each `.py` file in `agi_nodes/` should contain one or more node classes.
    -   Each node class must define `INPUT_TYPES()`, `RETURN_TYPES`, `FUNCTION`, and `CATEGORY`. It's recommended to use `CATEGORY = "AGI_Components"` to group these nodes in the UI.
    -   The module must expose `NODE_CLASS_MAPPINGS` (mapping string names to class objects) and optionally `NODE_DISPLAY_NAME_MAPPINGS` for UI presentation.
    -   See `agi_nodes/basic_agi_node.py` for an example.

### 2. "RUN BRAIN" Functionality
-   **API Endpoint**: A new backend API endpoint `/run_brain` (POST) has been added.
-   **Purpose**: This endpoint is intended to be the trigger for executing an AGI "brain" (a ComfyUI workflow). It currently functions similarly to the standard `/prompt` endpoint but provides a dedicated pathway for AGI executions.
-   **Frontend Integration**: A placeholder "RUN BRAIN" button has been added to the frontend (`index.html`) which, when clicked, sends the current (dummy) workflow to this endpoint.

### 3. Hot-Reloading for AGI Components
-   **API Endpoint**: A new backend API endpoint `/reload_agi_modules` (POST) allows for hot-reloading of all modules within the `agi_nodes/` directory.
-   **Functionality**: When called, this endpoint will:
    1.  Identify all currently registered nodes that originated from `agi_nodes/`.
    2.  Remove their definitions from ComfyUI's node mappings.
    3.  Clear the Python modules from `sys.modules`.
    4.  Re-scan the `agi_nodes/` directory and load all modules found, registering any new or modified nodes.
-   **Usage**: This is primarily a developer feature to allow iteration on AGI components without restarting the full ComfyUI server. It can be triggered manually (e.g., via `curl` or a developer tool).

### 4. Frontend Theming (Dark & Neon) - Initial Phase
-   **Custom Frontend Root**: The system is set up to serve a custom frontend from a directory specified by the `--front-end-root` argument when launching ComfyUI (e.g., `--front-end-root comfy_cortex_dist/`).
-   **`comfy_cortex_dist/`**: This directory contains initial frontend files:
    -   `index.html`: Basic page structure with a "RUN BRAIN" button.
    -   `style.css`: Implements a dark theme with neon green, cyan, and magenta accents. Includes placeholder styles for UI elements, graph nodes (with specific styling for `.agi-component` nodes), and connections.
    -   `tailwind.config.js`: (Conceptual) Defines the color palette used in `style.css`.
    -   `main.js`: Placeholder for Vue app initialization, currently handles the "RUN BRAIN" button click.
-   **Aesthetic**: The theme aims for a dark, futuristic, neon look suitable for "Comfy Cortex."

## How to Use

1.  **Place AGI Components**: Create your Python AGI node modules in the `agi_nodes/` directory. Follow the conventions described above.
2.  **Run ComfyUI with Custom Frontend**:
    ```bash
    python main.py --front-end-root comfy_cortex_dist/
    ```
3.  **Access UI**: Open ComfyUI in your browser. You should see the initial dark theme and the "RUN BRAIN" button.
4.  **Add AGI Nodes**: Your components from `agi_nodes/` should appear in the "Add Node" menu, under the "AGI_Components" category (or as specified in your node).
5.  **"Run Brain"**: Clicking the "RUN BRAIN" button will (currently) send a dummy workflow to the `/run_brain` endpoint.
6.  **Hot-Reload (Developer)**: If you modify files in `agi_nodes/`, you can send a POST request to `/reload_agi_modules` to see changes without a server restart. For example:
    ```bash
    curl -X POST http://127.0.0.1:8188/reload_agi_modules
    ```

## Next Steps & Future Development

-   Fully implement the Vue.js frontend within `comfy_cortex_dist/` by adapting the official `ComfyUI_frontend` source.
-   Refine the visual wiring and representation of AGI components in the graph.
-   Develop more sophisticated AGI component examples.
-   Enhance the "RUN BRAIN" functionality with specific start/end node identification for brains.
-   Add UI controls for hot-reloading.
-   Implement true modularity for UI panels and sections.
-   Integrate dynamic loading/unloading of entire AGI "brain" configurations.

This represents the foundational work towards the Comfy Cortex vision.
