import React, { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, Line, Text, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';

// Terrain mesh component
function TerrainMesh({ heightmapData, features }) {
  const meshRef = useRef();
  
  const geometry = useMemo(() => {
    if (!heightmapData || !heightmapData.data) return null;
    
    const { data, width, height, scale } = heightmapData;
    const geo = new THREE.PlaneGeometry(scale, scale, width - 1, height - 1);
    
    // Apply heightmap to vertices
    const positions = geo.attributes.position.array;
    for (let i = 0; i < positions.length / 3; i++) {
      const x = Math.floor((i % width));
      const y = Math.floor(i / width);
      if (y < data.length && x < data[0].length) {
        positions[i * 3 + 2] = data[y][x] * 50; // Scale height for visibility
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
        wireframe={false}
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
      {features.slice(0, 50).map((feature, idx) => (
        <mesh
          key={idx}
          position={[feature.x / 2, (feature.z || 0) * 50 + 5, feature.y / 2]}
        >
          <sphereGeometry args={[feature.size / 5, 8, 8]} />
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

// Trajectory line
function TrajectoryLine({ poses, color = '#00FF00', lineWidth = 2 }) {
  if (!poses || poses.length < 2) return null;
  
  const points = useMemo(() => {
    return poses.map(p => new THREE.Vector3(p.x / 2, p.z / 2, p.y / 2));
  }, [poses]);
  
  return (
    <Line
      points={points}
      color={color}
      lineWidth={lineWidth}
    />
  );
}

// Lander model
function Lander({ pose, showAxes = true }) {
  const meshRef = useRef();
  
  useFrame(() => {
    if (meshRef.current && pose) {
      meshRef.current.position.set(pose.x / 2, pose.z / 2, pose.y / 2);
      meshRef.current.rotation.set(
        pose.pitch * Math.PI / 180,
        pose.yaw * Math.PI / 180,
        pose.roll * Math.PI / 180
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
      {showAxes && (
        <axesHelper args={[30]} />
      )}
    </group>
  );
}

// Event visualization as particles
function EventParticles({ events }) {
  const pointsRef = useRef();
  
  const { positions, colors } = useMemo(() => {
    if (!events || !events.length) {
      return { positions: new Float32Array(0), colors: new Float32Array(0) };
    }
    
    const pos = new Float32Array(events.length * 3);
    const col = new Float32Array(events.length * 3);
    
    events.forEach((event, i) => {
      // Map 2D event coordinates to 3D space around lander
      pos[i * 3] = (event.x - 320) / 10;
      pos[i * 3 + 1] = 100 + Math.random() * 50;
      pos[i * 3 + 2] = (event.y - 240) / 10;
      
      // Color based on polarity
      if (event.polarity > 0) {
        col[i * 3] = 0;      // R
        col[i * 3 + 1] = 0.3;  // G
        col[i * 3 + 2] = 1;   // B
      } else {
        col[i * 3] = 1;     // R
        col[i * 3 + 1] = 0.4; // G
        col[i * 3 + 2] = 0;   // B
      }
    });
    
    return { positions: pos, colors: col };
  }, [events]);
  
  if (positions.length === 0) return null;
  
  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={positions.length / 3}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={colors.length / 3}
          array={colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={2} vertexColors />
    </points>
  );
}

// Corner detection visualization
function CornerMarkers({ corners }) {
  if (!corners || !corners.length) return null;
  
  return (
    <group>
      {corners.map((corner, idx) => (
        <mesh
          key={idx}
          position={[(corner.x - 320) / 5, 150, (corner.y - 240) / 5]}
        >
          <octahedronGeometry args={[3]} />
          <meshBasicMaterial color="#FFFF00" wireframe />
        </mesh>
      ))}
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

// HUD overlay
function HUD({ altitude, speed, status }) {
  return (
    <group position={[0, 600, 0]}>
      <Text
        position={[-200, 0, 0]}
        fontSize={20}
        color="white"
        anchorX="left"
      >
        {`ALT: ${altitude?.toFixed(1) || 0}m`}
      </Text>
      <Text
        position={[0, 0, 0]}
        fontSize={20}
        color="white"
        anchorX="center"
      >
        {status || 'READY'}
      </Text>
    </group>
  );
}

// Main 3D Scene component
export default function Scene3D({ 
  terrainData, 
  currentPose, 
  groundTruthTrajectory,
  estimatedTrajectory,
  events,
  corners,
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
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
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
          <TerrainMesh 
            heightmapData={terrainData.heightmap} 
            features={terrainData.features}
          />
          <FeatureMarkers features={terrainData.features} />
        </>
      )}
      
      {/* Trajectories */}
      <TrajectoryLine poses={groundTruthTrajectory} color="#00FF00" lineWidth={3} />
      <TrajectoryLine poses={estimatedTrajectory} color="#FF6600" lineWidth={2} />
      
      {/* Lander */}
      <Lander pose={currentPose} />
      
      {/* Events visualization */}
      <EventParticles events={events} />
      
      {/* Corner detections */}
      <CornerMarkers corners={corners} />
      
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
