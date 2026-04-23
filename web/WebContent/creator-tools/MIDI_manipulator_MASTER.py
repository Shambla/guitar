import argparse
import os
from typing import List, Tuple, Set, Optional

from mido import MidiFile, MidiTrack, Message, MetaMessage, merge_tracks


def _ticks_per_measure(ticks_per_beat: int, numerator: int, denominator: int) -> int:
    """MIDI quarter = ticks_per_beat; notated time sig nn/dd → length of one bar in ticks."""
    if denominator <= 0:
        denominator = 4
    return max(1, int(round(ticks_per_beat * numerator * 4 / denominator)))


def _collect_time_signatures(abs_events: List[Tuple[int, Message]]) -> List[Tuple[int, int, int]]:
    """Sorted (tick, numerator, denominator) from time_signature meta; default 4/4 at 0."""
    sigs: List[Tuple[int, int, int]] = []
    for t, m in abs_events:
        if m.type == "time_signature":
            sigs.append((t, int(m.numerator), int(m.denominator)))
    sigs.sort(key=lambda x: x[0])
    if not sigs or sigs[0][0] > 0:
        sigs.insert(0, (0, 4, 4))
    return sigs


def _time_sig_at(sigs: List[Tuple[int, int, int]], tick: int) -> Tuple[int, int]:
    cur = (4, 4)
    for t, nn, dd in sigs:
        if t <= tick:
            cur = (nn, dd)
    return cur


def _build_measure_ranges(
    ticks_per_beat: int,
    end_tick: int,
    sigs: List[Tuple[int, int, int]],
) -> List[Tuple[int, int]]:
    """List of [start, end) measure boundaries in original tick space, through end_tick."""
    ranges: List[Tuple[int, int]] = []
    cur = 0
    guard = 0
    max_measures = max(1, end_tick + 1) * 4  # avoid infinite loop if ml broken
    while cur < end_tick and guard < max_measures:
        nn, dd = _time_sig_at(sigs, cur)
        ml = _ticks_per_measure(ticks_per_beat, nn, dd)
        nxt = cur + ml
        ranges.append((cur, nxt))
        cur = nxt
        guard += 1
    return ranges


def _four_bar_rubato_map_tick_float(
    old_tick: float,
    measure_ranges: List[Tuple[int, int]],
    slow_factor: float,
) -> float:
    """
    Piecewise linear map: measures with index ≡ 0 or 3 (mod 4) stretch by slow_factor;
    others keep factor 1. Bar 1,4,5,8,9,… slower; bars 2–3, 6–7,… nominal.
    """
    if not measure_ranges:
        return old_tick

    prefix: List[float] = [0.0]
    for i, (start, end) in enumerate(measure_ranges):
        length = end - start
        s = slow_factor if (i % 4) in (0, 3) else 1.0
        prefix.append(prefix[-1] + length * s)

    for i, (start, end) in enumerate(measure_ranges):
        if old_tick < end:
            s = slow_factor if (i % 4) in (0, 3) else 1.0
            return prefix[i] + (old_tick - start) * s

    i = len(measure_ranges) - 1
    start, end = measure_ranges[i]
    s = slow_factor if (i % 4) in (0, 3) else 1.0
    return prefix[i] + (old_tick - start) * s


