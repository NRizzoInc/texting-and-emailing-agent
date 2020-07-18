"""
    @File: Helper class for monitoring keyboard event
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#


#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pynput.keyboard import Key, Controller, Listener # to monitor keyboard

#--------------------------------OUR DEPENDENCIES--------------------------------#


class KeyboardMonitor():
    def __init__(self):
        super().__init__()
        
    def _onPressGenerator(self, stopKey):
        """Helper function that generates function that stops the listener if 'stopKey' is pressed"""
        def __onPress(pressedKey):
            print(f"{pressedKey} pressed")
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
    keyMonitor = KeyboardMonitor()
    keyMonitor.initListener()