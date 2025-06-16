from flask import Flask, render_template, request, send_file
import mido
from mido import Message, MidiFile, MidiTrack
import io
import os
import time
import fluidsynth

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def add_track(mid, notes_str, channel, name):
    if not notes_str.strip():
        return

    track = MidiTrack()
    track.append(mido.MetaMessage('track_name', name=name))
    mid.tracks.append(track)

    notes = [int(note.strip()) for note in notes_str.split(',') if note.strip().isdigit()]

    for note in notes:
        track.append(Message('note_on', note=note, velocity=64, time=0, channel=channel))
        track.append(Message('note_off', note=note, velocity=64, time=480, channel=channel))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        bass_notes = request.form['bass']
        drums_notes = request.form['drums']
        guitar_notes = request.form['guitar']
        leads_notes = request.form['leads']
        chords_notes = request.form['chords']
        soundfont = request.files.get('soundfont')

        try:
            mid = MidiFile()

            add_track(mid, bass_notes, channel=0, name='Bass')
            add_track(mid, guitar_notes, channel=1, name='Guitar')
            add_track(mid, leads_notes, channel=2, name='Leads')
            add_track(mid, chords_notes, channel=3, name='Chords')
            add_track(mid, drums_notes, channel=9, name='Drums')

            midi_bytes = io.BytesIO()
            mid.save(file=midi_bytes)
            midi_bytes.seek(0)

            if soundfont and soundfont.filename.endswith('.sf2'):
                sf2_path = os.path.join(app.config['UPLOAD_FOLDER'], soundfont.filename)
                soundfont.save(sf2_path)

                # Optional: Playback using the uploaded SoundFont
                fs = fluidsynth.Synth()
                fs.start(driver="alsa" if os.name == 'posix' else 'dsound')  # Adjust driver if needed
                sfid = fs.sfload(sf2_path)
                fs.program_select(0, sfid, 0, 0)

                midi_bytes.seek(0)
                fs.midi_player_add(midi_bytes)
                time.sleep(5)  # Play 5 seconds (optional demo)

                fs.delete()

                return send_file(
                    midi_bytes,
                    as_attachment=True,
                    download_name='multi_instrument_with_sf2.mid',
                    mimetype='audio/midi'
                )

            else:
                return send_file(
                    midi_bytes,
                    as_attachment=True,
                    download_name='multi_instrument_midi.mid',
                    mimetype='audio/midi'
                )

        except Exception as e:
            return f"Error: {e}"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
