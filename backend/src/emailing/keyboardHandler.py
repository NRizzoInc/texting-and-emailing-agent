"""
    @File: Helper class for monitoring keyboard event
    @Note: Return False for callbacks trigger stop monitoring
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import argparse # for CLI Flags

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pynput.keyboard import Key, KeyCode, Controller, Listener # to monitor keyboard

#--------------------------------OUR DEPENDENCIES--------------------------------#


class KeyboardMonitor():
    def __init__(self):
        super().__init__()
        
    def _onPressGenerator(self, stopKey):
        """Helper function that generates function that stops the listener if 'stopKey' is pressed"""
        def __onPress(pressedKey):
            print(f"{pressedKey} pressed")
            # have to stop on release or else leaves thread hanging
            # return not pressedKey == stopKey
        return __onPress

    def _onReleaseGenerator(self, stopKey):
        """Helper function that generates function that stops the listener if 'stopKey' is released"""
        def __onRelease(releasedKey):
            print(f"{releasedKey} released")
            return not releasedKey == stopKey
        return __onRelease

    def initListener(self, stopKey:str=None):
        """Collect events until 'stopKey' is pressed and released (defaults to 'escape' key)"""
        # Have to convert 'stopKey' to its KeyCode
        stopKeycode = KeyCode.from_char(stopKey) if stopKey != None else Key.esc
        with Listener(on_press=self._onPressGenerator(stopKey), on_release=self._onReleaseGenerator(stopKeycode)) as listener:
            listener.join()

# Test functionality
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keyboard Handler & Monitoring Tester")
    parser.add_argument(
        "-k", "--stop-key",
        metavar="<key to stop on>",
        default=None,
        required=False,
        dest="stopKey",
        help="The key to stop listening on",
    )

    # Actually Parse Flags (turn into dictionary)
    # converts all '-' after '--' to '_'
    args = vars(parser.parse_args())

    stopKey = args["stopKey"]
    print(f"Stopping on '{stopKey}' key")

    keyMonitor = KeyboardMonitor()
    keyMonitor.initListener(stopKey=stopKey)