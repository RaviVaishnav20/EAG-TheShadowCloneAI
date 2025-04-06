from pywinauto.application import Application
import win32gui
import win32con
from win32api import GetSystemMetrics
from functools import partial

class PaintManager:
    TOOL_COORDINATES = {
        'rectangle': (530, 82),
        'text': (528, 92),
        'canvas_click': (810, 533),
        'canvas_exit': (1050, 800)
    }
    
    def __init__(self):
        self.app = None
        self.window = None
        self.canvas = None
        
    def initialize(self):
        if not self.app:
            self.app = Application().start('mspaint.exe')
            self._position_window()
            
    def _position_window(self):
        self.window = self.app.window(class_name='MSPaintApp')
        hwnd = self.window.handle
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            GetSystemMetrics(0) + 1, 0,
            0, 0,
            win32con.SWP_NOSIZE | win32con.SW_MAXIMIZE
        )
        self.canvas = self.window.child_window(class_name='MSPaintView')
    
    def execute_sequence(self, actions):
        for action in actions:
            if action[0] == 'click':
                self.window.click_input(coords=action[1])
            elif action[0] == 'type':
                self.window.type_keys(action[1])
            elif action[0] == 'press':
                self.canvas.press_mouse_input(coords=action[1])
            elif action[0] == 'move':
                self.canvas.move_mouse_input(coords=action[1])
            elif action[0] == 'release':
                self.canvas.release_mouse_input(coords=action[1])