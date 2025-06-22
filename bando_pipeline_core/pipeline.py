# FILE: bando_pipeline_core/pipeline.py
# VERSION: v1.0.0-GODCORE-FUSION-LIB
# NAME: BandoCognitionPipeline Core Library
# AUTHOR: Brandon "iambandobandz" Emery x Victor (Fractal Architect Mode)
# PURPOSE: Core classes for the BandoCognitionPipeline framework.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import uuid
import time
import copy
import json # Added for potential use within classes if they handle serialization directly
import logging # Added for consistency

# Setup a logger for this library module if desired, or rely on calling module's logger
pipeline_logger = logging.getLogger(__name__)
if not pipeline_logger.handlers: # Avoid adding multiple handlers during reloads
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    pipeline_logger.addHandler(handler)
    pipeline_logger.setLevel(logging.INFO) # Or whatever default level is appropriate
    pipeline_logger.propagate = False # Prevent double logging if root logger is also configured


class PulseTelemetry:
    """
    Tracks, logs, and routes cognition pulses, signals, feedback, errors, and meta-traces.
    """
    def __init__(self):
        self.pulse_log = []
        self.last_signal = None
        self.telemetry_map = {}
        pipeline_logger.debug("PulseTelemetry initialized.")

    def pulse(self, signal_type, data=None, meta=None):
        pulse_data = {
            "pulse_id": str(uuid.uuid4()),
            "signal_type": signal_type,
            "data": data, # Keep original data for internal log
            "meta": meta or {},
            "timestamp": time.time()
        }
        self.pulse_log.append(pulse_data)
        self.last_signal = pulse_data
        if signal_type not in self.telemetry_map:
            self.telemetry_map[signal_type] = []
        self.telemetry_map[signal_type].append(pulse_data)
        pipeline_logger.debug(f"Pulse: {signal_type}, Data: {str(data)[:50]}...")
        return pulse_data

    def get_last(self, n=5, signal_type=None):
        if not signal_type:
            return self.pulse_log[-n:]
        return self.telemetry_map.get(signal_type, [])[-n:]

    def summary(self):
        # For summary, ensure data is serializable or summarized
        last_signal_summary = None
        if self.last_signal:
            last_signal_summary = dict(self.last_signal) # Create a copy
            last_signal_summary['data'] = str(last_signal_summary['data'])[:200] + ('...' if len(str(last_signal_summary['data'])) > 200 else '')
            last_signal_summary['meta'] = {k: (str(v)[:200] + ('...' if len(str(v)) > 200 else '')) for k,v in last_signal_summary.get('meta',{}).items()}

        return {
            "total_pulses": len(self.pulse_log),
            "signals": list(self.telemetry_map.keys()),
            "last_signal_summary": last_signal_summary,
        }

    def get_serializable_pulse_log_summary(self, n=20):
        """ Returns a serializable summary of the last n pulses. """
        return [
            dict(p,
                 data=str(p['data'])[:200] + ('...' if len(str(p['data'])) > 200 else ''),
                 meta={k:(str(v)[:200] + ('...' if len(str(v)) > 200 else '')) for k,v in p.get('meta',{}).items()}
            ) for p in self.get_last(n=n)
        ]


class DirectiveRouter:
    """
    Routes directives, goals, cognitive modes, and manages directive-driven switching.
    """
    def __init__(self, modes=None):
        self.modes = modes or ["reflect", "defend", "repair", "expand", "dream"]
        self.current_mode = self.modes[0]
        self.directive_log = [] # Stores dicts: {"directive": ..., "context": ..., "new_mode_set": ..., "timestamp": ...}
        self.active_directive = None # The most recent directive text received
        pipeline_logger.debug(f"DirectiveRouter initialized. Modes: {self.modes}, Current: {self.current_mode}")

    def route(self, directive, context=None):
        original_mode = self.current_mode
        mode_to_set = self.current_mode # Default to current mode if directive isn't a mode change

        if directive in self.modes:
            mode_to_set = directive # Directive is a direct mode change

        self.current_mode = mode_to_set
        self.active_directive = directive # Store the raw directive text

        log_entry = {
            "directive": directive,
            "context": context,
            "new_mode_set": self.current_mode,
            "previous_mode": original_mode,
            "timestamp": time.time()
        }
        self.directive_log.append(log_entry)
        pipeline_logger.info(f"Directive '{directive}' routed. Mode changed from '{original_mode}' to '{self.current_mode}'. Context: {str(context)[:100]}")
        return self.current_mode

    def get_last(self, n=5):
        return self.directive_log[-n:]

    def summary(self):
        return {
            "current_mode": self.current_mode,
            "last_directive_processed_info": self.directive_log[-1] if self.directive_log else None,
            "available_modes": self.modes,
            "log_size": len(self.directive_log)
        }

