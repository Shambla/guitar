"""
MusicXML Manipulator - All-in-one: interactive menu + full processing in a single file.
No dependencies on other MIDI_manipulator_* modules. Run with no arguments for the
menu; pass -i / -o and flags for command-line use.
"""

# =============================================================================
# DEPENDENCIES (install before first use)
# =============================================================================
# Python 3.7+. Standard library: argparse, copy, os, sys, typing.
#
# External (pip):
#   pip install music21
#
# That is the only required package. music21 reads/writes MusicXML and many
# other formats.
# =============================================================================
# PATHS WITH SPACES OR QUOTES
# =============================================================================
# File paths often contain spaces (e.g. "My Song.musicxml"). This script handles
# them: when you type or paste a path in the menu, spaces are preserved and
# surrounding quotes are stripped, so you can paste paths like:
#   /Users/me/My Folder/My Song.musicxml
#   "C:\Documents\My Song.xml"
# Do not run the path as a shell command; enter it only when the script asks
# for "Input MusicXML file path" or "Output MusicXML file path".
# =============================================================================
# FEATURES (menu options 1–8, 0)
# =============================================================================
# 1. Merge all parts into one
# 2. Min pitch (raise notes below) — e.g. 40 = E2
# 3. Remove unison duplicates
# 4. Remove redundant pitch classes (one note per note name in chords)
# 5. Quantize timing (whole → thirtysecond)
# 6. Add text annotations (lyric, expression, fingering, articulation)
# 7. Auto-number (guitar string or finger labels)
# 8. Process MusicXML
# 0. Quit
# =============================================================================
# HOW TO USE
# =============================================================================
# Menu:  python MIDI_manipulator_XML_MASTER3.py
# CLI:   python MIDI_manipulator_XML_MASTER3.py -i input.musicxml -o output.musicxml [options]
# =============================================================================

import argparse
import os
import sys
from copy import deepcopy
from typing import Callable, Dict, List, Optional, Set, Tuple

from music21 import converter, stream, note, expressions, articulations


GRID_MAP = {
    "whole": 4.0,
    "half": 2.0,
    "quarter": 1.0,
    "eighth": 0.5,
    "sixteenth": 0.25,
    "thirtysecond": 0.125,
}

DEFAULT_TIME_WINDOW = 0.01

GUITAR_STRINGS: List[Tuple[int, int]] = [
    (6, 40), (5, 45), (4, 50), (3, 55), (2, 59), (1, 64),
]


def load_score(path: str) -> stream.Score:
    return converter.parse(path)


def save_score(score: stream.Score, path: str) -> None:
    score.write("musicxml", fp=path)


def merge_parts(score: stream.Score) -> stream.Score:
    merged_score = stream.Score()
    merged_part = stream.Part()
    for part in score.parts:
        for elem in part.flat.notesAndRests:
            merged_part.insert(elem.offset, deepcopy(elem))
    if score.metadata:
        merged_score.insert(0, score.metadata)
    merged_score.append(merged_part)
    return merged_score


def lift_notes_below_pitch(score: stream.Score, min_pitch: int) -> None:
    for n in score.recurse().notes:
        while n.pitch.midi < min_pitch:
            n.pitch.midi = min(n.pitch.midi + 12, 127)


def _group_notes_by_time(part: stream.Part, time_window: float) -> Dict[int, List[note.Note]]:
    buckets: Dict[int, List[note.Note]] = {}
    for n in part.recurse().notes:
        key = round(n.offset / time_window)
        buckets.setdefault(key, []).append(n)
    return buckets


def _remove_element(elem) -> None:
    parent = elem.activeSite
    if parent is not None:
        parent.remove(elem, failSilently=True)


def remove_unison_notes(score: stream.Score, time_window: float = DEFAULT_TIME_WINDOW) -> None:
    for part in score.parts:
        buckets = _group_notes_by_time(part, time_window)
        for notes_at_time in buckets.values():
            seen: Set[int] = set()
            for n in sorted(notes_at_time, key=lambda x: (x.offset, x.pitch.midi)):
                midi_pitch = int(round(n.pitch.midi))
                if midi_pitch in seen:
                    _remove_element(n)
                else:
                    seen.add(midi_pitch)


def remove_redundant_pitch_classes(
    score: stream.Score, time_window: float = DEFAULT_TIME_WINDOW
) -> None:
    for part in score.parts:
        buckets = _group_notes_by_time(part, time_window)
        for notes_at_time in buckets.values():
            seen_classes: Set[int] = set()
            for n in sorted(notes_at_time, key=lambda x: (x.offset, x.pitch.midi)):
                pitch_class = n.pitch.pitchClass
                if pitch_class in seen_classes:
                    _remove_element(n)
                else:
                    seen_classes.add(pitch_class)


