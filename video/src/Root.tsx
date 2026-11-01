import { Composition } from "remotion";
import { AgriVerifyDemo } from "./AgriVerifyDemo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="AgriVerifyDemo"
      component={AgriVerifyDemo}
      durationInFrames={3192}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
