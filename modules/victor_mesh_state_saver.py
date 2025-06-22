# FILE: modules/victor_mesh_state_saver.py
# VERSION: v5.0.0-REALITY-MESH-GODCORE-SAVER-VM
# NAME: VictorModule (MeshStateSaverNode Wrapper)
# AUTHOR: Brandon "iambandobandz" Emery x Victor (Fractal Architect Mode) / Jules @ Dev (VM Integration)
# PURPOSE: Save current monolith mesh state (summary and history) to disk.
# LICENSE: Proprietary – Massive Magnetics / Ethica AI / BHeard Network

import json
import os
import time
import logging

class VictorModule: # Standard class name for victor_loader.py
    """
    VictorModule: Dumps the mesh state (summary + history from JSON inputs) to a .json file.
    """
    # ComfyUI Node Attributes
    FUNCTION = "save_mesh_state"
    CATEGORY = "Victor/AGI/Mesh/State"
    OUTPUT_NODE = True # Crucial for nodes that perform actions like saving

    # VictorModule Standard Attributes
    VERSION = "v5.0.0-REALITY-MESH-GODCORE-SAVER-VM"

    @classmethod
    def INPUT_TYPES(cls):
        # Get ComfyUI's output directory as a potential default
        # This requires importing folder_paths, which might be tricky at class definition time
        # For now, using a relative path. A better solution might involve a global config.
        default_output_dir = "saved_mesh_states"
        # try:
        #     import folder_paths
        #     default_output_dir = os.path.join(folder_paths.get_output_directory(), "saved_mesh_states")
        # except ImportError:
        #     pass # Keep default if folder_paths isn't available at this exact moment

        return {
            "required": {
                "mesh_summary_json": ("STRING", {"multiline": True, "tooltip": "JSON string of the mesh summary."}),
                "mesh_history_json": ("STRING", {"multiline": True, "tooltip": "JSON string of the mesh history."}),
            },
            "optional": {
                "output_directory": ("STRING", {"default": default_output_dir, "tooltip": "Directory to save mesh state files."}),
                "filename_tag": ("STRING", {"default": "snapshot", "tooltip": "Custom tag for the output filename."}), # Renamed from 'tag' to be more specific
            }
        }

    RETURN_TYPES = () # This node saves to disk, doesn't output ComfyUI data flow

    def __init__(self):
        self.logger = logging.getLogger(f"ComfyCortex.VM.{self.get_metadata()['node_name']}") # Use node_name from metadata
        self.logger.info(f"Instance created.")

    def save_mesh_state(self, mesh_summary_json: str, mesh_history_json: str, output_directory: str, filename_tag: str):
        self.logger.info(f"Attempting to save mesh state. Tag: '{filename_tag}', Dir: '{output_directory}'")

        # Ensure output directory exists.
        # Note: ComfyUI's folder_paths usually handles output folder creation, but this node might save outside.
        # For security, it's better if this path is relative to a known ComfyUI output/data directory.
        # For now, allowing relative/absolute as per input, but in production, this would need sandboxing.
        # Let's assume output_directory can be relative to ComfyUI root or an absolute path.
        # If relative, make it relative to ComfyUI root.
        if not os.path.isabs(output_directory):
             import folder_paths # Try to import here for base_path
             base_dir = folder_paths.base_path if hasattr(folder_paths, 'base_path') else os.getcwd()
             output_directory = os.path.join(base_dir, output_directory)

        try:
            os.makedirs(output_directory, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create output directory '{output_directory}': {e}", exc_info=True)
            # ComfyUI doesn't have a direct way to signal UI error from OUTPUT_NODE's function.
            # Raising an exception might stop the queue, which could be desired.
            # Or, just log and return. For now, log and proceed to show file path error if save fails.
            # return {} # Keep queue running

        timestamp = int(time.time())
        filename = f"mesh_state_{filename_tag}_{timestamp}.json"
        full_path = os.path.join(output_directory, filename)

        try:
            summary_data = json.loads(mesh_summary_json)
            history_data = json.loads(mesh_history_json) # History is already a list of dicts of lists

            state_to_save = {
                "saved_by_node_version": self.VERSION,
                "comfy_cortex_save_format_version": "1.0", # For future compatibility
                "timestamp_unix": timestamp,
                "timestamp_iso": time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime(timestamp)),
                "filename_tag": filename_tag,
                "mesh_summary": summary_data,
                "mesh_history": history_data, # History from monolith is already tolist()'d
            }

            with open(full_path, "w", encoding='utf-8') as f:
                json.dump(state_to_save, f, indent=2)

            self.logger.info(f"Mesh state successfully saved to {full_path}")
            # For OUTPUT_NODE, UI display can be provided via the return dict
            # Example: return {"ui": {"text": [f"Saved to: {full_path}"]}}
            # This would require the frontend to have a way to display such text.
            # For now, just returning empty dict as per original template.
            # A text preview could be useful.
            return {"ui": {"saved_filepath": [full_path]}} # Provide filepath to UI

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse input JSON for saving to '{full_path}': {e}", exc_info=True)
            # raise RuntimeError(f"JSON parsing error: {e}") # Option to halt queue
            return {"ui": {"error": [f"JSON parsing error: {e}"]}}
        except IOError as e:
            self.logger.error(f"Failed to write mesh state to '{full_path}': {e}", exc_info=True)
            # raise RuntimeError(f"File I/O error: {e}")
            return {"ui": {"error": [f"File I/O error: {e}"]}}
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while saving mesh state to '{full_path}': {e}", exc_info=True)
            # raise RuntimeError(f"Unexpected error: {e}")
            return {"ui": {"error": [f"Unexpected error: {e}"]}}

        return {} # Should not be reached if using UI return above

    # VictorModule Standard Method
    def get_metadata(self):
        return {
            "node_name": "MeshStateSaverNode",
            "display_name": "Save Reality Mesh State (VM)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Saves the current Reality Mesh state (summary and history JSONs) to a timestamped JSON file on disk for persistence and later reloading.",
            "author": "Brandon 'iambandobandz' Emery x Victor / Jules @ Dev"
        }

NODE_CLASS_MAPPINGS = {
    "MeshStateSaverNode": VictorModule
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MeshStateSaverNode": "Save Reality Mesh State (VM)"
}
