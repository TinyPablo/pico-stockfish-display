# OLED rendering (stub)from machine import I2C, Pin
from lib.ssd1306 import SSD1306_I2C
from machine import I2C, Pin


class Display:
    def __init__(self):
        # I2C0 -> INPUT / STATE OLED
        self.i2c0 = I2C(
            0,
            sda=Pin(0),
            scl=Pin(1),
            freq=400_000,
        )

        # I2C1 -> ANALYSIS OLED
        self.i2c1 = I2C(
            1,
            sda=Pin(6),
            scl=Pin(7),
            freq=400_000,
        )

        self.state_oled = SSD1306_I2C(128, 64, self.i2c0)
        self.analysis_oled = SSD1306_I2C(128, 64, self.i2c1)

        self.clear_all()

    def clear_all(self):
        self.state_oled.fill(0)
        self.state_oled.show()

        self.analysis_oled.fill(0)
        self.analysis_oled.show()

    def show_state(self, turn, move_number, last_move):
        oled = self.state_oled
        oled.fill(0)

        oled.text("STATE", 0, 0)
        oled.text(f"Turn: {turn}", 0, 16)
        oled.text(f"Move: {move_number}", 0, 26)

        if last_move:
            oled.text(f"Last: {last_move}", 0, 36)
        else:
            oled.text("Last: --", 0, 36)

        oled.show()

    def show_analysis(self, depth, lines):
        oled = self.analysis_oled
        oled.fill(0)

        oled.text(f"D:{depth}", 0, 0)

        y = 16
        for i, line in enumerate(lines[:3], 1):
            move = line["move"]
            eval_ = line["eval"]
            sign = "+" if eval_ >= 0 else ""
            oled.text(f"{i} {move} {sign}{eval_:.2f}", 0, y)
            y += 12

        oled.show()