import abc
import threading

from .. import logger


class DaemonThread(abc.ABC):
    ACTIVE: "list[DaemonThread]" = []
    WAIT_TIMEOUT: float = 1

    @staticmethod
    def clean_all() -> None:
        for d in DaemonThread.ACTIVE:
            d.cleanup()

        DaemonThread.ACTIVE.clear()

    def __init__(self, thread_name: str) -> None:
        DaemonThread.ACTIVE.append(self)

        self._running: bool = True
        self._thread = threading.Thread(
            target=self._thread_runner, name=thread_name, daemon=True
        )
        self._thread.start()

    def _thread_runner(self) -> None:
        while self._running:
            self.thread_loop()

    def cleanup(self) -> None:
        logger.debug("Cleaning up daemon thread %s", self.__class__.__name__)

        self._running = False
        self.thread_cleanup()
        self._thread.join(DaemonThread.WAIT_TIMEOUT)

        if self._thread.is_alive():
            logger.info(
                "Daemon thread %s did not cleanup within given time!",
                self.__class__.__name__,
            )

    def thread_cleanup(self) -> None:
        pass

    @abc.abstractmethod
    def thread_loop(self) -> None:
        pass
