import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import * as THREE from 'three';

// Terrain mesh component
function TerrainMesh({ heightmapData }) {
  const meshRef = useRef();
  
  const geometry = useMemo(() => {
    if (!heightmapData || !heightmapData.data) return null;
    
    const { data, width, height, scale } = heightmapData;
    const geo = new THREE.PlaneGeometry(scale, scale, Math.min(width - 1, 127), Math.min(height - 1, 127));
    
    const positions = geo.attributes.position.array;
    const stepX = width / 128;
    const stepY = height / 128;
    
    for (let i = 0; i <= 127; i++) {
      for (let j = 0; j <= 127; j++) {
        const idx = i * 128 + j;
        const dataX = Math.min(Math.floor(j * stepX), width - 1);
        const dataY = Math.min(Math.floor(i * stepY), height - 1);
        if (dataY < data.length && dataX < data[0]?.length) {
          positions[idx * 3 + 2] = (data[dataY][dataX] || 0) * 50;
        }
      }
    }
    geo.computeVertexNormals();
    
    return geo;
  }, [heightmapData]);
  
  if (!geometry) return null;
  
  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
      <primitive object={geometry} />
      <meshStandardMaterial 
        color="#8B7355" 
        roughness={0.9}
        metalness={0.1}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

// Feature markers (craters, rocks)
function FeatureMarkers({ features }) {
  if (!features || !features.length) return null;
  
  return (
    <group>
      {features.slice(0, 30).map((feature, idx) => (
        <mesh
          key={idx}
          position={[feature.x / 2, (feature.z || 0) * 50 + 5, feature.y / 2]}
        >
          <sphereGeometry args={[Math.max(2, feature.size / 5), 8, 8]} />
          <meshStandardMaterial 
            color={feature.type === 'crater' ? '#4A4A4A' : '#8B4513'} 
            transparent
            opacity={0.7}
          />
        </mesh>
      ))}
    </group>
  );
}

// Simple trajectory visualization using spheres
function TrajectoryPath({ poses, color = '#00FF00' }) {
  if (!poses || poses.length < 2) return null;
  
  // Only show every Nth point to avoid clutter
  const filteredPoses = poses.filter((_, i) => i % 5 === 0 || i === poses.length - 1);
  
  return (
    <group>
      {filteredPoses.map((p, idx) => (
        <mesh key={idx} position={[p.x / 2, p.z / 2, p.y / 2]}>
          <sphereGeometry args={[3, 6, 6]} />
          <meshBasicMaterial color={color} />
        </mesh>
      ))}
    </group>
  );
}

// Lander model
function Lander({ pose }) {
  const meshRef = useRef();
  
  useFrame(() => {
    if (meshRef.current && pose) {
      meshRef.current.position.set(pose.x / 2, pose.z / 2, pose.y / 2);
      meshRef.current.rotation.set(
        (pose.pitch || 0) * Math.PI / 180,
        (pose.yaw || 0) * Math.PI / 180,
        (pose.roll || 0) * Math.PI / 180
      );
    }
  });
  
  if (!pose) return null;
  
  return (
    <group ref={meshRef}>
      {/* Lander body */}
      <mesh castShadow>
        <coneGeometry args={[15, 30, 8]} />
        <meshStandardMaterial color="#C0C0C0" metalness={0.5} roughness={0.3} />
      </mesh>
      
      {/* Landing legs */}
      {[0, 90, 180, 270].map((angle, idx) => (
        <mesh 
          key={idx} 
          position={[
            Math.cos(angle * Math.PI / 180) * 12,
            -15,
            Math.sin(angle * Math.PI / 180) * 12
          ]}
          rotation={[0.3, angle * Math.PI / 180, 0]}
        >
          <cylinderGeometry args={[1, 1, 20]} />
          <meshStandardMaterial color="#808080" />
        </mesh>
      ))}
      
      {/* Thrust effect */}
      {pose.z > 10 && (
        <mesh position={[0, -25, 0]}>
          <coneGeometry args={[8, 30, 8]} />
          <meshBasicMaterial color="#FF6600" transparent opacity={0.6} />
        </mesh>
      )}
      
      {/* Coordinate axes */}
      <axesHelper args={[30]} />
    </group>
  );
}

// Camera controller for smooth following
function CameraController({ pose, followMode }) {
  const { camera } = useThree();
  
  useFrame(() => {
    if (followMode && pose) {
      const targetX = pose.x / 2;
      const targetY = pose.z / 2 + 200;
      const targetZ = pose.y / 2 + 300;
      
      camera.position.lerp(new THREE.Vector3(targetX, targetY, targetZ), 0.02);
      camera.lookAt(pose.x / 2, pose.z / 2, pose.y / 2);
    }
  });
  
  return null;
}

// Stars background
function Stars() {
  const starsRef = useRef();
  
  const positions = useMemo(() => {
    const pos = new Float32Array(3000);
    for (let i = 0; i < 1000; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 4000;
      pos[i * 3 + 1] = Math.random() * 2000 + 500;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 4000;
    }
    return pos;
  }, []);
  
  return (
    <points ref={starsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={1000}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={2} color="#FFFFFF" sizeAttenuation={false} />
    </points>
  );
}

// Main 3D Scene component
export default function Scene3D({ 
  terrainData, 
  currentPose, 
  groundTruthTrajectory,
  estimatedTrajectory,
  isRunning,
  followCamera = false 
}) {
  return (
    <Canvas shadows camera={{ position: [0, 600, 800], fov: 60 }}>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <directionalLight
        position={[200, 500, 300]}
        intensity={1}
        castShadow
      />
      <pointLight position={[-200, 300, -200]} intensity={0.3} />
      
      {/* Sky */}
      <color attach="background" args={['#0a0a1a']} />
      <fog attach="fog" args={['#0a0a1a', 500, 2000]} />
      
      {/* Stars */}
      <Stars />
      
      {/* Grid */}
      <Grid
        args={[2000, 2000]}
        cellSize={50}
        cellColor="#1a1a2e"
        sectionSize={200}
        sectionColor="#2a2a4e"
        fadeDistance={1500}
        infiniteGrid
      />
      
      {/* Terrain */}
      {terrainData && (
        <>
          <TerrainMesh heightmapData={terrainData.heightmap} />
          <FeatureMarkers features={terrainData.features} />
        </>
      )}
      
      {/* Trajectories */}
      <TrajectoryPath poses={groundTruthTrajectory} color="#00FF00" />
      <TrajectoryPath poses={estimatedTrajectory} color="#FF6600" />
      
      {/* Lander */}
      <Lander pose={currentPose} />
      
      {/* Camera control */}
      <CameraController pose={currentPose} followMode={followCamera} />
      <OrbitControls 
        enableDamping 
        dampingFactor={0.05}
        maxDistance={2000}
        minDistance={50}
      />
    </Canvas>
  );
}
