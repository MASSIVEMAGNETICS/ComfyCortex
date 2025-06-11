from __future__ import annotations
from typing import Any
from comfy.comfy_types.node_typing import ComfyNodeABC, IO, InputTypeDict, InputTypeOptions

class GenericCognitiveNode(ComfyNodeABC):
    DESCRIPTION = "A base class for cognitive modules in the Comfy Cortex framework."
    CATEGORY = "CognitiveCortex/Base" # Grouping for all cognitive nodes

    @classmethod
    def INPUT_TYPES(s) -> InputTypeDict:
        return {
            "required": {
                "input_data": (IO.ANY, {}),
            },
            "optional": {
                "state_in": (IO.ANY, {}), # For potential state passing
            }
        }

    RETURN_TYPES = (IO.ANY,)
    RETURN_NAMES = ("output_data",)
    OUTPUT_TOOLTIPS = ("The primary output of the cognitive node.",)
    FUNCTION = "execute"

    # --- Optional attributes ---
    # OUTPUT_NODE = False # Default is False
    # INPUT_IS_LIST = False # Default is False
    # OUTPUT_IS_LIST = (False,) # Default is all False

    def __init__(self):
        super().__init__()
        self.state: dict[str, Any] = {} # Basic internal state

    def execute(self, input_data: Any, state_in: Any | None = None, **kwargs) -> tuple[Any, ...]:
        # Simple pass-through for the base class
        # Concrete implementations will override this.

        current_output = input_data

        # Basic state handling example
        if state_in is not None:
            if isinstance(state_in, dict):
                self.state.update(state_in)
            else:
                # Potentially log a warning or handle non-dict state input
                pass

        # Child nodes might modify self.state here

        # For this base class, we'll just return the input data and the current internal state
        # However, the defined RETURN_TYPES is just one IO.ANY.
        # So, to make it a working node, we'll just pass through input_data.
        # A more complex node might return its state as a second output if defined in RETURN_TYPES.

        # For now, let's make it a simple pass-through to fit the (IO.ANY,) return type
        return (current_output,)

# It's good practice to also have mappings for any nodes defined in this file,
# even if this base class itself isn't directly instantiated in the UI.
# However, since this is a base class not intended for direct use,
# we might skip adding it to NODE_CLASS_MAPPINGS unless we create a specific
# "GenericCognitiveNodePassthrough" for testing.

# For now, we'll keep it clean and assume child nodes will be in their own files
# or added to a central mapping elsewhere.
# If we were to make it usable, it would be:
# NODE_CLASS_MAPPINGS = {
# "GenericCognitiveNode": GenericCognitiveNode
# }
# NODE_DISPLAY_NAME_MAPPINGS = {
# "GenericCognitiveNode": "Generic Cognitive Node (Base)"
# }