def four_bar_rubato_track(
    track: MidiTrack,
    ticks_per_beat: int,
    slow_bpm_delta: float = 3.0,
    reference_bpm: float = 120.0,
) -> MidiTrack:
    """
    Apply a repeating 4-bar rubato by locally stretching time (not inserting tempo events):
    bar 1 and 4 of each group slower, bars 2–3 at nominal speed.

    The *knobs* are in BPM (not score symbols / note shapes): slow bars are interpreted as
    ``reference_bpm - slow_bpm_delta`` BPM vs ``reference_bpm``, i.e. stretch factor
    ``reference_bpm / (reference_bpm - slow_bpm_delta)``. Playback uses tick spacing only;
    the file is not given new tempo meta events spelling out BPM.

    All events (notes + meta) move on the same timeline so playback stays coherent.
    """
    if slow_bpm_delta <= 0:
        raise ValueError("slow_bpm_delta must be > 0")
    if slow_bpm_delta >= reference_bpm - 1:
        raise ValueError("slow_bpm_delta must be less than reference_bpm - 1")

    slow_factor = float(reference_bpm) / (float(reference_bpm) - float(slow_bpm_delta))

    abs_events: List[Tuple[int, Message]] = []
    current_time = 0
    for msg in track:
        current_time += msg.time
        abs_events.append((current_time, msg))

    if not abs_events:
        return MidiTrack()

    max_tick = max(t for t, _ in abs_events)
    sigs = _collect_time_signatures(abs_events)
    measure_ranges = _build_measure_ranges(ticks_per_beat, max_tick + 1, sigs)

    warped_f: List[Tuple[float, Message]] = []
    for abs_t, msg in abs_events:
        new_t = _four_bar_rubato_map_tick_float(float(abs_t), measure_ranges, slow_factor)
        warped_f.append((new_t, msg))

    warped_f.sort(key=lambda x: (x[0], id(x[1])))

    new_track = MidiTrack()
    prev_rounded = 0
    for abs_f, msg in warped_f:
        r = int(round(abs_f))
        if r < prev_rounded:
            r = prev_rounded
        delta = r - prev_rounded
        prev_rounded = r
        new_track.append(msg.copy(time=delta))
    return new_track

# Standard six-string guitar tuning (string number, open-string MIDI pitch)
GUITAR_STRINGS: List[Tuple[int, int]] = [
    (6, 40),  # E2
    (5, 45),  # A2
    (4, 50),  # D3
    (3, 55),  # G3
    (2, 59),  # B3
    (1, 64),  # E4
]


def merge_all_tracks(mid: MidiFile) -> MidiFile:
    """
    Merge all tracks in a MIDI file into a single track.
    Meta events (tempo, time signature, etc.) are preserved in order.
    """
    merged = MidiFile(ticks_per_beat=mid.ticks_per_beat)
    merged_track = merge_tracks(mid.tracks)
    merged.tracks.append(merged_track)
    return merged


def lift_notes_below_pitch(track: MidiTrack, min_pitch: int) -> MidiTrack:
    """
    Raise any note_on/note_off note numbers below min_pitch by octaves (12 semitones)
    until they are >= min_pitch.
    """
    new_track = MidiTrack()
    for msg in track:
        if msg.type in ("note_on", "note_off"):
            note = msg.note
            while note < min_pitch:
                note += 12
                if note > 127:
                    note = 127
                    break
            new_msg = msg.copy(note=note)
            new_track.append(new_msg)
        else:
            new_track.append(msg.copy())
    return new_track


def remove_unison_notes(track: MidiTrack) -> MidiTrack:
    """
    Remove duplicate unison note_on events (same abs_time, channel, note).
    We keep the first note_on and drop subsequent duplicates; note_off messages
    are left as-is, which is harmless when they coincide in time.
    """
    # Convert to absolute time events
    abs_events: List[Tuple[int, Message]] = []
    current_time = 0
    for msg in track:
        current_time += msg.time
        abs_events.append((current_time, msg))

    seen_note_ons: Set[Tuple[int, int, int]] = set()  # (abs_time_ticks, channel, note)
    kept_events: List[Tuple[int, Message]] = []

    for abs_time, msg in abs_events:
        if msg.type == "note_on" and msg.velocity > 0:
            chan = getattr(msg, "channel", 0)
            key = (abs_time, chan, msg.note)
            if key in seen_note_ons:
                # Skip duplicate unison note
                continue
            seen_note_ons.add(key)
            kept_events.append((abs_time, msg))
        else:
            kept_events.append((abs_time, msg))

    # Rebuild track with delta times
    new_track = MidiTrack()
    prev_time = 0
    for abs_time, msg in kept_events:
        delta = abs_time - prev_time
        prev_time = abs_time
        new_msg = msg.copy(time=delta)
        new_track.append(new_msg)

    return new_track