def quantize_score(score: stream.Score, grid_label: str) -> None:
    grid = GRID_MAP[grid_label]
    eps = 1e-6
    for part in score.parts:
        for n in list(part.recurse().notesAndRests):
            if n.duration.isGrace:
                continue
            parent = n.activeSite
            if parent is None:
                continue
            old_offset = n.offset
            new_offset = round(old_offset / grid) * grid
            if abs(new_offset - old_offset) > eps:
                parent.remove(n, failSilently=True)
                parent.insert(new_offset, n)
            new_duration = max(grid, round(n.quarterLength / grid) * grid)
            n.quarterLength = new_duration


def add_text_to_notes(
    score: stream.Score,
    text_type: str = "expression",
    text: Optional[str] = None,
    filter_func: Optional[Callable] = None,
) -> None:
    if text_type == "lyric":
        default_text = text or "la"
        for n in score.recurse().notes:
            if filter_func is None or filter_func(n):
                n.addLyric(default_text)
    elif text_type == "expression":
        default_text = text or "con fuoco"
        for part in score.parts:
            for n in part.recurse().notes:
                if filter_func is None or filter_func(n):
                    measure = n.getContextByClass('Measure')
                    if measure is not None:
                        expr = expressions.TextExpression(default_text)
                        expr.placement = 'above'
                        measure.insert(n.offset, expr)
    elif text_type == "fingering":
        default_text = text or "1"
        for n in score.recurse().notes:
            if filter_func is not None and not filter_func(n):
                continue
            fingering = articulations.Fingering(default_text)
            n.articulations.append(fingering)
    elif text_type == "articulation":
        articulation_type = text or "staccato"
        for n in score.recurse().notes:
            if filter_func is None or filter_func(n):
                if articulation_type.lower() == "staccato":
                    n.articulations.append(articulations.Staccato())
                elif articulation_type.lower() == "accent":
                    n.articulations.append(articulations.Accent())
                elif articulation_type.lower() == "tenuto":
                    n.articulations.append(articulations.Tenuto())
                elif articulation_type.lower() == "fermata":
                    n.articulations.append(articulations.Fermata())


def add_text_by_pitch(
    score: stream.Score,
    pitch_midi: int,
    text: str,
    text_type: str = "expression",
) -> None:
    def pitch_filter(n):
        return hasattr(n, 'pitch') and int(round(n.pitch.midi)) == pitch_midi
    add_text_to_notes(score, text_type=text_type, text=text, filter_func=pitch_filter)


def add_text_by_rhythm(
    score: stream.Score,
    offset: float,
    text: str,
    text_type: str = "expression",
) -> None:
    def rhythm_filter(n):
        return abs(n.offset - offset) < 0.01
    add_text_to_notes(score, text_type=text_type, text=text, filter_func=rhythm_filter)


def compute_basic_guitar_string(midi_pitch: int) -> int:
    for string_num, open_pitch in sorted(GUITAR_STRINGS, key=lambda x: x[1], reverse=True):
        if midi_pitch >= open_pitch:
            return string_num
    return GUITAR_STRINGS[-1][0]


def compute_guitar_string_and_finger(midi_pitch: int) -> Optional[Tuple[int, int]]:
    for string_num, open_pitch in GUITAR_STRINGS:
        delta = midi_pitch - open_pitch
        if 0 <= delta <= 4:
            return string_num, delta
    return None


def add_auto_number_annotations(score: stream.Score, mode: str = "string") -> None:
    if mode not in ("string", "finger"):
        raise ValueError(f"Unsupported auto number mode '{mode}'.")
    for n in score.recurse().notes:
        midi_pitch = int(round(n.pitch.midi))
        if mode == "string":
            string_number = compute_basic_guitar_string(midi_pitch)
            n.articulations.append(articulations.Fingering(str(string_number)))
        elif mode == "finger":
            result = compute_guitar_string_and_finger(midi_pitch)
            if result is None:
                continue
            _, finger = result
            n.articulations.append(articulations.Fingering(str(finger)))


