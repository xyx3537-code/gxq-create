import { motion } from 'framer-motion'
import { Atom, Cpu, Dna, ArrowRight, CheckCircle2, Clock } from 'lucide-react'

const MODULES = [
  {
    icon: <Dna size={20} className="text-blue-400" />,
    title: 'D1 · Genomic k-mer Analysis',
    desc: '3-mer frequency spectrum (64 features) + genome length + GC content. SVM with RBF kernel trained on 860 viral genomes across 6 host categories.',
    stats: '94.9% acc · 66 features',
    status: 'active',
  },
  {
    icon: <Cpu size={20} className="text-violet-400" />,
    title: 'D2 · ESM-2 Protein Language Model',
    desc: 'facebook/esm2_t6_8M_UR50D generates 320-dim embeddings from protein sequences via mean-pooling (up to 15 proteins per virus). Fuses with D1 for final prediction.',
    stats: '95.5% acc · 320-dim',
    status: 'active',
  },
  {
    icon: <Atom size={20} className="text-cyan-400" />,
    title: 'D2+ · Structural Validation (Future)',
    desc: 'AlphaFold2 / ColabFold 3D structure prediction for viral surface proteins. Binding site analysis against host receptor structures. Mentioned in project proposal.',
    stats: 'AlphaFold2 · planned',
    status: 'planned',
  },
]

export default function D2Module() {
  return (
    <section id="how-it-works" className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass
                         border border-violet-400/20 text-violet-300 text-xs font-medium mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
            XQ_Data · Dual-Modal Prediction Framework
          </div>
          <h2 className="text-4xl sm:text-5xl font-extrabold text-white mb-4">
            How{' '}
            <span className="gradient-text">GXQ_Create</span>
            {' '}Works
          </h2>
          <p className="text-white/45 max-w-xl mx-auto text-lg leading-relaxed">
            D1 and D2 feature vectors are fused via weighted averaging.
            Protein sequences — from NCBI annotation or 6-frame ORF translation —
            feed into ESM-2 for D2 embedding.
          </p>
        </motion.div>

        {/* Module cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-14">
          {MODULES.map((m, i) => (
            <motion.div
              key={m.title}
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ delay: i * 0.12, duration: 0.55 }}
            >
              <div className="glass glass-hover rounded-2xl p-6 h-full relative">
                {/* Status badge */}
                {m.status === 'active' ? (
                  <div className="absolute top-4 right-4 flex items-center gap-1 px-2 py-0.5 rounded-full
                                 text-[10px] bg-green-400/10 border border-green-400/25 text-green-400 font-medium">
                    <CheckCircle2 size={9} /> ACTIVE
                  </div>
                ) : (
                  <div className="absolute top-4 right-4 flex items-center gap-1 px-2 py-0.5 rounded-full
                                 text-[10px] bg-white/[0.05] border border-white/10 text-white/30 font-medium">
                    <Clock size={9} /> PLANNED
                  </div>
                )}

                <div className="w-10 h-10 rounded-xl bg-white/[0.05] flex items-center justify-center mb-4">
                  {m.icon}
                </div>
                <h3 className="text-white font-semibold text-sm mb-2 pr-16">{m.title}</h3>
                <p className="text-white/40 text-sm leading-relaxed mb-4">{m.desc}</p>
                <div className="font-mono text-[11px] text-blue-300/50">{m.stats}</div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Fusion diagram */}
        <motion.div
          initial={{ opacity: 0, y: 28 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.6 }}
        >
          <div className="glass rounded-2xl p-8 gradient-border relative overflow-hidden">
            <div className="absolute inset-0 opacity-[0.025]"
              style={{
                backgroundImage: 'linear-gradient(rgba(139,92,246,1) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,1) 1px, transparent 1px)',
                backgroundSize: '40px 40px',
              }} />

            <div className="relative">
              <div className="text-xs font-mono text-white/30 mb-6 tracking-widest uppercase">
                Prediction Pipeline
              </div>

              {/* Pipeline flow */}
              <div className="flex flex-col sm:flex-row items-center gap-3 justify-center flex-wrap">
                {[
                  { label: 'Genome DNA', sub: 'input', color: 'blue' },
                  { label: 'k-mer extraction', sub: 'D1 · 66-dim', color: 'blue' },
                  { label: 'SVM classifier', sub: 'D1 probabilities', color: 'blue' },
                ].map((node, i) => (
                  <PipeNode key={i} {...node} />
                ))}

                <div className="text-white/20 font-mono text-lg hidden sm:block">+</div>

                {[
                  { label: 'Protein seqs', sub: 'NCBI or ORF auto-translate', color: 'violet' },
                  { label: 'ESM-2 embedding', sub: 'D2 · 320-dim', color: 'violet' },
                  { label: 'SVM classifier', sub: 'D2 probabilities', color: 'violet' },
                ].map((node, i) => (
                  <PipeNode key={i + 10} {...node} />
                ))}

                <ArrowRight size={16} className="text-white/20 hidden sm:block" />

                <div className="px-4 py-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-500/20
                               border border-blue-400/25 text-center">
                  <div className="text-white font-semibold text-sm">Weighted Fusion</div>
                  <div className="text-xs font-mono mt-1">
                    <span className="text-blue-300">D1×0.4</span>
                    <span className="text-white/30"> + </span>
                    <span className="text-violet-300">D2×0.6</span>
                  </div>
                  <div className="text-[10px] text-white/30 mt-1">D1×0.7 + D2×0.3 (ORF mode)</div>
                </div>

                <ArrowRight size={16} className="text-white/20 hidden sm:block" />

                <div className="px-4 py-3 rounded-xl bg-gradient-to-br from-green-500/15 to-cyan-500/15
                               border border-green-400/20 text-center">
                  <div className="text-white font-semibold text-sm">Host Prediction</div>
                  <div className="text-xs text-green-300/70 font-mono mt-1">6 categories · 96.4%</div>
                </div>
              </div>

              {/* Weight note */}
              <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-white/40">
                <div className="bg-white/[0.02] rounded-xl p-4 border border-white/[0.05]">
                  <div className="text-white/70 font-semibold mb-1">
                    🧬 DNA + Annotated Proteins &nbsp;
                    <span className="text-green-400/70 font-mono text-[10px]">recommended</span>
                  </div>
                  Proteins from NCBI (or provided by user) → ESM-2 encodes → D1×0.4 + D2×0.6.
                  Demo confidence: ~96%.
                </div>
                <div className="bg-white/[0.02] rounded-xl p-4 border border-white/[0.05]">
                  <div className="text-white/70 font-semibold mb-1">⚡ DNA Only (ORF mode)</div>
                  6-frame ORF translation from genome → ESM-2 encodes → D1×0.7 + D2×0.3.
                  Core innovation: no annotation required. Validated 90.9% on ≥5 kb sequences.
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

function PipeNode({ label, sub, color }) {
  const borderColor = color === 'blue' ? 'border-blue-400/20' : 'border-violet-400/20'
  const textColor   = color === 'blue' ? 'text-blue-300/60' : 'text-violet-300/60'
  return (
    <div className={`flex items-center gap-2`}>
      <div className={`px-3 py-2 rounded-lg bg-white/[0.03] border ${borderColor} text-center`}>
        <div className="text-white/70 text-xs font-medium">{label}</div>
        <div className={`text-[10px] font-mono mt-0.5 ${textColor}`}>{sub}</div>
      </div>
      <ArrowRight size={12} className="text-white/15 hidden sm:block flex-shrink-0" />
    </div>
  )
}
