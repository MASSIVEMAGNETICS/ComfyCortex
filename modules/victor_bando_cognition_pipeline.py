# FILE: modules/victor_bando_cognition_pipeline.py
# VERSION: v1.0.1-GODCORE-FUSION-NODE-REFACTORED
# NAME: VictorModule (BandoCognitionPipelineNode)
# AUTHOR: Jules @ Dev (for Bando)
# PURPOSE: Wraps the BandoCognitionPipelineCore as a Comfy Cortex VictorModule supernode.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import json
import logging
import sys
import os
import time # Keep time for any direct use if needed, though core pipeline handles its own.

# Ensure bando_pipeline_core is discoverable.
# This assumes ComfyUI's execution environment or PYTHONPATH includes the project root.
# For robustness, especially if ComfyUI's sys.path manipulation is complex for custom nodes,
# an alternative might be needed, but this is standard for Python project structures.
try:
    from bando_pipeline_core.pipeline import BandoCognitionPipelineCore, PulseTelemetry, DirectiveRouter, MetaLoop
    # PulseTelemetry etc. might not be directly used here but good to confirm import works.
except ImportError as e:
    # Fallback for environments where sys.path might not be immediately set up by ComfyUI for sibling directories
    # This is a common pattern in some ComfyUI custom nodes.
    comfy_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # Assuming modules is one level down from root
    if comfy_root not in sys.path:
        sys.path.append(comfy_root)
    try:
        from bando_pipeline_core.pipeline import BandoCognitionPipelineCore, PulseTelemetry, DirectiveRouter, MetaLoop
    except ImportError:
        logging.error(f"CRITICAL: Could not import BandoCognitionPipelineCore from bando_pipeline_core.pipeline. Ensure bando_pipeline_core is in PYTHONPATH. Error: {e}", exc_info=True)
        # Define a dummy class so the rest of the file can parse, but it will fail at runtime.
        class BandoCognitionPipelineCore:
            def __init__(self, *args, **kwargs): raise RuntimeError("BandoCognitionPipelineCore not loaded")
            def run(self, *args, **kwargs): raise RuntimeError("BandoCognitionPipelineCore not loaded")
            def get_serializable_state(self): return {"error": "BandoCognitionPipelineCore not loaded"}
            def load_serializable_state(self, *args, **kwargs): pass


# --- VictorModule Wrapper ---

