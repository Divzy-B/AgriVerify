import { Audio } from "@remotion/media";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import {
  Brand,
  Hook,
  HowItWorks,
  Outro,
  Principles,
  Problem,
  Reviewer,
  Satellite,
  Verdict,
  VoiceCall,
} from "./scenes";

// Each scene lasts its voiceover + ~1.2s (see scripts/make_audio.py output).
// 10 scenes (3327 frames) minus 9 transitions of 15 frames = 3192 frames.

const Music: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  return (
    <Audio
      name="Music"
      src={staticFile("music.wav")}
      volume={interpolate(
        frame,
        [0, 1 * fps, durationInFrames - 3 * fps, durationInFrames - 1],
        [0, 0.16, 0.16, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
      )}
    />
  );
};

// Starts once the incoming transition has finished.
const VO: React.FC<{ file: string }> = ({ file }) => (
  <Audio name={`VO ${file}`} src={staticFile(`voiceover/${file}.mp3`)} from={12} />
);

export const AgriVerifyDemo: React.FC = () => (
  <>
    <TransitionSeries>
      <TransitionSeries.Sequence name="Hook" durationInFrames={213}>
        <Hook />
        <VO file="hook" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="Problem" durationInFrames={407}>
        <Problem />
        <VO file="problem" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="Brand" durationInFrames={198}>
        <Brand />
        <VO file="brand" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="How it works" durationInFrames={303}>
        <HowItWorks />
        <VO file="how" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="Voice call" durationInFrames={375}>
        <VoiceCall />
        <VO file="voice" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="Satellite" durationInFrames={503}>
        <Satellite />
        <VO file="satellite" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="Verdict" durationInFrames={414}>
        <Verdict />
        <VO file="verdict" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="Reviewer" durationInFrames={350}>
        <Reviewer />
        <VO file="reviewer" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="Principles" durationInFrames={285}>
        <Principles />
        <VO file="principles" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
      <TransitionSeries.Sequence name="Outro" durationInFrames={279}>
        <Outro />
        <VO file="outro" />
      </TransitionSeries.Sequence>
    </TransitionSeries>
    <Music />
  </>
);
