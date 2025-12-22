import threading
import queue
from datetime import datetime
from typing import List, Dict, Any

class LogManager:
    """
    Thread-safe manager for file operation logs using queue-based architecture.
    
    This implementation follows the recommendation to use a queue for cross-thread
    communication between the orchestrator worker thread and the Streamlit UI thread.
    
    Architecture:
    - Worker threads (orchestrator) push events to a thread-safe queue
    - UI thread drains the queue and appends to a persistent list
    - Separation of concerns: collecting events vs displaying them
    """
    def __init__(self):
        # Thread-safe queue for cross-thread communication
        self._event_queue: queue.Queue = queue.Queue()
        
        # Persistent list of all events (drained from queue)
        self._logs: List[Dict[str, Any]] = []
        
        # Lock for the persistent list (used during draining)
        self._lock = threading.Lock()
    
    def add_log(self, operation_type: str, location: str, status: str, details: str = ""):
        """
        Add a log entry from any thread (typically orchestrator worker thread).
        This is non-blocking and thread-safe via the queue.
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation_type,
            'location': location,
            'status': status,
            'details': details
        }
        # Put into queue - this is thread-safe and non-blocking
        self._event_queue.put_nowait(entry)
    
    def drain_queue(self) -> int:
        """
        Drain all pending events from the queue into the persistent log list.
        Should be called from the UI thread on each render/rerun.
        
        Returns:
            Number of new events drained
        """
        drained_count = 0
        
        # Drain all pending events from the queue
        while True:
            try:
                entry = self._event_queue.get_nowait()
                with self._lock:
                    self._logs.append(entry)
                drained_count += 1
            except queue.Empty:
                break
        
        return drained_count
            
    def get_logs(self) -> List[Dict[str, Any]]:
        """
        Get a copy of the current logs.
        Note: Call drain_queue() first to ensure you have the latest events.
        """
        with self._lock:
            return list(self._logs)
    
    def get_logs_with_drain(self) -> List[Dict[str, Any]]:
        """
        Convenience method: drain queue and return current logs in one call.
        """
        self.drain_queue()
        return self.get_logs()
            
    def clear(self):
        """Clear all logs (both queue and persistent list)."""
        # Clear the queue
        while True:
            try:
                self._event_queue.get_nowait()
            except queue.Empty:
                break
        
        # Clear the persistent list
        with self._lock:
            self._logs.clear()
            
    def __len__(self):
        """Return the number of events in the persistent list (not the queue)."""
        with self._lock:
            return len(self._logs)
    
    def queue_size(self) -> int:
        """Return the number of pending events in the queue."""
        return self._event_queue.qsize()

