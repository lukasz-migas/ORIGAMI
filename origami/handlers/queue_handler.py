"""Event queue handler"""
# Standard library imports
import queue
import logging
from threading import Thread

# Third-party imports
from pubsub import pub

# Local imports
from origami.handlers.call import Call

LOGGER = logging.getLogger(__name__)


class QueueHandler:
    """Simple Queue handler that executes code as its being added to the queue"""

    def __init__(self, parent, n_threads=2, *args):
        super().__init__(*args)

        max_size = 0

        # initialize queue
        self.parent = parent
        self.q = queue.Queue(maxsize=max_size)

        for _ in range(n_threads):
            worker = Thread(target=self.process, args=(self.q,))
            worker.setDaemon(True)
            worker.start()

    def add(self, call_obj):
        """Add call object to the queue

        Parameters
        ----------
        call_obj : Call instance
        """
        if not isinstance(call_obj, Call):
            raise ValueError("You can only add 'Call' objects to the queue")

        self.q.put(call_obj)
        LOGGER.debug(f"Added new task to the queue (queue size ~{self.count()})")
        self.update()

    def clear(self):
        """Safely empty queue from waiting tasks"""
        with self.q.mutex:
            self.q.queue.clear()

        LOGGER.debug("Queue > Cleared queue")

    def join(self):
        """Start queue"""
        self.q.join()

    def process(self, q):
        """Process the call

        Parameters
        ----------
        q : Queue
        """
        while True:
            # get object
            call_obj = q.get()
            # call function
            call_obj.run()
            q.task_done()
            LOGGER.info("Queue > Completed task")

            # update statusbar
            self.update()

    def count(self):
        """Retrieves the count of items in the queue"""
        return self.q.qsize()

    def update(self):
        """Sends update to the statusbar"""
        pub.sendMessage("statusbar.update.queue", msg=f"Queue: ~{self.count()}")

    def __repr__(self):
        return f"Queue<count={self.count()}>"
