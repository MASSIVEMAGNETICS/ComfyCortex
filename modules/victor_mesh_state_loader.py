# FILE: modules/victor_mesh_state_loader.py
# VERSION: v5.0.0-REALITY-MESH-GODCORE-LOADER-VM
# NAME: VictorModule (MeshStateLoaderNode Wrapper)
# AUTHOR: Brandon "iambandobandz" Emery x Victor (Fractal Architect Mode) / Jules @ Dev (VM Integration)
# PURPOSE: Load a previously saved mesh state (summary and history) from disk.
# LICENSE: Proprietary – Massive Magnetics / Ethica AI / BHeard Network

import json
import os
import logging

class VictorModule: # Standard class name for victor_loader.py
    """
    VictorModule: Loads mesh summary and history from a previously saved JSON state file.
    Outputs these as JSON strings, ready to feed back into other mesh nodes.
    """
    # ComfyUI Node Attributes
    FUNCTION = "load_mesh_state"
    CATEGORY = "Victor/AGI/Mesh/State"
    # This node provides data, so it's not an OUTPUT_NODE in the sense of having no data outputs.

    # VictorModule Standard Attributes
    VERSION = "v5.0.0-REALITY-MESH-GODCORE-LOADER-VM"

    @classmethod
    def INPUT_TYPES(cls):
        # To make file selection easier, ComfyUI has conventions for file inputs.
        # A simple STRING can be used, but a custom widget or specific file type string
        # (like those used by LoadImage) would provide a file dialog.
        # For now, a STRING input for the full path is simplest.
        # Example: `("STRING", {"default": "saved_mesh_states/mesh_snapshot_1678886400.json"})`
        # If we want a file dialog, we might need to explore custom widgets or how LoadImage does it.
        # For now, let's make it a simple string input.
        # `folder_paths.get_input_directory()` could be a base for relative paths.

        # A simple way to get a list of files for a combo box:
        input_dir = "saved_mesh_states" # Default relative to ComfyUI root
        if not os.path.isabs(input_dir):
             import folder_paths
             base_dir = folder_paths.base_path if hasattr(folder_paths, 'base_path') else os.getcwd()
             input_dir = os.path.join(base_dir, input_dir)

        if not os.path.exists(input_dir):
            os.makedirs(input_dir, exist_ok=True) # Create if it doesn't exist

        files = []
        if os.path.isdir(input_dir):
            files = [f for f in os.listdir(input_dir) if f.endswith(".json") and f.startswith("mesh_state_")]

        # If no files, provide a way for user to input path directly.
        # A combo box with an option for manual path input is not standard.
        # So, we'll use a STRING input and user must provide the path.
        # Tooltip can guide them.

        return {
            "required": {
                # Using a simple STRING input. User needs to provide the full or relative path.
                "filepath": ("STRING", {"default": "saved_mesh_states/your_mesh_file.json", "tooltip": "Full or relative path to the saved mesh state JSON file."}),
            }
            # Optional: A way to list files in a default directory via a dropdown?
            # "saved_state_file": (sorted(files) if files else ["None"], )
            # This would require the files to be present at ComfyUI startup.
            # For dynamic loading of files selected by user, STRING input is more robust.
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING") # Adding filename as an output for reference
    RETURN_NAMES = ("mesh_summary_json", "mesh_history_json", "loaded_filepath_str")

    def __init__(self):
        self.logger = logging.getLogger(f"ComfyCortex.VM.{self.get_metadata()['node_name']}")
        self.logger.info(f"Instance created.")

    def load_mesh_state(self, filepath: str):
        self.logger.info(f"Attempting to load mesh state from: '{filepath}'")

        # If filepath is relative, assume it's relative to ComfyUI root directory
        if not os.path.isabs(filepath):
            import folder_paths
            base_dir = folder_paths.base_path if hasattr(folder_paths, 'base_path') else os.getcwd()
            filepath_abs = os.path.join(base_dir, filepath)
        else:
            filepath_abs = filepath

        if not os.path.exists(filepath_abs) or not os.path.isfile(filepath_abs):
            error_msg = f"File not found or is not a file: {filepath_abs}"
            self.logger.error(error_msg)
            empty_json = json.dumps({})
            empty_list_json = json.dumps([])
            return (empty_json, empty_list_json, f"ERROR: {error_msg}")

        try:
            with open(filepath_abs, "r", encoding='utf-8') as f:
                loaded_state_data = json.load(f)

            # Extract the core components saved by MeshStateSaverNode
            mesh_summary_data = loaded_state_data.get("mesh_summary", {})
            mesh_history_data = loaded_state_data.get("mesh_history", []) # History is a list

            # Re-serialize them to JSON strings for output, ensuring consistent format
            mesh_summary_json_out = json.dumps(mesh_summary_data, indent=2, default=str)
            mesh_history_json_out = json.dumps(mesh_history_data, default=str) # History can be compact

            self.logger.info(f"Successfully loaded and parsed mesh state from {filepath_abs}")
            return (mesh_summary_json_out, mesh_history_json_out, filepath_abs)

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON from file '{filepath_abs}': {e}"
            self.logger.error(error_msg, exc_info=True)
            empty_json = json.dumps({})
            empty_list_json = json.dumps([])
            return (empty_json, empty_list_json, f"ERROR: {error_msg}")
        except IOError as e:
            error_msg = f"Failed to read file '{filepath_abs}': {e}"
            self.logger.error(error_msg, exc_info=True)
            empty_json = json.dumps({})
            empty_list_json = json.dumps([])
            return (empty_json, empty_list_json, f"ERROR: {error_msg}")
        except Exception as e:
            error_msg = f"An unexpected error occurred while loading mesh state from '{filepath_abs}': {e}"
            self.logger.error(error_msg, exc_info=True)
            empty_json = json.dumps({})
            empty_list_json = json.dumps([])
            return (empty_json, empty_list_json, f"ERROR: {error_msg}")

    # VictorModule Standard Method
    def get_metadata(self):
        return {
            "node_name": "MeshStateLoaderNode",
            "display_name": "Load Reality Mesh State (VM)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Loads a previously saved Reality Mesh state (summary and history) from a JSON file on disk. Outputs JSON strings suitable for other mesh nodes.",
            "author": "Brandon 'iambandobandz' Emery x Victor / Jules @ Dev"
        }

NODE_CLASS_MAPPINGS = {
    "MeshStateLoaderNode": VictorModule
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MeshStateLoaderNode": "Load Reality Mesh State (VM)"
}
