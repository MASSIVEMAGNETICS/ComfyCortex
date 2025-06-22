# FILE: modules/victor_meta_loop_trend.py
# VERSION: v1.0.0-METALOOP-TREND-NODE
# NAME: VictorModule (MetaLoopTrendNode)
# AUTHOR: Jules @ Dev (for Bando)
# PURPOSE: Extracts and displays MetaLoop trends and scores from a BandoCognitionPipeline's state.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import json
import time
import logging

class VictorModule:
    VERSION = "v1.0.0-METALOOP-TREND-NODE"
    FUNCTION = "view_metaloop_info"
    CATEGORY = "VictorModules/Pipeline Inspectors"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "pipeline_state_in_json": ("STRING", {"multiline": True, "tooltip": "JSON state from BandoCognitionPipelineNode or compatible."}),
            },
            "optional": {
                "max_trends_to_display": ("INT", {"default": 5, "min": 1, "max": 50}),
                "max_scores_to_display": ("INT", {"default": 5, "min": 1, "max": 50}),
            }
        }

    RETURN_TYPES = ("STRING", "FLOAT", "INT")
    RETURN_NAMES = ("metaloop_summary_str", "last_score_float", "total_evaluations_int")

    def __init__(self, **kwargs):
        self.name = "MetaLoopTrendNode"

    def format_trend(self, trend_entry):
        ts, trend_data = trend_entry
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
        # Summarize complex data within trend_data for display
        trend_data_summary = {k: (str(v)[:70] + '...' if len(str(v)) > 70 else str(v)) for k, v in trend_data.items()}
        return f"  - Time: {time_str}\n    Trend: {json.dumps(trend_data_summary)}"

    def format_score(self, score_entry):
        ts = score_entry.get('timestamp', 0)
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
        meta_summary = {k: (str(v)[:70] + '...' if len(str(v)) > 70 else str(v)) for k, v in score_entry.get('meta', {}).items()}
        return f"  - Time: {time_str}\n    Score: {score_entry.get('score', 'N/A')}\n    Meta: {json.dumps(meta_summary)}"

    def view_metaloop_info(self, pipeline_state_in_json, max_trends_to_display=5, max_scores_to_display=5):
        output_str = "--- MetaLoop Information ---\n"
        last_score_val = float('nan')
        total_evals_val = 0

        pipeline_state = {}
        try:
            if pipeline_state_in_json and pipeline_state_in_json.strip():
                pipeline_state = json.loads(pipeline_state_in_json)
            else:
                return (output_str + "Error: No pipeline state provided or state is empty.", last_score_val, total_evals_val)
        except json.JSONDecodeError as e:
            error_msg = f"Error decoding pipeline_state_in_json: {e}"
            logging.error(error_msg)
            return (output_str + error_msg, last_score_val, total_evals_val)
        except Exception as e:
            error_msg = f"Error processing input pipeline state: {e}"
            logging.error(error_msg, exc_info=True)
            return (output_str + error_msg, last_score_val, total_evals_val)

        # Extract MetaLoop summary part from the state
        # Based on BandoCognitionPipelineCore.get_serializable_state() and MetaLoop.summary()
        metaloop_summary_state = pipeline_state.get("meta_loop_summary", {})

        trend_count = metaloop_summary_state.get('trend_count', 0)
        eval_count = metaloop_summary_state.get('eval_count', 0)
        total_evals_val = eval_count
        distillation_steps = metaloop_summary_state.get('distillation_steps', 0)

        output_str += f"Total Trends Logged: {trend_count}\n"
        output_str += f"Total Evaluations Performed: {eval_count}\n"
        output_str += f"Distillation Steps: {distillation_steps}\n"

        # The serialized state for MetaLoop (`meta_loop_eval_scores_summary`) contains
        # a sample of recent scores. Trends and distillation states are only counts in the summary.
        # To display actual trend data, the main pipeline state would need to serialize them.
        # For now, we work with what `get_serializable_state` provides.

        # Display recent evaluation scores (from state's `meta_loop_eval_scores_summary`)
        scores_sample = pipeline_state.get("meta_loop_eval_scores_summary", [])
        output_str += f"\nRecent Evaluation Scores (up to {len(scores_sample)} available in state, displaying last {max_scores_to_display}):\n"
        if not scores_sample:
            output_str += "  No evaluation scores available in the provided state.\n"
        else:
            for score_entry in scores_sample[-max_scores_to_display:]:
                output_str += self.format_score(score_entry)

            # Extract the very last score for the float output
            if scores_sample:
                last_score_data = scores_sample[-1].get('score')
                if isinstance(last_score_data, (int, float)):
                    last_score_val = float(last_score_data)

        # Note: Actual trend data (beyond count) is not in the current get_serializable_state().
        # If it were, it would be displayed here.
        # Example:
        # trend_log_sample = pipeline_state.get("meta_loop_trend_log_summary", [])
        # output_str += f"\nRecent Trends (up to {len(trend_log_sample)} available, displaying last {max_trends_to_display}):\n"
        # if not trend_log_sample:
        #     output_str += "  No trend data available in the provided state.\n"
        # else:
        #     for trend_entry in trend_log_sample[-max_trends_to_display:]:
        #         output_str += self.format_trend(trend_entry) # Assuming trend_entry is (timestamp, data_dict)

        logging.info(f"[{self.get_metadata()['display_name']}] Viewing MetaLoop info. Last score: {last_score_val}, Total Evals: {total_evals_val}")
        return (output_str, last_score_val, total_evals_val)

    def get_metadata(self):
        return {
            "node_name": "MetaLoopTrendVictorNode",
            "display_name": "MetaLoop Info (Victor)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Views MetaLoop data (trends, scores, distillation steps) from a BandoCognitionPipeline's JSON state. Outputs a summary string, the last evaluation score, and total evaluation count.",
            "author": "Jules @ Dev for Bando"
        }
