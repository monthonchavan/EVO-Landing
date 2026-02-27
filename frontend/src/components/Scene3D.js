import React, { useRef, useMemo, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

// Simple Ground Plane
function GroundPlane() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]} receiveShadow>
      <planeGeometry args={[2000, 2000]} />
      <meshStandardMaterial color="#1a1a2e" />
    </mesh>
  );
}

// Terrain mesh component
function TerrainMesh({ heightmapData }) {
  const meshRef = useRef();
  
  const geometry = useMemo(() => {
    if (!heightmapData || !heightmapData.data) return null;
    
    const { data, scale } = heightmapData;
    const width = Math.min(data[0]?.length || 64, 64);
    const height = Math.min(data.length, 64);
    
    const geo = new THREE.PlaneGeometry(scale || 1000, scale || 1000, width - 1, height - 1);
    
    const positions = geo.attributes.position.array;
    const stepX = (data[0]?.length || 64) / width;
    const stepY = data.length / height;
    
    for (let i = 0; i < height; i++) {
      for (let j = 0; j < width; j++) {
        const idx = i * width + j;
        const dataX = Math.floor(j * stepX);
        const dataY = Math.floor(i * stepY);
        if (dataY < data.length && data[dataY] && dataX < data[dataY].length) {
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
      <mesh castShadow>
        <coneGeometry args={[15, 30, 8]} />
        <meshStandardMaterial color="#C0C0C0" metalness={0.5} roughness={0.3} />
      </mesh>
      
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
      
      {pose.z > 10 && (
        <mesh position={[0, -25, 0]}>
          <coneGeometry args={[8, 30, 8]} />
          <meshBasicMaterial color="#FF6600" transparent opacity={0.6} />
        </mesh>
      )}
      
      <axesHelper args={[30]} />
    </group>
  );
}

// Camera controller
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
    <points>
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

// Loading fallback
function LoadingFallback() {
  return (
    <mesh position={[0, 0, 0]}>
      <boxGeometry args={[50, 50, 50]} />
      <meshStandardMaterial color="#666" />
    </mesh>
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
    <Canvas 
      shadows 
      camera={{ position: [0, 600, 800], fov: 60 }}
      onCreated={({ gl }) => {
        gl.setClearColor('#0a0a1a');
      }}
    >
      <Suspense fallback={<LoadingFallback />}>
        <ambientLight intensity={0.4} />
        <directionalLight position={[200, 500, 300]} intensity={1} castShadow />
        <pointLight position={[-200, 300, -200]} intensity={0.3} />
        
        <fog attach="fog" args={['#0a0a1a', 500, 2000]} />
        
        <Stars />
        <GroundPlane />
        
        {terrainData && (
          <>
            <TerrainMesh heightmapData={terrainData.heightmap} />
            <FeatureMarkers features={terrainData.features} />
          </>
        )}
        
        <TrajectoryPath poses={groundTruthTrajectory} color="#00FF00" />
        <TrajectoryPath poses={estimatedTrajectory} color="#FF6600" />
        
        <Lander pose={currentPose} />
        
        <CameraController pose={currentPose} followMode={followCamera} />
        <OrbitControls 
          enableDamping 
          dampingFactor={0.05}
          maxDistance={2000}
          minDistance={50}
        />
      </Suspense>
    </Canvas>
  );
}
