from multiprocessing import Process, Value, freeze_support
from tkinter import *
from PIL import Image, ImageTk, ImageGrab
import win32gui
import win32con
from time import sleep
from configparser import ConfigParser
import keyboard

from Toaster import Toaster


def set_click_through(winfo_id):
    try:
        styles = win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(winfo_id, win32con.GWL_EXSTYLE, styles)
        win32gui.SetLayeredWindowAttributes(winfo_id, 0, 255, win32con.LWA_ALPHA)
    except Exception as e:
        print(e)


def scale_image(image: Image, scale_factor: float) -> Image:
    try:
        width, height = image.size
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        return image.resize((new_width, new_height), Image.ANTIALIAS)
    except Exception as e:
        print(f"Error occurred: {e}")


class MainWindow:
    root: Tk
    scale: float
    background_canvas: Canvas
    scan_rect: tuple[int, int, int, int]
    refresh_interval: int
    image: ImageTk
    cleared: bool
    map_visible: Value

    def __init__(self, rect: tuple[int, int, int, int],
                 pos: tuple[int, int], refresh_interval: int,
                 scale: float,
                 opacity: float, map_visible):
        self.map_visible = map_visible
        self.cleared = False
        self.scale = scale
        self.scan_rect = rect
        self.refresh_interval = refresh_interval
        width = int(abs(rect[2] - rect[0]) * scale)
        height = int(abs(rect[3] - rect[1]) * scale)
        pos_x = pos[0] - int(width / 2)
        pos_y = pos[1] - int(height / 2)

        self.root = Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", opacity)
        self.root.attributes('-transparentcolor', 'white', '-topmost', 1)
        self.root.config(bg='white')
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        self.background_canvas = Canvas(self.root, bg='white', highlightthickness=0)
        self.background_canvas.configure(width=width, height=height)
        self.background_canvas.pack()
        set_click_through(self.background_canvas.winfo_id())

    def run(self):
        self.draw_image()
        self.root.mainloop()

    def draw_image(self):
        with self.map_visible.get_lock():
            lock = self.map_visible.value
        if lock:
            if self.cleared:
                self.background_canvas.pack()
            capture = ImageGrab.grab(bbox=self.scan_rect)
            self.image = ImageTk.PhotoImage(scale_image(capture, self.scale))
            self.background_canvas.delete("all")
            self.background_canvas.create_image(0, 0, image=self.image, anchor='nw')
            self.cleared = False
        elif not self.cleared:
            self.background_canvas.pack_forget()
            self.cleared = True

        self.background_canvas.after(self.refresh_interval, self.draw_image)


def overlay(config: ConfigParser, map_visible):
    scan_rect = config.getint("SCAN_AREA", "x1"), \
        config.getint("SCAN_AREA", "y1"), \
        config.getint("SCAN_AREA", "x2"), \
        config.getint("SCAN_AREA", "y2")
    overlay_pos = config.getint("POSITION", "x"), config.getint("POSITION", "y")
    refresh_interval = config.getint("REFRESH_INTERVAL", "ms")
    scale = config.getfloat("DISPLAY", "scale")
    opacity = config.getfloat("DISPLAY", "opacity")

    window = MainWindow(scan_rect, overlay_pos, refresh_interval, scale, opacity, map_visible)
    window.run()


def key_listener(config: ConfigParser, map_visible, running):
    while True:
        if keyboard.is_pressed(config.get("KEY_BINDS", "toggle")):
            with map_visible.get_lock():
                map_visible.value = not map_visible.value
            sleep(1)
        if keyboard.is_pressed(config.get("KEY_BINDS", "stop")):
            with running.get_lock():
                running.value = False
        sleep(0.01)


def main():
    freeze_support()
    toaster = Toaster("Overlay")
    toaster.send_windows_notification("Ready!")

    running = Value('b', True)
    map_visible = Value('b', False)
    config = ConfigParser()
    config.read("config.ini")
    # Create the second thread that uses the shared variable

    overlay_process = Process(target=overlay, args=[config, map_visible])
    key_listener_process = Process(target=key_listener, args=[config, map_visible, running])

    overlay_process.start()
    key_listener_process.start()

    while running.value:
        continue

    overlay_process.terminate()
    key_listener_process.terminate()

    overlay_process.join()
    key_listener_process.join()
    toaster.send_windows_notification("Closing!")


if __name__ == '__main__':
    main()