def manipulate_musicxml(
    input_path: str,
    output_path: str,
    min_pitch: Optional[int] = None,
    merge_parts_flag: bool = False,
    remove_unisons_flag: bool = False,
    remove_redundant_pitch_classes_flag: bool = False,
    quantize: Optional[str] = None,
    add_text: Optional[str] = None,
    text_type: str = "expression",
    text_pitch: Optional[int] = None,
    text_offset: Optional[float] = None,
    auto_number: bool = False,
    auto_number_mode: str = "string",
) -> None:
    score = load_score(input_path)
    if merge_parts_flag:
        score = merge_parts(score)
    if min_pitch is not None:
        lift_notes_below_pitch(score, min_pitch=min_pitch)
    if remove_unisons_flag:
        remove_unison_notes(score)
    if remove_redundant_pitch_classes_flag:
        remove_redundant_pitch_classes(score)
    if quantize:
        if quantize.lower() not in GRID_MAP:
            raise ValueError(f"Invalid quantize value: {quantize}. Use: {list(GRID_MAP.keys())}")
        quantize_score(score, quantize.lower())
    if add_text:
        if text_pitch is not None:
            add_text_by_pitch(score, text_pitch, add_text, text_type)
        elif text_offset is not None:
            add_text_by_rhythm(score, text_offset, add_text, text_type)
        else:
            add_text_to_notes(score, text_type=text_type, text=add_text)
    if auto_number:
        add_auto_number_annotations(score, mode=auto_number_mode)
    save_score(score, output_path)


# --- Menu constants and path helpers (handle spaces and quoted paths) ---
QUANTIZE_CHOICES = ["whole", "half", "quarter", "eighth", "sixteenth", "thirtysecond"]
AUTO_NUMBER_MODES = ["string", "finger"]
TEXT_TYPES = ["lyric", "expression", "fingering", "articulation"]


def strip_path(s: str) -> str:
    """Strip whitespace and surrounding quotes so paths with spaces work when pasted."""
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


def prompt_float(prompt_text: str, default: Optional[float] = None) -> Optional[float]:
    while True:
        raw = prompt(prompt_text, str(default) if default is not None else "")
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a number (e.g. 0.0 for first beat), or leave blank for none.")


