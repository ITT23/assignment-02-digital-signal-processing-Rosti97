import numpy as np
import pyaudio
import pyglet
from pyglet import shapes, clock
import pynput
from pynput.keyboard import Key, Controller

# TODO
# Filter?


WINDOW_WIDTH = 600
WINDOW_HEIGHT = 800
CHUNK_SIZE = 1024  # Number of frames per buffer, *3 for detection of half tones
SAMPLE_RATE = 44100  # Sampling rate (Hz)
THRESHOLD = 800

class Interactor:

    # # Initialize PyAudio
    # audio = pyaudio.PyAudio()
    # # Open microphone stream
    # stream = audio.open(format=pyaudio.paInt16, channels=1,
    #                     rate=SAMPLE_RATE, input=True,
    #                     frames_per_buffer=CHUNK_SIZE)

    def __init__(self):
        self.input_freq = []
        self.threshold_exceeded = False
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1,
                        rate=SAMPLE_RATE, input=True,
                        frames_per_buffer=CHUNK_SIZE)
        self.keyboard = Controller()

    def changeThres(self, b : bool):
        self.threshold_exceeded = b

    def checkArrow(self):
        # max_index = np.argmax(notes)
        # min_index = np.argmin(notes)

        # if max_index > min_index:
        #     print("OUI")
        # else:
        #     print("IOU")
        count_prev_higher = 0
        count_prev_lower = 0
        length = len(self.input_freq)
        if length >=5:
            for i in range(1,length):
                if self.input_freq[i] - self.input_freq[i-1] > 0:
                    count_prev_lower += 1
                elif self.input_freq[i] - self.input_freq [i-1] < 0:
                    count_prev_higher +=1       
            if count_prev_higher > count_prev_lower:
                self.keyboard.press(Key.down)
                self.keyboard.release(Key.down)
                print("down")
            else:
                print("up")
                self.keyboard.press(Key.up)
                self.keyboard.release(Key.up)
            

    def get_audio(self):
        data = self.stream.read(CHUNK_SIZE)
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        if np.max(np.abs(audio_data)) > THRESHOLD:
            
            #print(frequencie)
            fft_data = np.abs(np.fft.fft(audio_data))
            # same as (np.argmax(fft_data)/CHUNK * SAMPLE
            frequency_bins = np.fft.fftfreq(len(fft_data), d=1/SAMPLE_RATE)
            major_frequency = np.abs(frequency_bins[np.argmax(fft_data)])
            if major_frequency >= 500: # whistling mostly above 1000 Hz
                print(major_frequency)
                self.input_freq.append(major_frequency)
                self.changeThres(True)
        elif np.max(np.abs(audio_data)) < THRESHOLD and self.threshold_exceeded:
            print("...")
            self.changeThres(False)
            self.checkArrow()
            self.input_freq.clear()

class Menu():

    def __init__(self):
        self.color_unselected = (0,240,0,255)
        self.color_selected = (255,0,0,255)
        self.menu_items = [pyglet.shapes.Rectangle(x=10, y=10, width=10, height=10, color=self.color_selected),
                           pyglet.shapes.Rectangle(x=10, y=30, width=10, height=10, color=self.color_unselected),
                           pyglet.shapes.Rectangle(x=10, y=60, width=10, height=10, color=self.color_unselected)]
        self.selected_item = 0 # lower one

    def draw_menu(self):
        for item in self.menu_items:
            item.draw()

    def reset_colors(self):
        for item in self.menu_items:
            item.color = self.color_unselected
    
    def update_menu(self, direction):
        if self.selected_item + direction < len(self.menu_items) and self.selected_item + direction >= 0:
            self.selected_item += direction
            self.reset_colors()
            self.menu_items[self.selected_item].color = self.color_selected

window = pyglet.window.Window(WINDOW_WIDTH,WINDOW_HEIGHT)
interactor = Interactor()
menu = Menu()

@window.event
def on_key_press(symbol, modifier):         
    if symbol == pyglet.window.key.UP:
        menu.update_menu(1)
    elif symbol == pyglet.window.key.DOWN:
        menu.update_menu(-1)

@window.event 
def on_draw():
    window.clear()
    menu.draw_menu()
    interactor.get_audio()


pyglet.app.run()