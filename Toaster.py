from windows_toasts import WindowsToaster, ToastText1, ToastDuration


class Toaster:
    wintoaster: WindowsToaster

    def __init__(self, name):
        self.wintoaster = WindowsToaster(name)

    def send_windows_notification(self, text: str):
        new_toast = ToastText1()
        new_toast.SetBody(text)
        new_duration = ToastDuration('short')
        new_toast.SetDuration(new_duration)
        self.wintoaster.show_toast(new_toast)
