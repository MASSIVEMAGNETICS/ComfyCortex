from __future__ import annotations
from typing import Any, Tuple
import json # For potential complex route_map parsing if we extend it

from .cognitive_nodes import GenericCognitiveNode
# Assuming cognitive_nodes.py is in the same directory (comfy_extras)
# If GenericCognitiveNode was in a sub-package of comfy_extras, adjust path.
# Or, if it's meant to be globally accessible, it might be from a top-level import if added to ComfyUI's path.
# For now, direct relative import is fine if they are sibling modules in comfy_extras.

from comfy.comfy_types.node_typing import IO, InputTypeDict, InputTypeOptions

class SimpleTextMemoryNode(GenericCognitiveNode):
    DESCRIPTION = "Stores and retrieves text strings. Each instance can manage multiple named memories."
    CATEGORY = "CognitiveCortex/Memory"

    # Static member to hold all memories across all instances of this node type,
    # if we want shared memory. For instance-specific memory, use self.memories.
    # For this example, let's use instance-specific memory initialized in __init__.
    # class_memories: dict[str, str] = {}

    def __init__(self):
        super().__init__()
        self.instance_memories: dict[str, str] = {} # Instance-specific memory

    @classmethod
    def INPUT_TYPES(s) -> InputTypeDict:
        return {
            "required": {
                "memory_id": (IO.STRING, {"default": "default", "tooltip": "Identifier for this specific memory slot."}),
                "store_value": (IO.STRING, {"multiline": True, "default": "", "tooltip": "Value to store if write_trigger is active."}),
                # Using boolean for triggers; could also be impulse-based if ComfyUI supports it
                "write_trigger": ("BOOLEAN", {"default": False, "tooltip": "Set to True to store the value."}),
                "read_trigger": ("BOOLEAN", {"default": True, "tooltip": "Set to True to output the stored value."}),
            },
            "optional": {
                "clear_trigger": ("BOOLEAN", {"default": False, "tooltip": "Set to True to clear this memory slot."}),
            }
        }

    RETURN_TYPES = (IO.STRING,)
    RETURN_NAMES = ("retrieved_value",)
    OUTPUT_TOOLTIPS = ("The value retrieved from the specified memory_id.",)
    FUNCTION = "access_memory"

    def access_memory(self, memory_id: str, store_value: str, write_trigger: bool, read_trigger: bool, clear_trigger: bool = False) -> Tuple[str]:
        output_value = ""

        if clear_trigger:
            if memory_id in self.instance_memories:
                del self.instance_memories[memory_id]
                # print(f"[SimpleTextMemoryNode] Cleared memory for ID: {memory_id}") # For debugging
            return ("",) # Return empty string after clearing

        if write_trigger:
            self.instance_memories[memory_id] = store_value
            # print(f"[SimpleTextMemoryNode] Stored value for ID '{memory_id}': {store_value[:50]}...") # For debugging
            # Typically, after writing, you might want to output the written value or just acknowledge
            output_value = store_value

        if read_trigger:
            output_value = self.instance_memories.get(memory_id, "")
            # print(f"[SimpleTextMemoryNode] Read value for ID '{memory_id}': {output_value[:50]}...") # For debugging

        # If only write was triggered, and not read, what should be output?
        # Current logic: if write is true, output_value becomes store_value. If read is also true, it gets overwritten by memory content.
        # If neither, it's empty. This seems reasonable.
        # If both write and read are true, it writes then reads (which would return the value just written).

        return (output_value,)

    # To make IS_CHANGED work with instance memory, it's tricky because IS_CHANGED is a classmethod.
    # It would typically be used for inputs that are file paths, etc.
    # For dynamic internal state, the node usually just runs.
    # If we wanted to show changes for specific memory_id, it would require more complex handling.


