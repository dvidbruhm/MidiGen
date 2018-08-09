import numpy

from mido import MidiFile, MidiTrack, Message

class MarkovChain(dict):
    def __init__(self, order):
        self.order = order
    
    def create(self, chords):
        i = self.order

        while i < len(chords):

            current_chord = chords[i]
            previous_chords = []

            for j in range(i - self.order, i):
                previous_chords.append(chords[j])
            
            key = chords_to_key(previous_chords)
            current_chord_key = current_chord.to_key_str()
            
            if key not in self:
                self[key] = {}
            
            if current_chord_key in self[key]:
                self[key][current_chord_key] += 1
            else:
                self[key][current_chord_key] = 1
            
            i += 1

        self._normalize_probs()

    def _chords_to_chain_key(self, chords):
        key = ""
        for chord in chords:
            key += self._chord_to_chain_key(chord) + ":"
        key = key[:-1]
        return key
            
    def _chord_to_chain_key(self, chord):
        key = ""
        for note in chord.notes:
            key += str(note.note) + ","
        key = key[:-1]
        return key

    def _normalize_probs(self):
        for key in self:
            self[key] = { x : self[key][x] / sum(list(self[key].values())) for x in self[key] }

class Chord:
    def __init__(self, notes):
        self.notes = notes

    def add_note(self, note):
        self.notes.append(note)

    def __str__(self):
        formatted_string = str(len(self.notes)) + " notes "

        for note in self.notes:
            formatted_string += " | " + str(note.note) + " , " + str(note.duration) + " , " + str(round(note.time, 2))

        formatted_string += " |"

        return formatted_string

    def to_key_str(self):
        formatted_string = ""
        for note in self.notes:
            formatted_string += str(note.note) + ","
        formatted_string = formatted_string[:-1]
        return formatted_string

    def from_key_str(self, key):
        chords_str = key.split(":")
        print(chords_str)

class Note:
    def __init__(self, note, duration, time):
        self.note = int(note)
        self.duration = round(duration, 3)
        self.time = time

def add_to_dict(dict, key, element):
    if key in dict:
        if element in dict[key]:
            dict[key][element] += 1
        else:
            dict[key][element] = 1
    else:
        dict[key] = {}
        dict[key][element] = 1

def chords_to_key(chords):
    key = ""
    for chord in chords:
        key += chord.to_key_str() + ":"
    key = key[:-1]
    return key       

def clean_track(track, events_to_keep):
    track[:] = [msg for msg in track if msg.type in events_to_keep]
    return track

def print_track(track):
    print("------------------")
    print(track)
    for msg in track:
        print(msg)
    print("------------------")

def read_midi(file_name):
    midi = MidiFile(file_name)
    print("Ticks per second: ", midi.ticks_per_beat)
    notes = []
    for i, track in enumerate(midi.tracks):
        current_time = 0
        
        notes_only_track = clean_track(track, ["note_on", "note_off"])
        for i, msg in enumerate(notes_only_track):
            current_time += msg.time / midi.ticks_per_beat
            if msg.type == "note_on" and msg.velocity != 0:
                current_note = msg.note
                current_note_start_time = current_time
                current_note_stop_time = current_note_start_time
                for j, msg2 in enumerate(notes_only_track[i+1:]):
                    current_note_stop_time += msg2.time / midi.ticks_per_beat
                    if (msg2.note == current_note and msg2.type == "note_off") or \
                       (msg2.note == current_note and msg2.type == "note_on" and msg2.velocity == 0):
                        notes.append(Note(current_note, current_note_stop_time - current_note_start_time, current_note_start_time))
                        break

    print("Number of notes: ", len(notes))
    chords = notes_to_chords(notes)

    #for chord in chords:
    #    print(chord)

    return chords

def notes_to_chords(notes):

    chords = []

    i = 0
    while i < len(notes):

        current_note = notes[i]
        current_chord = Chord([current_note])
        j = i + 1

        if j < len(notes):

            next_note = notes[j]

            while current_note.time == next_note.time:

                current_chord.add_note(next_note)

                if j + 1 < len(notes):
                    j += 1
                    next_note = notes[j]
                else:
                    break

        chords.append(current_chord)

        i = i + len(current_chord.notes)

    return chords

def create_midi_data(markov_chain, nb_notes=100):
    generated_chords = []

    duration = 1
    current_time = 0

    # choose random chords (number of the markov chain order) for the start of the midi
    random_start = numpy.random.choice(list(markov_chain.keys()))
    
    for chord_name in random_start.split(":"):
            
        generated_chords.append(name_to_chord(chord_name, duration, current_time))
        current_time += duration

    for i in range(markov_chain.order, nb_notes):
        previous_chords = []
        
        for j in range(i - markov_chain.order, i):
            previous_chords.append(generated_chords[j])
        
        key = chords_to_key(previous_chords)

        next_chord = numpy.random.choice(list(markov_chain[key].keys()), p=list(markov_chain[key].values()))

        generated_chords.append(name_to_chord(next_chord, duration, current_time))
        current_time += duration

    return generated_chords

def name_to_chord(name, duration, time):
    notes_name = name.split(",")
    notes = []

    for note in notes_name:
        notes.append(Note(note, duration, time)) 
    
    return Chord(notes)

def write_chord(track, chord):
    for note in chord.notes:
        note_number = note.note

        track.append(Message('note_on', note=note_number, velocity=100, time=0))

    i = 0
    for note in chord.notes:
        duration = note.duration
        note_number = note.note
        if i == 0:
            track.append(Message('note_off', note=note_number, velocity=0, time=duration))
        else:
            track.append(Message('note_off', note=note_number, velocity=0, time=duration))
        i += 1


def write_midi(file_name, chords):
    generated_midi = MidiFile()
    generated_midi.ticks_per_beat = 3

    track = MidiTrack()
    generated_midi.tracks.append(track)

    track.append(Message('program_change', program=0, channel=0, time=0))
    track.append(Message('control_change', control=10, channel=0, value=64, time=0))

    for chord in chords:
        write_chord(track, chord)

    generated_midi.save(file_name)
    print("Midi file : ", file_name)

def create_table(notes):
    table = {}
    for note in notes:
        pass
    return table

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))

chords = read_midi("data/chpn_op10_e12.mid")

chain = MarkovChain(2)
chain.create(chords)
chords = create_midi_data(chain)
write_midi('gen/gen.mid', chords)
