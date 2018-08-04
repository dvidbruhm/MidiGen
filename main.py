from mido import MidiFile, MidiTrack, Message
import matplotlib.pyplot as plt
import random
import numpy
import glob

def init():
    
    prob_table = {
        0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        1: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        2: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        3: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        4: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        5: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        6: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        7: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        8: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        9: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        10: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        11: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
    duration_prob = {}
    return prob_table, duration_prob

def print_midi(file):
    midi = MidiFile(file)
    for i, track in enumerate(midi.tracks):
        print('Track {}: {}'.format(i, track.name))
        for msg in track:
            print(msg)

def read_midi(file):
    midi = MidiFile(file)

    tracks_notes = []
    tracks_durations = []
    
    for i, track in enumerate(midi.tracks):
        print('Track {}: {}'.format(i, track.name))
        notes = []
        durations = []
        for msg in track[::2]:
            # print(msg)
            if not msg.is_meta and msg.type == "note_on" or msg.type == "note_off":
                # print(msg)
                notes.append(int(msg.note) % 12)
                durations.append(int(msg.time))
        if len(notes) > 1:
            tracks_notes.append(notes)
            tracks_durations.append(durations)
    print("Nb of tracks : ", len(tracks_notes))
    return tracks_notes, tracks_durations

def update_prob_table(prob_table, duration_prob, tracks_notes, tracks_durations):
    for notes in tracks_notes:
        for i in range(1, len(notes)):
            note = notes[i]
            prev_note = notes[i - 1]
            prob_table[prev_note][note] += 1
    
    for durations in tracks_durations:
        for duration in durations:
            if duration in duration_prob:
                duration_prob[duration] += 1
            else:
                duration_prob[duration] = 1

    duration_prob.pop(0, None)

    durations = list(duration_prob.keys())
    duration_probs = list(duration_prob.values())
    duration_table = [durations, duration_probs]

    return prob_table, duration_table

def print_prob_table(prob_table):
    print("A\tA#\tB\tC\tC#\tD\tD#\tE\tF\tF#\tG\tG#")
    for row in prob_table:
        row_str = ""
        for prob in prob_table[row]:
            row_str += str(round(prob, 2)) + "\t"
        print(row_str)

def normalize_prob_table(prob_table):
    for note in range(len(prob_table)):

        prob_table[note] = [float(i)/sum(prob_table[note]) if sum(prob_table[note]) > 0 else 0 for i in prob_table[note]]
    return prob_table

def normalize_duration_table(duration_table):
    duration_table[1] = [dur/sum(duration_table[1]) for dur in duration_table[1]]
    return duration_table

def create_markov_midi(path, prob_table, duration_table, nb_notes, speed, tracks=1, instrument=0):

    new_song = MidiFile()
    new_song.ticks_per_beat = speed

    for i in range(tracks):
        track = MidiTrack()
        new_song.tracks.append(track)

        track.append(Message('program_change', program=0, channel=0, time=0))
        track.append(Message('control_change', channel=0, control=10, value=64, time=0))

        base_tone = 72
        first_note = random.randint(0, 12)
        track.append(Message('note_on', note=first_note + base_tone, velocity=100, time=0))
        track.append(Message('note_off', note=first_note + base_tone, velocity=0, time=120))

        prev_note = first_note
        for i in range(nb_notes):
            next_note = numpy.random.choice(range(0, 12), p=prob_table[prev_note])
            note_duration = numpy.random.choice(duration_table[0], p=duration_table[1])
            track.append(Message('note_on', note=next_note + base_tone, velocity=100, time=0))
            track.append(Message('note_off', note=next_note + base_tone, velocity=0, time=note_duration))
            prev_note = next_note

    new_song.save("gen/gen.mid")

if __name__ == "__main__":
    prob_table, duration_prob = init()

    for i, file in enumerate(glob.glob("data/satie_gymnopedie_no1.mid")):
        print("\n-------- Midi {} ---------\n".format(i))
        print_midi(file)
        tracks_notes, tracks_durations = read_midi(file)
        prob_table, duration_table = update_prob_table(prob_table, duration_prob, tracks_notes, tracks_durations)

    prob_table = normalize_prob_table(prob_table)
    duration_table = normalize_duration_table(duration_table)
    create_markov_midi("gen/gen.mid", prob_table, duration_table, 100, 240, tracks=1)
    
    print_prob_table(prob_table)
