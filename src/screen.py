import time
import subprocess
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


class Screen:
    def __init__(self):
        # Create the I2C interface.
        i2c = busio.I2C(SCL, SDA)
        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height. Change these
        # to the right size for your display!
        self.disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
        self.width = self.disp.width
        self.height = self.disp.height

        self.font = ImageFont.load_default()
        self.padding = -2
        self.top = self.padding
        self.bottom = self.height - self.padding

    def clear_display(self):
        self.disp.fill(0)
        self.disp.show()

    def _blank_image(self):
        # Create blank image for drawing.
        image = Image.new("1", (self.width, self.height))
        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        return image, draw

    def display(self, lines):
        image, draw = self._blank_image()
        # Move left to right keeping track of the current x position for drawing shapes.
        x = 0

        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        # Write four lines of text.
        k = 0
        for i in range(0, len(lines)):
            draw.text((x, self.top + k), lines[i], font=self.font, fill=255)
            k += 8

        # Display image.
        self.disp.image(image)
        self.disp.show()
