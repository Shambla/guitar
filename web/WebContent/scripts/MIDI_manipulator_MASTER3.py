"""
MIDI Manipulator - All-in-one: interactive menu + full processing in a single file.
No dependencies on other MIDI_manipulator_* modules. Run with no arguments for the
menu; pass -i / -o and flags for command-line use.
"""

# =============================================================================
# DEPENDENCIES (install before first use)
# =============================================================================
# Python 3.7+. Standard library: argparse, os, sys, typing.
#
# External (pip):
#   pip install mido
#
# That is the only required package. Optional: python-rtmidi for real-time
# MIDI ports (mido works for file read/write without it).
# =============================================================================
# FEATURES (what each menu option does)
# =============================================================================
# 1. Merge all tracks into one
# 2. Min pitch (raise notes below) — e.g. 40 = E2
# 3. Remove unison duplicates
# 4. Remove redundant pitch classes (one note per note name in chords)
# 5. Quantize timing (whole → thirtysecond)
# 6. Auto-number (guitar string or finger labels)
# 7. Process MIDI
# 0. Quit
# =============================================================================
# HOW TO USE
# =============================================================================
# Menu:  python MIDI_manipulator_MASTER3.py
# CLI:   python MIDI_manipulator_MASTER3.py -i input.mid -o output.mid [options]
# Paths with spaces are fine; you can paste the full path.
# =============================================================================

import argparse
import os
import sys
from typing import List, Tuple, Set, Optional

from mido import MidiFile, MidiTrack, Message, MetaMessage, merge_tracks

# Standard six-string guitar tuning (string number, open-string MIDI pitch)
GUITAR_STRINGS: List[Tuple[int, int]] = [
    (6, 40), (5, 45), (4, 50), (3, 55), (2, 59), (1, 64),
]


def merge_all_tracks(mid: MidiFile) -> MidiFile:
    merged = MidiFile(ticks_per_beat=mid.ticks_per_beat)
    merged.tracks.append(merge_tracks(mid.tracks))
    return merged


def lift_notes_below_pitch(track: MidiTrack, min_pitch: int) -> MidiTrack:
    new_track = MidiTrack()
    for msg in track:
        if msg.type in ("note_on", "note_off"):
            note = msg.note
            while note < min_pitch:
                note += 12
                if note > 127:
                    note = 127
                    break
            new_track.append(msg.copy(note=note))
        else:
            new_track.append(msg.copy())
    return new_track


def remove_unison_notes(track: MidiTrack) -> MidiTrack:
    abs_events: List[Tuple[int, Message]] = []
    current_time = 0
    for msg in track:
        current_time += msg.time
        abs_events.append((current_time, msg))
    seen_note_ons: Set[Tuple[int, int, int]] = set()
    kept_events: List[Tuple[int, Message]] = []
    for abs_time, msg in abs_events:
        if msg.type == "note_on" and msg.velocity > 0:
            chan = getattr(msg, "channel", 0)
            key = (abs_time, chan, msg.note)
            if key in seen_note_ons:
                continue
            seen_note_ons.add(key)
            kept_events.append((abs_time, msg))
        else:
            kept_events.append((abs_time, msg))
    kept_events.sort(key=lambda x: (x[0], id(x[1])))
    new_track = MidiTrack()
    prev_time = 0
    for abs_time, msg in kept_events:
        delta = abs_time - prev_time
        if delta < 0:
            delta = 0
        prev_time = abs_time
        new_track.append(msg.copy(time=delta))
    return new_track


