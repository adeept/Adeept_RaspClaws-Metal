#!/usr/bin/env python3 
# File name   : OLED.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2026/01/29
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
from PIL import ImageFont
import time

def draw_text_with_wrap(draw, text, x, y, font, fill, max_width):
    lines = []
    current_line = ""
    for word in text.split():
        test_line = current_line + word + " "
        # getbbox (x0, y0, x1, y1) width= x1 - x0
        test_width = font.getbbox(test_line)[2] - font.getbbox(test_line)[0]
        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    for line in lines:
        if line.strip():  
            draw.text((x, y), line.strip(), font=font, fill=fill)
        
        line_height = font.getbbox(line)[3] - font.getbbox(line)[1]
        y += line_height

serial = i2c(port=1, address=0x3C) 
device = ssd1306(serial, width=128, height=64, rotate=0)  

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

display_text = " Adeept RaspClaws Metal \n  for Raspberry Pi"

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw_text_with_wrap(draw, display_text, 0, 0, font, 255, device.width)

while True:
    time.sleep(10)
