import React, { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import SpindleModel from "./SpindleModel";

export default function SpindleView() {
  return (
    <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} />
      <Suspense fallback={null}>
        <SpindleModel />
      </Suspense>
      <OrbitControls enableZoom={true} />
    </Canvas>
  );
}