class VictorModule:
    VERSION = "v1.0.1-GODCORE-FUSION-NODE-REFACTORED" # Updated version
    FUNCTION = "execute_pipeline"
    CATEGORY = "VictorModules/Pipelines"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_data_json": ("STRING", {"multiline": True, "default": "{\"prompt\": \"Hello Bando!\"}", "tooltip": "Main input data for the pipeline (JSON string)."}),
            },
            "optional": {
                "context_json": ("STRING", {"multiline": True, "default": "{}", "tooltip": "Contextual information for the pipeline run (JSON string)."}),
                "directive_str": ("STRING", {"multiline": False, "default": "", "tooltip": "Initial directive (e.g., 'expand', 'reflect'). Empty for default."}),
                "pipeline_state_in_json": ("STRING", {"multiline": True, "default": "", "tooltip":"JSON state from a previous run to rehydrate the pipeline."}),
                # "attention_fn_module_name": ("STRING", {"default": "", "tooltip": "Name of another VictorModule to use as attention_fn (conceptual)."}),
                "initial_modes_json_list": ("STRING", {"default": json.dumps(["reflect", "defend", "repair", "expand", "dream"]), "tooltip": "JSON list of modes for the directive router."})
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("output_summary_json", "pipeline_state_out_json")

    def __init__(self, **kwargs):
        self.name = "BandoCognitionPipelineNode"
        # Each execution will get its own pipeline instance via _init_pipeline in execute_pipeline
        # This makes the node more stateless from ComfyUI's perspective between graph runs,
        # relying on pipeline_state_in_json for continuity if desired.

    def _init_pipeline(self, pipeline_state_in_json=None, attention_fn_override=None, initial_modes=None):
        # This method now correctly instantiates the imported BandoCognitionPipelineCore

        # Default attention function (can be overridden if logic is added for attention_fn_module_name)
        # For now, using the example_attention_function if it were defined in bando_pipeline_core.pipeline
        # Or, pass None to use the default_comprehension within BandoCognitionPipelineCore.
        # Let's assume BandoCognitionPipelineCore has its own default or handles None for attention_fn.

        # A simple example attention function that could be passed:
        def _internal_example_attention(input_data, context):
            input_s = str(input_data)[:100]
            return {"attention_summary": f"Attended to: {input_s}", "context_keys": list(context.keys()) if context else []}

        current_attention_fn = _internal_example_attention # Defaulting to this internal one for now

        # If attention_fn_override is provided (e.g. from a dynamic source in future)
        if attention_fn_override:
            current_attention_fn = attention_fn_override

        pipeline = BandoCognitionPipelineCore(
            attention_fn=current_attention_fn,
            initial_modes=initial_modes,
            initial_state_dict=None # Initial state dict will be loaded by load_serializable_state if provided
        )

        if pipeline_state_in_json and pipeline_state_in_json.strip():
            try:
                state_dict = json.loads(pipeline_state_in_json)
                pipeline.load_serializable_state(state_dict)
                logging.info(f"[{self.name}] Pipeline state loaded successfully.")
            except json.JSONDecodeError as e:
                logging.error(f"[{self.name}] Failed to decode pipeline_state_in_json: {e}. Initializing new pipeline.")
            except Exception as e:
                logging.error(f"[{self.name}] Error loading pipeline state: {e}. Initializing new pipeline.", exc_info=True)
        return pipeline

    def execute_pipeline(self, input_data_json, context_json="", directive_str="", pipeline_state_in_json="", initial_modes_json_list=""):
        logging.info(f"[{self.name}] EXECUTE: input_data_json (len={len(input_data_json)}), context_json (len={len(context_json)}), directive='{directive_str}', pipeline_state_in (len={len(pipeline_state_in_json)})")

        try:
            input_data = json.loads(input_data_json)
        except json.JSONDecodeError as e:
            error_msg = f"Error decoding input_data_json: {e}"
            logging.error(f"[{self.name}] {error_msg}")
            return (json.dumps({"error": error_msg, "details": "Input data must be valid JSON."}),
                    pipeline_state_in_json or json.dumps({"error": "No prior state, input data failed."}))

        context = {}
        if context_json and context_json.strip():
            try:
                context = json.loads(context_json)
            except json.JSONDecodeError as e:
                logging.warning(f"[{self.name}] Failed to decode context_json: {e}. Using empty context.")

        if directive_str and directive_str.strip():
            context["directive"] = directive_str

        initial_modes = None
        if initial_modes_json_list and initial_modes_json_list.strip():
            try:
                parsed_modes = json.loads(initial_modes_json_list)
                if isinstance(parsed_modes, list):
                    initial_modes = parsed_modes
                else:
                    logging.warning(f"[{self.name}] initial_modes_json_list was not a list. Using default modes.")
            except json.JSONDecodeError as e:
                logging.warning(f"[{self.name}] Failed to decode initial_modes_json_list: {e}. Using default modes.")

        current_pipeline = self._init_pipeline(pipeline_state_in_json, initial_modes=initial_modes)

        output_summary_json = ""
        pipeline_state_out_json = ""

        try:
            run_output = current_pipeline.run(input_data, context=context)
            # Ensure all parts of run_output are serializable before full dump
            serializable_run_output = {k: (str(v)[:1000] + '...' if len(str(v)) > 1000 else v) if not isinstance(v, (dict,list)) else v for k,v in run_output.items()}

            output_summary_json = json.dumps(serializable_run_output, indent=2, default=str)

            pipeline_state_out = current_pipeline.get_serializable_state()
            pipeline_state_out_json = json.dumps(pipeline_state_out, indent=2, default=str)
            logging.info(f"[{self.name}] Pipeline run successful. Output summary length: {len(output_summary_json)}, State out length: {len(pipeline_state_out_json)}")

        except Exception as e:
            logging.error(f"[{self.name}] Error during pipeline execution: {e}", exc_info=True)
            err_summary = json.dumps({"error": "Pipeline execution failed", "details": str(e)}, indent=2)
            err_state_dict = {"error": "Pipeline execution failed, state might be partial."}
            if current_pipeline: # Try to get state even on error
                try:
                    err_state_dict.update(current_pipeline.get_serializable_state())
                except Exception as state_err:
                    err_state_dict["state_error"] = str(state_err)
            err_state = json.dumps(err_state_dict, indent=2, default=str)
            return (err_summary, err_state)

        return (output_summary_json, pipeline_state_out_json)

    def get_metadata(self):
        return {
            "node_name": "BandoCognitionPipelineNode", # This should be globally unique for ComfyUI
            "display_name": "Bando Cognition Pipeline Core", # UI friendly name
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Core node for running the Bando AGI Cognition Pipeline. Manages focus, directives, telemetry, and meta-loop processes. Uses imported core logic from 'bando_pipeline_core'.",
            "author": "Jules @ Dev (for Bando)"
        }
