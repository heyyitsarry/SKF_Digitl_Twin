import React, { useRef, useEffect } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";

export default function SpindleModel() {
  const outerGroup = useRef(); // stays fixed → lighting stays correct
  const innerGroup = useRef(); // vibrates
  const mainShaft = useRef();

  const shaftMeshes = useRef([]);
  const originalMaterials = useRef([]);

  const isOverheating = useRef(false);
  const timer = useRef(0);

  const { scene } = useGLTF("/models/spindle2.glb");

  const baseRotation = new THREE.Euler(0, 0, Math.PI / 2);

  // Find all meshes in MainShaft
  useEffect(() => {
    const shaftRoot = scene.getObjectByName("MainShaft");
    if (!shaftRoot) {
      console.warn("MainShaft not found");
      return;
    }

    mainShaft.current = shaftRoot;

    const meshes = [];
    shaftRoot.traverse((o) => {
      if (o.isMesh) meshes.push(o);
    });

    shaftMeshes.current = meshes;
    originalMaterials.current = meshes.map((m) => m.material);
  }, [scene]);

  // Random overheating trigger
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isOverheating.current && Math.random() < 0.3) {
        isOverheating.current = true;
        timer.current = 1.0;

        shaftMeshes.current.forEach((mesh) => {
          mesh.material.color.set("#ff0000");
          mesh.material.metalness = 1.0;
          mesh.material.roughness = 0.25;
        });
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Animation loop
  useFrame((state, delta) => {
    // Shaft spin
    if (mainShaft.current) {
      mainShaft.current.rotation.y += delta * 15;
    }

    // When overheating — vibrate INNER GROUP ONLY
    if (isOverheating.current) {
      timer.current -= delta;

      if (innerGroup.current) {
        const t = performance.now() * 0.005;

        const jitterPos = 0.03;
        const jitterRot = 0.03;

        // 🔥 ONLY inner group vibrates
        innerGroup.current.position.x = Math.sin(t * 25) * jitterPos;
        innerGroup.current.position.y = Math.cos(t * 20) * jitterPos;

        innerGroup.current.rotation.set(
          0,
          0,
          Math.sin(t * 40) * jitterRot
        );
      }

      // cooling down
      if (timer.current <= 0) {
        isOverheating.current = false;

        // Restore materials
        shaftMeshes.current.forEach((mesh, i) => {
          mesh.material = originalMaterials.current[i];
        });

        // Reset vibrations
        if (innerGroup.current) {
          innerGroup.current.position.set(0, 0, 0);
          innerGroup.current.rotation.set(0, 0, 0);
        }
      }
    }
  });

  return (
    <group
      ref={outerGroup}
      scale={1.2}
      position={[4, -0.4, 0]}
      rotation={[0, 0, Math.PI / 2]}   // always horizontal
    >
      <group ref={innerGroup}>
        <primitive object={scene} />
      </group>
    </group>
  );
}

useGLTF.preload("/models/spindle2.glb");
