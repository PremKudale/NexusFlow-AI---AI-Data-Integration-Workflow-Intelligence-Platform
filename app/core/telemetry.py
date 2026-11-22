import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from config.settings import settings

class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: f"span_{uuid.uuid4().hex[:8]}")
    name: str
    agent_name: Optional[str] = None
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "RUNNING"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tokens_per_sec: float = 0.0
    estimated_cost_usd: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    subspans: List["TraceSpan"] = Field(default_factory=list)

class ExecutionTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:12]}")
    session_id: str
    query: str
    workflow_type: str
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    avg_tokens_per_sec: float = 0.0
    total_cost_usd: float = 0.0
    spans: List[TraceSpan] = Field(default_factory=list)
    final_output: Optional[str] = None
    evaluation_metrics: Dict[str, Any] = Field(default_factory=dict)

class TelemetryCollector:
    def __init__(self):
        self.traces: Dict[str, ExecutionTrace] = {}

    def start_trace(self, query: str, session_id: str = "default_session", workflow_type: str = "crew_multi_agent") -> ExecutionTrace:
        trace = ExecutionTrace(
            session_id=session_id,
            query=query,
            workflow_type=workflow_type,
            start_time=time.time()
        )
        self.traces[trace.trace_id] = trace
        return trace

    def start_span(self, trace_id: str, span_name: str, agent_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> TraceSpan:
        span = TraceSpan(
            name=span_name,
            agent_name=agent_name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        if trace_id in self.traces:
            self.traces[trace_id].spans.append(span)
        return span

    def finish_span(
        self,
        span: TraceSpan,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        status: str = "SUCCESS",
        metadata_update: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        span.end_time = time.time()
        span.duration_ms = round((span.end_time - span.start_time) * 1000, 2)
        span.status = status
        span.prompt_tokens = prompt_tokens
        span.completion_tokens = completion_tokens
        span.total_tokens = prompt_tokens + completion_tokens

        # Latency / tokens per second calculation
        duration_sec = max(span.duration_ms / 1000.0, 0.001)
        span.tokens_per_sec = round(span.total_tokens / duration_sec, 2)

        # Financial cost calculation based on configurable Vertex / LLM tiered pricing
        prompt_cost = (span.prompt_tokens / 1000.0) * settings.EVALUATION_COST_PER_1K_PROMPT_TOKENS
        completion_cost = (span.completion_tokens / 1000.0) * settings.EVALUATION_COST_PER_1K_COMPLETION_TOKENS
        span.estimated_cost_usd = round(prompt_cost + completion_cost, 6)

        if metadata_update:
            span.metadata.update(metadata_update)
        return span

    def finish_trace(self, trace_id: str, final_output: str = "", eval_metrics: Optional[Dict[str, Any]] = None) -> ExecutionTrace:
        if trace_id not in self.traces:
            raise KeyError(f"Trace {trace_id} not found")
        trace = self.traces[trace_id]
        trace.end_time = time.time()
        trace.total_duration_ms = round((trace.end_time - trace.start_time) * 1000, 2)
        trace.final_output = final_output

        total_prompt = sum(s.prompt_tokens for s in trace.spans)
        total_comp = sum(s.completion_tokens for s in trace.spans)
        trace.total_prompt_tokens = total_prompt
        trace.total_completion_tokens = total_comp
        trace.total_tokens = total_prompt + total_comp

        duration_sec = max(trace.total_duration_ms / 1000.0, 0.001)
        trace.avg_tokens_per_sec = round(trace.total_tokens / duration_sec, 2)
        trace.total_cost_usd = round(sum(s.estimated_cost_usd for s in trace.spans), 6)

        if eval_metrics:
            trace.evaluation_metrics = eval_metrics

        return trace

    def get_recent_traces(self, limit: int = 20) -> List[ExecutionTrace]:
        all_traces = list(self.traces.values())
        return sorted(all_traces, key=lambda t: t.start_time, reverse=True)[:limit]

telemetry = TelemetryCollector()