def remove_redundant_pitch_classes(track: MidiTrack, time_window_ticks: int = 10) -> MidiTrack:
    """
    Remove redundant note names in chords (same pitch class in different octaves).
    For example, if a chord has Bb3 and Bb4 at the same time, keep only one.
    Also removes corresponding note_off events for removed notes.
    
    time_window_ticks: Notes within this many ticks are considered simultaneous (default 10)
    """
    # Convert to absolute time events
    abs_events: List[Tuple[int, Message]] = []
    current_time = 0
    for msg in track:
        current_time += msg.time
        abs_events.append((current_time, msg))
    
    # Track which notes to remove (by MIDI note number)
    notes_to_remove: Set[int] = set()
    
    # First pass: identify redundant pitch classes in simultaneous chords
    i = 0
    while i < len(abs_events):
        abs_time, msg = abs_events[i]
        
        # If it's a note_on event, check for simultaneous notes
        if msg.type == "note_on" and msg.velocity > 0:
            # Find all notes in the same time window
            simultaneous_notes: List[Tuple[int, Message]] = [(abs_time, msg)]
            j = i + 1
            
            # Collect all notes within the time window
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
            
            # Group by pitch class (note name modulo 12)
            # Keep only one note per pitch class (prefer the first one encountered)
            seen_pitch_classes: Set[int] = set()
            for note_time, note_msg in simultaneous_notes:
                pitch_class = note_msg.note % 12  # 0-11 (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
                
                if pitch_class not in seen_pitch_classes:
                    # First occurrence of this pitch class - keep it
                    seen_pitch_classes.add(pitch_class)
                else:
                    # Duplicate pitch class - mark for removal
                    notes_to_remove.add(note_msg.note)
            
            # Move past all simultaneous notes we just processed
            i = j
        else:
            i += 1
    
    # Second pass: filter out removed notes (both note_on and note_off)
    kept_events: List[Tuple[int, Message]] = []
    for abs_time, msg in abs_events:
        if msg.type in ("note_on", "note_off"):
            # Check if this note should be removed
            if msg.note not in notes_to_remove:
                kept_events.append((abs_time, msg))
            # Otherwise, skip it (removed)
        else:
            # Non-note event - keep as-is
            kept_events.append((abs_time, msg))
    
    # Rebuild track with delta times (sort so delta is never negative)
    kept_events.sort(key=lambda x: (x[0], id(x[1])))
    new_track = MidiTrack()
    prev_time = 0
    for abs_time, msg in kept_events:
        delta = abs_time - prev_time
        if delta < 0:
            delta = 0
        prev_time = abs_time
        new_msg = msg.copy(time=delta)
        new_track.append(new_msg)
    
    return new_track


def compute_guitar_string_and_finger(midi_pitch: int) -> Optional[Tuple[int, int]]:
    """
    Map a MIDI pitch to (string_number, finger_number) for first-position guitar fingering.
    Finger numbers: 0=open, 1=index, 2=middle, 3=ring, 4=pinky.
    Only handles notes within four semitones of each open string.
    """
    for string_num, open_pitch in GUITAR_STRINGS:
        delta = midi_pitch - open_pitch
        if 0 <= delta <= 4:
            return string_num, delta
    return None


def annotate_finger_numbers(track: MidiTrack) -> MidiTrack:
    """
    Insert lyric meta events containing guitar finger numbers next to note_on events.
    """
    new_track = MidiTrack()
    for msg in track:
        if msg.type == "note_on" and msg.velocity > 0:
            result = compute_guitar_string_and_finger(msg.note)
            if result is not None:
                _, finger = result
                lyric_msg = MetaMessage("lyrics", text=str(finger), time=msg.time)
                new_track.append(lyric_msg)
                new_track.append(msg.copy(time=0))
                continue
        new_track.append(msg.copy())
    return new_track


