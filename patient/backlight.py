import pigpio


class Backlight:
    PIN_RED = 16
    PIN_GREEN = 20
    PIN_BLUE = 21

    def __init__(self, *, shade=255, pi=None):
        self.pi = pigpio.pi() if pi is None else pi
        self.shade = shade

    def color(self, red: int, green: int, blue: int):
        self.pi.set_PWM_dutycycle(self.PIN_RED, red)
        self.pi.set_PWM_dutycycle(self.PIN_GREEN, green)
        self.pi.set_PWM_dutycycle(self.PIN_BLUE, blue)

    def white(self):
        self.color(self.shade, self.shade, self.shade)

    def red(self):
        self.color(self.shade, 0, 0)

    def green(self):
        self.color(0, self.shade, 0)

    def blue(self):
        self.color(0, 0, self.shade)

    def cyan(self):
        self.color(0, self.shade, self.shade)

    def magenta(self):
        self.color(self.shade, 0, self.shade)

    def yellow(self):
        self.color(self.shade, self.shade, 0)

    def __del__(self):
        self.pi.stop()  # Not critical to call
