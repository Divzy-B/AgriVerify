import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
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

// 10 scenes (2490 frames) minus 9 transitions of 15 frames = 2355 frames.
export const AgriVerifyDemo: React.FC = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence name="Hook" durationInFrames={150}>
      <Hook />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="Problem" durationInFrames={240}>
      <Problem />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="Brand" durationInFrames={150}>
      <Brand />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="How it works" durationInFrames={270}>
      <HowItWorks />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="Voice call" durationInFrames={330}>
      <VoiceCall />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="Satellite" durationInFrames={330}>
      <Satellite />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="Verdict" durationInFrames={300}>
      <Verdict />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="Reviewer" durationInFrames={270}>
      <Reviewer />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="Principles" durationInFrames={210}>
      <Principles />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 15 })} />
    <TransitionSeries.Sequence name="Outro" durationInFrames={240}>
      <Outro />
    </TransitionSeries.Sequence>
  </TransitionSeries>
);
