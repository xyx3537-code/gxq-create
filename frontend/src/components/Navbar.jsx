import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Github, Dna, FlaskConical } from 'lucide-react'

function scrollTo(id, offset = 80) {
  const el = document.getElementById(id)
  if (!el) return
  window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - offset, behavior: 'smooth' })
}

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <motion.nav
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'glass border-b border-white/[0.06] shadow-[0_4px_30px_rgba(0,0,0,0.4)]'
          : 'bg-transparent border-b border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo — click to scroll top */}
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="flex items-center gap-2.5 group"
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600
                         flex items-center justify-center
                         shadow-[0_0_16px_rgba(139,92,246,0.5)]
                         group-hover:shadow-[0_0_24px_rgba(139,92,246,0.7)] transition-shadow">
            <Dna size={18} className="text-white" />
          </div>
          <span className="font-bold text-base tracking-tight">
            <span className="gradient-text">GXQ</span>
            <span className="text-white/70">_Create</span>
          </span>
          <span className="hidden sm:inline text-[10px] font-mono text-blue-400/60
                          border border-blue-400/20 rounded px-1.5 py-0.5 ml-1">
            v0.6
          </span>
        </button>

        {/* Nav actions */}
        <div className="flex items-center gap-1">
          {/* How it works → scrolls to pipeline section */}
          <button
            onClick={() => scrollTo('how-it-works')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm
                       text-white/60 hover:text-white hover:bg-white/[0.06] transition-all"
          >
            <FlaskConical size={14} />
            <span className="hidden sm:inline">How it works</span>
          </button>

          {/* GitHub */}
          <a
            href="https://github.com/Aphria"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm
                       text-white/60 hover:text-white hover:bg-white/[0.06] transition-all"
          >
            <Github size={15} />
            <span className="hidden sm:inline">GitHub</span>
          </a>

          {/* Run Prediction CTA */}
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="ml-2 btn-primary flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm"
          >
            <span>Run Prediction</span>
          </button>
        </div>
      </div>
    </motion.nav>
  )
}