class MetaLoop:
    """
    Tracks cognition trends, feedback, self-distillation, evolution score.
    """
    def __init__(self):
        self.trend_log = [] # Stores tuples: (timestamp, trend_data_dict)
        self.evaluation_scores = [] # Stores dicts: {"score": ..., "meta": ..., "timestamp": ...}
        self.distillation_states = [] # Stores deep copies of states for self-distillation
        pipeline_logger.debug("MetaLoop initialized.")

    def log_trend(self, trend_data): # trend_data should be a dictionary
        entry = (time.time(), trend_data)
        self.trend_log.append(entry)
        pipeline_logger.debug(f"Trend logged: {str(trend_data)[:100]}...")

    def evaluate(self, score, meta=None):
        entry = {
            "score": score,
            "meta": meta or {},
            "timestamp": time.time()
        }
        self.evaluation_scores.append(entry)
        pipeline_logger.debug(f"Evaluation logged: Score {score}, Meta: {str(meta)[:100]}...")


    def distill(self, state):
        copied_state = copy.deepcopy(state)
        self.distillation_states.append(copied_state)
        pipeline_logger.debug(f"State distilled. Total states: {len(self.distillation_states)}")


    def summary(self):
        last_score_info = None
        if self.evaluation_scores:
            last_score_info = dict(self.evaluation_scores[-1]) # copy
            last_score_info['meta'] = {k:(str(v)[:200] + ('...' if len(str(v)) > 200 else '')) for k,v in last_score_info.get('meta',{}).items()}

        return {
            "trend_count": len(self.trend_log),
            "eval_count": len(self.evaluation_scores),
            "last_score_info": last_score_info,
            "distillation_steps": len(self.distillation_states)
        }

    def get_serializable_scores_summary(self, n=20):
        """ Returns a serializable summary of the last n scores. """
        return [
            dict(s, meta={k:(str(v)[:200] + ('...' if len(str(v)) > 200 else '')) for k,v in s.get('meta',{}).items()})
            for s in self.evaluation_scores[-n:]
        ]

    def get_serializable_trends_summary(self, n=20):
        """ Returns a serializable summary of the last n trends. """
        return [
            {'timestamp': ts, 'trend_data': {k:(str(v)[:200] + ('...' if len(str(v)) > 200 else '')) for k,v in trend_data.items()}}
            for ts, trend_data in self.trend_log[-n:]
        ]


