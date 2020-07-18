"""
    @File: Helper class for monitoring keyboard event
    @Note: Return False for callbacks trigger stop monitoring
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import argparse # for CLI Flags
from queue import Queue # used to collect inputs during 'initListener'

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pynput.keyboard import Key, KeyCode, Controller, Listener # to monitor keyboard

#--------------------------------OUR DEPENDENCIES--------------------------------#


class KeyboardMonitor():
    def __init__(self, printMessages=True):
        """
            \n@Brief: Class that help monitor when a certain key is clicked
            \n@Param: printMessages - Set to false if you do not want it printing which keys were clicked
            \n@Note: Most likely will use the 'initListener()' function
        """
        super().__init__()
        self.printMessages = printMessages

    def _onPressGenerator(self, stopKey:KeyCode):
        """
            \n@Brief: Helper function that generates function that stops the listener if 'stopKey' is pressed
            \n@Param: stopKey - The KeyCode to stop on
            \n@Returns: Function pointer to the real on "onPress" callback
        """
        def __onPress(pressedKey:KeyCode):
            if self.printMessages: print(f"{pressedKey.char} pressed")
        return __onPress

    def _onReleaseGenerator(self, stopKey:KeyCode, inputQueue:Queue):
        """
            \n@Brief: Helper function that generates function that stops the listener if 'stopKey' is released
            \n@Param: stopKey - The KeyCode to stop on
            \n@Param: inputQueue - The queue to push input data to
            \n@Returns: Function pointer to the real on "onRelease" callback
        """
        def __onRelease(releasedKey:KeyCode):
            if self.printMessages: print(f"{releasedKey.char} released")
            # if not the 'stopKey', add the pressed key into the queue
            if releasedKey != stopKey: inputQueue.put(releasedKey.char)
            else: return False

        return __onRelease

    def initListener(self, stopKey:str=None)->str():
        """
            \n@Brief: Collect events until 'stopKey' is pressed and released (defaults to 'escape' key)
            \n@Param: stopKey - the keyboard character to stop on
            \n@Returns: What was typed until 'stopKey' was pressed
        """
        # Have to convert 'stopKey' to its KeyCode
        stopKeycode = KeyCode.from_char(stopKey) if stopKey != None else Key.esc

        # Create a queue in which the pressed keys can be added to
        inputQueue = Queue()

        with Listener(
            on_press=self._onPressGenerator(stopKey),
            on_release=self._onReleaseGenerator(stopKeycode, inputQueue),
            suppress=True # if True, anything typed while listening is not registered (i.e. wont appear in terminal)
        ) as listener: listener.join()

        # After 'stopKey', pop each element from queue until empty to form a single string
        inputStr = ""
        while not inputQueue.empty():
            inputStr+=inputQueue.get()
        return inputStr

# Test functionality
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keyboard Handler & Monitoring Tester (note, will not work over ssh)")
    parser.add_argument(
        "-k", "--stop-key",
        metavar="<key to stop on>",
        default="escape",
        required=False,
        dest="stopKey",
        help="The key to stop listening on",
    )
    parser.add_argument(
        "-n", "--dont-print-messages",
        action="store_false",
        required=False,
        dest="printMessages",
        help="Use this to not have the program print out which keys were clicked",
    )

    # Actually Parse Flags (turn into dictionary)
    # converts all '-' after '--' to '_'
    args = vars(parser.parse_args())

    stopKey = args["stopKey"]
    print(f"Stopping on '{stopKey}' key")

    keyMonitor = KeyboardMonitor(printMessages=args["printMessages"])
    typedStr = keyMonitor.initListener(stopKey=stopKey)
    print(f"You typed:\n{typedStr}")