def quantize_track(track: MidiTrack, ticks_per_beat: int, quantize_ticks: int) -> MidiTrack:
    """
    Quantize note start times to the nearest grid position.
    Uses a 32nd note grid as the finest resolution to ensure 32nd notes and faster
    notes/rests are quantized to their nearest neighbor accurately.
    
    quantize_ticks: number of ticks per quantization step (e.g., ticks_per_beat // 4 for 16th notes)
    """
    # Always use 32nd note grid as finest resolution for accurate quantization
    # This ensures 32nd notes and faster notes/rests snap to nearest neighbor
    finest_grid = ticks_per_beat // 8  # 32nd note grid
    
    # Convert to absolute time events
    abs_events: List[Tuple[int, Message]] = []
    current_time = 0
    for msg in track:
        current_time += msg.time
        abs_events.append((current_time, msg))
    
    # First pass: quantize all note events to finest grid (32nd notes)
    # This ensures fast notes and rests are quantized to nearest neighbor
    fine_quantized: List[Tuple[int, Message]] = []
    for abs_time, msg in abs_events:
        if msg.type in ("note_on", "note_off"):
            # Quantize to nearest 32nd note grid position
            quantized_time = round(abs_time / finest_grid) * finest_grid
            fine_quantized.append((quantized_time, msg))
        else:
            # Keep non-note events at original time
            fine_quantized.append((abs_time, msg))
    
    # Second pass: if requested grid is coarser than 32nd notes, snap to that grid
    quantized_events: List[Tuple[int, Message]] = []
    for abs_time, msg in fine_quantized:
        if msg.type in ("note_on", "note_off") and quantize_ticks > finest_grid:
            # Snap to coarser grid if requested
            quantized_time = round(abs_time / quantize_ticks) * quantize_ticks
            quantized_events.append((quantized_time, msg))
        else:
            # Use fine-quantized time (or original for non-notes)
            quantized_events.append((abs_time, msg))
    
    # Sort by time so deltas are never negative (quantization can reorder events)
    quantized_events.sort(key=lambda x: (x[0], id(x[1])))
    
    # Rebuild track with delta times
    new_track = MidiTrack()
    prev_time = 0
    for abs_time, msg in quantized_events:
        delta = abs_time - prev_time
        if delta < 0:
            delta = 0
        prev_time = abs_time
        new_msg = msg.copy(time=delta)
        new_track.append(new_msg)
    
    return new_track


def compute_basic_guitar_string(midi_pitch: int) -> int:
    """
    Basic heuristic: choose the highest string whose open pitch is <= midi_pitch.
    """
    for string_num, open_pitch in sorted(GUITAR_STRINGS, key=lambda x: x[1], reverse=True):
        if midi_pitch >= open_pitch:
            return string_num
    return GUITAR_STRINGS[-1][0]