class BandoCognitionPipelineCore:
    """
    Fused meta-pipeline for AGI cognition. (Internal Core Logic)
    """
    def __init__(self, focus_stack=None, attention_fn=None, initial_modes=None, initial_state_dict=None):
        pipeline_logger.info(f"BandoCognitionPipelineCore initializing...")
        self.pulse_telemetry = PulseTelemetry()
        self.directive_router = DirectiveRouter(modes=initial_modes)
        self.meta_loop = MetaLoop()

        self.focus_stack = [] # List of (focus_item_summary, timestamp)
        self.current_focus = None # current focus_item_summary

        if focus_stack: # focus_stack should be list of (item_summary, timestamp)
            self.focus_stack = focus_stack
            if self.focus_stack:
                 self.current_focus = self.focus_stack[-1][0]

        self.attention_fn = attention_fn # Pluggable function

        if initial_state_dict:
            self.load_serializable_state(initial_state_dict)

        pipeline_logger.info(f"BandoCognitionPipelineCore initialized. Mode: {self.directive_router.current_mode}")


    def _summarize_data_for_log_or_state(self, data, length=200):
        """Helper to create a string summary of data."""
        if isinstance(data, (dict, list)):
            try:
                s_data = json.dumps(data)
            except TypeError:
                s_data = str(data)
        else:
            s_data = str(data)

        if len(s_data) > length:
            return s_data[:length] + "..."
        return s_data

    def set_focus(self, focus_item):
        focus_summary = self._summarize_data_for_log_or_state(focus_item)
        timestamp = time.time()
        self.focus_stack.append((focus_summary, timestamp))
        self.current_focus = focus_summary
        self.pulse_telemetry.pulse("focus_set", data={"focus_summary": focus_summary}, meta={"stack_depth": len(self.focus_stack)})

    def shift_focus(self, focus_item): # Alias for set_focus, as per original
        self.set_focus(focus_item)
        # Original also had a "focus_shift" pulse, could be added if semantics differ from "focus_set"

    def get_focus(self): # Returns the summary
        return self.current_focus

    def route_directive(self, directive, context=None): # context should be a dict
        context_summary = self._summarize_data_for_log_or_state(context)
        mode = self.directive_router.route(directive, context_summary) # Pass summary to router log
        self.pulse_telemetry.pulse("directive_routed",
                                   data={"directive": directive, "context_summary": context_summary},
                                   meta={"mode_set": mode})
        return mode

    def run(self, input_data, context=None): # context should be a dict
        if context is None:
            context = {}

        input_data_summary = self._summarize_data_for_log_or_state(input_data)
        context_summary = self._summarize_data_for_log_or_state(context)

        self.set_focus(input_data) # Focus is set to the input_data itself (summarized)

        directive = context.get("directive") # Directive comes from the context dict
        if directive:
            mode = self.route_directive(directive, context) # context is passed for logging by router
        else:
            mode = self.directive_router.current_mode

        self.pulse_telemetry.pulse("input_received",
                                   data={"input_summary": input_data_summary},
                                   meta={"mode": mode, "context_summary": context_summary})

        # Attention function receives original input_data and context
        comprehension_output = self.attention_fn(input_data, context) if self.attention_fn else self.default_comprehension(input_data, context)
        comprehension_summary = self._summarize_data_for_log_or_state(comprehension_output)
        self.pulse_telemetry.pulse("comprehend_result", data={"comprehension_summary": comprehension_summary}, meta={"mode":mode})

        self.meta_loop.log_trend({"input_summary": input_data_summary, "comprehension_summary": comprehension_summary, "mode": mode})

        # Score could be more meaningful. For now, length of comprehension summary.
        current_score = len(comprehension_summary)
        self.meta_loop.evaluate(score=current_score, meta={"input_summary": input_data_summary, "mode":mode})

        current_state_for_distill = {
            "input_summary": input_data_summary,
            "focus_summary": self.current_focus,
            "mode": mode,
            "comprehension_summary": comprehension_summary,
            "score": current_score,
            "timestamp": time.time()
        }
        self.meta_loop.distill(state=current_state_for_distill)

        self.pulse_telemetry.pulse("run_complete", data={"output_summary": comprehension_summary}, meta={"mode": mode})

        return { # This is the direct output of a single run
            "final_focus_summary": self.current_focus,
            "final_mode": mode,
            "comprehension_output": comprehension_output, # Potentially large, non-serializable if not careful
            "last_trend_logged_summary": self.meta_loop.trend_log[-1][1] if self.meta_loop.trend_log else None, # [1] is the trend_data dict
        }

    def default_comprehension(self, input_data, context=None): # context is dict
        input_summary = self._summarize_data_for_log_or_state(input_data)
        return {"summary": f"Default comprehension of: {input_summary}", "context_keys_received": list(context.keys()) if context else []}

    def get_serializable_state(self):
        """ Returns a dictionary that can be JSON serialized to save pipeline state. """
        pipeline_logger.debug("Serializing pipeline state...")
        state = {
            "focus_stack": self.focus_stack[-50:], # Limit history for serialization
            "current_focus_summary": self.current_focus,
            "directive_router_state": {
                "current_mode": self.directive_router.current_mode,
                "directive_log": self.directive_router.get_last(n=20) # Log is already list of dicts
            },
            "pulse_telemetry_state": {
                "pulse_log_summary": self.pulse_telemetry.get_serializable_pulse_log_summary(n=20),
                "signals": self.pulse_telemetry.telemetry_map.keys(), # just keys for summary
                "last_signal_summary": self.pulse_telemetry.summary()['last_signal_summary']
            },
            "meta_loop_state": {
                "trend_log_summary": self.meta_loop.get_serializable_trends_summary(n=20),
                "evaluation_scores_summary": self.meta_loop.get_serializable_scores_summary(n=20),
                "distillation_steps_count": len(self.meta_loop.distillation_states),
            },
            "timestamp": time.time()
        }
        return state

    def load_serializable_state(self, state_dict: dict):
        """ Loads pipeline state from a previously serialized dictionary. Simplified. """
        pipeline_logger.info("Loading pipeline state from dictionary...")

        self.focus_stack = state_dict.get("focus_stack", [])
        self.current_focus = state_dict.get("current_focus_summary", None)

        dr_state = state_dict.get("directive_router_state", {})
        self.directive_router.current_mode = dr_state.get("current_mode", self.directive_router.modes[0])
        self.directive_router.directive_log = dr_state.get("directive_log", []) # Overwrites log

        # PulseTelemetry and MetaLoop logs are harder to fully rehydrate meaningfully from summaries alone.
        # This simplified load primarily restores current mode and focus.
        # For a true "resume", these components would need their own robust serialize/deserialize.
        # For now, we are mostly restoring the config and some recent history.

        # Example: re-init parts of telemetry based on summary (very basic)
        pt_state = state_dict.get("pulse_telemetry_state", {})
        # self.pulse_telemetry.pulse_log = pt_state.get("pulse_log_summary", []) # This would replace with summaries
        # self.pulse_telemetry.last_signal = pt_state.get("last_signal_summary")

        pipeline_logger.info(f"Pipeline state loaded. Mode: {self.directive_router.current_mode}, Focus: {self.current_focus}")

# Example of a pluggable attention function
def example_attention_function(input_data, context):
    # This function would contain actual AGI logic for comprehension
    # It could call other VictorModules, LLMs, etc.
    input_str = str(input_data)
    directive = context.get("directive", "None")
    return {
        "processed_length": len(input_str),
        "first_10_chars": input_str[:10],
        "directive_in_context": directive,
        "custom_message": "Attention function processed this."
    }
