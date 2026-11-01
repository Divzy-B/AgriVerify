import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { c, monoFamily } from "./theme";
import {
  Card,
  Eyebrow,
  Headline,
  Leaf,
  Orbits,
  Reveal,
  Scene,
  StatusPill,
  useProgress,
} from "./ui";

const center: React.CSSProperties = {
  justifyContent: "center",
  alignItems: "center",
  textAlign: "center",
};
const sub: React.CSSProperties = {
  fontSize: 44,
  lineHeight: 1.4,
  color: c.muted,
  marginTop: 32,
};

/* 1 — Hook */
const TypedDate: React.FC<{ start: number }> = ({ start }) => {
  const frame = useCurrentFrame();
  const text = "reported_planting_date = 2025-05-25";
  const n = Math.floor(
    interpolate(frame, [start, start + 35], [0, text.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  const caret = Math.floor(frame / 15) % 2 === 0;
  return (
    <span
      style={{
        fontFamily: monoFamily,
        fontSize: 40,
        color: c.amber,
        border: `2px solid #796432`,
        background: "rgba(174,133,49,.12)",
        borderRadius: 16,
        padding: "20px 30px",
      }}
    >
      {text.slice(0, n)}
      <span style={{ opacity: caret ? 1 : 0 }}>▍</span>
    </span>
  );
};

export const Hook: React.FC = () => (
  <Scene style={{ justifyContent: "center" }}>
    <Reveal>
      <Eyebrow>Crop insurance</Eyebrow>
    </Reveal>
    <Reveal delay={8}>
      <Headline size={150} style={{ marginTop: 30 }}>
        One date decides
      </Headline>
    </Reveal>
    <Reveal delay={18}>
      <Headline size={150}>
        a farmer’s <span style={{ color: c.green }}>claim.</span>
      </Headline>
    </Reveal>
    <Reveal delay={45} style={{ marginTop: 70 }}>
      <TypedDate start={50} />
    </Reveal>
  </Scene>
);

/* 2 — Problem */
const problems = [
  ["01", "An inspector per farm", "Field visits are slow and costly for every single claim."],
  ["02", "Forms farmers can’t use", "Many farmers can’t easily use apps or paperwork."],
  ["03", "Hard to prove later", "Once the crop is up, the planting date is hard to check."],
];

export const Problem: React.FC = () => (
  <Scene style={{ justifyContent: "center" }}>
    <Reveal>
      <Eyebrow color={c.red}>The problem</Eyebrow>
    </Reveal>
    <Reveal delay={8}>
      <Headline style={{ marginTop: 24 }}>
        Checking that date today
        <br />
        is slow and expensive.
      </Headline>
    </Reveal>
    <div style={{ display: "flex", gap: 36, marginTop: 80 }}>
      {problems.map(([n, title, body], i) => (
        <Reveal key={n} delay={35 + i * 14} style={{ flex: 1 }}>
          <Card style={{ height: "100%" }}>
            <div style={{ fontFamily: monoFamily, fontSize: 30, color: c.red }}>{n}</div>
            <div style={{ fontSize: 46, fontWeight: 800, marginTop: 20, letterSpacing: "-0.03em" }}>
              {title}
            </div>
            <div style={{ fontSize: 32, color: c.muted, marginTop: 16, lineHeight: 1.4 }}>{body}</div>
          </Card>
        </Reveal>
      ))}
    </div>
  </Scene>
);

/* 3 — Brand reveal */
export const Brand: React.FC = () => (
  <Scene style={center}>
    <Orbits />
    <Reveal rise={0}>
      <Leaf size={140} />
    </Reveal>
    <Reveal delay={8}>
      <Headline size={190} style={{ marginTop: 20 }}>
        AgriVerify
      </Headline>
    </Reveal>
    <Reveal delay={22}>
      <div style={{ ...sub, fontSize: 52, color: c.mint }}>
        Verify planting dates with a phone call and a satellite.
      </div>
    </Reveal>
  </Scene>
);

/* 4 — How it works */
const steps = [
  ["Farmer calls", "Bolna AI voice agent"],
  ["Satellite looks", "Sentinel-2 NDVI"],
  ["Rule decides", "7-day tolerance"],
  ["Human reviews", "Evidence + PDF report"],
];

const Pipeline: React.FC = () => {
  const p = useProgress(30, 190);
  return (
    <div style={{ position: "relative", marginTop: 110 }}>
      <div style={{ position: "absolute", left: 200, right: 200, top: 70, height: 6, background: c.line, borderRadius: 3 }}>
        <div style={{ width: `${p * 100}%`, height: "100%", background: c.green, borderRadius: 3, boxShadow: `0 0 24px ${c.green}` }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        {steps.map(([title, body], i) => {
          const on = p >= i / 3 - 0.001;
          return (
            <div key={title} style={{ width: 400, display: "flex", flexDirection: "column", alignItems: "center" }}>
              <div
                style={{
                  width: 146,
                  height: 146,
                  borderRadius: "50%",
                  display: "grid",
                  placeItems: "center",
                  fontFamily: monoFamily,
                  fontSize: 52,
                  fontWeight: 600,
                  position: "relative",
                  background: on ? c.green : c.panel2,
                  color: on ? "#063022" : c.muted,
                  border: `3px solid ${on ? c.green : c.line}`,
                  boxShadow: on ? `0 0 0 14px #68e1a522` : "none",
                }}
              >
                {i + 1}
              </div>
              <div style={{ fontSize: 46, fontWeight: 800, marginTop: 36, letterSpacing: "-0.03em", opacity: on ? 1 : 0.4 }}>
                {title}
              </div>
              <div style={{ fontSize: 32, color: c.muted, marginTop: 10, opacity: on ? 1 : 0.4 }}>{body}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const HowItWorks: React.FC = () => (
  <Scene style={{ justifyContent: "center" }}>
    <Reveal>
      <Eyebrow>How it works</Eyebrow>
    </Reveal>
    <Reveal delay={8}>
      <Headline style={{ marginTop: 24 }}>
        From a phone call to evidence
        <br />a reviewer can trust.
      </Headline>
    </Reveal>
    <Pipeline />
  </Scene>
);

/* 5 — Voice call */
const lines: [string, string, number][] = [
  ["agent", "Hi Alma, this is AgriVerify. Which crop did you plant on Torres Cotton South?", 20],
  ["farmer", "Cotton.", 65],
  ["agent", "And when did you plant it?", 95],
  ["farmer", "Around the twenty-fifth of May.", 130],
  ["agent", "Got it: May 25, 2025. Is that right?", 175],
  ["farmer", "Yes, that’s right.", 215],
];

const Waveform: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center", height: 60, justifyContent: "center" }}>
      {Array.from({ length: 28 }, (_, i) => (
        <div
          key={i}
          style={{
            width: 6,
            borderRadius: 3,
            background: c.green,
            height: 8 + Math.abs(Math.sin(frame * 0.25 + i * 0.7) * Math.cos(frame * 0.07 + i)) * 48,
          }}
        />
      ))}
    </div>
  );
};

const CallTimer: React.FC = () => {
  const frame = useCurrentFrame();
  const s = Math.floor(frame / 30) + 3;
  return <span>00:{String(s).padStart(2, "0")}</span>;
};

const Phone: React.FC = () => (
  <div
    style={{
      width: 500,
      height: 840,
      borderRadius: 64,
      border: "10px solid #1d4a43",
      background: "#061716",
      padding: "44px 26px",
      display: "flex",
      flexDirection: "column",
      boxShadow: "0 40px 80px rgba(0,0,0,.45)",
    }}
  >
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: 30, fontWeight: 800 }}>AgriVerify</div>
      <div style={{ fontSize: 22, color: c.muted, marginTop: 6 }}>
        Bolna AI voice agent · <CallTimer />
      </div>
      <div style={{ marginTop: 18 }}>
        <Waveform />
      </div>
    </div>
    <div style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 24 }}>
      {lines.map(([who, text, at]) => (
        <Reveal
          key={at}
          delay={at}
          rise={20}
          style={{
            alignSelf: who === "agent" ? "flex-start" : "flex-end",
            maxWidth: "86%",
            background: who === "agent" ? "#1a5143" : "#303e5b",
            borderRadius: 20,
            padding: "14px 18px",
            fontSize: 24,
            lineHeight: 1.4,
          }}
        >
          {text}
        </Reveal>
      ))}
    </div>
  </div>
);

const Captured: React.FC<{ label: string; value: string; at: number }> = ({ label, value, at }) => {
  const frame = useCurrentFrame();
  const done = frame >= at;
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 0", borderBottom: `2px solid ${c.line}` }}>
      <span style={{ fontSize: 32, color: c.muted }}>{label}</span>
      <span style={{ fontFamily: monoFamily, fontSize: 34, color: done ? c.mint : c.line }}>
        {done ? value : "…"}
        {done ? <span style={{ color: c.green }}>  ✓</span> : null}
      </span>
    </div>
  );
};

export const VoiceCall: React.FC = () => (
  <Scene style={{ flexDirection: "row", alignItems: "center", gap: 110 }}>
    <Reveal rise={60}>
      <Phone />
    </Reveal>
    <div style={{ flex: 1 }}>
      <Reveal>
        <Eyebrow>Step 1 · Voice intake</Eyebrow>
      </Reveal>
      <Reveal delay={8}>
        <Headline size={96} style={{ marginTop: 24 }}>
          The farmer just talks.
        </Headline>
      </Reveal>
      <Reveal delay={16}>
        <div style={{ ...sub, fontSize: 40 }}>No app, no forms. Matched by caller number.</div>
      </Reveal>
      <Reveal delay={30}>
        <Card style={{ marginTop: 56, padding: "24px 40px" }}>
          <Captured label="Farm" value="TX-001" at={30} />
          <Captured label="Crop" value="Cotton" at={75} />
          <Captured label="Planting date" value="2025-05-25" at={225} />
        </Card>
      </Reveal>
    </div>
  </Scene>
);

/* 6 — Satellite NDVI */
// TX-001 demo observations (backend/app/services/data.py), x = days after May 1.
const ndvi: [number, number][] = [
  [0, 0.12], [7, 0.13], [15, 0.15], [22, 0.18], [32, 0.24], [40, 0.31], [48, 0.42],
];
const W = 820;
const H = 520;
const X = (d: number) => 60 + (d / 50) * (W - 90);
const Y = (v: number) => H - 60 - (v / 0.5) * (H - 110);

const NdviChart: React.FC = () => {
  const frame = useCurrentFrame();
  const draw = useProgress(20, 120);
  const fade = (at: number) =>
    interpolate(frame, [at, at + 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const path = ndvi.map(([d, v], i) => `${i ? "L" : "M"}${X(d)},${Y(v)}`).join(" ");
  const ticks: [number, string][] = [[0, "May 1"], [15, "May 16"], [31, "Jun 1"], [48, "Jun 18"]];

  return (
    <svg width={W} height={H} style={{ overflow: "visible" }}>
      {[0.1, 0.2, 0.3, 0.4].map((v) => (
        <g key={v}>
          <line x1={60} x2={W - 30} y1={Y(v)} y2={Y(v)} stroke={c.line} strokeWidth={1.5} />
          <text x={44} y={Y(v) + 8} fill={c.muted} fontSize={22} textAnchor="end" fontFamily={monoFamily}>
            {v.toFixed(1)}
          </text>
        </g>
      ))}
      {ticks.map(([d, t]) => (
        <text key={t} x={X(d)} y={H - 18} fill={c.muted} fontSize={22} textAnchor="middle" fontFamily={monoFamily}>
          {t}
        </text>
      ))}

      {/* Estimated planting window May 19–29 */}
      <g opacity={fade(170)}>
        <rect x={X(18)} width={X(28) - X(18)} y={40} height={H - 100} fill="#68e1a522" stroke={c.green} strokeDasharray="8 6" strokeWidth={2} />
        <text x={(X(18) + X(28)) / 2} y={28} fill={c.green} fontSize={24} fontWeight={700} textAnchor="middle">
          Planting window
        </text>
      </g>

      {/* Green-up threshold */}
      <g opacity={fade(130)}>
        <line x1={60} x2={W - 30} y1={Y(0.213)} y2={Y(0.213)} stroke={c.blue} strokeDasharray="10 8" strokeWidth={2} />
        <text x={W - 30} y={Y(0.213) - 12} fill={c.blue} fontSize={22} textAnchor="end">
          green-up threshold
        </text>
      </g>

      <path d={path} fill="none" stroke={c.green} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} />
      {ndvi.map(([d, v]) => (
        <circle key={d} cx={X(d)} cy={Y(v)} r={10} fill={d === 32 ? c.mint : c.ink} stroke={c.green} strokeWidth={4} opacity={draw >= d / 48 ? 1 : 0} />
      ))}

      {/* Reported date May 25 */}
      <g opacity={fade(225)}>
        <line x1={X(24)} x2={X(24)} y1={40} y2={H - 60} stroke={c.amber} strokeWidth={4} />
        <rect x={X(24) - 110} y={Y(0.42)} width={220} height={52} rx={26} fill="#60481d" />
        <text x={X(24)} y={Y(0.42) + 35} fill={c.amber} fontSize={24} fontWeight={700} textAnchor="middle">
          Reported May 25
        </text>
      </g>
    </svg>
  );
};

export const Satellite: React.FC = () => (
  <Scene style={{ flexDirection: "row", alignItems: "center", gap: 60 }}>
    <div style={{ width: 680 }}>
      <Reveal>
        <Eyebrow>Step 2 · Satellite</Eyebrow>
      </Reveal>
      <Reveal delay={8}>
        <Headline size={88} style={{ marginTop: 24 }}>
          The satellite
          <br />
          checks.
        </Headline>
      </Reveal>
      <Reveal delay={16}>
        <div style={{ ...sub, fontSize: 36 }}>
          Sentinel-2 vegetation index (NDVI) shows green-up on Jun 2, which points back to planting between May 19 and 29.
        </div>
      </Reveal>
      <Reveal delay={30}>
        <div style={{ fontFamily: monoFamily, fontSize: 26, color: c.muted, marginTop: 40 }}>
          cloud-screened · 4–14 day emergence lag
        </div>
      </Reveal>
    </div>
    <Reveal delay={10} style={{ flex: 1 }}>
      <Card style={{ padding: "50px 40px 30px" }}>
        <div style={{ fontSize: 30, fontWeight: 800, marginBottom: 20 }}>
          TX-001 · Torres Cotton South <span style={{ color: c.muted, fontWeight: 400 }}>· NDVI</span>
        </div>
        <NdviChart />
      </Card>
    </Reveal>
  </Scene>
);

/* 7 — Verdict */
const verdicts = [
  ["TX-001", "Torres Cotton South", "May 25 · inside May 19–29", "WITHIN_TOLERANCE"],
  ["TX-002", "Bennett Cotton East", "Jul 4 · 35 days off window", "REVIEW_REQUIRED"],
  ["TX-003", "Shah Cotton North", "1 image, 58% cloud", "INSUFFICIENT_EVIDENCE"],
];

export const Verdict: React.FC = () => (
  <Scene style={{ justifyContent: "center" }}>
    <Reveal>
      <Eyebrow>Step 3 · Deterministic rule</Eyebrow>
    </Reveal>
    <Reveal delay={8}>
      <Headline style={{ marginTop: 24 }}>
        A fixed rule decides. <span style={{ color: c.green }}>Not an AI.</span>
      </Headline>
    </Reveal>
    <div style={{ display: "flex", flexDirection: "column", gap: 24, marginTop: 64 }}>
      {verdicts.map(([id, name, detail, status], i) => (
        <Reveal key={id} delay={35 + i * 30} rise={0}>
          <SlideIn delay={35 + i * 30}>
            <Card style={{ display: "flex", alignItems: "center", padding: "30px 44px", gap: 40 }}>
              <span style={{ fontFamily: monoFamily, fontSize: 34, color: c.mint, width: 150 }}>{id}</span>
              <span style={{ fontSize: 36, fontWeight: 800, width: 400 }}>{name}</span>
              <span style={{ fontSize: 30, color: c.muted, flex: 1 }}>{detail}</span>
              <StatusPill status={status} size={28} />
            </Card>
          </SlideIn>
        </Reveal>
      ))}
    </div>
    <Reveal delay={140}>
      <div style={{ fontFamily: monoFamily, fontSize: 28, color: c.muted, marginTop: 44 }}>
        review-policy-v1 · 7-day tolerance · same input, same answer, every time
      </div>
    </Reveal>
  </Scene>
);

const SlideIn: React.FC<{ delay: number; children: React.ReactNode }> = ({ delay, children }) => {
  const p = useProgress(delay, delay + 25);
  return <div style={{ translate: `${(1 - p) * -80}px 0` }}>{children}</div>;
};

/* 8 — Reviewer dashboard + report */
const metrics = [
  ["Claims", "3", c.white],
  ["Within tolerance", "1", c.green],
  ["Review required", "1", c.amber],
  ["Insufficient", "1", c.red],
];

const Report: React.FC = () => {
  const rows = [
    ["Window", "2025-05-19 → 05-29"],
    ["Reported", "2025-05-25"],
    ["Estimator", "baseline-greenup-v1"],
    ["Policy", "review-policy-v1"],
  ];
  return (
    <div style={{ background: c.white, color: "#112522", borderRadius: 24, padding: 44, boxShadow: "0 40px 80px rgba(0,0,0,.45)", rotate: "2deg" }}>
      <div style={{ fontSize: 22, letterSpacing: "0.16em", fontWeight: 800, color: "#4d776a" }}>PDF · VERIFICATION REPORT</div>
      <div style={{ fontSize: 38, fontWeight: 800, marginTop: 14, letterSpacing: "-0.03em" }}>TX-001 · Torres Cotton South</div>
      <div style={{ margin: "22px 0 18px" }}>
        <StatusPill status="WITHIN_TOLERANCE" size={24} />
      </div>
      {rows.map(([k, v]) => (
        <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 26, padding: "14px 0", borderBottom: "2px solid #dbe8e2" }}>
          <span style={{ color: "#597169" }}>{k}</span>
          <span style={{ fontFamily: monoFamily }}>{v}</span>
        </div>
      ))}
      <div style={{ fontSize: 22, color: "#597169", marginTop: 20, lineHeight: 1.45 }}>
        Limitations listed. A human reviewer makes the final decision.
      </div>
    </div>
  );
};

export const Reviewer: React.FC = () => (
  <Scene style={{ justifyContent: "center" }}>
    <Reveal>
      <Eyebrow>Step 4 · Human review</Eyebrow>
    </Reveal>
    <Reveal delay={8}>
      <Headline size={88} style={{ marginTop: 24 }}>
        Reviewers get evidence, not guesses.
      </Headline>
    </Reveal>
    <div style={{ display: "flex", gap: 50, marginTop: 64, alignItems: "center" }}>
      <div style={{ flex: 1.35, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        {metrics.map(([label, value, color], i) => (
          <Reveal key={label} delay={30 + i * 10}>
            <Card style={{ padding: "34px 40px" }}>
              <div style={{ fontSize: 30, color: c.muted }}>{label}</div>
              <div style={{ fontSize: 96, fontWeight: 800, color, letterSpacing: "-0.05em", marginTop: 6 }}>{value}</div>
            </Card>
          </Reveal>
        ))}
      </div>
      <Reveal delay={80} rise={120} style={{ flex: 1 }}>
        <Report />
      </Reveal>
    </div>
  </Scene>
);

/* 9 — Principles */
const principles = [
  "A human always makes the final call.",
  "The voice AI collects data. It never decides.",
  "Every estimate shows its evidence and limits.",
];

export const Principles: React.FC = () => (
  <Scene style={{ justifyContent: "center" }}>
    <Reveal>
      <Eyebrow>Built to be trusted</Eyebrow>
    </Reveal>
    <div style={{ marginTop: 50, display: "flex", flexDirection: "column", gap: 44 }}>
      {principles.map((p, i) => (
        <Reveal key={p} delay={15 + i * 25}>
          <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
            <div style={{ width: 84, height: 84, borderRadius: "50%", background: c.green, color: "#063022", display: "grid", placeItems: "center", fontSize: 48, fontWeight: 800, flexShrink: 0 }}>
              ✓
            </div>
            <Headline size={64} style={{ letterSpacing: "-0.04em" }}>
              {p}
            </Headline>
          </div>
        </Reveal>
      ))}
    </div>
  </Scene>
);

/* 10 — Outro */
const stack = ["Bolna AI", "Sentinel-2", "Google Earth Engine", "FastAPI", "Next.js"];

export const Outro: React.FC = () => (
  <Scene style={center}>
    <Orbits />
    <Reveal>
      <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
        <Leaf size={130} />
        <Headline size={170}>AgriVerify</Headline>
      </div>
    </Reveal>
    <Reveal delay={12}>
      <div style={{ ...sub, fontSize: 56, color: c.mint }}>Fewer field visits. Faster, fairer claims.</div>
    </Reveal>
    <div style={{ display: "flex", gap: 20, marginTop: 80 }}>
      {stack.map((s, i) => (
        <Reveal key={s} delay={35 + i * 6}>
          <span style={{ border: "2px solid #4c7d6c", background: "#153d3588", borderRadius: 999, padding: "16px 30px", fontSize: 30, color: "#d5f3e2" }}>
            {s}
          </span>
        </Reveal>
      ))}
    </div>
  </Scene>
);
