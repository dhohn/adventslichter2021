from machine import Pin, reset
from time import sleep_ms
from ws2812 import WS2812
import random
import json

class KeyHandler:
    # https://github.com/muka/micropython-nodemcu-maxtix-keypad
    def __init__(self, index, pin_id):
        self.index = index
        self.pin_id = pin_id
        self.pin = Pin(pin_id, Pin.IN)

    def reinit(self):
        self.pin = Pin(self.pin_id, Pin.IN, Pin.PULL_UP)
        self.pin.value(1)

    def read(self):
        return self.pin.value()

    def begin_pulse(self):
        self.pin = Pin(self.pin_id, Pin.OUT)
        self.pin.off()

    def end_pulse(self):
        self.pin.on()
        self.pin = Pin(self.pin_id, Pin.IN)


class Keypad:
    # https://github.com/muka/micropython-nodemcu-maxtix-keypad
    def __init__(self, row_pins, col_pins, keymap):

        self.keymap = keymap

        self.row_pins = []
        for (index, row_pin) in enumerate(row_pins):
            self.row_pins.append(KeyHandler(index, row_pin))

        self.col_pins = []
        for index, col_pin in enumerate(col_pins):
            self.col_pins.append(KeyHandler(index, col_pin))

    def get_keys(self):

        pressed = []

        # Re-intialize the row pins. Allows sharing these pins with other hardware
        for row in self.row_pins:
            row.reinit()

        # check the column pins, which ones are pulled down
        for col in self.col_pins:
            col.begin_pulse()
            for row in self.row_pins:
                row_val = row.read()
                # row_col = col.read()
                if row_val == 0:
                    pressed.append(self.keymap[row.index][col.index])
            col.end_pulse()

        return pressed

def main():
    print("Keypad example")
    keypad = Keypad(
        #  rows
        ['Y1', 'Y2', 'Y3', 'Y4'],
        # cols
        ['X22', 'X21', 'X20', 'X19', 'X18', 'X17'],
        # keys map
        [
            ['A1', 'A2', 'A3', 'A4', 'A5', 'A6'],
            ['B1', 'B2', 'B3', 'B4', 'B5', 'B6'],
            ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'],
            ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']
        ]
        # [[f"{R}{C}" for C in range(1, 7)] for R in ["A", "B", "C", "D"]],
    )

    button_to_led = {}
    button_to_led['D1'] = (1, 2)
    button_to_led['D2'] = (3, 4)
    button_to_led['D3'] = (5, 6)
    button_to_led['D4'] = (7, 8)
    button_to_led['D5'] = (9, 10)
    button_to_led['D6'] = (11, 12)

    button_to_led['C1'] = (23, 24)
    button_to_led['C2'] = (21, 22)
    button_to_led['C3'] = (19, 20)
    button_to_led['C4'] = (17, 18)
    button_to_led['C5'] = (15, 16)
    button_to_led['C6'] = (13, 14)

    button_to_led['B1'] = (25, 26)
    button_to_led['B2'] = (27, 28)
    button_to_led['B3'] = (29, 30)
    button_to_led['B4'] = (31, 32)
    button_to_led['B5'] = (33, 34)
    button_to_led['B6'] = (35, 36)

    button_to_led['A1'] = (47, 48)
    button_to_led['A2'] = (45, 46)
    button_to_led['A3'] = (43, 44)
    button_to_led['A4'] = (41, 42)
    button_to_led['A5'] = (39, 40)
    button_to_led['A6'] = (37, 38)

    #make zero indexed
    for k, v in button_to_led.items():
        button_to_led[k] = (v[0] - 1 , v[1] - 1)

    
    leds = WS2812(spi_bus=1, led_count=48)

    def rcolor():
        r, g, b = random.randint(0, 256), random.randint(0, 256),  random.randint(0, 256)
        return r, g, b
    
    def off():
        return 0, 0, 0

    # def toggle(x, y, state):
    #     if state[x][y].count(0) == 3:
    #         # 3 zeros aka was off
    #         state[x][y] = rcolor()
    #     else:
    #         state[x][y] = off()
    #     return state

    def toggle(rc, state):
        if state[rc].count(0) == 3:
            # 3 zeros aka was off
            state[rc] = rcolor()
        else:
            state[rc] = off()
        return state[rc]

    def pprint(array):
        for r in array:
            print(*r)

    def RCtoXY2(rc, keys=keypad.keymap):
        for r in range(len(keys)):
            for c in range(len(keys[r])):
                if keys[r][c] == rc:
                    return r, c

    def XYtoRC(x, y, keys=keypad.keymap):
        if not keys:
            return None
        return keys[x][y]

    def save_state(state):
        try:
            with open("/sd/state.json", "w") as f:
                json.dump(state, f)
        except OSError:
            pass

    def load_state():
        try:
            with open("/sd/state.json", "r") as f:
                state = json.load(f)
            return state
        except (OSError, ValueError):
            # start blank
            # return [[off() for c in range(6)] for r in range(4)]
            return { rc:off() for rc in [f"{R}{C}" for C in range(1, 7) for R in ["A", "B", "C", "D"]]}

    def flatten(state):
        flat = []
        for r in state:
            flat += r
        return flat
    
    def map_button_state_to_leds(button_state, leds):
        for rc, led_indices in button_to_led.items():
            for led in led_indices:
                leds.state[led] = button_state[rc]
            
    button_state = load_state()
    map_button_state_to_leds(button_state, leds)
    leds.show()
    pprint(button_state)
        
    while True:
        keys = keypad.get_keys()
        if len(keys) > 0:
            print(keys)
            for k in keys:
                c = toggle(k, state=button_state)
                for led in button_to_led[k]:
                    leds.state[led] = c
            leds.show()
            pprint(button_state)
            sleep_ms(300)
            save_state(button_state)

if __name__ == '__main__':
    main()
