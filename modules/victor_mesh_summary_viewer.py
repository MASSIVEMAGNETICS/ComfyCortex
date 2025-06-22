# FILE: modules/victor_mesh_summary_viewer.py
# VERSION: v1.0.1-MESH-SUMMARY-VM
# NAME: VictorModule (MeshSummaryNode)
# AUTHOR: Jules @ Dev (for Bando)
# PURPOSE: Displays the summary JSON from the BandoRealityMeshMonolith in a readable format.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import json
import logging

class VictorModule: # Standard class name for victor_loader.py
    VERSION = "v1.0.1-MESH-SUMMARY-VM"
    FUNCTION = "display_summary"
    CATEGORY = "Victor/AGI/Mesh/Inspectors"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "summary_json": ("STRING", {"multiline": True, "default": "{}", "tooltip": "JSON string containing the mesh summary from RealityMeshMonolithNode."}),
            },
            "optional": {
                "indent_level": ("INT", {"default": 2, "min": 0, "max": 8, "step": 1, "tooltip": "Indentation level for JSON pretty printing. 0 for compact."}),
                "max_block_assignments_preview": ("INT", {"default": 5, "min": 0, "max": 50, "tooltip": "Max items for 'block_assignments' preview if too large. 0 for all."})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("formatted_summary_str",)

    def __init__(self):
        self.logger = logging.getLogger(f"ComfyCortex.VM.{self.__class__.__name__}")
        self.logger.info(f"Instance created.")

    def display_summary(self, summary_json: str, indent_level: int = 2, max_block_assignments_preview: int = 5):
        self.logger.info(f"Received summary JSON (length: {len(summary_json)})")

        try:
            summary_dict = json.loads(summary_json)
            if not isinstance(summary_dict, dict):
                raise ValueError("summary_json did not parse to a dictionary.")
        except json.JSONDecodeError as e:
            error_msg = f"Error decoding summary_json: {e}\nInput (first 200 chars): {summary_json[:200]}..."
            self.logger.error(error_msg)
            return (error_msg,)
        except ValueError as e:
            error_msg = f"Error: summary_json not a valid dictionary structure: {e}"
            self.logger.error(error_msg)
            return (error_msg,)
        except Exception as e:
            error_msg = f"Unexpected error processing summary_json: {e}"
            self.logger.error(error_msg, exc_info=True)
            return (error_msg,)

        display_dict_for_json_dump = summary_dict.copy()

        if "block_assignments" in display_dict_for_json_dump and isinstance(display_dict_for_json_dump["block_assignments"], dict):
            assignments = display_dict_for_json_dump["block_assignments"]
            if max_block_assignments_preview > 0 and len(assignments) > max_block_assignments_preview:
                display_dict_for_json_dump["block_assignments"] = {
                    f"preview_first_{max_block_assignments_preview}_items": dict(list(assignments.items())[:max_block_assignments_preview]),
                    "_total_block_assignments": len(assignments)
                }

        json_dump_str = ""
        try:
            if indent_level == 0:
                 json_dump_str = json.dumps(display_dict_for_json_dump, default=str)
            else:
                 json_dump_str = json.dumps(display_dict_for_json_dump, indent=indent_level, default=str)
        except Exception as e:
            self.logger.error(f"Error formatting summary for JSON display: {e}", exc_info=True)
            json_dump_str = f"Error during JSON formatting: {e}\nRaw data: {str(display_dict_for_json_dump)[:500]}"

        readable_output_parts = [f"--- Reality Mesh Summary ---"]
        readable_output_parts.append(f"Dimension: {summary_dict.get('dim', 'N/A')}")
        readable_output_parts.append(f"Mesh Depth Configured: {summary_dict.get('mesh_depth_configured', 'N/A')}")
        readable_output_parts.append(f"Mesh Nodes: {summary_dict.get('mesh_nodes', 'N/A')}")
        readable_output_parts.append(f"Mesh Connections: {summary_dict.get('mesh_connections', 'N/A')}")

        block_counts = summary_dict.get('block_type_counts', {})
        if block_counts:
            readable_output_parts.append("Block Type Counts:")
            for block_type, count in block_counts.items():
                readable_output_parts.append(f"  - {block_type}: {count}")
        else:
            readable_output_parts.append("Block Type Counts: N/A")

        mean_act = summary_dict.get('current_mean_activation_on_embedding', 'N/A')
        if isinstance(mean_act, float):
            readable_output_parts.append(f"Current Mean Activation (Embedding): {mean_act:.4f}")
        else:
            readable_output_parts.append(f"Current Mean Activation (Embedding): {mean_act}")

        readable_output_parts.append(f"History Length Recorded: {summary_dict.get('history_length', 'N/A')}")

        if "block_assignments" in summary_dict and isinstance(summary_dict["block_assignments"], dict):
            assignments = summary_dict["block_assignments"]
            readable_output_parts.append(f"\nBlock Assignments (Preview - first {max_block_assignments_preview if max_block_assignments_preview > 0 else 'all'} of {len(assignments)} total):")
            count = 0
            for node_id, block_name in assignments.items():
                if max_block_assignments_preview == 0 or count < max_block_assignments_preview:
                    readable_output_parts.append(f"  - Node '{node_id}': {block_name}")
                else:
                    readable_output_parts.append(f"  ... and {len(assignments) - count} more.")
                    break
                count += 1

        readable_output_parts.append(f"\n--- Full JSON (block_assignments possibly truncated in this part if preview was active) ---\n{json_dump_str}")

        final_output_str = "\n".join(readable_output_parts)
        self.logger.info("Formatted summary generated.")
        return (final_output_str,)

    def get_metadata(self):
        return {
            "node_name": "MeshSummaryViewerNode",
            "display_name": "Reality Mesh Summary Viewer (VM)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Takes a mesh summary JSON string (from BandoRealityMeshMonolith) and displays it in a more readable, pretty-printed format, with options for truncation.",
            "author": "Jules @ Dev (for Bando)"
        }

NODE_CLASS_MAPPINGS = {
    "MeshSummaryViewerNode": VictorModule
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MeshSummaryViewerNode": "Reality Mesh Summary Viewer (VM)"
}
