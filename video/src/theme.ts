import { loadFont } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

export const { fontFamily } = loadFont("normal", {
  weights: ["400", "600", "800"],
  subsets: ["latin"],
});
export const { fontFamily: monoFamily } = loadMono("normal", {
  weights: ["400", "600"],
  subsets: ["latin"],
});

// Same palette as frontend/app/globals.css so the video matches the product.
export const c = {
  ink: "#071b1a",
  panel: "#0d2927",
  panel2: "#123330",
  line: "#2b5650",
  green: "#68e1a5",
  mint: "#b9f7d7",
  sand: "#e7d9bf",
  muted: "#9fbbb3",
  white: "#f4fbf8",
  amber: "#f5bf60",
  red: "#ff8f85",
  blue: "#b8d0f5",
};

export const background = `radial-gradient(circle at 78% -5%, #1b4c41 0, transparent 900px), ${c.ink}`;
