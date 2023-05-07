import numpy as np
import pyaudio
from pynput.keyboard import Key, Controller

# For universal usage, not bound to pyglet window
# Same code though as in whistle-input.py

CHUNK_SIZE = 1024  # Number of frames per buffer, *3 for detection of half tones
RATE = 44100  # Sampling rate (Hz)
CHANNELS = 1
THRESHOLD = 400 # for preventing silent fft chaos

# holds they microphone input stream 
class Interactor:

    def __init__(self):
        self.input_freq = []
        self.threshold_exceeded = False
        self.p = pyaudio.PyAudio()
        self.stream = self.setup_stream(self.p)
        self.keyboard = Controller()

    # opportunity to select input device and opens the input stream
    def setup_stream(self, p: pyaudio):
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

        print('select audio device:')
        input_device = int(input())

        return p.open(format=pyaudio.paInt16, channels=CHANNELS,
                                rate=RATE, input=True,
                                frames_per_buffer=CHUNK_SIZE,
                                input_device_index=input_device)
    
    def change_threshold_exceeded(self, b : bool):
        self.threshold_exceeded = b

    # checks the data from input
    # goes through the list of frequencies in input and compares them with each other
    def check_input(self):
        count_prev_higher = 0
        count_prev_lower = 0
        length = len(self.input_freq)
        # to ensure it's not some random, not wanted input 
        if length >=5:
            # comparision of the frequencies
            for i in range(1,length):
                if self.input_freq[i] - self.input_freq[i-1] > 0:
                    count_prev_lower += 1 # earlier frequency is lower than following
                elif self.input_freq[i] - self.input_freq [i-1] < 0:
                    count_prev_higher +=1 # earlier frequency is higher than following     
            if count_prev_higher > count_prev_lower:
                # whistly goes lower -> down input
                self.keyboard.press(Key.down)
                self.keyboard.release(Key.down)
            else:
                # whistle goes higher -> up input
                self.keyboard.press(Key.up)
                self.keyboard.release(Key.up)
            
    # analyses the frequencies
    def get_audio(self):
        data = self.stream.read(CHUNK_SIZE)
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # to prevent random, not wanted input 
        if np.max(np.abs(audio_data)) > THRESHOLD:
            fft_data = np.abs(np.fft.fft(audio_data)) # FFT
            frequency_bins = np.fft.fftfreq(len(fft_data), d=1/RATE) # sorts the frequencies in list
            major_frequency = np.abs(frequency_bins[np.argmax(fft_data)]) # gets the most common frequency out of input
            if major_frequency >= 800: 
                # whistling mostly above 1000 Hz, normal speaking voice should not come through as much
                # code is mainly meant for whistling
                self.input_freq.append(major_frequency) 
                self.change_threshold_exceeded(True) # for knowing when input starts
        elif np.max(np.abs(audio_data)) < THRESHOLD and self.threshold_exceeded:
            self.change_threshold_exceeded(False) # for knowing when input ends
            self.check_input()
            self.input_freq.clear() # after check, list gets cleared for new input


interactor = Interactor()

while (True):
    interactor.get_audio()

