from mido import MidiFile

class Note():
    def __init__(self, note, duration, time):
        self.note = note
        self.duration = round(duration, 3)
        self.time = time
    
    def print(self):
        print("Note: ", self.note, ", duration: ", self.duration, ", start_time: ", self.time)

class MarkovChain():
    def __init__(self, order):
        self.order = order

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
    for note in notes:
        note.print()

    return notes

def create_table(notes):
    table = {}
    for note in notes:
        pass
    return table

read_midi("data/fp-1all.mid")
