import time
from queue import Queue
from typing import List
from threading import Thread
from cement import Handler
from cement.core.log import LogHandler

from nexus.core.data.store import Runner, Task
from nexus.core.handlers.task import TaskHandler
from nexus.core.handlers.tool import ToolHandler
from nexus.core.interfaces.runner import RunnerInterface
from nexus.core.handlers.benchmark import BenchmarkHandler


class TaskWorker(Thread):
    def __init__(self, queue: Queue, logger: LogHandler, task_handler: TaskHandler, benchmark_handler: BenchmarkHandler,
                 tool_handler: ToolHandler):
        Thread.__init__(self)
        self.queue = queue
        self.daemon = True
        self.logger = logger
        self.task_handler = task_handler
        self.tool_handler = tool_handler
        self.benchmark_handler = benchmark_handler
        self.start()

    def run(self):
        while True:
            (task, callback) = self.queue.get()
            task.start()

            try:
                self.logger.info((f"Running {self.tool_handler.Meta.label} on {self.benchmark_handler.Meta.label}'s "
                                  f"{task.vuln}."), __name__)
                self.task_handler.run(task, benchmark=self.benchmark_handler, tool=self.tool_handler)
            except Exception as e:
                task.error(str(e))
                raise e.with_traceback(e.__traceback__)
            finally:
                if callback is not None:
                    callback(task)
                self.queue.task_done()
                self.logger.info(f"Task duration: {task.duration()}")
                print(task)


class ThreadPoolWorker(Thread):
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, runner_data: Runner, tasks: List[Task], threads: int, task_handler: TaskHandler,
                 benchmark_handler: BenchmarkHandler, tool_handler: ToolHandler, logger: LogHandler):
        Thread.__init__(self)
        self.runner_data = runner_data
        self.tasks = tasks
        self.daemon = True
        self.logger = logger
        self.task_handler = task_handler
        self.queue = Queue(threads)
        self.workers = []

        for _ in range(threads):
            self.workers.append(TaskWorker(self.queue, logger, task_handler, benchmark_handler, tool_handler))

    def run(self):
        for task in self.tasks:
            self.runner_data.running += [task]
            task.wait()
            self.logger.info(f"Adding task for {self.task_handler.Meta.label} handler to the queue.")
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

    def __call__(self, tasks: List[Task], benchmark: BenchmarkHandler, tool: ToolHandler, task: TaskHandler) -> Runner:
        runner_data = Runner()
        threads = self.app.pargs.threads if self.app.pargs.threads else self.app.get_config('local_threads')
        worker = ThreadPoolWorker(runner_data, tasks=tasks, threads=threads, task_handler=task,
                                  benchmark_handler=benchmark, tool_handler=tool, logger=self.app.log)
        worker.start()

        # TODO: not sure if this is necessary, enable back in case of error
        while worker.is_alive():
            time.sleep(1)

        return runner_data
