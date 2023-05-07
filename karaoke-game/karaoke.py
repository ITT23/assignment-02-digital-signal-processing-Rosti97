import numpy as np
import pyaudio
import sys
import os
import pyglet
from pyglet import shapes, clock
from mido import MidiFile

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600
CHUNK_SIZE = 1024 * 3  # Number of frames per buffer, * 3 for detecting more differences
RATE = 44100  # Sampling rate in Hz
CHANNELS = 1
FORMAT = pyaudio.paInt16  # Audio format
THRESHOLD = 100 # for preventing silent fft chaos

# rough midi file shortly made with bandlab, Song: My heart will go on - Celine Dion | Titanic-theme-song
MIDI_FILE_PATH = os.path.normpath('assets/titanic.mid')

# from https://pixabay.com/de/illustrations/eis-schnee-hintergrund-wallpaper-2065622/
BACKGROUND_IMAGE_PATH = os.path.normpath('assets/background.png')

midi = MidiFile(MIDI_FILE_PATH)

# holds mido-code and creates the visual note-blocks
class NoteManager:

    def __init__(self, midi_file: MidiFile):
        self.midi_file = midi_file 
        self.notes_midi = [] # midi information
        self.note_blocks = [] # visual notes
        self.current_time = 0
        self.game_finished = False
        self.current_time_midi = 0 # for counting midi time
        
    def start_midi(self):
        # mido documentation
        for msg in self.midi_file:
            self.current_time_midi += msg.time 
            if msg.type == 'note_on': # note_on = note starts playing in midi
                note = msg.note # midi-note 
                duration_note = msg.time # how long note is being played
                duration = self.current_time_midi # real time notes
                self.notes_midi.append((note, duration, duration_note))

    def get_frequency(self, note: int): 
        # from https://gist.github.com/YuxiUx/ef84328d95b10d0fcbf537de77b936cd
        a = 440
        return (a/32) * (2** ((note -9) /12))

    # creates the visual block shapes with the time notes are played in midi file
    def check_notes(self, dt):
        self.current_time += dt # every 0.1s
        for note in self.notes_midi:
            # if it's time to play the note
            # creates the shape and sets the height to the frequency
            if self.current_time >= note[1]:
                frequency = self.get_frequency(note[0])
                block = pyglet.shapes.Rectangle(x=WINDOW_WIDTH, y=frequency, width=40, height= 20, color=(37, 65, 178))
                self.note_blocks.append(block) # visual block list
                self.notes_midi.remove(note) # midi note list for creation
        if len(self.note_blocks) > 0:
            last_note = self.note_blocks[len(self.note_blocks)-1] # gets the last midi-note
            # game ends as soon as the last note block disappears to the left
            if last_note.x + last_note.width < 0:
                if not self.game_finished and len(self.notes_midi) == 0:
                    self.game_finished = True

    # constant movement of blocks to the left
    def update_blocks(self):
        for block in self.note_blocks:
            block.x -= 10
            block.draw()

    def draw_blocks(self):
        for block in self.note_blocks:
            block.draw()

# holds the pyaudio code and frequency analysis
class InputManager: 
    def __init__(self):
        self.threshold_exceeded = False
        self.p = pyaudio.PyAudio()
        self.stream = self.setup_stream(self.p)

    # opportunity to select input device and opens the input stream
    def setup_stream(self, p: pyaudio):
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

        print('select audio device:')
        input_device = int(input())

        return p.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, input=True,
                                frames_per_buffer=CHUNK_SIZE,
                                input_device_index=input_device)
            
    # analyses the frequencies and returns most common
    def get_freq(self):
        data = self.stream.read(CHUNK_SIZE)
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # to prevent random, not wanted input 
        if np.max(np.abs(audio_data)) > THRESHOLD:
            fft_data = np.abs(np.fft.fft(audio_data)) # FFT
            # why I thought I should use this that way:
            # https://stackoverflow.com/questions/59979354/what-is-the-difference-between-numpy-fft-fft-and-numpy-fft-fftfreq
            frequency_bins = np.fft.fftfreq(len(fft_data), d=1/RATE) # sorts the frequencies in list/bins
            major_frequency = np.abs(frequency_bins[np.argmax(fft_data)]) # gets the most common frequency out of input
            return major_frequency
        return 0
                  
# holds the playbale shape
class Player:

    def __init__(self):
        self.shape = pyglet.shapes.Rectangle(x=10, y=0, width=20, height=20, color=(232, 98, 82))

    def updatePlayer(self): 
        frequency = inputmanager.get_freq()  # gets frequency from input
        if frequency != 0:     
            # for not losing the shape outside the window
            if frequency <= 600 - self.shape.height:
                self.shape.y = frequency # y axis = frequency
            else:
                self.shape.y = WINDOW_HEIGHT - self.shape.height - ui.border_width
        else:
            # no input above trehshold -> shape will come back to 0 on y-axis
            if self.shape.y > ui.border_width:
                self.shape.y -= 10
            else: self.shape.y = ui.border_width

    # checks the collison between player and note blocks
    def get_collision_code(self):
        nice_factor = 15 # you don't have to hit the correct note, because nobody can sing like celine dion
        for block in notemanager.note_blocks:
            hit_frequency = (self.shape.y > block.y - nice_factor and 
                self.shape.y + self.shape.height < block.y + block.height + nice_factor) # y-axis position
            if (hit_frequency and 
                self.shape.x > block.x and self.shape.x < block.x + block.width): # note hit
                return 'hit'
            elif (not hit_frequency and 
                self.shape.x > block.x and self.shape.x < block.x + block.width): # note miss
                #print("nopes")
                return 'miss'
        return ''

    def draw(self):
        self.shape.draw()

