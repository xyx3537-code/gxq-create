import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Zap, ChevronRight, AlertCircle, Layers,
  Upload, FileText, Download, Clipboard,
} from 'lucide-react'


const HOST_COLORS = {
  fungi: '#34d399', algae: '#38bdf8', protozoa: '#fbbf24',
  bacteria: '#f87171', plant: '#4ade80', invertebrate: '#c084fc',
}
const HOST_CN   = { fungi:'Fungi', algae:'Algae', protozoa:'Protozoa', bacteria:'Bacteria', plant:'Plant', invertebrate:'Invertebrate' }
const HOST_ICON = { fungi:'🍄', algae:'🌊', protozoa:'🔬', bacteria:'🦠', plant:'🌿', invertebrate:'🦋' }

function parseFasta(text) {
  const clean = text.trim()
  if (!clean) return ''
  if (clean.startsWith('>')) return clean.split('\n').filter(l => !l.startsWith('>')).join('').replace(/\s/g, '')
  return clean.replace(/\s+/g, '')
}

function parseMultiFasta(text) {
  return text.trim().split(/(?=>)/).filter(Boolean).map(b => {
    const lines = b.trim().split('\n')
    return { id: lines[0].replace('>', '').split(' ')[0], seq: lines.slice(1).join('').replace(/\s/g, '') }
  }).filter(r => r.seq.length >= 100)
}