def main_menu() -> None:
    print()
    print("=" * 60)
    print("  MusicXML Manipulator - Menu")
    print("=" * 60)
    print()
    print("  How it works: Enter input and output MusicXML paths, then choose")
    print("  options (1–7). Option 8 runs processing; 0 quits. You can type")
    print("  several numbers at once (e.g. 1 3 5 8 or 1,3,5,8).")
    print("  Paths with spaces are fine — paste or type the full path.")
    print()

    input_path = prompt("Input MusicXML file path")
    if not input_path:
        print("No input file given. Exiting.")
        return
    if not os.path.isfile(input_path):
        print(f"File not found: {input_path}")
        return
    base, _ = os.path.splitext(input_path)
    default_out = base + "_processed.musicxml"
    output_path = strip_path(prompt("Output MusicXML file path", default_out))
    if not output_path:
        print("No output file given. Exiting.")
        return

    merge_parts = False
    min_pitch: Optional[int] = None
    remove_unisons = False
    remove_redundant_pitch_classes = False
    quantize: Optional[str] = None
    add_text: Optional[str] = None
    text_type = "expression"
    text_pitch: Optional[int] = None
    text_offset: Optional[float] = None
    auto_number = False
    auto_number_mode = "string"

    while True:
        print()
        print("-" * 60)
        print("  Current settings")
        print("-" * 60)
        print(f"  1. Merge all parts into one      : {'Yes' if merge_parts else 'No'}")
        print(f"  2. Min pitch (raise notes below) : {min_pitch if min_pitch is not None else 'Off'}")
        print(f"  3. Remove unison duplicates      : {'Yes' if remove_unisons else 'No'}")
        print(f"  4. Remove redundant pitch classes : {'Yes' if remove_redundant_pitch_classes else 'No'}")
        print(f"  5. Quantize timing               : {quantize or 'Off'}")
        print(f"  6. Add text annotations          : {add_text or 'Off'}")
        if add_text:
            print(f"     Type / pitch / offset          : {text_type} / {text_pitch} / {text_offset}")
        print(f"  7. Auto-number (guitar labels)   : {'Yes' if auto_number else 'No'}")
        if auto_number:
            print(f"     Mode                          : {auto_number_mode}")
        print("-" * 60)
        print("  8. Process MusicXML (run with above settings)")
        print("  0. Quit (no processing)")
        print("  You can enter several at once, e.g.  1 3 5 8  or  1,3,5,8")
        print()

        raw = prompt("Choose 1–8 or 0", "8").strip().lower()
        choices = [c for part in raw.replace(",", " ").split() for c in part if c in "012345678"]
        if not choices:
            choices = ["8"]

        for choice in choices:
            if choice == "0":
                print("Exiting.")
                return
            if choice == "1":
                merge_parts = not merge_parts
                print(f"  Merge parts is now: {'Yes' if merge_parts else 'No'}")
            elif choice == "2":
                print("  Min pitch: notes below this MIDI note are raised by octaves.")
                print("  Example: 40 = E2 (low E on guitar). Leave blank to turn off.")
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
                if add_text:
                    add_text = None
                    text_pitch = None
                    text_offset = None
                    print("  Add text is now: Off")
                else:
                    add_text = prompt("  Text to add (e.g. 'con fuoco', 'la', '1')", "con fuoco").strip() or "con fuoco"
                    print("  Types: " + ", ".join(TEXT_TYPES))
                    tt = prompt("  Text type", text_type).strip().lower()
                    if tt in TEXT_TYPES:
                        text_type = tt
                    text_pitch = prompt_int("  Only at MIDI pitch (blank = all notes)", None)
                    text_offset = prompt_float("  Only at offset in quarter notes (blank = all)", None)
                    print(f"  Add text is now: '{add_text}' (type={text_type})")
            elif choice == "7":
                auto_number = not auto_number
                if auto_number:
                    print("  Mode: 'string' = string numbers 6–1, 'finger' = 0=open, 1–4 fretted")
                    m = prompt("  Auto-number mode", auto_number_mode).strip().lower()
                    if m in AUTO_NUMBER_MODES:
                        auto_number_mode = m
                    print(f"  Auto-number is now: Yes (mode={auto_number_mode})")
                else:
                    print("  Auto-number is now: No")
            elif choice == "8":
                print()
                print("Processing...")
                try:
                    manipulate_musicxml(
                        input_path=os.path.abspath(input_path),
                        output_path=os.path.abspath(output_path),
                        min_pitch=min_pitch,
                        merge_parts_flag=merge_parts,
                        remove_unisons_flag=remove_unisons,
                        remove_redundant_pitch_classes_flag=remove_redundant_pitch_classes,
                        quantize=quantize,
                        add_text=add_text,
                        text_type=text_type,
                        text_pitch=text_pitch,
                        text_offset=text_offset,
                        auto_number=auto_number,
                        auto_number_mode=auto_number_mode,
                    )
                    print(f"[+] Processed MusicXML saved to: {output_path}")
                except Exception as e:
                    print(f"[!] Error: {e}")
                return


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="MusicXML Manipulator - Merge parts, lift pitch, remove unisons, remove redundant pitch classes, quantize, add text, auto-number.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", required=True, help="Input MusicXML file path")
    parser.add_argument("--output", "-o", required=True, help="Output MusicXML file path")
    parser.add_argument("--min-pitch", type=int, default=None, help="Min MIDI pitch; notes below raised by octaves (e.g. 40 = E2)")
    parser.add_argument("--merge-parts", action="store_true", help="Merge all parts into one")
    parser.add_argument("--remove-unisons", action="store_true", help="Remove unison duplicates")
    parser.add_argument("--remove-redundant-pitch-classes", action="store_true", help="Remove redundant note names in chords")
    parser.add_argument("--quantize", type=str, choices=list(GRID_MAP.keys()), default=None, help="Quantize to grid")
    parser.add_argument("--add-text", type=str, default=None, help="Add text to notes")
    parser.add_argument("--text-type", type=str, choices=TEXT_TYPES, default="expression", help="lyric, expression, fingering, articulation")
    parser.add_argument("--text-pitch", type=int, default=None, help="Only add text to this MIDI pitch")
    parser.add_argument("--text-offset", type=float, default=None, help="Only add text at this offset (quarter notes)")
    parser.add_argument("--auto-number", action="store_true", help="Add guitar string/finger labels")
    parser.add_argument("--auto-number-mode", type=str, choices=AUTO_NUMBER_MODES, default="string", help="string or finger")
    args = parser.parse_args()
    input_path = strip_path(os.path.abspath(args.input))
    output_path = strip_path(os.path.abspath(args.output))
    manipulate_musicxml(
        input_path=input_path,
        output_path=output_path,
        min_pitch=args.min_pitch,
        merge_parts_flag=args.merge_parts,
        remove_unisons_flag=args.remove_unisons,
        remove_redundant_pitch_classes_flag=args.remove_redundant_pitch_classes,
        quantize=args.quantize,
        add_text=args.add_text,
        text_type=args.text_type,
        text_pitch=args.text_pitch,
        text_offset=args.text_offset,
        auto_number=args.auto_number,
        auto_number_mode=args.auto_number_mode,
    )
    print(f"[+] Processed MusicXML saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        main_menu()