# holds the menu / UI
class UI:

    def __init__(self):
        self.color = (232, 98, 82, 255) # orange
        self.score_label = pyglet.text.Label('Score: 0', font_name="Times New Roman",
                                       font_size= 20, x= 20, y=WINDOW_HEIGHT-40,color=self.color)
        self.score = 0
        self.score_points = 10
        self.feeback = pyglet.text.Label('', font_name="Times New Roman",
                                       font_size= 20, x= 400, y=WINDOW_HEIGHT-40,color=self.color)
        self.final_score_label = pyglet.text.Label('Final Score: 0', font_name="Times New Roman",
                                       font_size= 20, x= WINDOW_WIDTH / 2, y=WINDOW_HEIGHT-200,
                                       anchor_x='center', color=self.color)
        self.final_score_text= f"Final Score: {self.score}."
        self.final_feedback_label = pyglet.text.Label('', font_name="Times New Roman",
                                       font_size= 20, x= WINDOW_WIDTH / 2, y=WINDOW_HEIGHT / 2,
                                       anchor_x='center',color=self.color)
        self.final_menu_label = pyglet.text.Label('ESCAPE for exit', font_name="Times New Roman",
                                       font_size= 15, x= WINDOW_WIDTH / 2, y=WINDOW_HEIGHT / 2 - 100,
                                       anchor_x='center',color=self.color)
        self.start_menu_label = pyglet.text.Label('Press S for start and sing the notes', font_name="Times New Roman",
                                       font_size= 15, x= WINDOW_WIDTH / 2, y=WINDOW_HEIGHT/2,
                                       anchor_x='center', anchor_y='center',color=self.color)
        #self.pause = True
        self.border_width = 10
        self.borders = [pyglet.shapes.Rectangle(x = 0, y = 0, width = self.border_width, height=WINDOW_HEIGHT),
            pyglet.shapes.Rectangle(x=WINDOW_WIDTH-self.border_width, y=0, width= self.border_width, height=WINDOW_HEIGHT),
            pyglet.shapes.Rectangle(x=0,y=WINDOW_HEIGHT-self.border_width, width=WINDOW_WIDTH, height=self.border_width),
            pyglet.shapes.Rectangle(x=0,y=0, width= WINDOW_WIDTH, height=self.border_width)]
        
    def update_score(self):
        self.score += self.score_points
        self.score_label.text = f"Score: {self.score}"
          
    def draw_ui(self):
        self.score_label.draw()
        self.feeback.draw()

    def draw_good_feedback(self):
        self.feeback.text = 'Nice!'

    def draw_bad_feedback(self):
        self.feeback.text = 'oooouuuch....'
    
    def draw_end_menu(self):
        if self.score >= 1300: # are you celine dion?
            self.final_feedback_label.text = 'Wonderful <3'
        elif self.score < 1300 and self.score >= 500: # some notes were hit
            self.final_feedback_label.text = 'That\'s okay'
        else: # motivation
            self.final_feedback_label.text = 'Uff, let\'s not talk about it'
        self.final_score_label.text = f"Final Score: {self.score}"
        self.final_score_label.draw()
        self.final_feedback_label.draw()
        self.final_menu_label.draw()  

    def draw_start_menu(self):
        self.start_menu_label.draw()
    
    def get_game_status(self):
        return self.pause

    def change_game_status(self):
        self.pause = not self.pause

    def draw_border(self):
        for border in self.borders:
            border.draw()

inputmanager = InputManager() # mic input stuff
window = pyglet.window.Window(WINDOW_WIDTH,WINDOW_HEIGHT)
background = pyglet.image.load(BACKGROUND_IMAGE_PATH)
player = Player() 
notemanager = NoteManager(midi) # midi stuff
ui = UI()

def check_collisions():
    hit = player.get_collision_code()
    if hit == 'hit':
        ui.update_score()
        ui.draw_good_feedback()
    elif hit == 'miss':
        ui.draw_bad_feedback()

@window.event
def on_key_press(symbol, modifier):
    if symbol == pyglet.window.key.ESCAPE:
        sys.exit(0)

@window.event
def on_show():
    notemanager.start_midi()

@window.event
def on_draw():
    window.clear()
    background.blit(0,0)   
    if not notemanager.game_finished:
        player.updatePlayer()
        check_collisions()
        notemanager.update_blocks()
        player.draw()
        ui.draw_ui()
    else:
        ui.draw_end_menu()
    ui.draw_border()

clock.schedule_interval(notemanager.check_notes, 0.1)   

pyglet.app.run()