import { motion } from 'framer-motion'
import { Github, Mail, Dna } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t border-white/[0.05] mt-12 py-12 px-6">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity:0, y:16 }}
          whileInView={{ opacity:1, y:0 }}
          viewport={{ once:true }}
          transition={{ duration:0.5 }}
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8"
        >
          {/* Brand + description */}
          <div className="max-w-sm">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600
                             flex items-center justify-center shadow-[0_0_12px_rgba(139,92,246,0.4)]">
                <Dna size={15} className="text-white"/>
              </div>
              <span className="font-bold text-sm">
                <span className="gradient-text">GXQ</span>
                <span className="text-white/60">_Create</span>
              </span>
            </div>
            <p className="text-white/35 text-sm leading-relaxed">
              Environmental virus host prediction platform for eukaryotic virology research.
              D1 (k-mer SVM) + D2 (ESM-2) dual-modal fusion, 96.4% cross-validation accuracy
              across 6 host categories.
            </p>
            <p className="text-white/20 text-xs mt-3">
              China Ocean University · SRDP Project · 2026
            </p>
          </div>

          {/* Key stats */}
          <div className="flex flex-wrap gap-4 text-center">
            {[
              { v:'860',    l:'Training genomes' },
              { v:'96.4%',  l:'CV accuracy' },
              { v:'6',      l:'Host classes' },
              { v:'320-dim',l:'ESM-2 embedding' },
            ].map(s=>(
              <div key={s.l}>
                <div className="text-blue-300 font-bold text-sm">{s.v}</div>
                <div className="text-white/25 text-xs">{s.l}</div>
              </div>
            ))}
          </div>

          {/* Contact */}
          <div className="flex flex-col gap-2">
            <p className="text-white/40 text-xs font-semibold uppercase tracking-wide mb-1">Contact</p>
            <a href="https://github.com/Aphria" target="_blank" rel="noreferrer"
              className="flex items-center gap-2 text-sm text-white/45 hover:text-white transition-colors">
              <Github size={14}/> github.com/Aphria
            </a>
            <a href="mailto:xyx3537@gmail.com"
              className="flex items-center gap-2 text-sm text-white/45 hover:text-white transition-colors">
              <Mail size={14}/> xyx3537@gmail.com
            </a>
          </div>
        </motion.div>

        {/* Bottom bar */}
        <div className="mt-10 pt-6 border-t border-white/[0.04] flex flex-col sm:flex-row items-center
                       justify-between gap-2 text-xs text-white/20">
          <span>© 2026 GXQ_Create · Aphria</span>
          <span className="font-mono">D1: k-mer SVM · D2: ESM-2 · Fusion: late weighted average</span>
        </div>
      </div>
    </footer>
  )
}
