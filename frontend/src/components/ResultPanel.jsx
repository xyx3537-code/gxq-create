import { motion } from 'framer-motion'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RTooltip,
} from 'recharts'
import { Activity, Dna } from 'lucide-react'

const HOST_META = {
  fungi:        { cn:'Fungi',        icon:'🍄', color:'#34d399' },
  algae:        { cn:'Algae',        icon:'🌊', color:'#38bdf8' },
  protozoa:     { cn:'Protozoa',     icon:'🔬', color:'#fbbf24' },
  bacteria:     { cn:'Bacteria',     icon:'🦠', color:'#f87171' },
  plant:        { cn:'Plant',        icon:'🌿', color:'#4ade80' },
  invertebrate: { cn:'Invertebrate', icon:'🦋', color:'#c084fc' },
}

/* Gradient-feel colors for donut segments */
const DONUT_COLORS = {
  fungi:        '#9333ea',
  algae:        '#3b82f6',
  protozoa:     '#06b6d4',
  bacteria:     '#10b981',
  plant:        '#22c55e',
  invertebrate: '#6366f1',
}

/* ── Confidence arc ───────────────────────────────────── */
function ConfidenceArc({ value }) {
  const r = 48, circ = 2 * Math.PI * r
  const arc = circ * 0.75
  return (
    <svg width="130" height="90" viewBox="0 0 130 90">
      <defs>
        <linearGradient id="cg" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#06b6d4"/>
          <stop offset="100%" stopColor="#6366f1"/>
        </linearGradient>
      </defs>
      <circle cx="65" cy="70" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="7"
        strokeDasharray={`${arc} ${circ}`} strokeDashoffset={-circ*0.125} strokeLinecap="round"/>
      <circle cx="65" cy="70" r={r} fill="none" stroke="url(#cg)" strokeWidth="7"
        strokeDasharray={`${arc * Math.min(value,1)} ${circ}`}
        strokeDashoffset={-circ*0.125} strokeLinecap="round"
        style={{ filter:'drop-shadow(0 0 6px rgba(6,182,212,0.6))' }}/>
      <text x="65" y="62" textAnchor="middle" fill="white" fontSize="20" fontWeight="700">
        {(value*100).toFixed(0)}%
      </text>
      <text x="65" y="76" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="8" letterSpacing="1.5">
        CONFIDENCE
      </text>
    </svg>
  )
}

/* ── Donut tooltip ────────────────────────────────────── */
const DonutTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const host  = payload[0]?.payload?.host
  const value = payload[0]?.value
  const m     = HOST_META[host] || {}
  return (
    <div className="glass rounded-lg px-3 py-1.5 border border-white/10 text-xs shadow-lg">
      <span style={{ color: DONUT_COLORS[host] }} className="font-semibold">{m.icon} {m.cn}</span>
      <span className="text-white/60 ml-2">{value?.toFixed(1)}%</span>
    </div>
  )
}

/* ── Loading skeleton ─────────────────────────────────── */
function Skeleton() {
  return (
    <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
      className="mt-8 max-w-3xl mx-auto glass rounded-2xl p-8 text-center">
      <div className="w-9 h-9 border-2 border-white/15 border-t-cyan-400 rounded-full animate-spin mx-auto mb-4"/>
      <p className="text-white/45 text-sm">Analyzing sequence…</p>
      <p className="text-white/20 text-xs mt-1 font-mono">D1 k-mer · ESM-2 protein embedding · fusion</p>
    </motion.div>
  )
}

