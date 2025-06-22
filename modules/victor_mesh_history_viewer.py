# FILE: modules/victor_mesh_history_viewer.py
# VERSION: v1.0.0-MESH-HISTORY-VM
# NAME: VictorModule (MeshHistoryViewerNode)
# AUTHOR: Jules @ Dev (for Bando)
# PURPOSE: Displays or analyzes the history JSON from the BandoRealityMeshMonolith.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import json
import logging
import numpy as np # For potential calculations on history data

class VictorModule: # Standard class name for victor_loader.py
    VERSION = "v1.0.0-MESH-HISTORY-VM"
    FUNCTION = "display_history"
    CATEGORY = "Victor/AGI/Mesh/Inspectors"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mesh_history_json": ("STRING", {"multiline": True, "default": "[]", "tooltip": "JSON string containing the mesh history from RealityMeshMonolithNode."}),
            },
            "optional": {
                "max_steps_to_analyze": ("INT", {"default": 5, "min": 1, "max": 100, "tooltip": "Max number of history steps to analyze/display from the end of the log."}),
                "nodes_to_sample_per_step": ("INT", {"default": 3, "min": 0, "max": 20, "tooltip": "Max number of nodes to sample per step for detailed view. 0 for no node sampling."}),
                "analysis_mode": (["summary_stats", "full_step_sample", "activation_trajectory"], {"default": "summary_stats"}),
                "trajectory_node_id": ("STRING", {"default": "", "tooltip": "Specific node ID to track activation trajectory (for 'activation_trajectory' mode)."})
            }
        }

    RETURN_TYPES = ("STRING",) # Primarily a text-based analysis for now
    RETURN_NAMES = ("history_analysis_str",)

    def __init__(self):
        self.logger = logging.getLogger(f"ComfyCortex.VM.{self.__class__.__name__}")
        self.logger.info(f"Instance created.")

    def display_history(self, mesh_history_json: str, max_steps_to_analyze: int = 5,
                        nodes_to_sample_per_step: int = 3, analysis_mode: str = "summary_stats",
                        trajectory_node_id: str = ""):
        self.logger.info(f"Received mesh_history_json (length: {len(mesh_history_json)})")

        try:
            # mesh_history is a list of dicts, where each dict is {node_id: state_list}
            history_list_of_steps = json.loads(mesh_history_json)
            if not isinstance(history_list_of_steps, list):
                raise ValueError("mesh_history_json did not parse to a list.")
        except json.JSONDecodeError as e:
            error_msg = f"Error decoding mesh_history_json: {e}\nInput (first 200 chars): {mesh_history_json[:200]}..."
            self.logger.error(error_msg)
            return (error_msg,)
        except ValueError as e:
            error_msg = f"Error: mesh_history_json not a valid list structure: {e}"
            self.logger.error(error_msg)
            return (error_msg,)
        except Exception as e:
            error_msg = f"Unexpected error processing mesh_history_json: {e}"
            self.logger.error(error_msg, exc_info=True)
            return (error_msg,)

        if not history_list_of_steps:
            return ("Mesh history is empty.",)

        total_steps_in_history = len(history_list_of_steps)
        output_parts = [f"--- Mesh History Analysis (Mode: {analysis_mode}) ---"]
        output_parts.append(f"Total Steps in History: {total_steps_in_history}")

        # Analyze the last N steps
        steps_to_process = history_list_of_steps[-max_steps_to_analyze:]

        if analysis_mode == "summary_stats":
            output_parts.append(f"\nSummary Statistics for the last {len(steps_to_process)} steps (up to {max_steps_to_analyze} requested):")
            for i, step_data in enumerate(steps_to_process):
                step_index_from_end = len(steps_to_process) - 1 - i
                actual_step_number = total_steps_in_history - step_index_from_end

                if not isinstance(step_data, dict):
                    output_parts.append(f"  Step {actual_step_number}: Invalid data format (not a dict).")
                    continue

                num_nodes_in_step = len(step_data)
                activations = []
                for node_state_list in step_data.values():
                    if isinstance(node_state_list, list):
                        activations.extend(node_state_list)

                mean_activation = np.mean(activations) if activations else float('nan')
                min_activation = np.min(activations) if activations else float('nan')
                max_activation = np.max(activations) if activations else float('nan')
                std_dev_activation = np.std(activations) if activations else float('nan')

                output_parts.append(
                    f"  Step {actual_step_number} (Nodes: {num_nodes_in_step}): "
                    f"Mean Act: {mean_activation:.4f}, Min: {min_activation:.4f}, Max: {max_activation:.4f}, StdDev: {std_dev_activation:.4f}"
                )

        elif analysis_mode == "full_step_sample":
            output_parts.append(f"\nSampled Node States for the last {len(steps_to_process)} steps:")
            for i, step_data in enumerate(steps_to_process):
                step_index_from_end = len(steps_to_process) - 1 - i
                actual_step_number = total_steps_in_history - step_index_from_end
                output_parts.append(f"  --- Step {actual_step_number} ---")
                if not isinstance(step_data, dict) or not step_data:
                    output_parts.append("    No node data or invalid format for this step.")
                    continue

                node_ids_sample = list(step_data.keys())
                if nodes_to_sample_per_step > 0 and len(node_ids_sample) > nodes_to_sample_per_step:
                    node_ids_sample = random.sample(node_ids_sample, nodes_to_sample_per_step)

                for node_id in node_ids_sample:
                    state_list = step_data.get(node_id, [])
                    state_summary = str(state_list)[:50] + "..." if len(str(state_list)) > 50 else str(state_list)
                    mean_node_state = np.mean(state_list) if isinstance(state_list, list) and state_list else 'N/A'
                    output_parts.append(f"    Node '{node_id}': Mean State = {mean_node_state:.4f} (Sample: {state_summary})")


        elif analysis_mode == "activation_trajectory":
            if not trajectory_node_id or not trajectory_node_id.strip():
                output_parts.append("Error: 'trajectory_node_id' must be provided for 'activation_trajectory' mode.")
            else:
                output_parts.append(f"\nActivation Trajectory for Node ID '{trajectory_node_id}':")
                trajectory_found = False
                for i, step_data in enumerate(history_list_of_steps): # Iterate full history for trajectory
                    actual_step_number = i + 1 # History is 0-indexed list, steps are 1-indexed
                    if isinstance(step_data, dict) and trajectory_node_id in step_data:
                        node_state_list = step_data[trajectory_node_id]
                        mean_node_state = np.mean(node_state_list) if isinstance(node_state_list, list) and node_state_list else float('nan')
                        output_parts.append(f"  Step {actual_step_number}: Mean Activation = {mean_node_state:.4f}")
                        trajectory_found = True
                if not trajectory_found:
                    output_parts.append(f"  Node ID '{trajectory_node_id}' not found in history or no valid state data.")

        final_output_str = "\n".join(output_parts)
        self.logger.info(f"History analysis generated. Mode: {analysis_mode}, Length: {len(final_output_str)}")
        return (final_output_str,)

    def get_metadata(self):
        return {
            "node_name": "MeshHistoryViewerNode",
            "display_name": "Reality Mesh History Viewer (VM)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Analyzes and displays mesh history JSON from BandoRealityMeshMonolith. Provides summary stats, step samples, or activation trajectories for specific nodes.",
            "author": "Jules @ Dev (for Bando)"
        }

NODE_CLASS_MAPPINGS = {
    "MeshHistoryViewerNode": VictorModule
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MeshHistoryViewerNode": "Reality Mesh History Viewer (VM)"
}