class TextDirectiveRouterNode(GenericCognitiveNode):
    DESCRIPTION = "Routes input_data to one of several outputs based on a text directive and a route map."
    CATEGORY = "CognitiveCortex/Logic"

    # Maximum number of dynamic outputs this node can have.
    # This helps in defining RETURN_TYPES and RETURN_NAMES somewhat statically,
    # though ComfyUI might have specific ways to handle truly dynamic outputs if needed.
    # For now, let's assume a fixed, reasonable number of potential outputs.
    MAX_OUTPUTS = 5

    @classmethod
    def INPUT_TYPES(s) -> InputTypeDict:
        return {
            "required": {
                "directive": (IO.STRING, {"default": "", "tooltip": "The directive string to match."}),
                "input_data": (IO.ANY, {"tooltip": "Data to be routed."}),
                "route_map": (IO.STRING, {
                    "multiline": True,
                    "default": "default_route:0\nroute_A:1\nroute_B:2",
                    "tooltip": "Mapping of directive strings to output indexes (0-based).\nExample: 'process_image:0\nprocess_text:1\nfallback:2'"
                }),
            },
            "optional": {
                "default_data": (IO.ANY, {"tooltip": "Data to output on non-matched routes if input_data is not passed through."}),
                "passthrough_unmatched": ("BOOLEAN", {"default": True, "tooltip": "If True, unmatched routes output input_data. If False, they output default_data or None."})
            }
        }

    @classmethod
    def _get_return_types_and_names(cls, max_outputs=MAX_OUTPUTS):
        return_types = tuple([IO.ANY] * max_outputs)
        return_names = tuple([f"output_{i}" for i in range(max_outputs)])
        output_tooltips = tuple([f"Output port {i}." for i in range(max_outputs)])
        return return_types, return_names, output_tooltips

    RETURN_TYPES, RETURN_NAMES, OUTPUT_TOOLTIPS = _get_return_types_and_names.__func__(MAX_OUTPUTS) # type: ignore
    # OUTPUT_IS_LIST = tuple([False] * MAX_OUTPUTS) # Each output is a single item

    FUNCTION = "route_by_directive"

    def parse_route_map(self, route_map_str: str) -> dict[str, int]:
        parsed_map = {}
        for line in route_map_str.strip().split('\n'): # Using escaped newline from default
            line = line.strip()
            if not line or ':' not in line:
                continue
            directive_key, index_str = line.split(':', 1)
            try:
                index = int(index_str.strip())
                if 0 <= index < self.MAX_OUTPUTS:
                    parsed_map[directive_key.strip()] = index
                else:
                    print(f"[TextDirectiveRouterNode] Warning: Index {index} for directive '{directive_key}' is out of range (0-{self.MAX_OUTPUTS-1}). Skipping.")
            except ValueError:
                print(f"[TextDirectiveRouterNode] Warning: Could not parse index '{index_str}' for directive '{directive_key}'. Skipping.")
        return parsed_map

    def route_by_directive(self, directive: str, input_data: Any, route_map: str, default_data: Any = None, passthrough_unmatched: bool = True) -> Tuple[Any, ...]:
        parsed_route_map = self.parse_route_map(route_map)

        outputs = [None] * self.MAX_OUTPUTS

        # Determine what to output on unmatched routes
        unmatched_output_value = input_data if passthrough_unmatched else default_data

        for i in range(self.MAX_OUTPUTS):
            outputs[i] = unmatched_output_value

        routed = False
        if directive in parsed_route_map:
            target_index = parsed_route_map[directive]
            # First, set all to unmatched_output_value (or default_data if passthrough is false)
            for i in range(self.MAX_OUTPUTS):
                outputs[i] = input_data if passthrough_unmatched else default_data
            # Then, set the target index to input_data
            outputs[target_index] = input_data
            routed = True
            # print(f"[TextDirectiveRouterNode] Directive '{directive}' routed data to output_{target_index}.") # For debugging
        else:
            # Fallback or default route handling
            if "default_route" in parsed_route_map:
                target_index = parsed_route_map["default_route"]
                for i in range(self.MAX_OUTPUTS): # Ensure others are default/passthrough
                    outputs[i] = input_data if passthrough_unmatched else default_data
                outputs[target_index] = input_data # Route to default_route
                # print(f"[TextDirectiveRouterNode] Directive '{directive}' fell back to 'default_route' at output_{target_index}.") # For debugging
            elif not passthrough_unmatched:
                 for i in range(self.MAX_OUTPUTS):
                    outputs[i] = default_data # All outputs get default_data if no route and not passthrough
                # print(f"[TextDirectiveRouterNode] Directive '{directive}' not matched. No default_route. Outputting default_data to all (passthrough_unmatched=False).")
            # else: passthrough_unmatched is True, all outputs already have input_data

        return tuple(outputs)


NODE_CLASS_MAPPINGS = {
    "SimpleTextMemoryNode": SimpleTextMemoryNode,
    "TextDirectiveRouterNode": TextDirectiveRouterNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleTextMemoryNode": "Simple Text Memory (Cortex)",
    "TextDirectiveRouterNode": "Text Directive Router (Cortex)",
}