def remove_redundant_pitch_classes(track: MidiTrack, time_window_ticks: int = 10) -> MidiTrack:
    abs_events: List[Tuple[int, Message]] = []
    current_time = 0
    for msg in track:
        current_time += msg.time
        abs_events.append((current_time, msg))
    notes_to_remove: Set[int] = set()
    i = 0
    while i < len(abs_events):
        abs_time, msg = abs_events[i]
        if msg.type == "note_on" and msg.velocity > 0:
            simultaneous_notes: List[Tuple[int, Message]] = [(abs_time, msg)]
            j = i + 1
            while j < len(abs_events):
                next_time, next_msg = abs_events[j]
                if next_msg.type == "note_on" and next_msg.velocity > 0:
                    if next_time - abs_time <= time_window_ticks:
                        simultaneous_notes.append((next_time, next_msg))
                        j += 1
                    else:
                        break
                else:
                    j += 1
            seen_pitch_classes: Set[int] = set()
            for _, note_msg in simultaneous_notes:
                pitch_class = note_msg.note % 12
                if pitch_class in seen_pitch_classes:
                    notes_to_remove.add(note_msg.note)
                else:
                    seen_pitch_classes.add(pitch_class)
            i = j
        else:
            i += 1
    kept_events = [(t, m) for t, m in abs_events if m.type not in ("note_on", "note_off") or m.note not in notes_to_remove]
    kept_events.sort(key=lambda x: (x[0], id(x[1])))
    new_track = MidiTrack()
    prev_time = 0
    for abs_time, msg in kept_events:
        delta = abs_time - prev_time
        if delta < 0:
            delta = 0
        prev_time = abs_time
        new_track.append(msg.copy(time=delta))
    return new_track


def compute_guitar_string_and_finger(midi_pitch: int) -> Optional[Tuple[int, int]]:
    for string_num, open_pitch in GUITAR_STRINGS:
        delta = midi_pitch - open_pitch
        if 0 <= delta <= 4:
            return string_num, delta
    return None