def add_auto_number_annotations(
    track: MidiTrack,
    mode: str = "string",
) -> MidiTrack:
    """
    Insert MetaMessage text events alongside note_on messages to represent guitar string or finger numbers.
    """
    valid_modes = {"string", "finger"}
    if mode not in valid_modes:
        raise ValueError(f"Unsupported auto number mode '{mode}'. Available modes: {sorted(valid_modes)}")

    new_track = MidiTrack()

    for msg in track:
        if msg.type == "note_on" and msg.velocity > 0:
            annotation_text: Optional[str] = None
            if mode == "string":
                annotation_text = str(compute_basic_guitar_string(msg.note))
            elif mode == "finger":
                result = compute_guitar_string_and_finger(msg.note)
                if result is not None:
                    _, finger = result
                    annotation_text = str(finger)

            if annotation_text is not None:
                text_msg = MetaMessage("text", text=annotation_text, time=msg.time)
                new_track.append(text_msg)
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
    rubato_four_bar: bool = False,
    rubato_slow_bpm_delta: float = 3.0,
    rubato_reference_bpm: float = 120.0,
) -> None:
    """
    General MIDI manipulation function that can apply multiple operations:
    - Merge tracks
    - Lift notes below min_pitch by octaves
    - Remove unison duplicate notes
    - Remove redundant pitch classes (same note name in different octaves in chords)
    - Quantize note timing
    - Add guitar string/fingering annotations as MetaMessage text events
    - Optional --rubato-four-bar: repeating 4-bar mild stretch (bars 1 & 4 slower)

    quantize: 'whole', 'half', 'quarter', 'eighth', 'sixteenth', 'thirtysecond'
              or None to skip quantization
    """
    mid = MidiFile(input_path)
    
    # Merge tracks if requested
    if merge_tracks_flag and len(mid.tracks) > 1:
        mid = merge_all_tracks(mid)
    
    if not mid.tracks:
        raise RuntimeError("No tracks found in input MIDI.")
    
    track = mid.tracks[0]
    
    # Apply operations in order
    if min_pitch is not None:
        track = lift_notes_below_pitch(track, min_pitch=min_pitch)
    
    if remove_unisons_flag:
        track = remove_unison_notes(track)
    
    if remove_redundant_pitch_classes_flag:
        track = remove_redundant_pitch_classes(track)
    
    if quantize:
        # Map quantize string to ticks
        quantize_map = {
            'whole': mid.ticks_per_beat * 4,
            'half': mid.ticks_per_beat * 2,
            'quarter': mid.ticks_per_beat,
            'eighth': mid.ticks_per_beat // 2,
            'sixteenth': mid.ticks_per_beat // 4,
            'thirtysecond': mid.ticks_per_beat // 8,
        }
        if quantize.lower() not in quantize_map:
            raise ValueError(f"Invalid quantize value: {quantize}. Use: {list(quantize_map.keys())}")
        quantize_ticks = quantize_map[quantize.lower()]
        track = quantize_track(track, mid.ticks_per_beat, quantize_ticks)

    if auto_number:
        track = add_auto_number_annotations(track, mode=auto_number_mode)

    if rubato_four_bar:
        track = four_bar_rubato_track(
            track,
            ticks_per_beat=mid.ticks_per_beat,
            slow_bpm_delta=rubato_slow_bpm_delta,
            reference_bpm=rubato_reference_bpm,
        )

    # Save result
    new_mid = MidiFile(ticks_per_beat=mid.ticks_per_beat)
    new_mid.tracks.append(track)
    new_mid.save(output_path)


