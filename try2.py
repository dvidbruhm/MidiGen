import numpy

from mido import MidiFile, MidiTrack, Message

class MarkovChain(dict):
    def __init__(self, order):
        self.order = order
        self.durations = {}
    
    def update(self, chords):
        i = self.order

        while i < len(chords):

            current_chord = chords[i]
            previous_chords = []

            for j in range(i - self.order, i):
                previous_chords.append(chords[j])
            
            chords_note_key, chords_duration_key = chords_to_key(previous_chords)
            current_chord_note_key, current_chord_duration_key = current_chord.to_key()
            

            # Update markov chain for the notes of the chord
            if chords_note_key not in self:
                self[chords_note_key] = {}
           
            if current_chord_note_key in self[chords_note_key]:
                self[chords_note_key][current_chord_note_key] += 1
            else:
                self[chords_note_key][current_chord_note_key] = 1
            
            # Update markov chain for the duration of the chord
            if chords_duration_key not in self.durations:
                self.durations[chords_duration_key] = {}

            if current_chord_duration_key in self.durations[chords_duration_key]:
                self.durations[chords_duration_key][current_chord_duration_key] += 1
            else:
                self.durations[chords_duration_key][current_chord_duration_key] = 1

            i += 1
        
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

    def normalize_probs(self):
        for key in self:
            self[key] = { x : self[key][x] / sum(list(self[key].values())) for x in self[key] }

        for key in self.durations:
            self.durations[key] = { x : self.durations[key][x] / sum(list(self.durations[key].values())) for x in self.durations[key] }

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

    def to_key(self):
        chord_key = ""
        duration_key = str(self.get_mean_duration())
        for note in self.notes:
            chord_key += str(note.note) + ","
        chord_key = chord_key[:-1]
        return chord_key, duration_key

    def from_key_str(self, key):
        chords_str = key.split(":")
        print(chords_str)

    def get_mean_duration(self):
        mean = sum([note.duration for note in self.notes]) / len(self.notes)
        return int(mean)


class Note:
    def __init__(self, note, duration, time):
        self.note = int(note)
        self.duration = int(duration)
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
    note_key = ""
    duration_key = ""
    for chord in chords:
        chord_note_key, chord_duration_key = chord.to_key()
        note_key += chord_note_key + ":"
        duration_key += chord_duration_key + ":"
    note_key = note_key[:-1]
    duration_key = duration_key[:-1]
    return note_key, duration_key

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
            current_time += msg.time / midi.ticks_per_beat * 10
            if msg.type == "note_on" and msg.velocity != 0:
                current_note = msg.note
                current_note_start_time = current_time
                current_note_stop_time = current_note_start_time
                for j, msg2 in enumerate(notes_only_track[i+1:]):
                    current_note_stop_time += msg2.time / midi.ticks_per_beat * 10
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

    current_time = 0

    # choose random chords (number of the markov chain order) for the start of the midi
    random_start = numpy.random.choice(list(markov_chain.keys()))
    random_duration = numpy.random.choice(list(markov_chain.durations.keys()))

    for chord_name, duration in zip(random_start.split(":"), random_duration.split(":")):

        generated_chords.append(name_to_chord(chord_name, int(duration), current_time))
        current_time += float(duration)

    for i in range(markov_chain.order, nb_notes):
        previous_chords = []
        
        for j in range(i - markov_chain.order, i):
            previous_chords.append(generated_chords[j])
        
        note_key, duration_key = chords_to_key(previous_chords)
        
        try:
            next_chord = numpy.random.choice(list(markov_chain[note_key].keys()), p=list(markov_chain[note_key].values()))
            next_duration = numpy.random.choice(list(markov_chain.durations[duration_key].keys()), p=list(markov_chain.durations[duration_key].values()))
        except KeyError as err:
            print("Choosing random chord for : ", i)
            next_chord = numpy.random.choice(list(markov_chain.keys())).split(":")[-1]
            next_duration = numpy.random.choice(list(markov_chain.durations.keys())).split(":")[-1]

        generated_chords.append(name_to_chord(next_chord, int(next_duration), current_time))
        current_time += float(next_duration)

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
            track.append(Message('note_off', note=note_number, velocity=0, time=0))
        i += 1


def write_midi(file_name, chords):
    generated_midi = MidiFile()
    generated_midi.ticks_per_beat = 10

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
         pretty(value, indent+2)
      else:
         print('\t' * (indent+2) + str(value))

chain = MarkovChain(2)

chords = read_midi("data/chpn-p4.mid")
chain.update(chords)

chords = read_midi("data/chpn_op10_e12.mid")
chain.update(chords)

chain.normalize_probs()

chords = create_midi_data(chain)
write_midi('gen/gen.mid', chords)
