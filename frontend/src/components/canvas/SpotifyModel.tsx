import * as THREE from 'three'
import React, { useRef, useState } from 'react'
import { useGLTF, Float, Center, OrbitControls } from '@react-three/drei'
import type { GLTF } from 'three-stdlib'
import { useFrame } from '@react-three/fiber'

type GLTFResult = GLTF & {
  nodes: {
    ['tripo_node_f283790e-b79e-49be-9094-fce12c0c6dc5']: THREE.Mesh
  }
  materials: {
    ['tripo_mat_f283790e-b79e-49be-9094-fce12c0c6dc5']: THREE.MeshStandardMaterial
  }
}

export function SpotifyModel(props: React.JSX.IntrinsicElements['group']) {
  const { nodes, materials } = useGLTF('/SpotifyModel-transformed.glb') as unknown as GLTFResult
  const group = useRef<THREE.Group>(null!)
  const innerGroup = useRef<THREE.Group>(null!)
  const controlsRef = useRef<any>(null)
  const [isInteracting, setIsInteracting] = useState(false)

  useFrame((state) => {
    // 1. OrbitControls Auto-Return
    if (!isInteracting && controlsRef.current) {
      const currentAzimuth = controlsRef.current.getAzimuthalAngle()
      const currentPolar = controlsRef.current.getPolarAngle()

      controlsRef.current.setAzimuthalAngle(THREE.MathUtils.lerp(currentAzimuth, 0, 0.05))
      controlsRef.current.setPolarAngle(THREE.MathUtils.lerp(currentPolar, Math.PI / 2, 0.05))
      controlsRef.current.update()
    }

    // 2. 3D Idle Drift & Mouse Parallax (Applied to innerGroup)
    if (innerGroup.current) {
      const mouseTiltY = state.mouse.x * 0.2
      const mouseTiltX_target = -state.mouse.y * 0.2

      const breathing = !isInteracting ? Math.sin(state.clock.elapsedTime * 0.5) * 0.1 : 0

      // X-Axis: Look up/down + Breathing tilt 
      innerGroup.current.rotation.x = THREE.MathUtils.lerp(innerGroup.current.rotation.x, mouseTiltX_target + breathing, 0.1)

      // Z-Axis: Bank left/right based on mouse X
      innerGroup.current.rotation.z = THREE.MathUtils.lerp(innerGroup.current.rotation.z, -mouseTiltY, 0.1)

      // Y-Axis: Continuous slow spin when idle
      if (!isInteracting) {
        innerGroup.current.rotation.y += 0.005
      }
    }
  })

  React.useEffect(() => {
    const mat = materials['tripo_mat_f283790e-b79e-49be-9094-fce12c0c6dc5']
    if (mat) {
      mat.emissiveMap = mat.map
      mat.emissive = new THREE.Color('#1DB954')
      mat.emissiveIntensity = 4
      mat.toneMapped = false
      mat.roughness = 0.1
      mat.metalness = 0.8
      mat.needsUpdate = true
    }
  }, [materials])

  return (
    <group {...props} dispose={null}>
      {/* Interaction Controls */}
      <OrbitControls
        ref={controlsRef}
        enableZoom={false}
        enablePan={false}
        enableDamping={true}
        onStart={() => setIsInteracting(true)}
        onEnd={() => setIsInteracting(false)}
      />

      {/* Unified Group for Particles + Model */}
      <group ref={innerGroup}>
        <EnergyPlume />

        <Float
          speed={2}
          rotationIntensity={0.5}
          floatIntensity={0.5}
          floatingRange={[-0.1, 0.1]}
        >
          <Center>
            {/* Rotate X by 90deg if needed to face user, dependent on model bake */}
            <group ref={group} rotation={[0, -Math.PI / 2, 0]}>
              <mesh
                geometry={nodes['tripo_node_f283790e-b79e-49be-9094-fce12c0c6dc5'].geometry}
                material={materials['tripo_mat_f283790e-b79e-49be-9094-fce12c0c6dc5']}
                scale={[1.5, 1.5, 1.5]}
              />
            </group>
          </Center>
        </Float>
      </group>
    </group>
  )
}

function EnergyPlume() {
  const count = 60
  // useMemo for static initializations
  const { positions, randoms, sizes } = React.useMemo(() => {
    const positions = new Float32Array(count * 3)
    const randoms = new Float32Array(count * 3)
    const sizes = new Float32Array(count)

    for (let i = 0; i < count; i++) {
      // Initial X: range -0.5 to 0.5
      positions[i * 3] = (Math.random() - 0.5) * 1.0
      // Initial Y: starts lower
      positions[i * 3 + 1] = -0.4
      // Initial Z: Random spread for volumetric depth (-0.1 to -0.4 range approx)
      positions[i * 3 + 2] = -0.25 + (Math.random() + 0.2) * 0.3

      // Randoms
      randoms[i * 3] = Math.random() * Math.PI * 2 // Phase
      // Speed: Much slower (approx 0.008 avg)
      randoms[i * 3 + 1] = 0.003 + Math.random() * 0.01
      randoms[i * 3 + 2] = (Math.random() - 0.5) * 0.5 // X drift

      // Size
      sizes[i] = 0.1 + Math.random() * 0.03
    }
    return { positions, randoms, sizes }
  }, [])

  const pointsRef = useRef<THREE.Points>(null!)

  const shaderMaterial = React.useMemo(() => new THREE.ShaderMaterial({
    uniforms: {
      uColor: { value: new THREE.Color('#1DB954') },
      uTime: { value: 0 }
    },
    vertexShader: `
      attribute float size;
      varying float vOpacity;
      void main() {
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        gl_Position = projectionMatrix * mvPosition;
        
        gl_PointSize = size * (300.0 / -mvPosition.z);
        
        // Opacity fade over longer distance (-0.4 to 3.5 = range 4.3)
        // Fade out mostly at the top 30%
        float normalizedY = (position.y - (-0.4)) / 4.3;
        vOpacity = 1.0 - (normalizedY * 0.5); // Fade a bit faster than full height
        if (vOpacity < 0.0) vOpacity = 0.0;
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      varying float vOpacity;
      void main() {
        vec2 coord = gl_PointCoord - vec2(0.5);
        float dist = length(coord);
        if (dist > 0.5) discard;
        
        // Soft edge
        float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
        // Boosted color (3.0x) for neon glow
        gl_FragColor = vec4(uColor * 3.0, vOpacity * alpha * 0.6);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false
  }), [])

  useFrame((state) => {
    if (!pointsRef.current) return
    const positionsAttr = pointsRef.current.geometry.attributes.position
    const time = state.clock.getElapsedTime()

    for (let i = 0; i < count; i++) {
      let x = positionsAttr.getX(i)
      let y = positionsAttr.getY(i)

      const speed = randoms[i * 3 + 1]
      const wigglePhase = randoms[i * 3]

      // Rise slowly
      y += speed

      // Gentle Wiggle
      x += Math.sin(time * 2.0 + wigglePhase) * 0.001

      // Reset Height increased to 3.5
      if (y > 3.5) {
        y = -0.4
        x = (Math.random() - 0.5) * 0.8
      }

      positionsAttr.setXY(i, x, y)
    }
    positionsAttr.needsUpdate = true
  })

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={positions.length / 3}
          array={positions}
          itemSize={3}
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-size"
          count={sizes.length}
          array={sizes}
          itemSize={1}
          args={[sizes, 1]}
        />
      </bufferGeometry>
      <primitive object={shaderMaterial} attach="material" />
    </points>
  )
}

useGLTF.preload('/SpotifyModel-transformed.glb')