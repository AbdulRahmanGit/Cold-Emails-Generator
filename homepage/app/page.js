"use client";
import React, { useEffect, useRef } from "react";
import Head from "next/head";
import Link from "next/link";
import { motion, useAnimation } from "framer-motion";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

export default function Home() {
  const controls = useAnimation();
  const containerRef = useRef(null);

  useEffect(() => {
    controls.start({
      opacity: 1,
      y: 0,
      transition: { duration: 0.8, ease: "easeOut" },
    });
  }, [controls]);

  const EmailModel = () => {
    const meshRef = useRef();

    useEffect(() => {
      if (meshRef.current) {
        meshRef.current.rotation.x = Math.PI / 5;
        meshRef.current.rotation.y = Math.PI / 5;
      }
    }, []);

    return (
      <mesh ref={meshRef} castShadow>
        <boxGeometry args={[1, 0.8, 0.1]} />
        <meshStandardMaterial color="#4A90E2" />
      </mesh>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 text-white">
      <Head>
        <title>AI-Powered Cold Email Generator</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={controls}
          className="text-center"
        >
          <h1 className="text-5xl font-bold mb-6">
            AI-Powered Cold Email Generator
          </h1>
          <p className="text-xl mb-12">
            Revolutionize your job search with personalized, AI-generated cold
            emails
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            <h2 className="text-3xl font-semibold mb-4">Key Features</h2>
            <motion.ul
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                delay: 0.2,
                duration: 0.8,
                staggerChildren: 0.1,
              }}
              className="list-disc list-inside space-y-2"
            >
              <li>Personalized emails based on job listings and your resume</li>
              <li>Secure Gmail integration with OAuth2</li>
              <li>AI-powered content generation using Google's Gemini model</li>
              <li>Direct email sending through Gmail API</li>
              <li>User-friendly interface built with Streamlit</li>
            </motion.ul>
          </motion.div>

          <div className="h-64 w-full" ref={containerRef}>
            <Canvas shadows>
              <ambientLight intensity={0.8} />
              <spotLight
                position={[10, 10, 10]}
                angle={0.3}
                penumbra={1}
                intensity={1}
                castShadow
              />
              <EmailModel />
              <OrbitControls enableZoom={true} autoRotate={true} />
            </Canvas>
          </div>
        </div>

        <motion.div
          className="mt-16 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <Link
            href="/auth/google"
            className="bg-white text-blue-900 px-8 py-3 rounded-full text-lg font-semibold hover:bg-blue-100 hover:scale-105 transition duration-300"
          >
            Get Started with Google
          </Link>
        </motion.div>

        <motion.div
          className="mt-12 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.8 }}
        >
          <Link
            href="/terms"
            className="text-sm underline hover:text-blue-300 transition duration-300"
          >
            Terms and Conditions / Privacy Policy
          </Link>
        </motion.div>
      </main>
    </div>
  );
}
