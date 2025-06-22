# FILE: modules/victor_telemetry_viewer.py
# VERSION: v1.0.0-TELEMETRY-VIEWER-NODE
# NAME: VictorModule (TelemetryViewerNode)
# AUTHOR: Jules @ Dev (for Bando)
# PURPOSE: Extracts and displays telemetry from a BandoCognitionPipeline's state.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import json
import time
import logging

class VictorModule:
    VERSION = "v1.0.0-TELEMETRY-VIEWER-NODE"
    FUNCTION = "view_telemetry"
    CATEGORY = "VictorModules/Pipeline Inspectors"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "pipeline_state_in_json": ("STRING", {"multiline": True, "tooltip": "JSON state from BandoCognitionPipelineNode or compatible."}),
            },
            "optional": {
                "signal_type_filter": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional: Filter telemetry by this signal type."}),
                "last_n_entries": ("INT", {"default": 5, "min": 1, "max": 100, "tooltip": "Number of recent entries to display per signal type or overall."}),
                "output_format": (["summary", "full_log_sample", "signal_specific_log"], {"default": "summary"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("telemetry_output_str",)

    def __init__(self, **kwargs):
        self.name = "TelemetryViewerNode"

    def format_pulse(self, pulse):
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pulse.get('timestamp', 0)))
        data_summary = str(pulse.get('data', {}))[:100] # Summarize data
        meta_summary = str(pulse.get('meta', {}))[:100] # Summarize meta
        return (f"  - ID: {pulse.get('pulse_id', 'N/A')[:8]}...\n"
                f"    Time: {ts}\n"
                f"    Signal: {pulse.get('signal_type', 'N/A')}\n"
                f"    Data: {data_summary}{'...' if len(str(pulse.get('data', {}))) > 100 else ''}\n"
                f"    Meta: {meta_summary}{'...' if len(str(pulse.get('meta', {}))) > 100 else ''}\n")


    def view_telemetry(self, pipeline_state_in_json, signal_type_filter="", last_n_entries=5, output_format="summary"):
        output_str = f"--- Telemetry Viewer (Mode: {output_format}) ---\n"

        pipeline_state = {}
        try:
            if pipeline_state_in_json and pipeline_state_in_json.strip():
                pipeline_state = json.loads(pipeline_state_in_json)
            else:
                return (output_str + "Error: No pipeline state provided or state is empty.",)
        except json.JSONDecodeError as e:
            error_msg = f"Error decoding pipeline_state_in_json: {e}"
            logging.error(error_msg)
            return (output_str + error_msg,)
        except Exception as e:
            error_msg = f"Error processing input pipeline state: {e}"
            logging.error(error_msg, exc_info=True)
            return (output_str + error_msg,)

        # Extract telemetry summary part from the state
        # Based on BandoCognitionPipelineCore.get_serializable_state() and PulseTelemetry.summary()
        telemetry_summary_state = pipeline_state.get("pulse_telemetry_summary", {})

        # The serialized state has `pulse_log_summary` which is the last N pulses from the *full* log,
        # and `telemetry_map` (via `signals` key) which is just the list of signal types.
        # For more detailed filtering, the full PulseTelemetry object or a more detailed serialization is needed.
        # For now, we work with what `get_serializable_state` provides.

        # `pulse_log_summary` in the state is already a list of the last N pulses (e.g., last 20).
        pulse_log_sample = telemetry_summary_state.get("pulse_log_summary", [])
        # `signals` is a list of unique signal types observed.
        observed_signals = telemetry_summary_state.get("signals", [])

        if output_format == "summary":
            output_str += f"Total Pulses (in source log): {telemetry_summary_state.get('total_pulses', 'N/A')}\n"
            output_str += f"Observed Signal Types: {', '.join(observed_signals) if observed_signals else 'None'}\n"
            last_signal = telemetry_summary_state.get('last_signal')
            if last_signal:
                output_str += "Last Signal Recorded:\n"
                output_str += self.format_pulse(last_signal)
            else:
                output_str += "Last Signal Recorded: None\n"

        elif output_format == "full_log_sample":
            output_str += f"Sample of Recent Pulses (up to {len(pulse_log_sample)} available in state):\n"
            if not pulse_log_sample:
                output_str += "  No pulse log data available in the provided state.\n"
            else:
                # Display the last_n_entries from the sample we have
                for pulse in pulse_log_sample[-last_n_entries:]:
                    output_str += self.format_pulse(pulse)

        elif output_format == "signal_specific_log":
            if not signal_type_filter or not signal_type_filter.strip():
                output_str += "Error: Signal type filter is required for 'signal_specific_log' format.\n"
                output_str += f"Available signals: {', '.join(observed_signals)}\n"
            elif signal_type_filter not in observed_signals:
                 output_str += f"Signal type '{signal_type_filter}' not found in observed signals.\n"
                 output_str += f"Available signals: {', '.join(observed_signals)}\n"
            else:
                output_str += f"Recent Pulses for Signal Type '{signal_type_filter}' (from available sample):\n"
                filtered_pulses = [p for p in pulse_log_sample if p.get('signal_type') == signal_type_filter]
                if not filtered_pulses:
                    output_str += f"  No pulses of type '{signal_type_filter}' found in the available sample.\n"
                else:
                    for pulse in filtered_pulses[-last_n_entries:]:
                        output_str += self.format_pulse(pulse)

        logging.info(f"[{self.get_metadata()['display_name']}] Viewing telemetry. Format: {output_format}, Filter: '{signal_type_filter}', N: {last_n_entries}")
        return (output_str,)

    def get_metadata(self):
        return {
            "node_name": "TelemetryViewerVictorNode",
            "display_name": "Telemetry Viewer (Victor)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Views telemetry data from a BandoCognitionPipeline's JSON state. Can output a summary, a sample of the full log, or logs for a specific signal type.",
            "author": "Jules @ Dev for Bando"
        }
