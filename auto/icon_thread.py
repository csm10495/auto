''' Used to run Icon in a thread '''

import pystray
import threading

class IconThread(threading.Thread):
    '''
    This allows us to workaround this issue:
    https://github.com/moses-palmer/pystray/issues/99

    The gist is that we run Icon in a thread so we can do other things at the
    same time, and we create Icon in the thread to workaround the above issue.
    '''
    def __init__(self, *icon_args, **icon_kwargs):
        self.icon = None
        self._icon_args = icon_args
        self._icon_kwargs = icon_kwargs

        threading.Thread.__init__(self, daemon=True)

    def __enter__(self):
        '''
        For use as a contextmanager

        Starts the thread
        '''
        self.run()

    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        For use as a contextmanager

        Stops the thread
        '''
        self.stop()

    def run(self):
        '''
        Automatically called within the just-started thread
        '''
        self.icon = pystray.Icon(*self._icon_args, **self._icon_kwargs)
        self.icon.run()

    def stop(self):
        '''
        Called to stop the thread and internal Icon instance
        '''
        if self.icon:
            self.icon.stop()
