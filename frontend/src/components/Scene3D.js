import React, { useRef, useMemo, useEffect } from 'react';

// Simple 3D scene using vanilla Three.js
export default function Scene3D({ 
  terrainData, 
  currentPose, 
  groundTruthTrajectory,
  estimatedTrajectory,
  isRunning,
  followCamera = false 
}) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  
  useEffect(() => {
    // Dynamically import Three.js to avoid SSR issues
    import('three').then((THREE) => {
      if (!containerRef.current) return;
      
      // Create scene
      const scene = new THREE.Scene();
      scene.background = new THREE.Color('#0a0a1a');
      scene.fog = new THREE.Fog('#0a0a1a', 500, 2000);
      
      // Camera
      const camera = new THREE.PerspectiveCamera(
        60,
        containerRef.current.clientWidth / containerRef.current.clientHeight,
        1,
        5000
      );
      camera.position.set(0, 600, 800);
      
      // Renderer
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
      renderer.shadowMap.enabled = true;
      containerRef.current.appendChild(renderer.domElement);
      
      // Lighting
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
      directionalLight.position.set(200, 500, 300);
      directionalLight.castShadow = true;
      scene.add(directionalLight);
      
      // Ground plane
      const groundGeo = new THREE.PlaneGeometry(2000, 2000);
      const groundMat = new THREE.MeshStandardMaterial({ color: '#1a1a2e' });
      const ground = new THREE.Mesh(groundGeo, groundMat);
      ground.rotation.x = -Math.PI / 2;
      ground.position.y = -1;
      ground.receiveShadow = true;
      scene.add(ground);
      
      // Terrain
      if (terrainData && terrainData.heightmap && terrainData.heightmap.data) {
        const { data, scale } = terrainData.heightmap;
        const width = Math.min(data[0]?.length || 64, 64);
        const height = Math.min(data.length, 64);
        
        const terrainGeo = new THREE.PlaneGeometry(scale || 1000, scale || 1000, width - 1, height - 1);
        const positions = terrainGeo.attributes.position.array;
        
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
        terrainGeo.computeVertexNormals();
        
        const terrainMat = new THREE.MeshStandardMaterial({ 
          color: '#8B7355',
          roughness: 0.9,
          side: THREE.DoubleSide
        });
        const terrain = new THREE.Mesh(terrainGeo, terrainMat);
        terrain.rotation.x = -Math.PI / 2;
        terrain.receiveShadow = true;
        scene.add(terrain);
      }
      
      // Lander
      const landerGroup = new THREE.Group();
      
      const bodyGeo = new THREE.ConeGeometry(15, 30, 8);
      const bodyMat = new THREE.MeshStandardMaterial({ color: '#C0C0C0', metalness: 0.5 });
      const body = new THREE.Mesh(bodyGeo, bodyMat);
      body.castShadow = true;
      landerGroup.add(body);
      
      // Landing legs
      const legGeo = new THREE.CylinderGeometry(1, 1, 20);
      const legMat = new THREE.MeshStandardMaterial({ color: '#808080' });
      [0, 90, 180, 270].forEach(angle => {
        const leg = new THREE.Mesh(legGeo, legMat);
        leg.position.set(
          Math.cos(angle * Math.PI / 180) * 12,
          -15,
          Math.sin(angle * Math.PI / 180) * 12
        );
        leg.rotation.set(0.3, angle * Math.PI / 180, 0);
        landerGroup.add(leg);
      });
      
      // Thrust effect
      const thrustGeo = new THREE.ConeGeometry(8, 30, 8);
      const thrustMat = new THREE.MeshBasicMaterial({ 
        color: '#FF6600', 
        transparent: true, 
        opacity: 0.6 
      });
      const thrust = new THREE.Mesh(thrustGeo, thrustMat);
      thrust.position.y = -25;
      landerGroup.add(thrust);
      
      // Axes helper
      const axes = new THREE.AxesHelper(30);
      landerGroup.add(axes);
      
      landerGroup.position.set(0, 500, 0);
      scene.add(landerGroup);
      
      // Stars
      const starsGeo = new THREE.BufferGeometry();
      const starPositions = new Float32Array(3000);
      for (let i = 0; i < 1000; i++) {
        starPositions[i * 3] = (Math.random() - 0.5) * 4000;
        starPositions[i * 3 + 1] = Math.random() * 2000 + 500;
        starPositions[i * 3 + 2] = (Math.random() - 0.5) * 4000;
      }
      starsGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
      const starsMat = new THREE.PointsMaterial({ color: '#ffffff', size: 2, sizeAttenuation: false });
      const stars = new THREE.Points(starsGeo, starsMat);
      scene.add(stars);
      
      // OrbitControls
      import('three/examples/jsm/controls/OrbitControls.js').then(({ OrbitControls }) => {
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxDistance = 2000;
        controls.minDistance = 50;
        
        sceneRef.current = { scene, camera, renderer, controls, landerGroup, thrust };
      });
      
      // Animation loop
      const animate = () => {
        requestAnimationFrame(animate);
        if (sceneRef.current?.controls) {
          sceneRef.current.controls.update();
        }
        renderer.render(scene, camera);
      };
      animate();
      
      // Handle resize
      const handleResize = () => {
        if (!containerRef.current) return;
        camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
      };
      window.addEventListener('resize', handleResize);
      
      // Cleanup
      return () => {
        window.removeEventListener('resize', handleResize);
        if (containerRef.current && renderer.domElement) {
          containerRef.current.removeChild(renderer.domElement);
        }
        renderer.dispose();
      };
    });
  }, [terrainData]);
  
  // Update lander position
  useEffect(() => {
    if (sceneRef.current && currentPose) {
      const { landerGroup, thrust } = sceneRef.current;
      if (landerGroup) {
        landerGroup.position.set(
          currentPose.x / 2,
          currentPose.z / 2,
          currentPose.y / 2
        );
        landerGroup.rotation.set(
          (currentPose.pitch || 0) * Math.PI / 180,
          (currentPose.yaw || 0) * Math.PI / 180,
          (currentPose.roll || 0) * Math.PI / 180
        );
        
        // Show/hide thrust
        if (thrust) {
          thrust.visible = currentPose.z > 10;
        }
      }
    }
  }, [currentPose]);
  
  return (
    <div 
      ref={containerRef} 
      style={{ 
        width: '100%', 
        height: '100%', 
        minHeight: '500px',
        background: '#0a0a1a',
        borderRadius: '8px',
        overflow: 'hidden'
      }}
    />
  );
}
