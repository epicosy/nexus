import time
from queue import Queue
from typing import List
from threading import Thread
from cement import Handler
from cement.core.log import LogHandler

from nexus.core.data.context import Context
from nexus.core.data.store import Runner, Task
from nexus.core.exc import CommandError, NexusError
from nexus.core.handlers.nexus import NexusHandler
from nexus.core.interfaces.runner import RunnerInterface


class TaskWorker(Thread):
    def __init__(self, queue: Queue, logger: LogHandler, nexus_handler: NexusHandler, context: Context):
        Thread.__init__(self)
        self.queue = queue
        self.daemon = True
        self.logger = logger
        self.nexus_handler = nexus_handler
        self.context = context
        self.start()

    def run(self):
        while True:
            (task, callback) = self.queue.get()
            task.start()

            try:
                self.logger.info((f"Running {self.context.tool.instance.name} on {self.context.benchmark.instance.name}'s "
                                  f"{task.vulnerability.id}."))
                self.nexus_handler.run(task.program, context=self.context, vulnerability=task.vulnerability)
            except (CommandError, NexusError) as err:
                task.error(str(err))
                self.logger.error(str(err))
            finally:
                if callback is not None:
                    callback(task)
                self.queue.task_done()
                self.logger.info(f"Task duration: {task.duration()}")
                print(task)


class ThreadPoolWorker(Thread):
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, runner_data: Runner, tasks: List[Task], threads: int, nexus_handler: NexusHandler,
                 context: Context, logger: LogHandler):
        Thread.__init__(self)
        self.runner_data = runner_data
        self.tasks = tasks
        self.daemon = True
        self.logger = logger
        self.nexus_handler = nexus_handler
        self.queue = Queue(threads)
        self.workers = []

        for _ in range(threads):
            self.workers.append(TaskWorker(self.queue, logger, nexus_handler, context))

    def run(self):
        for task in self.tasks:
            self.runner_data.running += [task]
            task.wait()
            self.logger.info(f"Adding task for {self.nexus_handler.Meta.label} handler to the queue.")
            self.add_task(task)

        """Wait for completion of all the tasks in the queue"""
        self.queue.join()

    def add_task(self, task: Task):
        """Add a task to the queue"""
        if task.status is not None:
            self.queue.put((task, self.runner_data.done))


class RunnerHandler(RunnerInterface, Handler):
    class Meta:
        label = 'runner'

    def __call__(self, tasks: List[Task], context: Context, nexus_handler: NexusHandler) -> Runner:
        runner_data = Runner()
        threads = self.app.pargs.threads if self.app.pargs.threads else self.app.get_config('local_threads')
        worker = ThreadPoolWorker(runner_data, tasks=tasks, threads=threads, nexus_handler=nexus_handler, context=context,
                                  logger=self.app.log)
        worker.start()

        while worker.is_alive():
            time.sleep(1)

        return runner_data
