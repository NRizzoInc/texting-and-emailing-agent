"""
    @File: Helper class for monitoring keyboard event
    @Note: Return False for callbacks trigger stop monitoring
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import os, sys
import argparse # for CLI Flags
from threading import Thread, Event

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pynput.keyboard import Key, KeyCode, Controller, Listener # to monitor keyboard

#--------------------------------OUR DEPENDENCIES--------------------------------#
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from backend.src.threadHelper.killableThreads import threadWithException, stopThreadOnSetCallback

class KeyboardMonitor():
    def __init__(self, printKeyPresses=False):
        """
            \n@Brief: Class that help monitor when a certain key is clicked
            \n@Param: printKeyPresses - Set to false if you do not want it printing which keys were clicked
            \n@Note: Most likely will use either '_getMultiLineInput()' or '_stopOnKeypress()'
        """
        super().__init__()
        self.printKeyPresses = printKeyPresses

    def _onPressGenerator(self, stopKey:KeyCode):
        """
            \n@Brief: Helper function that generates function that stops the listener if 'stopKey' is pressed
            \n@Param: stopKey - The KeyCode to stop on
            \n@Returns: Function pointer to the real on "onPress" callback
        """
        def __onPress(pressedKey:KeyCode):
            if self.printKeyPresses: print(f"{pressedKey} pressed")
        return __onPress

    def _onReleaseGenerator(self, stopKey:KeyCode):
        """
            \n@Brief: Helper function that generates function that stops the listener if 'stopKey' is released
            \n@Param: stopKey - The KeyCode to stop on
            \n@Returns: Function pointer to the real on "onRelease" callback
        """
        def __onRelease(releasedKey:KeyCode):
            if self.printKeyPresses: print(f"{releasedKey} released")
            if releasedKey == stopKey: return False

        return __onRelease

    def _pressEscape(self):
        """Helper function to press the escape ('esc') key"""
        keyboard = Controller()
        # press & release escape
        keyboard.press(Key.esc)
        keyboard.release(Key.esc)

    def inputUntil(self, 
            returnThread:bool=True,
            stopKey:str=None,
            suppressTerm:bool=False,
        )->Listener():
        """
            \n@Brief: Collects keypresses until 'stopKey' is pressed and released (defaults to 'escape' key)
            \n@Param: returnThread - If False, block until stop key. If True, return the thread to be handled locally
            \n@Param: stopKey - the keyboard character to stop on
            \n@Param: suppressTerm - (default = False) Should terminal inputs be shown (False = shown)
            \n@Returns: returnThread == True: listener thread that you can check if is still active.
            returnThread == False, returns None when done
            \n@Note: If returnThread=False is used, it will break on non-alphanumeric keys
        """
        # Have to convert 'stopKey' to its KeyCode
        stopKeycode = KeyCode.from_char(stopKey) if stopKey != None else Key.esc

        if returnThread:
            listener = Listener(
                on_press=self._onPressGenerator(stopKey),
                on_release=self._onReleaseGenerator(stopKeycode),
                suppress=suppressTerm # True: anything typed while listening is not registered (i.e. wont appear in terminal)
            )
            return listener
        else:
            with Listener(
                on_press=self._onPressGenerator(stopKey),
                on_release=self._onReleaseGenerator(stopKeycode),
                suppress=suppressTerm # True: anything typed while listening is not registered (i.e. wont appear in terminal)
            ) as listener: 
                listener.join()
                return None
    
    def _getMultiLineInput(self, prompt:str)->str():
        """
            \n@Brief: Helper function that allows for messages to span multiple lines, stops with 'escape'
            \n@Param: prompt - The prompt to the user before they start typing
            \n@Note: Do not end prompt with ':' as there will be on appended to it
            \n@Return: Returns the message as a string
        """
        msgToRtn = ""
        print(f"{prompt} (Press enter, escape. enter to stop): ")

        stopKeyThread = self.inputUntil(returnThread=True)
        stopKeyThread.start()
        while True:
            msgToRtn += input("") + "\n"
            if not stopKeyThread.is_alive():
                msgToRtn.rstrip()
                break

        # remove extra newlines
        return msgToRtn.strip()

    def _stopOnKeypress(self, workerFn, prompt:str="\b", toPrintOnStop:str="", printPrompts:bool=True):
        """
            \n@Brief: Stops running 'workerFn()' when a certain key is pressed
            \n@Param: workerFn - The function that should be stopped on the keypress 
            (Needs threading.Event arg that will stop worker if event.isSet())
            \n@Param: toPrintOnStop - (optional) What's printed when the thread is stopped during target's execution
            \n@Param: prompt - The prompt to the user before they wait to stop about wait they are waiting for
            \n@Param: printPrompts - Set to false to keep prints to a minimum
        """
        # hide terminal inputs (only care about 'escape')
        if printPrompts: print(f"Press escape ('esc') to {prompt}...")

        # Create Event & EventThread to stop keyboard thread if worker finishes
        # If worker fn finishes first, will trigger a callback that presses the escape key to stop keyboard monitor
        stopEvent = Event()
        stopEventCallback = stopThreadOnSetCallback(
            name="stopEventCallback",
            onStopCallback=self._pressEscape,
            stopEvent=stopEvent
        )

        # Create threads to run
        # worker that should be stopped when the key is pressed
        funcToRunThread = threadWithException(
            name="stop-me-on-keypress-thread",
            target=workerFn,
            toPrintOnStop=toPrintOnStop if printPrompts == True else "",
            stopEvent=stopEvent
        )

        # on 'esc' (suppressTerm = False so user can still use keyboard -- just not in terminal)
        stopKeyThread = self.inputUntil(returnThread=True, suppressTerm=False)

        # have the custom function run, but stop it when the stop key thread finishes
        # https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
        # start monitor threads first (might be delay, so it should be available prior)

        # checks if worker fn finishes first (if so, triggers callback to trigger stop on monitor)
        stopEventCallback.start()

        # montiors keyboard -- stopped when 'esc' is clicked or stopEventCallback is triggered by end of worker
        stopKeyThread.start()

        # start worker function
        funcToRunThread.start()

        # block main thread until monitoring thread stop (i.e. 'esc' is clicked)
        stopKeyThread.join()
        
        # ends the worker function by causing an exception
        funcToRunThread.raise_exception()

        # kill the threads completely
        # (make sure to set stopEvent to ensure stopEventCallback is killed)
        funcToRunThread.join()
        stopEvent.set() # Warning: Remove at risk of leaving thread up

# Test functionality
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keyboard Handler & Monitoring Tester (note, will not work over ssh)")
    testGroup = parser.add_argument_group(
        title="Test Flags",
        description="Helps to choose what you want to test",
    )
    
    # Stop Key Arg
    testGroup.add_argument(
        "-k", "--stop-key",
        metavar="<key to stop on>",
        default="escape",
        required=False,
        dest="stopKey",
        help="Test stopping on different keys",
    )

    # Print Message Bool Arg
    parser.add_argument(
        "-n", "--dont-print-messages",
        action="store_false",
        required=False,
        dest="printKeyPresses",
        help="Use this to not have the program print out which keys were clicked",
    )

    # Multi Line Input Test Flag
    testGroup.add_argument(
        "-m", "--multi-line-input",
        action="store_true",
        required=False,
        dest="isMultiLineInput",
        help="Use this to test the '_getMultiLineInput' function",
    )

    testGroup.add_argument(
        "-s", "--stop-on-keypress",
        action="store_true",
        required=False,
        dest="isStopOnKeypress",
        help="Use this to test the '_stopOnKeypress' function",
    )

    # Actually Parse Flags (turn into dictionary)
    # converts all '-' after '--' to '_'
    args = vars(parser.parse_args())

    stopKey = args["stopKey"]
    # Only print keys if not testing multiline inputs & user said to
    shouldPrintKeys = args["printKeyPresses"] if args["isMultiLineInput"] == False else False

    keyMonitor = KeyboardMonitor(printKeyPresses=shouldPrintKeys)
    if args["stopKey"] == True:
        print(f"Stopping on '{stopKey}' key")
        typedStr = keyMonitor.inputUntil(returnThread=False, stopKey=stopKey)
        print(f"You typed:\n{typedStr}")
    elif args["isMultiLineInput"] == True:
        inputStr = keyMonitor._getMultiLineInput("Type a multiline input")
        print(f"The multiline input was:\n{inputStr}")
    elif args["isStopOnKeypress"] == True:
        def testFn():
            while True: print("testing")
        keyMonitor._stopOnKeypress(testFn)
    else: print("Unknown action")
