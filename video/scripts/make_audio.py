"""Generate the voiceover (edge-tts) and a synthesized ambient music bed.

Usage (from video/):  python scripts/make_audio.py [--music-only]
Writes public/voiceover/<scene>.mp3 and public/music.wav, then prints each
voiceover duration so scene lengths in src/AgriVerifyDemo.tsx can match.
Requires: pip install edge-tts numpy
"""
import asyncio
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

VOICE = "en-US-AndrewMultilingualNeural"
PUBLIC = Path(__file__).resolve().parent.parent / "public"

SCRIPT = {
    "hook": "For a farmer, one date can decide an entire insurance claim: the day the crop was planted.",
    "problem": "But checking that date is hard. Inspectors can't visit every farm. Many farmers can't use apps or forms. And once the crop is up, the planting date is almost impossible to prove.",
    "brand": "Meet AgriVerify. It verifies planting dates with a phone call, and a satellite.",
    "how": "Here's how it works. The farmer calls. A satellite looks at the field. A fixed rule compares the two. And a human reviewer makes the final call.",
    "voice": "First, the farmer simply talks to our Bolna AI voice agent. No app, no forms. The caller is matched by phone number, and the agent confirms the crop and the planting date.",
    "satellite": "Next, the satellite checks. Sentinel-2 vegetation data shows this field greening up on June second. That points back to a planting window of May nineteenth to the twenty-ninth, and the reported date, May twenty-fifth, falls right inside it.",
    "verdict": "Then a fixed, auditable rule decides. Not an AI. Inside the window is within tolerance. Thirty-five days off needs review. And with only cloudy images, we make no estimate at all.",
    "reviewer": "Finally, reviewers get evidence, not guesses: a dashboard of every claim, and a PDF report with the window, the model versions, and the limitations.",
    "principles": "A human always makes the final call. The voice AI only collects data. And every estimate shows its evidence, and its limits.",
    "outro": "AgriVerify. Fewer field visits. Faster, fairer claims. Built with Bolna AI.",
}


async def voiceover() -> None:
    import edge_tts

    out = PUBLIC / "voiceover"
    out.mkdir(parents=True, exist_ok=True)
    for name, text in SCRIPT.items():
        await edge_tts.Communicate(text, VOICE, rate="+4%").save(str(out / f"{name}.mp3"))
        dur = subprocess.run(
            ["npx", "remotion", "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out / f"{name}.mp3")],
            capture_output=True, text=True, shell=True,
        ).stdout.strip()
        print(f"{name:11s} {float(dur):5.2f}s")


def music(seconds: float = 115, sr: int = 44100) -> None:
    """Calm ambient pad + soft arpeggio + sub bass. Royalty-free by construction."""
    t = np.arange(int(seconds * sr)) / sr
    bpm = 96
    beat = 60 / bpm
    bar = 4 * beat
    # Cmaj9 â€“ Am7 â€“ Fmaj7 â€“ G6, one chord per bar (MIDI notes)
    chords = [[48, 55, 64, 71, 74], [45, 52, 60, 67, 71], [41, 48, 57, 64, 69], [43, 50, 59, 62, 64]]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)

    left = np.zeros_like(t)
    right = np.zeros_like(t)
    n_bars = int(seconds / bar) + 1
    for b in range(n_bars):
        chord = chords[b % 4]
        start = int(b * bar * sr)
        end = min(int((b + 1) * bar * sr) + int(0.8 * sr), len(t))  # overlap for smooth changes
        if start >= len(t):
            break
        seg = t[start:end] - t[start]
        env = np.minimum(seg / 0.9, 1) * np.minimum((seg[-1] - seg + 1e-3) / 0.8, 1)
        for i, m in enumerate(chord):
            f = hz(m)
            # Two slightly detuned voices per note, panned apart, warm harmonics.
            for det, ch in ((0.997, left), (1.003, right)):
                tone = np.sin(2 * np.pi * f * det * seg) + 0.25 * np.sin(2 * np.pi * 2 * f * det * seg)
                ch[start:end] += 0.045 * env * tone
        # Sub bass on the root.
        bass = 0.11 * env * np.sin(2 * np.pi * hz(chord[0] - 12) * seg)
        left[start:end] += bass
        right[start:end] += bass
        # Arpeggio: eighth notes cycling up the chord, short plucks.
        for k in range(8):
            ps = start + int(k * beat / 2 * sr)
            pe = min(ps + int(0.6 * sr), len(t))
            if ps >= len(t):
                break
            pt = t[ps:pe] - t[ps]
            note = chord[1:][k % 4] + 12
            pluck = 0.05 * np.exp(-pt * 7) * np.sin(2 * np.pi * hz(note) * pt)
            pan = 0.35 + 0.3 * (k % 2)
            left[ps:pe] += pluck * (1 - pan)
            right[ps:pe] += pluck * pan

    stereo = np.stack([left, right], axis=1)
    stereo *= np.minimum(t / 2, 1)[:, None]  # 2s fade-in; fade-out is done in Remotion
    stereo /= np.abs(stereo).max() / 0.8
    pcm = (stereo * 32767).astype("<i2")
    with wave.open(str(PUBLIC / "music.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    print(f"music.wav   {seconds:.0f}s")


if __name__ == "__main__":
    if "--music-only" not in sys.argv:
        asyncio.run(voiceover())
    music()
