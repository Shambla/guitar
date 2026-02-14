import argparse
import os
from typing import Dict, List, Optional, Set, Callable
from copy import deepcopy

from music21 import converter, stream, note, expressions, articulations


GRID_MAP = {
    "whole": 4.0,
    "half": 2.0,
    "quarter": 1.0,
    "eighth": 0.5,
    "sixteenth": 0.25,
    "thirtysecond": 0.125,
}

DEFAULT_TIME_WINDOW = 0.01  # quarterLength units (~1/32 note in 4/4 at 120 BPM)

# Standard six-string guitar tuning (string number, open-string MIDI pitch)
GUITAR_STRINGS = [
    (6, 40),  # E2
    (5, 45),  # A2
    (4, 50),  # D3
    (3, 55),  # G3
    (2, 59),  # B3
    (1, 64),  # E4
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
        # Use list to avoid modifying while iterating
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
    """
    Add text annotations to notes in the score.

    Args:
        score: The MusicXML score to modify
        text_type: Type of text to add - "lyric", "expression", "fingering", or "articulation"
        text: The text string to add (or None to use default examples)
        filter_func: Optional function(note) -> bool to filter which notes get text
    """
    if text_type == "lyric":
        # Add lyrics to notes (for vocal parts)
        default_text = text or "la"
        for n in score.recurse().notes:
            if filter_func is None or filter_func(n):
                n.addLyric(default_text)

    elif text_type == "expression":
        # Add text expressions (like "con fuoco", "agitato") to measures at note positions
        default_text = text or "con fuoco"
        for part in score.parts:
            for n in part.recurse().notes:
                if filter_func is None or filter_func(n):
                    # Find the measure containing this note
                    measure = n.getContextByClass('Measure')
                    if measure is not None:
                        expr = expressions.TextExpression(default_text)
                        expr.placement = 'above'
                        measure.insert(n.offset, expr)

    elif text_type == "fingering":
        # Add fingering numbers (for guitar/piano)
        default_text = text or "1"
        for n in score.recurse().notes:
            if filter_func is not None and not filter_func(n):
                continue
            fingering = articulations.Fingering(default_text)
            n.articulations.append(fingering)

    elif text_type == "articulation":
        # Add articulation marks (staccato, accent, etc.)
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
                # Add more articulation types as needed


def add_text_by_pitch(
    score: stream.Score,
    pitch_midi: int,
    text: str,
    text_type: str = "expression"
) -> None:
    """Add text to notes matching a specific MIDI pitch."""
    def pitch_filter(n):
        return hasattr(n, 'pitch') and int(round(n.pitch.midi)) == pitch_midi

    add_text_to_notes(score, text_type=text_type, text=text, filter_func=pitch_filter)


def add_text_by_rhythm(
    score: stream.Score,
    offset: float,
    text: str,
    text_type: str = "expression"
) -> None:
    """Add text to notes at a specific rhythmic position."""
    def rhythm_filter(n):
        return abs(n.offset - offset) < 0.01  # Within 1/100 of a quarter note

    add_text_to_notes(score, text_type=text_type, text=text, filter_func=rhythm_filter)


def compute_basic_guitar_string(midi_pitch: int) -> int:
    """
    Basic heuristic: choose the highest string whose open pitch is <= midi_pitch.
    Falls back to string 1 if nothing matches.
    """
    for string_num, open_pitch in sorted(GUITAR_STRINGS, key=lambda x: x[1], reverse=True):
        if midi_pitch >= open_pitch:
            return string_num
    return GUITAR_STRINGS[-1][0]


def compute_guitar_string_and_finger(midi_pitch: int) -> Optional[tuple[int, int]]:
    """
    Return (string_number, finger_number) for first-position guitar fingering.
    Finger numbers follow: 0=open, 1=index, 2=middle, 3=ring, 4=pinky.
    Only handles notes within four semitones above the open string.
    """
    for string_num, open_pitch in GUITAR_STRINGS:
        delta = midi_pitch - open_pitch
        if 0 <= delta <= 4:
            return string_num, delta
    return None


def compute_guitar_string_number(midi_pitch: int) -> int:
    """Backward-compatible wrapper that returns a basic string number for any pitch."""
    return compute_basic_guitar_string(midi_pitch)


def add_auto_number_annotations(
    score: stream.Score,
    mode: str = "string",
) -> None:
    """
    Automatically add numeric annotations to each note.
    Currently supports 'string' mode, which emits guitar string numbers (6→1).
    """
    valid_modes = {"string", "finger"}
    if mode not in valid_modes:
        raise ValueError(f"Unsupported auto number mode '{mode}'. Available modes: {sorted(valid_modes)}")

    for n in score.recurse().notes:
        midi_pitch = int(round(n.pitch.midi))
        if mode == "string":
            string_number = compute_basic_guitar_string(midi_pitch)
            fingering = articulations.Fingering(str(string_number))
            n.articulations.append(fingering)
        elif mode == "finger":
            result = compute_guitar_string_and_finger(midi_pitch)
            if result is None:
                continue
            _, finger = result
            fingering = articulations.Fingering(str(finger))
            n.articulations.append(fingering)


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
            # Add text to all notes
            add_text_to_notes(score, text_type=text_type, text=add_text)

    if auto_number:
        add_auto_number_annotations(score, mode=auto_number_mode)

    save_score(score, output_path)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "MusicXML Manipulator - Apply MIDI-style cleaning steps directly to MusicXML scores:\n"
            "- Merge all parts into one\n"
            "- Raise notes below a minimum pitch by octaves\n"
            "- Remove unison duplicate notes (same pitch, same moment)\n"
            "- Remove redundant pitch classes (same note name in different octaves)\n"
            "- Quantize offsets/durations to standard grids"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove redundant pitch classes only
  %(prog)s -i input.musicxml -o output.musicxml --remove-redundant-pitch-classes

  # Quantize to 16th notes and raise bass notes to guitar range
  %(prog)s -i piano.musicxml -o guitar.musicxml --min-pitch 40 --quantize sixteenth

  # Add text expression to all notes
  %(prog)s -i input.musicxml -o output.musicxml --add-text "con fuoco" --text-type expression

  # Add fingering numbers to notes at middle C (MIDI 60)
  %(prog)s -i input.musicxml -o output.musicxml --add-text "1" --text-type fingering --text-pitch 60

  # Add lyrics to all notes
  %(prog)s -i input.musicxml -o output.musicxml --add-text "la" --text-type lyric

  # Add staccato articulation to all notes
  %(prog)s -i input.musicxml -o output.musicxml --add-text "staccato" --text-type articulation

  # Auto-label string numbers or finger numbers
  %(prog)s -i input.musicxml -o output.musicxml --auto-number --auto-number-mode finger

  # Full pipeline (merge, lift, dedupe, quantize, add text)
  %(prog)s -i input.musicxml -o clean.musicxml --merge-parts --min-pitch 40 \\
    --remove-unisons --remove-redundant-pitch-classes --quantize sixteenth \\
    --add-text "agitato" --text-type expression
        """,
    )
    parser.add_argument("--input", "-i", required=True, help="Input MusicXML file path")
    parser.add_argument("--output", "-o", required=True, help="Output MusicXML file path")
    parser.add_argument(
        "--min-pitch",
        type=int,
        default=None,
        help="Minimum MIDI pitch; notes below this are raised by octaves (e.g., 40 = E2)",
    )
    parser.add_argument(
        "--merge-parts",
        action="store_true",
        help="Merge all parts into a single part before processing",
    )
    parser.add_argument(
        "--remove-unisons",
        action="store_true",
        help="Remove unison duplicate notes (same pitch, channel, time)",
    )
    parser.add_argument(
        "--remove-redundant-pitch-classes",
        action="store_true",
        help="Remove redundant note names (same pitch class in different octaves)",
    )
    parser.add_argument(
        "--quantize",
        type=str,
        choices=list(GRID_MAP.keys()),
        default=None,
        help="Quantize offsets/durations to the specified grid",
    )
    parser.add_argument(
        "--add-text",
        type=str,
        default=None,
        help="Add text annotation to notes (e.g., 'con fuoco', '1', 'la'). Use with --text-type",
    )
    parser.add_argument(
        "--text-type",
        type=str,
        choices=["lyric", "expression", "fingering", "articulation"],
        default="expression",
        help="Type of text to add: lyric (vocal), expression (musical terms), fingering (numbers), or articulation (marks)",
    )
    parser.add_argument(
        "--text-pitch",
        type=int,
        default=None,
        help="Only add text to notes with this MIDI pitch (e.g., 60 for middle C)",
    )
    parser.add_argument(
        "--text-offset",
        type=float,
        default=None,
        help="Only add text to notes at this offset position (in quarter notes, e.g., 0.0 for first beat)",
    )
    parser.add_argument(
        "--auto-number",
        action="store_true",
        help="Automatically annotate notes with guitar string numbers (6→1) inspired by the Sibelius fingering scripts in this repo",
    )
    parser.add_argument(
        "--auto-number-mode",
        type=str,
        choices=["string", "finger"],
        default="string",
        help="Mode for automatic numbering: 'string' (6→1) or 'finger' (0=open, 1–4 fretted)",
    )

    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)

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
    main()
