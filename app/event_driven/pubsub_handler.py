import json
import uuid
import asyncio
from typing import Dict, Any, Callable, Optional, List
from config.settings import settings
from app.core.logging import structured_logger
from app.event_driven.retry_manager import retry_manager

class EventMessage:
    def __init__(self, topic: str, data: Dict[str, Any], event_id: Optional[str] = None):
        self.id = event_id or f"evt_{uuid.uuid4().hex[:10]}"
        self.topic = topic
        self.data = data
        self.timestamp = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "data": self.data,
            "timestamp": self.timestamp
        }

class EventBusPubSub:
    def __init__(self):
        self.backend = settings.PUBSUB_BACKEND
        self._gcp_publisher = None
        self._local_subscribers: Dict[str, List[Callable]] = {}
        self._async_queue: asyncio.Queue = asyncio.Queue()
        self._is_worker_running = False
        self._init_backend()

    def _init_backend(self):
        if self.backend == "pubsub" and settings.GOOGLE_APPLICATION_CREDENTIALS:
            try:
                from google.cloud import pubsub_v1
                self._gcp_publisher = pubsub_v1.PublisherClient()
                print(f"[PubSub] GCP Publisher initialized for project {settings.GCP_PROJECT_ID}")
            except Exception as e:
                print(f"[PubSub] Fallback to local async queue: {e}")
                self.backend = "local_async"

    def subscribe(self, topic: str, handler: Callable):
        if topic not in self._local_subscribers:
            self._local_subscribers[topic] = []
        self._local_subscribers[topic].append(handler)

    async def publish(self, topic: str, data: Dict[str, Any]) -> str:
        msg = EventMessage(topic=topic, data=data)

        # Audit event
        structured_logger.log_audit_event(
            event_type="PUBSUB_PUBLISH",
            user="system_event_bus",
            role="system",
            action="publish_message",
            resource=topic,
            details={"message_id": msg.id}
        )

        if self._gcp_publisher:
            try:
                data_bytes = json.dumps(msg.to_dict()).encode("utf-8")
                future = self._gcp_publisher.publish(topic, data_bytes)
                return future.result()
            except Exception as e:
                print(f"[PubSub] GCP publish error, fallback to async queue: {e}")

        # Local async event bus
        await self._async_queue.put(msg)

        # Immediately dispatch to registered subscribers with retry manager
        handlers = self._local_subscribers.get(topic, [])
        for handler in handlers:
            asyncio.create_task(
                retry_manager.execute_with_retry(handler, msg.to_dict())
            )

        return msg.id

    async def start_worker(self):
        """Background listener for queued events."""
        self._is_worker_running = True
        while self._is_worker_running:
            try:
                msg = await self._async_queue.get()
                handlers = self._local_subscribers.get(msg.topic, [])
                for h in handlers:
                    try:
                        await retry_manager.execute_with_retry(h, msg.to_dict())
                    except Exception as e:
                        print(f"[Worker Error] Unhandled exception in handler: {e}")
                self._async_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Worker Loop Error]: {e}")

event_bus = EventBusPubSub()

