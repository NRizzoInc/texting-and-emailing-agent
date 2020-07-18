#------------------------------STANDARD DEPENDENCIES-----------------------------#
# needed for receive code to stop fetching
import threading
from queue import Queue
import ctypes

class threadWithException(threading.Thread):
    def __init__(self, name:str, target, toPrintOnStop:str=""):
        """
            \n@Brief: Helper class that makes it easy to stop a thread
            \n@Param: name - The name of the thread
            \n@Param: target - the function to perform that will be stopped in the middle
            \n@Param: toPrintOnStop - (optional) What's printed when the thread is stopped during target's execution
            \n@Note: https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/ -- "raising exceptions"
            \n@Use: Create it -> start it -> sleep/do other action -> thisThread.raise_exception() -> thisThread.join()
        """
        threading.Thread.__init__(self) 
        self.name = name
        self.workerFn = target
        self.toPrintOnStop = toPrintOnStop

    def run(self): 
        # target function of the thread class 
        try:
            self.workerFn()
        finally:
            if self.toPrintOnStop != "": print(self.toPrintOnStop)

    def get_id(self): 
        # returns id of the respective thread 
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 
            ctypes.py_object(SystemExit))
        if res > 1: 
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')
