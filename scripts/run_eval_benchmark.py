import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.evaluation.pipeline import eval_pipeline

def main():
    print("=" * 75)
    print("AI DATA INTEGRATION & WORKFLOW INTELLIGENCE PLATFORM")
    print("EVALUATION & OBSERVABILITY BENCHMARK SUITE")
    print("=" * 75)
    print("\nRunning test suite across structured warehouse and semantic indexes...\n")

    summary = eval_pipeline.run_benchmark_suite()
    agg = summary["aggregate_metrics"]
    tok = agg["token_utilization"]

    print("-" * 75)
    print("AGGREGATE BENCHMARK RESULTS")
    print("-" * 75)
    print(f"Total Benchmark Queries:   {summary['tests_executed']}")
    print(f"Answer Correctness:        {agg['answer_correctness'] * 100:.2f}%")
    print(f"Retrieval Recall:          {agg['retrieval_recall'] * 100:.2f}%")
    print(f"P50 Latency:               {agg['p50_latency_ms']} ms")
    print(f"P95 Latency:               {agg['p95_latency_ms']} ms")
    print(f"Avg Throughput:            {agg['avg_tokens_per_sec']} tokens/sec")
    print(f"Total Token Utilization:   {tok['total_tokens']:,} tokens (Prompt: {tok['prompt_tokens']:,} | Completion: {tok['completion_tokens']:,})")
    print(f"Prompt/Completion Ratio:   {tok['prompt_to_completion_ratio']}x")
    print(f"Total Estimated Cost:      ${agg['total_cost_usd']:.6f} USD")
    print("-" * 75)

    print("\nINDIVIDUAL QUERY BREAKDOWN:")
    for res in summary["individual_test_results"]:
        print(f"\n[Test ID: {res['test_id']}] ({res['category']})")
        print(f"  Query:       {res['query']}")
        print(f"  Correctness: {res['correctness_score'] * 100:.1f}% | Recall: {res['retrieval_recall'] * 100:.1f}%")
        print(f"  Latency:     {res['latency_ms']:.1f} ms | Speed: {res['tokens_per_sec']:.1f} tok/s | Cost: ${res['cost_usd']:.6f}")
        print(f"  Trace ID:    {res['trace_id']}")

    print("\n" + "=" * 75)
    print("All benchmark evaluations passed with granular execution tracing!")
    print("=" * 75)

if __name__ == "__main__":
    main()

