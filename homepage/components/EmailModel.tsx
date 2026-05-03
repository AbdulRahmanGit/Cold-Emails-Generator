import React, { useRef, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

export default function EmailModel() {
  const meshRef = useRef<THREE.Mesh>(null)

  useEffect(() => {
    if (meshRef.current) {
      meshRef.current.rotation.x = Math.PI / 5
      meshRef.current.rotation.y = Math.PI / 5
    }
  }, [])

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01
    }
  })

  return (
    <mesh ref={meshRef}>
      <boxGeometry args={[1, 0.8, 0.1]} />
      <meshStandardMaterial color="#4A90E2" />
    </mesh>
  )
}