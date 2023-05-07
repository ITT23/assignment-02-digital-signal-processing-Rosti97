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
THRESHOLD = 100 # for preventing silent fft chaos
# Celine Dion, my love.
MIDI_FILE_PATH = os.path.normpath('assets/titanic.mid')
# from https://pixabay.com/de/illustrations/eis-schnee-hintergrund-wallpaper-2065622/
BACKGROUND_IMAGE_PATH = os.path.normpath('assets/background.png')
PLAYER_IMAGE_PATH = os.path.normpath('assets/player.png')

#TEST_PATH = path.join(path.dirname(__file__), 'titanic.mid')
#print(TEST_PATH)

window = pyglet.window.Window(WINDOW_WIDTH,WINDOW_HEIGHT)
midi = MidiFile('./assets/titanic.mid')
background = pyglet.image.load(BACKGROUND_IMAGE_PATH)

class NoteManager:
    
    notes_midi = []
    note_blocks = []
    current_time = 0
    game_finished = False

    def __init__(self, midi_file: MidiFile):
        self.midi_file = midi_file
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK_SIZE)
        self.current_time_midi = 0
        for msg in midi_file:
            self.current_time_midi += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                note = msg.note
                duration_note = msg.time
                duration = self.current_time_midi
                NoteManager.notes_midi.append((note, duration, duration_note))
                
    def get_frequency(note: int): # from https://gist.github.com/YuxiUx/ef84328d95b10d0fcbf537de77b936cd
        a = 440
        return (a/32) * (2** ((note -9) /12))

    def check_notes(dt):
        #print(NoteManager.current_time)
        NoteManager.current_time += dt
        for note in NoteManager.notes_midi:
            if NoteManager.current_time >= note[1]:
                frequency = NoteManager.get_frequency(note[0])
                block = pyglet.shapes.Rectangle(x=WINDOW_WIDTH, y=frequency, width=40, height= 20, color=(37, 65, 178))
                NoteManager.note_blocks.append(block)
                NoteManager.notes_midi.remove(note)
        last_note = NoteManager.note_blocks[len(NoteManager.note_blocks)-1]
        if last_note.x + last_note.width < 0:
            if not NoteManager.game_finished and len(NoteManager.notes_midi) == 0:
                NoteManager.game_finished = True

    def update_blocks():
        for block in NoteManager.note_blocks:
            block.x -= 10
            block.draw()

    def draw_blocks():
        for block in NoteManager.note_blocks:
            block.draw()

class Player:

    data = []
    stream = None

    def __init__(self):
        audio = pyaudio.PyAudio()
        Player.stream = audio.open(format=pyaudio.paInt16, channels=1,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK_SIZE)
        self.shape = pyglet.shapes.Rectangle(x=10, y=0, width=20, height=20, color=(232, 98, 82))
        #self.shape.opacity = 0

    def updatePlayer(self):
        Player.data = Player.stream.read(CHUNK_SIZE)
        audio_data = np.frombuffer(Player.data, dtype=np.int16)
    
        if np.max(np.abs(audio_data)) > THRESHOLD:
            #print(frequencie)
            fft_data = np.abs(np.fft.fft(audio_data))
        # same as (np.argmax(fft_data)/CHUNK * SAMPLE
            frequency_bins = np.fft.fftfreq(len(fft_data), d=1/RATE)
            major_frequency = np.abs(frequency_bins[np.argmax(fft_data)])
            #print(major_frequency)
            if major_frequency <= 600 - self.shape.height:
                self.shape.y = major_frequency
            else:
                self.shape.y = WINDOW_HEIGHT - self.shape.height - ui.border_width
        else:
            if self.shape.y > ui.border_width:
                self.shape.y -= 10
            else: self.shape.y = ui.border_width

    def get_collision_code(self):
        nice_factor = 15 # you don't have to hit the correct note, because chunk
        for block in NoteManager.note_blocks:
            hit_frequency = (self.shape.y > block.y - nice_factor and 
                self.shape.y + self.shape.height < block.y + block.height + nice_factor)
            if (hit_frequency and 
                self.shape.x > block.x and self.shape.x < block.x + block.width):
                # TODO give points
                #enu.update_score()
                #print("yas")
                return 'hit'
            elif (not hit_frequency and 
                self.shape.x > block.x and self.shape.x < block.x + block.width):
                #print("nopes")
                return 'miss'
        return ''

    def draw(self):
        self.shape.draw()


class UI:

    def __init__(self):
        self.color = (232, 98, 82, 255)
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
        self.feeback.text = 'Nice dude'
        #self.feeback.draw()

    def draw_bad_feedback(self):
        self.feeback.text = 'oooouuuch....'
        #self.feeback.draw()
    
    def draw_end_menu(self):
        if self.score >= 1500:
            self.final_feedback_label.text = 'Wonderful <3'
        elif self.score < 1500 and self.score >= 500:
            self.final_feedback_label.text = 'That\'s okay'
        else:
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
        

player = Player()
ui = UI()

def check_collisions():
    hit = player.get_collision_code()
    if hit == 'hit':
        ui.update_score()
        ui.draw_good_feedback()
    elif hit == 'miss':
        ui.draw_bad_feedback()

@window.event
def on_show():
    NoteManager(midi)

@window.event
def on_key_press(symbol, modifier):         
    if symbol == pyglet.window.key.ESCAPE:
            sys.exit(0)

@window.event
def on_draw():
    window.clear()
    background.blit(0,0)   
    if not NoteManager.game_finished:
        player.updatePlayer()
        check_collisions()
        NoteManager.update_blocks()
        player.draw()
        ui.draw_ui()
    else:
        ui.draw_end_menu()
    ui.draw_border()

clock.schedule_interval(NoteManager.check_notes, 0.1)   

pyglet.app.run()