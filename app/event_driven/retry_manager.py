import time
import random
import asyncio
from typing import Callable, Any, Optional, List, Dict
from config.settings import settings
from app.core.logging import structured_logger

class DeadLetterQueue:
    def __init__(self):
        self.poison_messages: List[Dict[str, Any]] = []

    def push(self, message: Dict[str, Any], error: str, retries_attempted: int):
        entry = {
            "timestamp": time.time(),
            "message": message,
            "error": error,
            "retries_attempted": retries_attempted,
            "status": "DLQ_PENDING_REVIEW"
        }
        self.poison_messages.append(entry)
        structured_logger.log_audit_event(
            event_type="DEAD_LETTER_QUEUE_ENTRY",
            user="system_retry_manager",
            role="system",
            action="dlq_push",
            resource=f"message_id: {message.get('id', 'unknown')}",
            status="FAILURE",
            details=entry
        )

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.poison_messages

dlq = DeadLetterQueue()

class RetryManager:
    def __init__(
        self,
        max_retries: int = settings.MAX_RETRY_ATTEMPTS,
        initial_delay: float = settings.RETRY_INITIAL_DELAY_SEC,
        backoff_factor: float = settings.RETRY_BACKOFF_FACTOR
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor

    def execute_sync(
        self,
        func: Callable[..., Any],
        payload: Dict[str, Any],
        *args,
        **kwargs
    ) -> Any:
        delay = self.initial_delay
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(payload, *args, **kwargs)
            except Exception as e:
                jitter = random.uniform(0.8, 1.2)
                sleep_time = delay * jitter

                structured_logger.log_audit_event(
                    event_type="RETRY_ATTEMPT",
                    user="system_retry_manager",
                    role="system",
                    action=f"attempt_{attempt}",
                    resource=f"func_{getattr(func, '__name__', 'unknown')}",
                    status="RETRYING",
                    details={"attempt": attempt, "error": str(e), "next_delay_sec": round(sleep_time, 2)}
                )

                if attempt == self.max_retries:
                    dlq.push(payload, error=str(e), retries_attempted=attempt)
                    raise RuntimeError(
                        f"Action permanently failed after {self.max_retries} attempts. Routed to DLQ. Root error: {e}"
                    ) from e

                time.sleep(sleep_time)
                delay *= self.backoff_factor

    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        payload: Dict[str, Any],
        *args,
        **kwargs
    ) -> Any:
        delay = self.initial_delay
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(payload, *args, **kwargs)
                else:
                    return func(payload, *args, **kwargs)
            except Exception as e:
                last_exception = e
                jitter = random.uniform(0.8, 1.2)
                sleep_time = delay * jitter

                structured_logger.log_audit_event(
                    event_type="RETRY_ATTEMPT",
                    user="system_retry_manager",
                    role="system",
                    action=f"attempt_{attempt}",
                    resource=f"func_{getattr(func, '__name__', 'unknown')}",
                    status="RETRYING",
                    details={"attempt": attempt, "error": str(e), "next_delay_sec": round(sleep_time, 2)}
                )

                if attempt == self.max_retries:
                    # Max retries exhausted -> Move to Dead Letter Queue
                    dlq.push(payload, error=str(e), retries_attempted=attempt)
                    raise RuntimeError(
                        f"Action permanently failed after {self.max_retries} attempts. Routed to DLQ. Root error: {e}"
                    ) from e

                await asyncio.sleep(sleep_time)
                delay *= self.backoff_factor

retry_manager = RetryManager()