/* ══════════════════════════════════════════════════════ */
export default function ResultPanel({ result, analyzing }) {
  if (analyzing && !result) return <Skeleton />
  if (!result) return null

  const { predicted_host, confidence, probabilities, genome_length,
          gc_content, protein_count, auto_translated, short_genome,
          d1_contribution, d2_contribution, top_kmers } = result

  const meta      = HOST_META[predicted_host] || {}
  const hostColor = meta.color || '#60a5fa'

  /* Donut data */
  const pieData = Object.entries(probabilities).map(([host, v]) => ({
    host,
    value: +(v * 100).toFixed(2),
  }))

  /* Top 3 sorted */
  const top3 = [...pieData].sort((a,b) => b.value - a.value).slice(0, 3)

  return (
    <motion.div
      initial={{ opacity:0, y:16 }}
      animate={{ opacity:1, y:0 }}
      exit={{ opacity:0 }}
      transition={{ duration:0.35 }}
      className="mt-8 max-w-3xl mx-auto space-y-4"
    >
      {/* Label */}
      <div className="flex items-center gap-2 text-[11px] text-cyan-300/50 font-mono tracking-widest uppercase">
        <Activity size={11}/> Prediction Results
      </div>

      {/* ── Row 1: host card + donut ─────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">

        {/* Host + confidence */}
        <div className="sm:col-span-2 glass rounded-2xl p-5 flex flex-col items-center text-center"
          style={{ boxShadow:`0 0 28px ${hostColor}18, inset 0 0 0 1px ${hostColor}20` }}>

          <div className="text-[10px] text-white/30 font-mono tracking-widest uppercase mb-3">
            Predicted Host
          </div>

          <div className="w-14 h-14 rounded-xl flex items-center justify-center text-3xl mb-2"
            style={{ background:`${hostColor}10`, boxShadow:`0 0 18px ${hostColor}35` }}>
            {meta.icon}
          </div>

          <div className="text-xl font-extrabold mb-0.5" style={{ color: hostColor }}>
            {meta.cn}
          </div>
          <div className="font-mono text-[10px] text-white/25 mb-3">{predicted_host}</div>

          <ConfidenceArc value={confidence}/>

          {short_genome && (
            <div className="mt-2 w-full text-[11px] text-amber-300/70 border border-amber-400/20
                           rounded-lg px-3 py-1.5 bg-amber-400/5 text-center">
              ⚠ Short sequence — lower reliability
            </div>
          )}
          {auto_translated && (
            <div className="mt-2 w-full text-[11px] text-cyan-300/60 border border-cyan-400/15
                           rounded-lg px-3 py-1.5 bg-cyan-400/5 text-center">
              ⚡ ORF auto-translate · {protein_count} proteins
            </div>
          )}
        </div>

        {/* Donut chart */}
        <div className="sm:col-span-3 glass rounded-2xl p-5"
          style={{ boxShadow:'inset 0 0 0 1px rgba(255,255,255,0.05)' }}>
          <div className="text-[10px] text-white/30 font-mono tracking-widest uppercase mb-1">
            Host Probability Distribution
          </div>

          <div className="relative h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <defs>
                  {Object.entries(DONUT_COLORS).map(([host, color]) => (
                    <radialGradient key={host} id={`grad-${host}`} cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor={color} stopOpacity="0.9"/>
                      <stop offset="100%" stopColor={color} stopOpacity="0.6"/>
                    </radialGradient>
                  ))}
                </defs>
                <Pie
                  data={pieData}
                  cx="50%" cy="50%"
                  innerRadius="44%" outerRadius="68%"
                  dataKey="value"
                  paddingAngle={3}
                  startAngle={90} endAngle={-270}
                  label={({ cx, cy, midAngle, outerRadius, host, value }) => {
                    if (value < 4) return null
                    const rad = Math.PI / 180
                    const r   = outerRadius + 16
                    const x   = cx + r * Math.cos(-midAngle * rad)
                    const y   = cy + r * Math.sin(-midAngle * rad)
                    return (
                      <text x={x} y={y} textAnchor="middle" dominantBaseline="central"
                        fontSize={11} fill={DONUT_COLORS[host]}
                        opacity={host === predicted_host ? 1 : 0.5}
                        fontWeight={host === predicted_host ? 700 : 400}>
                        {HOST_META[host]?.icon} {value.toFixed(0)}%
                      </text>
                    )
                  }}
                  labelLine={false}
                >
                  {pieData.map((entry) => (
                    <Cell
                      key={entry.host}
                      fill={`url(#grad-${entry.host})`}
                      opacity={entry.host === predicted_host ? 1 : 0.35}
                      stroke={entry.host === predicted_host ? DONUT_COLORS[entry.host] : 'transparent'}
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <RTooltip content={<DonutTooltip/>}/>
              </PieChart>
            </ResponsiveContainer>

            {/* Center label */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <div className="text-2xl">{meta.icon}</div>
                <div className="text-[11px] font-bold mt-0.5" style={{ color: hostColor }}>{meta.cn}</div>
                <div className="text-[10px] text-white/35 font-mono">{(confidence*100).toFixed(0)}%</div>
              </div>
            </div>
          </div>

          {/* Top 3 predictions */}
          <div className="border-t border-white/[0.06] pt-3 mt-1 space-y-1.5">
            <div className="text-[10px] text-white/25 font-mono uppercase tracking-widest mb-2">
              Top Predictions
            </div>
            {top3.map((item, i) => {
              const m = HOST_META[item.host] || {}
              return (
                <div key={item.host} className="flex items-center gap-3">
                  <span className="text-white/25 text-xs w-3">{i+1}</span>
                  <span className="text-base w-5">{m.icon}</span>
                  <span className="text-sm flex-1" style={{ color: i===0 ? DONUT_COLORS[item.host] : 'rgba(255,255,255,0.5)' }}>
                    {m.cn}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1 rounded-full bg-white/[0.06] overflow-hidden">
                      <div className="h-full rounded-full transition-all"
                        style={{ width:`${item.value}%`, background: i===0 ? DONUT_COLORS[item.host] : 'rgba(255,255,255,0.2)' }}/>
                    </div>
                    <span className="text-xs font-mono w-10 text-right"
                      style={{ color: i===0 ? DONUT_COLORS[item.host] : 'rgba(255,255,255,0.35)' }}>
                      {item.value.toFixed(1)}%
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* ── Row 2: Sequence features + fusion ────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

        {/* Sequence features (D1) */}
        <div className="glass rounded-2xl p-5"
          style={{ boxShadow:'inset 0 0 0 1px rgba(255,255,255,0.05)' }}>
          <div className="text-[10px] text-white/30 font-mono tracking-widest uppercase mb-4 flex items-center gap-1.5">
            <Dna size={10}/> Sequence Features (D1)
          </div>
          <div className="space-y-3">
            {[
              { label:'Genome Length', value:`${genome_length.toLocaleString()} bp`, pct: Math.min(genome_length/50000*100,100) },
              { label:'GC Content',    value:`${gc_content}%`,                        pct: gc_content },
              { label:auto_translated?'ORFs Translated':'Proteins Provided', value:String(protein_count), pct: Math.min(protein_count/15*100,100) },
            ].map(f => (
              <div key={f.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/40">{f.label}</span>
                  <span className="font-mono text-cyan-300/70">{f.value}</span>
                </div>
                <div className="h-1 rounded-full bg-white/[0.05]">
                  <motion.div className="h-full rounded-full"
                    style={{ background:'linear-gradient(90deg,#06b6d4,#6366f1)' }}
                    initial={{ width:0 }}
                    animate={{ width:`${f.pct}%` }}
                    transition={{ duration:0.8, ease:'easeOut' }}/>
                </div>
              </div>
            ))}

            <div className="pt-2 border-t border-white/[0.05]">
              <div className="text-[10px] text-white/25 font-mono uppercase tracking-widest mb-2.5">
                Top 3-mer Enrichment
              </div>
              {(top_kmers || []).slice(0,4).map((k,i) => (
                <div key={k.kmer} className="flex items-center gap-2 mb-1.5">
                  <span className="font-mono text-xs font-bold w-8"
                    style={{ color: hostColor }}>{k.kmer}</span>
                  <div className="flex-1 h-1 rounded-full bg-white/[0.04]">
                    <motion.div className="h-full rounded-full"
                      style={{ background:`${hostColor}80` }}
                      initial={{ width:0 }}
                      animate={{ width:`${(k.enrichment/2)*100}%` }}
                      transition={{ delay:0.3+i*0.06, duration:0.6, ease:'easeOut' }}/>
                  </div>
                  <span className="text-[11px] text-white/30 font-mono w-8 text-right">×{k.enrichment}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Fusion weights */}
        <div className="glass rounded-2xl p-5"
          style={{ boxShadow:'inset 0 0 0 1px rgba(255,255,255,0.05)' }}>
          <div className="text-[10px] text-white/30 font-mono tracking-widest uppercase mb-4">
            Model Fusion Weights
          </div>

          {[
            { label:'D1 · Genomic k-mer SVM', val:d1_contribution, c1:'#3b82f6', c2:'#06b6d4' },
            { label:'D2 · ESM-2 Protein LM',  val:d2_contribution, c1:'#8b5cf6', c2:'#6366f1' },
          ].map(w => (
            <div key={w.label} className="mb-5">
              <div className="flex justify-between items-baseline mb-2">
                <span className="text-xs text-white/50">{w.label}</span>
                <span className="font-mono text-lg font-bold"
                  style={{ color: w.c1 }}>{(w.val*100).toFixed(0)}%</span>
              </div>
              <div className="h-2 rounded-full bg-white/[0.05] overflow-hidden">
                <motion.div className="h-full rounded-full"
                  style={{ background:`linear-gradient(90deg,${w.c1},${w.c2})`,
                           boxShadow:`0 0 8px ${w.c1}60` }}
                  initial={{ width:0 }}
                  animate={{ width:`${w.val*100}%` }}
                  transition={{ duration:0.9, ease:'easeOut' }}/>
              </div>
            </div>
          ))}

          <div className="mt-6 pt-4 border-t border-white/[0.05] space-y-1.5 text-xs text-white/30 font-mono">
            <div className="flex justify-between">
              <span>Mode</span>
              <span className="text-cyan-300/60">{auto_translated ? 'ORF (DNA-only)' : 'Standard'}</span>
            </div>
            <div className="flex justify-between">
              <span>D1 features</span>
              <span>66-dim (3-mer + GC + len)</span>
            </div>
            <div className="flex justify-between">
              <span>D2 features</span>
              <span>320-dim ESM-2</span>
            </div>
            <div className="flex justify-between">
              <span>CV accuracy</span>
              <span className="text-cyan-300/60">96.4%</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
