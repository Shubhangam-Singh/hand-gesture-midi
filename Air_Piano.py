import cv2
import threading
import pygame.midi
import time
from cvzone.HandTrackingModule import HandDetector

# Initialize Pygame MIDI
pygame.midi.init()

# ======= CHANGE THIS: Choose the correct MIDI output device ID =======
# Usually 0 or 1 based on your system's MIDI device list.
midi_output_id = 0  # Try 1 if 0 gives errors

player = pygame.midi.Output(midi_output_id)

# ======= CHANGE THIS: Set MIDI instrument (0 = Acoustic Grand Piano) =======
instrument_id = 0
player.set_instrument(instrument_id)

# Initialize Webcam and Hand Detector
cap = cv2.VideoCapture(0)
detector = HandDetector(detectionCon=0.8, maxHands=2)

# Chord Mapping (D Major Scale) - Change notes here if you want different chords
chords = {
    "left": {
        "thumb": [62, 66, 69],   # D Major chord notes (MIDI numbers)
        "index": [64, 67, 71],   # E Minor
        "middle": [66, 69, 73],  # F# Minor
        "ring": [67, 71, 74],    # G Major
        "pinky": [69, 73, 76]    # A Major
    },
    "right": {
        "thumb": [62, 66, 69],
        "index": [64, 67, 71],
        "middle": [66, 69, 73],
        "ring": [67, 71, 74],
        "pinky": [69, 73, 76]
    }
}

# Sustain duration in seconds - how long the notes will play after you release finger
SUSTAIN_TIME = 2.0

# Track previous finger states to detect when fingers go up or down
prev_states = {hand: {finger: 0 for finger in chords[hand]} for hand in chords}

# Play a chord by turning on all notes
def play_chord(chord_notes):
    for note in chord_notes:
        player.note_on(note, 127)  # velocity 127 = max volume

# Stop a chord by turning off all notes after delay
def stop_chord_after_delay(chord_notes):
    time.sleep(SUSTAIN_TIME)
    for note in chord_notes:
        player.note_off(note, 127)

# Main loop
while True:
    success, img = cap.read()
    if not success:
        print("❌ Could not capture webcam.")
        continue

    hands, img = detector.findHands(img)

    if hands:
        for hand in hands:
            hand_type = "left" if hand["type"] == "Left" else "right"
            fingers = detector.fingersUp(hand)
            finger_names = ["thumb", "index", "middle", "ring", "pinky"]

            for i, finger in enumerate(finger_names):
                if finger in chords[hand_type]:
                    # Finger is now up and was previously down
                    if fingers[i] == 1 and prev_states[hand_type][finger] == 0:
                        play_chord(chords[hand_type][finger])
                    # Finger is now down and was previously up
                    elif fingers[i] == 0 and prev_states[hand_type][finger] == 1:
                        threading.Thread(
                            target=stop_chord_after_delay,
                            args=(chords[hand_type][finger],),
                            daemon=True
                        ).start()
                    prev_states[hand_type][finger] = fingers[i]
    else:
        # No hands detected — stop all chords
        for hand in chords:
            for finger in chords[hand]:
                threading.Thread(
                    target=stop_chord_after_delay,
                    args=(chords[hand][finger],),
                    daemon=True
                ).start()
        prev_states = {hand: {finger: 0 for finger in chords[hand]} for hand in chords}

    cv2.imshow("Air Piano 🎹", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup on exit
cap.release()
cv2.destroyAllWindows()
pygame.midi.quit()