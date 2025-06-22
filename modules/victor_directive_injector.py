# FILE: modules/victor_directive_injector.py
# VERSION: v1.0.0-DIRECTIVE-INJECTOR-NODE
# NAME: VictorModule (DirectiveInjectorNode)
# AUTHOR: Jules @ Dev (for Bando)
# PURPOSE: Injects a new directive into a BandoCognitionPipeline's state.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import json
import time
import logging

# Attempt to import the core pipeline classes if they are in a shared location.
# For now, we'll assume this node might need to simulate parts of DirectiveRouter logic
# if it only receives a serialized state rather than a live pipeline object.
# If BandoCognitionPipelineCore classes are available (e.g. from a util file or copied),
# it would be cleaner to rehydrate and use the actual DirectiveRouter.
# For this implementation, we'll work with the JSON state directly.

class VictorModule:
    VERSION = "v1.0.0-DIRECTIVE-INJECTOR-NODE"
    FUNCTION = "inject_directive"
    CATEGORY = "VictorModules/Pipeline Control"

    # These are the modes the DirectiveRouter in BandoCognitionPipelineCore knows.
    # This node should ideally get this list dynamically if the core pipeline is accessible,
    # but for now, we can hardcode or make it an input if necessary.
    KNOWN_MODES = ["reflect", "defend", "repair", "expand", "dream"]


    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "pipeline_state_in_json": ("STRING", {"multiline": True, "tooltip": "JSON state from BandoCognitionPipelineNode."}),
                "directive_to_inject": ("STRING", {"multiline": False, "default": "reflect"}),
            },
            "optional": {
                "injection_context_json": ("STRING", {"multiline": True, "default": "{}"}),
                "available_modes_override_json": ("STRING", {"multiline":False, "default": json.dumps(s.KNOWN_MODES), "tooltip": "JSON list of available modes for the router."})
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("pipeline_state_out_json", "new_mode_set_str")

    def __init__(self, **kwargs):
        self.name = "DirectiveInjectorNode"

    def inject_directive(self, pipeline_state_in_json, directive_to_inject, injection_context_json="{}", available_modes_override_json=json.dumps(KNOWN_MODES)):
        current_pipeline_state = {}
        original_mode = "reflect" # Default if not found
        directive_log = []

        try:
            if pipeline_state_in_json and pipeline_state_in_json.strip():
                current_pipeline_state = json.loads(pipeline_state_in_json)
                # Extract relevant parts of the state for the directive router
                # Based on BandoCognitionPipelineCore.get_serializable_state()
                original_mode = current_pipeline_state.get("current_directive_mode", original_mode)
                directive_log = current_pipeline_state.get("directive_log", []) # Assumes directive_log is part of the state
            else:
                # If no input state, start with a default state for the directive part
                current_pipeline_state = {"current_directive_mode": original_mode, "directive_log": []}
                logging.info(f"[{self.get_metadata()['display_name']}] No input pipeline state. Initializing directive state.")

        except json.JSONDecodeError as e:
            error_msg = f"Error decoding pipeline_state_in_json: {e}"
            logging.error(error_msg)
            return (pipeline_state_in_json, original_mode) # Return original state and mode on error
        except Exception as e:
            error_msg = f"Error processing input pipeline state: {e}"
            logging.error(error_msg, exc_info=True)
            return (pipeline_state_in_json, original_mode)

        injection_context = {}
        if injection_context_json and injection_context_json.strip():
            try:
                injection_context = json.loads(injection_context_json)
            except json.JSONDecodeError as e:
                logging.warning(f"Failed to decode injection_context_json: {e}. Using empty context.")

        available_modes = self.KNOWN_MODES
        try:
            if available_modes_override_json and available_modes_override_json.strip():
                parsed_modes = json.loads(available_modes_override_json)
                if isinstance(parsed_modes, list) and all(isinstance(m, str) for m in parsed_modes):
                    available_modes = parsed_modes
                else:
                    logging.warning("available_modes_override_json was not a valid list of strings. Using default modes.")
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to decode available_modes_override_json: {e}. Using default modes.")


        # Simulate DirectiveRouter.route() logic
        new_mode_set = original_mode # Start with the original mode
        if directive_to_inject in available_modes:
            new_mode_set = directive_to_inject
        # else: the directive is not a mode change, but an action for the current mode.
        # The original DirectiveRouter logic was:
        #   if directive in self.modes: self.current_mode = directive
        #   self.active_directive = directive (always set)
        # So, new_mode_set reflects the mode *after* considering if the directive is a mode change.

        # Log the new directive
        new_log_entry = {
            "directive": directive_to_inject,
            "context": injection_context,
            "new_mode_set": new_mode_set, # Mode after this directive
            "previous_mode": original_mode, # Mode before this directive
            "timestamp": time.time()
        }
        directive_log.append(new_log_entry)

        # Update the pipeline state
        current_pipeline_state["current_directive_mode"] = new_mode_set
        current_pipeline_state["directive_log"] = directive_log[-20:] # Keep log manageable in state
        current_pipeline_state["last_injected_directive_info"] = new_log_entry


        pipeline_state_out_json = json.dumps(current_pipeline_state, indent=2, default=str)

        logging.info(f"[{self.get_metadata()['display_name']}] Injected directive: '{directive_to_inject}'. Mode changed from '{original_mode}' to '{new_mode_set}'.")

        return (pipeline_state_out_json, new_mode_set)

    def get_metadata(self):
        return {
            "node_name": "DirectiveInjectorVictorNode",
            "display_name": "Directive Injector (Victor)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Injects a new directive into a BandoCognitionPipeline's state (provided as JSON). Updates and outputs the new pipeline state JSON and the resulting cognitive mode.",
            "author": "Jules @ Dev for Bando"
        }
