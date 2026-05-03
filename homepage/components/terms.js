import React from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { motion } from 'framer-motion'

export default function Terms() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 text-white">
      <Head>
        <title>Terms and Conditions / Privacy Policy</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-4xl font-bold mb-8">Terms and Conditions / Privacy Policy</h1>
          
          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">Terms of Use</h2>
            <p className="mb-4">By using the AI-Powered Cold Email Generator, you agree to the following terms:</p>
            <ul className="list-disc list-inside space-y-2">
              <li>You will use this tool responsibly and ethically</li>
              <li>You will not use this tool to send spam or unsolicited emails</li>
              <li>You understand that the AI-generated content may require human review and editing</li>
              <li>You accept that the tool's functionality is subject to API limitations and quotas</li>
            </ul>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">Privacy Policy</h2>
            <p className="mb-4">We are committed to protecting your privacy. Here's how we handle your data:</p>
            <ul className="list-disc list-inside space-y-2">
              <li>We only access the Gmail data necessary for email generation and sending</li>
              <li>Your resume and job listing information is processed securely and not stored permanently</li>
              <li>We do not sell or share your personal information with third parties</li>
              <li>You can revoke access to your Google account at any time</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">Limitations</h2>
            <ul className="list-disc list-inside space-y-2">
              <li>Email generation is limited to 5 per day with a 60-second cooldown between generations</li>
              <li>The tool's functionality depends on the availability and terms of the Google APIs used</li>
              <li>We do not guarantee the success or appropriateness of the generated emails for all situations</li>
            </ul>
          </section>
        </motion.div>

        <motion.div
          className="mt-12 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <Link href="/" className="text-sm underline hover:text-blue-300 transition duration-300">
            Back to Home
          </Link>
        </motion.div>
      </main>
    </div>
  )
}