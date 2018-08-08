from mido import MidiFile

class MarkovChain:
    def __init__(self, order):
        self.chain = {}
        self.order = order
    
    def create(self, chords):
        i = self.order

        while i < len(chords):

            current_chord = chords[i]
            previous_chords = []

            for j in range(i - self.order, i):
                previous_chords.append(chords[j])

            add_to_dict(self.chain, self._chords_to_chain_key(previous_chords), self._chord_to_chain_key(current_chord))

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

class Note:
    def __init__(self, note, duration, time):
        self.note = note
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

    for chord in chords:
        print(chord)

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

def create_table(notes):
    table = {}
    for note in notes:
        pass
    return table


chords = read_midi("data/satie_gymnopedie_no1.mid")

chain = MarkovChain(2)
chain.create(chords)
print(chain.chain)