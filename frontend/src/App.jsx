import { useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import ResultPanel from './components/ResultPanel'
import D2Module from './components/D2Module'
import Footer from './components/Footer'

const DEMO_RESULT = {
  predicted_host: 'fungi',
  confidence: 0.962,
  probabilities: {
    fungi:        0.962,
    bacteria:     0.018,
    algae:        0.009,
    protozoa:     0.006,
    plant:        0.003,
    invertebrate: 0.002,
  },
  genome_length: 9651,
  gc_content: 42.3,
  auto_translated: false,
  protein_count: 2,
  short_genome: false,
  d1_contribution: 0.40,
  d2_contribution: 0.60,
  top_kmers: [
    { kmer: 'ATG', enrichment: 1.82 },
    { kmer: 'CGT', enrichment: 1.74 },
    { kmer: 'GCT', enrichment: 1.61 },
    { kmer: 'TAC', enrichment: 1.55 },
    { kmer: 'AGC', enrichment: 1.48 },
    { kmer: 'TGG', enrichment: 1.39 },
  ],
}

const DEMO_RESULT_ORF = {
  ...DEMO_RESULT,
  confidence: 0.708,
  probabilities: {
    fungi:        0.708,
    bacteria:     0.112,
    algae:        0.082,
    protozoa:     0.054,
    plant:        0.028,
    invertebrate: 0.016,
  },
  auto_translated: true,
  protein_count: 3,
  d1_contribution: 0.70,
  d2_contribution: 0.30,
}

const makeBatchDemo = (n) =>
  Array.from({ length: n }, (_, i) => ({
    id: `sequence_${String(i + 1).padStart(3, '0')}`,
    length: 5000 + Math.floor(Math.random() * 50000),
    gc: (38 + Math.random() * 20).toFixed(1),
    predicted_host: ['fungi', 'bacteria', 'algae', 'plant', 'protozoa', 'invertebrate'][
      Math.floor(Math.random() * 6)
    ],
    confidence: (0.6 + Math.random() * 0.38).toFixed(3),
    orfs: Math.floor(3 + Math.random() * 12),
    short: false,
  }))

export default function App() {
  const [result, setResult]             = useState(null)
  const [analyzing, setAnalyzing]       = useState(false)
  const [apiError, setApiError]         = useState('')
  const [batchResults, setBatchResults] = useState(null)
  const [batchAnalyzing, setBatchAnalyzing] = useState(false)

  const handleAnalyze = async ({ genome, proteins }) => {
    setAnalyzing(true)
    setResult(null)
    setApiError('')
    try {
      const res = await fetch('/api/predict/sequence', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ genome, proteins }),
      })
      const data = await res.json()
      if (!res.ok) {
        setApiError(data.error || `Server error ${res.status}`)
      } else {
        setResult(data)
      }
    } catch {
      setApiError('Cannot reach the prediction server — is Docker running?')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleBatchAnalyze = async (count) => {
    setBatchAnalyzing(true)
    setBatchResults(null)
    await new Promise(r => setTimeout(r, 1500 + count * 20))
    setBatchResults(makeBatchDemo(count))
    setBatchAnalyzing(false)
  }

  return (
    <div className="min-h-screen bg-navy-900 text-white overflow-x-hidden">
      {/* Ambient blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
      </div>

      <div className="relative z-10">
        <Navbar />

        {/* Hero + Results in one continuous section */}
        <div className="max-w-7xl mx-auto px-6 pt-24 pb-12">
          <Hero
            onAnalyze={handleAnalyze}
            analyzing={analyzing}
            hasResult={!!result}
            apiError={apiError}
            onBatchAnalyze={handleBatchAnalyze}
            batchAnalyzing={batchAnalyzing}
            batchResults={batchResults}
            setBatchResults={setBatchResults}
          />

          {/* Result renders directly below input — no scroll needed */}
          <AnimatePresence mode="wait">
            {(result || analyzing) && (
              <ResultPanel key="result" result={result} analyzing={analyzing} />
            )}
          </AnimatePresence>
        </div>

        <D2Module />
        <Footer />
      </div>
    </div>
  )
}