def quantize_track(track: MidiTrack, ticks_per_beat: int, quantize_ticks: int) -> MidiTrack:
    finest_grid = max(1, ticks_per_beat // 8)
    abs_events: List[Tuple[int, Message]] = []
    current_time = 0
    for msg in track:
        current_time += msg.time
        abs_events.append((current_time, msg))
    fine_quantized: List[Tuple[int, Message]] = []
    for abs_time, msg in abs_events:
        if msg.type in ("note_on", "note_off"):
            fine_quantized.append((round(abs_time / finest_grid) * finest_grid, msg))
        else:
            fine_quantized.append((abs_time, msg))
    quantized_events: List[Tuple[int, Message]] = []
    for abs_time, msg in fine_quantized:
        if msg.type in ("note_on", "note_off") and quantize_ticks > finest_grid:
            quantized_events.append((round(abs_time / quantize_ticks) * quantize_ticks, msg))
        else:
            quantized_events.append((abs_time, msg))
    quantized_events.sort(key=lambda x: (x[0], id(x[1])))
    new_track = MidiTrack()
    prev_time = 0
    for abs_time, msg in quantized_events:
        delta = abs_time - prev_time
        if delta < 0:
            delta = 0
        prev_time = abs_time
        new_track.append(msg.copy(time=delta))
    return new_track


def compute_basic_guitar_string(midi_pitch: int) -> int:
    for string_num, open_pitch in sorted(GUITAR_STRINGS, key=lambda x: x[1], reverse=True):
        if midi_pitch >= open_pitch:
            return string_num
    return GUITAR_STRINGS[-1][0]


def add_auto_number_annotations(track: MidiTrack, mode: str = "string") -> MidiTrack:
    if mode not in ("string", "finger"):
        raise ValueError(f"Unsupported auto number mode '{mode}'.")
    new_track = MidiTrack()
    for msg in track:
        if msg.type == "note_on" and msg.velocity > 0:
            annotation_text: Optional[str] = None
            if mode == "string":
                annotation_text = str(compute_basic_guitar_string(msg.note))
            else:
                result = compute_guitar_string_and_finger(msg.note)
                if result is not None:
                    annotation_text = str(result[1])
            if annotation_text is not None:
                new_track.append(MetaMessage("text", text=annotation_text, time=msg.time))
                new_track.append(msg.copy(time=0))
                continue
        new_track.append(msg.copy())
    return new_track


def manipulate_midi(
    input_path: str,
    output_path: str,
    min_pitch: Optional[int] = None,
    merge_tracks_flag: bool = False,
    remove_unisons_flag: bool = False,
    remove_redundant_pitch_classes_flag: bool = False,
    quantize: Optional[str] = None,
    auto_number: bool = False,
    auto_number_mode: str = "string",
) -> None:
    mid = MidiFile(input_path)
    if merge_tracks_flag and len(mid.tracks) > 1:
        mid = merge_all_tracks(mid)
    if not mid.tracks:
        raise RuntimeError("No tracks found in input MIDI.")
    track = mid.tracks[0]
    if min_pitch is not None:
        track = lift_notes_below_pitch(track, min_pitch=min_pitch)
    if remove_unisons_flag:
        track = remove_unison_notes(track)
    if remove_redundant_pitch_classes_flag:
        track = remove_redundant_pitch_classes(track)
    if quantize:
        quantize_map = {
            'whole': mid.ticks_per_beat * 4, 'half': mid.ticks_per_beat * 2,
            'quarter': mid.ticks_per_beat, 'eighth': mid.ticks_per_beat // 2,
            'sixteenth': mid.ticks_per_beat // 4, 'thirtysecond': mid.ticks_per_beat // 8,
        }
        if quantize.lower() not in quantize_map:
            raise ValueError(f"Invalid quantize value: {quantize}. Use: {list(quantize_map.keys())}")
        track = quantize_track(track, mid.ticks_per_beat, quantize_map[quantize.lower()])
    if auto_number:
        track = add_auto_number_annotations(track, mode=auto_number_mode)
    new_mid = MidiFile(ticks_per_beat=mid.ticks_per_beat)
    new_mid.tracks.append(track)
    new_mid.save(output_path)


# --- Menu constants and helpers ---
QUANTIZE_CHOICES = ["whole", "half", "quarter", "eighth", "sixteenth", "thirtysecond"]
AUTO_NUMBER_MODES = ["string", "finger"]


def strip_path(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s


def prompt(prompt_text: str, default: str = "") -> str:
    if default:
        result = input(f"{prompt_text} [{default}]: ").strip()
        return strip_path(result) if result else default
    return strip_path(input(f"{prompt_text}: ").strip())


def prompt_int(prompt_text: str, default: Optional[int] = None) -> Optional[int]:
    while True:
        raw = prompt(prompt_text, str(default) if default is not None else "")
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a number (e.g. 40 for E2), or leave blank for none.")


def main_menu() -> None:
    print()
    print("=" * 60)
    print("  MIDI Manipulator - Menu")
    print("=" * 60)
    print()
    print("  How it works: Enter input and output MIDI paths, then choose")
    print("  options (1–6). Option 7 runs processing; 0 quits. You can type")
    print("  several numbers at once (e.g. 1 3 5 7 or 1,3,5,7).")
    print("  Paths with spaces are fine — paste or type the full path.")
    print()

    input_path = prompt("Input MIDI file path")
    if not input_path:
        print("No input file given. Exiting.")
        return
    if not os.path.isfile(input_path):
        print(f"File not found: {input_path}")
        return
    default_out = input_path.rsplit(".", 1)[0] + "_processed.mid" if "." in input_path else input_path + "_processed.mid"
    output_path = strip_path(prompt("Output MIDI file path", default_out))
    if not output_path:
        print("No output file given. Exiting.")
        return

    merge_tracks = False
    min_pitch: Optional[int] = None
    remove_unisons = False
    remove_redundant_pitch_classes = False
    quantize: Optional[str] = None
    auto_number = False
    auto_number_mode = "string"

    while True:
        print()
        print("-" * 60)
        print("  Current settings")
        print("-" * 60)
        print(f"  1. Merge all tracks into one     : {'Yes' if merge_tracks else 'No'}")
        print(f"  2. Min pitch (raise notes below) : {min_pitch if min_pitch is not None else 'Off'}")
        print(f"  3. Remove unison duplicates      : {'Yes' if remove_unisons else 'No'}")
        print(f"  4. Remove redundant pitch classes: {'Yes' if remove_redundant_pitch_classes else 'No'}")
        print(f"  5. Quantize timing               : {quantize or 'Off'}")
        print(f"  6. Auto-number (guitar labels)  : {'Yes' if auto_number else 'No'}")
        if auto_number:
            print(f"     Mode                         : {auto_number_mode}")
        print("-" * 60)
        print("  7. Process MIDI (run with above settings)")
        print("  0. Quit (no processing)")
        print("  You can enter several at once, e.g.  1 3 5 7  or  1,3,5,7")
        print()

        raw = prompt("Choose 1–7 or 0", "7").strip().lower()
        choices = [c for part in raw.replace(",", " ").split() for c in part if c in "01234567"]
        if not choices:
            choices = ["7"]

        for choice in choices:
            if choice == "0":
                print("Exiting.")
                return
            if choice == "1":
                merge_tracks = not merge_tracks
                print(f"  Merge tracks is now: {'Yes' if merge_tracks else 'No'}")
            elif choice == "2":
                print("  Min pitch: notes below this are raised by octaves (e.g. 40 = E2). Leave blank to turn off.")
                min_pitch = prompt_int("  Min pitch (0–127)", min_pitch)
            elif choice == "3":
                remove_unisons = not remove_unisons
                print(f"  Remove unisons is now: {'Yes' if remove_unisons else 'No'}")
            elif choice == "4":
                remove_redundant_pitch_classes = not remove_redundant_pitch_classes
                print(f"  Remove redundant pitch classes is now: {'Yes' if remove_redundant_pitch_classes else 'No'}")
            elif choice == "5":
                if quantize:
                    quantize = None
                    print("  Quantize is now: Off")
                else:
                    q = prompt("  Quantize grid (" + ", ".join(QUANTIZE_CHOICES) + ")", "sixteenth").strip().lower()
                    quantize = q if q in QUANTIZE_CHOICES else None
                    print(f"  Quantize is now: {quantize or 'Off'}")
            elif choice == "6":
                auto_number = not auto_number
                if auto_number:
                    m = prompt("  Auto-number mode (string / finger)", auto_number_mode).strip().lower()
                    if m in AUTO_NUMBER_MODES:
                        auto_number_mode = m
                    print(f"  Auto-number is now: Yes (mode={auto_number_mode})")
                else:
                    print("  Auto-number is now: No")
            elif choice == "7":
                print()
                print("Processing...")
                try:
                    manipulate_midi(
                        input_path=os.path.abspath(input_path),
                        output_path=os.path.abspath(output_path),
                        min_pitch=min_pitch,
                        merge_tracks_flag=merge_tracks,
                        remove_unisons_flag=remove_unisons,
                        remove_redundant_pitch_classes_flag=remove_redundant_pitch_classes,
                        quantize=quantize,
                        auto_number=auto_number,
                        auto_number_mode=auto_number_mode,
                    )
                    print(f"[+] Processed MIDI saved to: {output_path}")
                except Exception as e:
                    print(f"[!] Error: {e}")
                return


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="MIDI Manipulator - Merge tracks, lift pitch, remove unisons, remove redundant pitch classes, quantize, auto-number.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", required=True, help="Input MIDI file path")
    parser.add_argument("--output", "-o", required=True, help="Output MIDI file path")
    parser.add_argument("--min-pitch", type=int, default=None, help="Min MIDI note; notes below raised by octaves (e.g. 40 = E2)")
    parser.add_argument("--merge-tracks", action="store_true", help="Merge all tracks into one")
    parser.add_argument("--remove-unisons", action="store_true", help="Remove unison duplicates")
    parser.add_argument("--remove-redundant-pitch-classes", action="store_true", help="Remove redundant note names in chords")
    parser.add_argument("--quantize", type=str, choices=QUANTIZE_CHOICES, default=None, help="Quantize to grid")
    parser.add_argument("--auto-number", action="store_true", help="Add guitar string/finger labels")
    parser.add_argument("--auto-number-mode", type=str, choices=AUTO_NUMBER_MODES, default="string", help="string or finger")
    args = parser.parse_args()
    manipulate_midi(
        input_path=os.path.abspath(args.input),
        output_path=os.path.abspath(args.output),
        min_pitch=args.min_pitch,
        merge_tracks_flag=args.merge_tracks,
        remove_unisons_flag=args.remove_unisons,
        remove_redundant_pitch_classes_flag=args.remove_redundant_pitch_classes,
        quantize=args.quantize,
        auto_number=args.auto_number,
        auto_number_mode=args.auto_number_mode,
    )
    print(f"[+] Processed MIDI saved to: {args.output}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        main_menu()