// ── Batch result table ────────────────────────────────────
function BatchTable({ results, analyzing }) {
  if (analyzing) return (
    <div className="mt-6 flex items-center gap-3 py-6 text-white/40 text-sm">
      <div className="w-5 h-5 border-2 border-white/20 border-t-blue-400 rounded-full animate-spin" />
      Predicting sequences…
    </div>
  )
  if (!results) return null

  const csv = ['ID,Length,GC%,Predicted Host,Confidence,ORFs',
    ...results.map(r => `${r.id},${r.length},${r.gc},${r.predicted_host},${(r.confidence*100).toFixed(1)}%,${r.orfs}`)
  ].join('\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))

  const dist = {}
  results.forEach(r => { dist[r.predicted_host] = (dist[r.predicted_host] || 0) + 1 })

  return (
    <motion.div initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }} className="mt-5 space-y-4">
      {/* Summary */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(dist).sort((a,b)=>b[1]-a[1]).map(([h,n]) => (
          <span key={h} className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
            style={{ background:`${HOST_COLORS[h]}15`, color:HOST_COLORS[h], border:`1px solid ${HOST_COLORS[h]}30` }}>
            {HOST_ICON[h]} {HOST_CN[h]} ×{n}
          </span>
        ))}
        <span className="px-2.5 py-1 rounded-full text-xs text-white/35 border border-white/10">
          {results.length} total
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-white/[0.06] max-h-72 overflow-y-auto">
        <table className="w-full text-xs">
          <thead className="sticky top-0">
            <tr className="bg-navy-800 border-b border-white/[0.06]">
              {['Sequence ID','Length','GC%','Host','Confidence','ORFs'].map(h=>(
                <th key={h} className="px-3 py-2.5 text-left text-white/35 font-medium whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.slice(0,100).map((r,i)=>(
              <tr key={r.id} className={`border-b border-white/[0.04] ${i%2?'bg-white/[0.01]':''}`}>
                <td className="px-3 py-2 font-mono text-white/60 max-w-[140px] truncate">{r.id}</td>
                <td className="px-3 py-2 text-white/50">{Number(r.length).toLocaleString()}</td>
                <td className="px-3 py-2 text-white/50">{r.gc}%</td>
                <td className="px-3 py-2">
                  <span className="flex items-center gap-1 font-medium" style={{color:HOST_COLORS[r.predicted_host]}}>
                    {HOST_ICON[r.predicted_host]} {HOST_CN[r.predicted_host]}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="w-14 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <div className="h-full rounded-full" style={{width:`${r.confidence*100}%`,background:HOST_COLORS[r.predicted_host]}}/>
                    </div>
                    <span className="text-white/50">{(r.confidence*100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-3 py-2 text-white/40">{r.orfs}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {results.length > 100 && (
          <div className="px-3 py-2 text-xs text-white/25 text-center border-t border-white/[0.04]">
            Showing 100 of {results.length}
          </div>
        )}
      </div>

      <a href={url} download="gxq_predictions.csv"
        className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl
                   border border-white/10 text-sm text-white/60 hover:text-white hover:border-white/25 transition-all">
        <Download size={14}/> Download CSV
      </a>
    </motion.div>
  )
}

// ── Main Hero ─────────────────────────────────────────────
export default function Hero({ onAnalyze, analyzing, hasResult, apiError, onBatchAnalyze, batchAnalyzing, batchResults, setBatchResults }) {
  const [tab, setTab]         = useState('single')
  const [genome, setGenome]   = useState('')
  const [proteins, setProteins] = useState('')
  const [dragging, setDragging] = useState(false)
  const [batchSeqs, setBatchSeqs] = useState([])
  const [error, setError]     = useState('')
  const fileRef  = useRef()
  const batchRef = useRef()

  const handleSingleFile = useCallback((file) => {
    if (!file) return
    new FileReader().addEventListener
    const r = new FileReader()
    r.onload = e => { setGenome(e.target.result); setError('') }
    r.readAsText(file)
  }, [])

  const handleBatchFile = useCallback((file) => {
    if (!file) return
    const r = new FileReader()
    r.onload = e => {
      const seqs = parseMultiFasta(e.target.result)
      if (!seqs.length) { setError('No valid sequences (min 100 bp each).'); return }
      setBatchSeqs(seqs.slice(0, 500))
      setBatchResults(null)
      setError('')
    }
    r.readAsText(file)
  }, [setBatchResults])

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragging(false)
    const file = e.dataTransfer.files[0]
    if (tab === 'single') handleSingleFile(file)
    else handleBatchFile(file)
  }, [tab, handleSingleFile, handleBatchFile])

  const handleRun = () => {
    const seq = parseFasta(genome)
    if (!seq || seq.length < 100) { setError('Sequence too short — need at least 100 bp.'); return }
    setError('')
    // 解析多条蛋白质 FASTA → 氨基酸序列数组
    const protList = proteins.trim()
      ? proteins.trim().split(/(?=>)/).filter(Boolean).map(b =>
          b.split('\n').filter(l => !l.startsWith('>')).join('').replace(/\s/g, '')
        ).filter(s => s.length >= 10)
      : []
    onAnalyze({ genome: seq, proteins: protList })
  }

  const loadExample = async () => {
    try {
      const res  = await fetch('/api/example')
      const data = await res.json()
      if (data.genome_fasta) {
        setGenome(data.genome_fasta)
        setProteins(data.protein_fasta || '')
        setError('')
      }
    } catch {
      setError('Could not load example — is the server running?')
    }
  }

  const seqLen = parseFasta(genome).length
  const ready  = seqLen >= 100

  return (
    <div>
      {/* ── Title block ─────────────────────────────────── */}
      <motion.div initial={{ opacity:0, y:24 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.6 }}
        className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass border border-blue-400/20
                       text-blue-300 text-xs font-medium mb-5">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          D1 · k-mer SVM &nbsp;·&nbsp; D2 · ESM-2 Protein LM &nbsp;·&nbsp; 96.4% Accuracy
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight mb-4">
          Predict Environmental
          <span className="gradient-text block">Virus Hosts</span>
        </h1>

        <p className="text-white/50 text-base sm:text-lg max-w-2xl mx-auto">
          Dual-modal framework: genomic k-mer analysis + ESM-2 protein language model,
          fused for 6-class eukaryotic host prediction.
        </p>

        {/* Stats */}
        <div className="flex items-center justify-center gap-6 sm:gap-10 mt-6 text-sm">
          {[
            { v:'96.4%',   l:'Cross-val accuracy' },
            { v:'6',       l:'Host categories' },
            { v:'860',     l:'Training genomes' },
            { v:'320-dim', l:'ESM-2 embedding' },
          ].map(s=>(
            <div key={s.l} className="text-center">
              <div className="text-blue-300 font-bold">{s.v}</div>
              <div className="text-white/30 text-xs hidden sm:block">{s.l}</div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* ── Input card ──────────────────────────────────── */}
      <motion.div initial={{ opacity:0, y:28 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.15, duration:0.55 }}
        className="max-w-3xl mx-auto">
        <div className="glass rounded-2xl gradient-border p-6 shadow-[0_8px_60px_rgba(0,0,0,0.35)]">

          {/* Single / Batch tabs */}
          <div className="flex gap-1 p-1 rounded-xl bg-white/[0.03] border border-white/[0.05] w-fit mb-5">
            {[
              { id:'single', icon:<Clipboard size={13}/>, label:'Single Prediction' },
              { id:'batch',  icon:<Layers size={13}/>,    label:'Batch Prediction'  },
            ].map(t=>(
              <button key={t.id} onClick={()=>{setTab(t.id);setError('')}}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  tab===t.id ? 'bg-blue-500/20 text-blue-300' : 'text-white/40 hover:text-white/70'
                }`}>
                {t.icon} {t.label}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">

          {/* ── Single prediction ── */}
          {tab === 'single' && (
            <motion.div key="single" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>

              {/* Genome */}
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] text-white/35 font-mono uppercase tracking-wide">
                  Genome DNA <span className="text-blue-400/60">· required</span>
                </label>
                <div className="flex gap-1">
                  <button onClick={loadExample}
                    className="text-[11px] text-blue-400/80 hover:text-blue-300 transition-colors px-2 py-0.5 rounded border border-blue-400/35 hover:border-blue-400/60 bg-blue-400/[0.04] hover:bg-blue-400/[0.08]">
                    Load example
                  </button>
                  <button onClick={()=>fileRef.current?.click()}
                    className="text-[11px] text-white/50 hover:text-white/80 transition-colors px-2 py-0.5 rounded border border-white/[0.18] hover:border-white/30 flex items-center gap-1">
                    <Upload size={10}/> File
                  </button>
                  <input ref={fileRef} type="file" accept=".fasta,.fa,.fna" className="hidden"
                    onChange={e=>handleSingleFile(e.target.files[0])}/>
                </div>
              </div>
              <textarea value={genome} onChange={e=>{setGenome(e.target.value);setError('')}}
                onDrop={onDrop} onDragOver={e=>{e.preventDefault();setDragging(true)}} onDragLeave={()=>setDragging(false)}
                placeholder={`>accession  description\nATGAAAC…`}
                className={`w-full h-32 bg-white/[0.02] border rounded-xl px-4 py-3 font-mono text-sm
                           text-white/80 placeholder-white/15 resize-none focus:outline-none transition-all leading-relaxed
                           ${dragging?'border-blue-400/60 bg-blue-400/[0.04]':'border-white/[0.07] focus:border-blue-400/40 focus:bg-white/[0.04]'}`}
                spellCheck={false}/>

              {/* Proteins */}
              <label className="block text-[11px] text-white/35 font-mono uppercase tracking-wide mt-3 mb-1.5">
                Protein sequences{' '}
                <span className="text-white/20 normal-case font-normal">
                  · FASTA (optional — 6-frame ORF auto-translation if empty)
                </span>
              </label>
              <textarea value={proteins} onChange={e=>setProteins(e.target.value)}
                placeholder={`>protein_id\nMASSSS…`}
                className="w-full h-16 bg-white/[0.02] border border-white/[0.07] rounded-xl px-4 py-3
                           font-mono text-sm text-white/80 placeholder-white/15 resize-none
                           focus:outline-none focus:border-violet-400/30 focus:bg-white/[0.04] transition-all"
                spellCheck={false}/>

              {/* Stats row */}
              <div className="mt-2.5 flex items-center justify-between text-xs min-h-[18px]">
                <div className="flex items-center gap-3">
                  {seqLen > 0 && (
                    <span className="text-white/40 font-mono">
                      {seqLen.toLocaleString()} bp
                      {proteins.trim()
                        ? <span className="text-violet-400/60 ml-2">· {proteins.trim().split('>').filter(Boolean).length} protein(s) · D1×0.4 + D2×0.6</span>
                        : seqLen >= 100 && <span className="text-blue-400/50 ml-2">· ORF auto-translate · D1×0.7 + D2×0.3</span>
                      }
                    </span>
                  )}
                  {error && <span className="flex items-center gap-1 text-red-400"><AlertCircle size={12}/>{error}</span>}
                </div>
              </div>

              {/* Run button */}
              <button onClick={handleRun} disabled={!ready || analyzing}
                className="btn-primary w-full flex items-center justify-center gap-2 h-11 rounded-xl
                           text-sm font-semibold mt-4 disabled:opacity-35 disabled:cursor-not-allowed
                           disabled:hover:shadow-none disabled:transform-none">
                {analyzing
                  ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/><span>Analyzing…</span></>
                  : <><Zap size={15}/><span>Run Prediction</span><ChevronRight size={14}/></>
                }
              </button>

              {!ready && !genome && (
                <p className="text-center text-xs text-white/25 mt-2.5">
                  Paste a sequence or{' '}
                  <button onClick={loadExample} className="text-blue-400/60 hover:text-blue-400 underline underline-offset-2">
                    load the example
                  </button>
                  {' '}to get started
                </p>
              )}
              {apiError && (
                <div className="mt-3 flex items-center gap-2 text-xs text-red-400/80 bg-red-400/[0.06] border border-red-400/20 rounded-lg px-3 py-2">
                  <AlertCircle size={13}/> {apiError}
                </div>
              )}
            </motion.div>
          )}

          {/* ── Batch prediction ── */}
          {tab === 'batch' && (
            <motion.div key="batch" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
              <p className="text-xs text-white/40 mb-4">
                Upload a multi-sequence FASTA file. Predictions use DNA-only mode (6-frame ORF → ESM-2). Max 500 sequences.
              </p>

              <div onDrop={onDrop} onDragOver={e=>{e.preventDefault();setDragging(true)}} onDragLeave={()=>setDragging(false)}
                onClick={()=>batchRef.current?.click()}
                className={`h-32 rounded-xl border-2 border-dashed flex flex-col items-center justify-center gap-2.5
                           cursor-pointer transition-all ${dragging?'drop-active':'border-white/[0.18] hover:border-blue-400/50 hover:bg-blue-400/[0.03]'}`}>
                <FileText size={20} className={dragging?'text-blue-300':'text-white/35'}/>
                <div className="text-center">
                  <p className="text-sm text-white/65">
                    <span className="text-blue-400 font-semibold">Browse</span> or drag & drop
                  </p>
                  <p className="text-xs text-white/35 mt-0.5">.fasta / .fa / .fna · up to 500 sequences</p>
                </div>
                <input ref={batchRef} type="file" accept=".fasta,.fa,.fna" className="hidden"
                  onChange={e=>handleBatchFile(e.target.files[0])}/>
              </div>

              <div className="mt-2.5 min-h-[18px]">
                {batchSeqs.length > 0 && (
                  <span className="text-xs text-white/40 font-mono">{batchSeqs.length} sequences loaded</span>
                )}
                {error && <span className="flex items-center gap-1 text-xs text-red-400"><AlertCircle size={12}/>{error}</span>}
              </div>

              <button onClick={()=>{ if(!batchSeqs.length){setError('Upload a FASTA file first.');return} setError(''); onBatchAnalyze(batchSeqs.length) }}
                disabled={!batchSeqs.length || batchAnalyzing}
                className="btn-primary w-full flex items-center justify-center gap-2 h-11 rounded-xl
                           text-sm font-semibold mt-4 disabled:opacity-35 disabled:cursor-not-allowed
                           disabled:hover:shadow-none disabled:transform-none">
                {batchAnalyzing
                  ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/><span>Predicting…</span></>
                  : <><Layers size={15}/><span>Run Batch</span>{batchSeqs.length>0&&<span className="ml-1 px-2 py-0.5 rounded-full bg-white/10 text-xs">{batchSeqs.length}</span>}</>
                }
              </button>

              <BatchTable results={batchResults} analyzing={batchAnalyzing}/>
            </motion.div>
          )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}
