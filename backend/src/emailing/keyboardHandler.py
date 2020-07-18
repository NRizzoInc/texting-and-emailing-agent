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
        
    def _onPress(self, key):
        """Helper function that stops the listener if 'escape' is pressed"""
        # print(f"{key} pressed")
        if key == Key.esc: return False

    def _onRelease(self, key):
        """Helper function that stops the listener if 'escape' is released"""
        # print(f"{key} released")
        # Stop listener
        if key == Key.esc: return False

    def initListener(self):
        """Collect events until 'escape' is pressed and released"""
        with Listener(on_press=self._onPress, on_release=self._onRelease) as listener:
            listener.join()

# Test functionality
if __name__ == "__main__":
    keyMonitor = KeyboardMonitor()
    keyMonitor.initListener()