#!/usr/bin/env python3
"""
Reset LEDs

Util to turn off all LEDs on the Pimoroni LED SHIM.
"""
import ledshim

ledshim.set_all(0, 0, 0)
ledshim.show()
print("LEDs turned off")