def piano_to_guitar(
    input_path: str,
    output_path: str,
    min_pitch: int = 40,
    merge_tracks_flag: bool = True,
    remove_unisons_flag: bool = True,
) -> None:
    """
    Convert 2-staff piano MIDI to 1-staff guitar-style MIDI:
      - optionally merge all tracks,
      - raise any notes below min_pitch (default E2=40) by octaves,
      - optionally remove unison duplicate notes.
    """
    mid = MidiFile(input_path)

    if merge_tracks_flag and len(mid.tracks) > 1:
        mid = merge_all_tracks(mid)

    # Process the single main track (index 0)
    if not mid.tracks:
        raise RuntimeError("No tracks found in input MIDI.")

    track = mid.tracks[0]

    # Lift bass notes into guitar range
    track = lift_notes_below_pitch(track, min_pitch=min_pitch)

    # Remove unison notes if requested
    if remove_unisons_flag:
        track = remove_unison_notes(track)

    # Replace track and save
    new_mid = MidiFile(ticks_per_beat=mid.ticks_per_beat)
    new_mid.tracks.append(track)
    new_mid.save(output_path)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "MIDI Manipulator - Apply various operations to MIDI files:\n"
            "- Merge multiple tracks into one\n"
            "- Raise notes below a minimum pitch by octaves\n"
            "- Remove unison duplicate notes (same pitch, channel, time)\n"
            "- Remove redundant pitch classes (same note name in different octaves, e.g., Bb3 and Bb4)\n"
            "- Quantize note timing to a grid (whole, half, quarter, eighth, sixteenth, thirtysecond)\n"
            "- Optional 4-bar rubato pattern (--rubato-four-bar) for subtle humanization"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove unisons only:
  %(prog)s -i input.mid -o output.mid --remove-unisons

  # Remove redundant pitch classes (e.g., Bb3 and Bb4 in same chord):
  %(prog)s -i input.mid -o output.mid --remove-redundant-pitch-classes

  # Quantize to 16th notes:
  %(prog)s -i input.mid -o output.mid --quantize sixteenth

  # Piano to guitar (merge, lift notes, remove unisons):
  %(prog)s -i piano.mid -o guitar.mid --merge-tracks --min-pitch 40 --remove-unisons

  # All operations:
  %(prog)s -i input.mid -o output.mid --merge-tracks --min-pitch 40 --remove-unisons --remove-redundant-pitch-classes --quantize eighth

  # Auto-label guitar string numbers or finger numbers:
  %(prog)s -i input.mid -o output.mid --auto-number --auto-number-mode finger

  # Mild 4-bar rubato (optional; run last — lengthens bar 1 & 4 of each group):
  %(prog)s -i input.mid -o output.mid --rubato-four-bar
  %(prog)s -i input.mid -o output.mid --rubato-four-bar --rubato-slow-bpm-delta 2 --rubato-reference-bpm 120
        """
    )
    parser.add_argument("--input", "-i", required=True, help="Input MIDI file path")
    parser.add_argument("--output", "-o", required=True, help="Output MIDI file path")
    parser.add_argument(
        "--min-pitch",
        type=int,
        default=None,
        help="Minimum MIDI note; notes below this are raised by octaves (e.g., 40 = E2). Default: None (no pitch lifting)",
    )
    parser.add_argument(
        "--merge-tracks",
        action="store_true",
        help="Merge all tracks into a single track",
    )
    parser.add_argument(
        "--remove-unisons",
        action="store_true",
        help="Remove unison duplicate notes (same pitch, channel, start time)",
    )
    parser.add_argument(
        "--remove-redundant-pitch-classes",
        action="store_true",
        help="Remove redundant note names in chords (e.g., if chord has Bb3 and Bb4, keep only one)",
    )
    parser.add_argument(
        "--quantize",
        type=str,
        choices=['whole', 'half', 'quarter', 'eighth', 'sixteenth', 'thirtysecond'],
        default=None,
        help="Quantize note timing to grid (whole, half, quarter, eighth, sixteenth, thirtysecond)",
    )
    parser.add_argument(
        "--auto-number",
        action="store_true",
        help="Automatically annotate note_on events with guitar string numbers (MetaMessage text events)",
    )
    parser.add_argument(
        "--auto-number-mode",
        type=str,
        choices=["string", "finger"],
        default="string",
        help="Mode for automatic numbering: 'string' (6→1) or 'finger' (0=open, 1–4 fretted)",
    )
    parser.add_argument(
        "--rubato-four-bar",
        action="store_true",
        help=(
            "Risky / optional: humanize timing with a repeating 4-bar rubato (bar 1 & 4 slower, "
            "bars 2–3 nominal; pattern repeats 5–8, 9–12, …). Strength is set in BPM via "
            "--rubato-slow-bpm-delta / --rubato-reference-bpm (tick stretch, not score symbols)."
        ),
    )
    parser.add_argument(
        "--rubato-slow-bpm-delta",
        type=float,
        default=3.0,
        help=(
            "With --rubato-four-bar: slow bars feel ~this many BPM under --rubato-reference-bpm "
            "(default 3). Smaller = subtler."
        ),
    )
    parser.add_argument(
        "--rubato-reference-bpm",
        type=float,
        default=120.0,
        help=(
            "With --rubato-four-bar: nominal BPM for the math only (default 120). "
            "Match your piece’s approximate tempo so --rubato-slow-bpm-delta reads like real BPM."
        ),
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)

    # Use general manipulation function
    manipulate_midi(
        input_path=input_path,
        output_path=output_path,
        min_pitch=args.min_pitch,
        merge_tracks_flag=args.merge_tracks,
        remove_unisons_flag=args.remove_unisons,
        remove_redundant_pitch_classes_flag=args.remove_redundant_pitch_classes,
        quantize=args.quantize,
        auto_number=args.auto_number,
        auto_number_mode=args.auto_number_mode,
        rubato_four_bar=args.rubato_four_bar,
        rubato_slow_bpm_delta=args.rubato_slow_bpm_delta,
        rubato_reference_bpm=args.rubato_reference_bpm,
    )
    
    print(f"[+] Processed MIDI saved to: {output_path}")


if __name__ == "__main__":
    main()


