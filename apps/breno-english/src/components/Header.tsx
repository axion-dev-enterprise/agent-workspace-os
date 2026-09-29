import React, { useState } from 'react'
import { Menu, X, GraduationCap } from 'lucide-react'
import { WhatsAppIcon } from './WhatsAppIcon'

interface HeaderProps {
  onOpenQuiz: () => void
  onOpenFlyer: () => void
}

export const Header: React.FC<HeaderProps> = ({ onOpenQuiz, onOpenFlyer }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const basePhone = '5511996795882'

  const navLinks = [
    { label: 'Modalidades', href: '#modalidades' },
    { label: 'Metodologia', href: '#metodo' },
    { label: 'Laboratório', href: '#audio-lab' },
    { label: 'Sobre o Professor', href: '#sobre' },
    { label: 'Dúvidas', href: '#faq' }
  ]

  return (
    <header className="sticky top-0 z-40 w-full bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-2xs">
      <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Brand identity */}
        <a href="#" className="flex flex-col group">
          <span className="font-editorial text-lg sm:text-xl font-bold tracking-tight text-slate-900 group-hover:text-amber-800 transition-colors">
            Breno Roncaglione
          </span>
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
            Aulas Particulares • Inglês
          </span>
        </a>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-8 text-xs font-semibold text-slate-600">
          {navLinks.map((link, idx) => (
            <a
              key={idx}
              href={link.href}
              className="hover:text-slate-900 transition-colors py-1 hover:underline underline-offset-4"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Action CTAs */}
        <div className="hidden sm:flex items-center gap-4">
          <button
            onClick={onOpenQuiz}
            type="button"
            className="btn-tactile text-xs font-semibold text-slate-700 hover:text-slate-900 transition-colors px-3.5 py-2.5 rounded-xl hover:bg-slate-100 flex items-center gap-1.5 cursor-pointer border border-transparent hover:border-slate-200"
          >
            <GraduationCap className="w-4 h-4 text-amber-700" />
            <span>Diagnóstico Gratuito</span>
          </button>

          {/* Official WhatsApp Button with pulsating ring */}
          <a
            href={`https://wa.me/${basePhone}?text=${encodeURIComponent('Olá Breno! Gostaria de saber mais sobre as aulas de inglês.')}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-tactile relative group px-4 py-2.5 rounded-full bg-[#25D366] hover:bg-[#20ba59] text-white text-xs font-bold transition-all flex items-center gap-2 shadow-sm hover:shadow-md cursor-pointer"
          >
            <span className="absolute -inset-0.5 rounded-full bg-[#25D366] opacity-30 group-hover:opacity-60 animate-ping pointer-events-none" />
            <WhatsAppIcon className="w-4 h-4 fill-white relative z-10" />
            <span className="relative z-10">(11) 99679-5882</span>
          </a>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex lg:hidden items-center gap-3">
          <a
            href={`https://wa.me/${basePhone}?text=${encodeURIComponent('Olá Breno! Gostaria de saber mais sobre as aulas de inglês.')}`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2.5 rounded-full bg-[#25D366] text-white shadow-sm"
            aria-label="WhatsApp"
          >
            <WhatsAppIcon className="w-4 h-4 fill-white" />
          </a>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-700 hover:text-slate-900"
            aria-label="Menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-slate-200 bg-white px-6 py-6 space-y-4 shadow-xl">
          <nav className="flex flex-col gap-3">
            {navLinks.map((link, idx) => (
              <a
                key={idx}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-semibold text-slate-700 hover:text-amber-700 py-1"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="pt-4 border-t border-slate-200 space-y-3">
            <button
              onClick={() => {
                setMobileMenuOpen(false)
                onOpenQuiz()
              }}
              type="button"
              className="btn-tactile w-full py-3.5 rounded-2xl text-xs font-bold text-slate-800 bg-slate-100 hover:bg-slate-200 flex items-center justify-center gap-2 cursor-pointer border border-slate-200"
            >
              <GraduationCap className="w-4 h-4 text-amber-700" />
              Fazer Diagnóstico de Nível
            </button>

            <a
              href={`https://wa.me/${basePhone}?text=${encodeURIComponent('Olá Breno! Gostaria de falar sobre as aulas de inglês.')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full py-3.5 rounded-full bg-[#25D366] text-white text-xs font-bold text-center flex items-center justify-center gap-2 shadow-sm"
            >
              <WhatsAppIcon className="w-4 h-4 fill-white" />
              Conversar no WhatsApp (11 99679-5882)
            </a>
          </div>
        </div>
      )}
    </header>
  )
}
