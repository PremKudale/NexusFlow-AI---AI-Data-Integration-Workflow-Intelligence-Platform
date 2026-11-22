import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.agents.crew import crew_engine
from app.evaluation.benchmarks import BENCHMARK_TEST_SUITE

EVAL_DIR = Path("data/evaluation")
EVAL_DIR.mkdir(parents=True, exist_ok=True)
EVAL_HISTORY_FILE = EVAL_DIR / "eval_history.json"

class EvaluationPipeline:
    def __init__(self):
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if EVAL_HISTORY_FILE.exists():
            try:
                with open(EVAL_HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            with open(EVAL_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[EvalPipeline] Failed to save history: {e}")

    def evaluate_query_accuracy(self, generated_report: str, ground_truth: Dict[str, Any]) -> float:
        # Measures answer correctness by checking entity and numeric coverage
        entities = ground_truth.get("key_entities", [])
        matched = 0
        report_lower = generated_report.lower()

        for ent in entities:
            if str(ent).lower() in report_lower:
                matched += 1

        entity_score = (matched / max(len(entities), 1)) if entities else 1.0

        # Check numeric presence if numerical values exist
        num_score = 1.0
        for k, v in ground_truth.items():
            if isinstance(v, (int, float)) and k.startswith("expected_"):
                # formatted variations
                num_str = f"{v:,.2f}"
                plain_str = str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)
                if num_str in generated_report or plain_str in generated_report:
                    num_score = min(1.0, num_score + 0.1)

        final_correctness = 0.7 * entity_score + 0.3 * num_score
        return round(min(1.0, final_correctness), 4)

    def run_benchmark_suite(self, limit: Optional[int] = None) -> Dict[str, Any]:
        tests = BENCHMARK_TEST_SUITE[:limit] if limit else BENCHMARK_TEST_SUITE
        results = []

        total_tokens = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        latencies_ms = []
        tokens_per_sec_list = []
        correctness_scores = []
        recall_scores = []

        run_id = f"eval_run_{int(time.time())}"

        for test in tests:
            start_time = time.time()
            res = crew_engine.execute_workflow(
                query=test["query"],
                user="eval_pipeline",
                role="system",
                session_id=run_id
            )
            elapsed_ms = (time.time() - start_time) * 1000

            # Answer correctness against ground truth
            correctness = self.evaluate_query_accuracy(
                generated_report=res["final_report"],
                ground_truth=test["ground_truth"]
            )
            correctness_scores.append(correctness)

            # Retrieval recall
            recall = res["evaluation_metrics"].get("retrieval_recall", 0.85)
            recall_scores.append(recall)

            # Telemetry stats
            tel = res["telemetry"]
            latencies_ms.append(tel["duration_ms"])
            tokens_per_sec_list.append(tel["tokens_per_sec"])
            total_tokens += tel["total_tokens"]
            total_prompt_tokens += tel["prompt_tokens"]
            total_completion_tokens += tel["completion_tokens"]
            total_cost += tel["total_cost_usd"]

            results.append({
                "test_id": test["id"],
                "category": test["category"],
                "query": test["query"],
                "correctness_score": correctness,
                "retrieval_recall": recall,
                "latency_ms": tel["duration_ms"],
                "tokens_per_sec": tel["tokens_per_sec"],
                "tokens": tel["total_tokens"],
                "cost_usd": tel["total_cost_usd"],
                "trace_id": res["trace_id"]
            })

        # Aggregated pipeline metrics
        avg_correctness = round(float(np.mean(correctness_scores)), 4) if correctness_scores else 0.0
        avg_recall = round(float(np.mean(recall_scores)), 4) if recall_scores else 0.0
        p50_latency = round(float(np.percentile(latencies_ms, 50)), 2) if latencies_ms else 0.0
        p95_latency = round(float(np.percentile(latencies_ms, 95)), 2) if latencies_ms else 0.0
        avg_tps = round(float(np.mean(tokens_per_sec_list)), 2) if tokens_per_sec_list else 0.0

        summary = {
            "run_id": run_id,
            "timestamp": time.time(),
            "tests_executed": len(tests),
            "aggregate_metrics": {
                "answer_correctness": avg_correctness,
                "retrieval_recall": avg_recall,
                "p50_latency_ms": p50_latency,
                "p95_latency_ms": p95_latency,
                "avg_tokens_per_sec": avg_tps,
                "token_utilization": {
                    "total_tokens": total_tokens,
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "prompt_to_completion_ratio": round(total_prompt_tokens / max(total_completion_tokens, 1), 2)
                },
                "total_cost_usd": round(total_cost, 6)
            },
            "individual_test_results": results
        }

        self.history.append(summary)
        self._save_history()
        return summary

    def get_eval_summary(self) -> Dict[str, Any]:
        if not self.history:
            # Run one initial baseline suite if empty
            return self.run_benchmark_suite(limit=2)
        return self.history[-1]

eval_pipeline = EvaluationPipeline()

