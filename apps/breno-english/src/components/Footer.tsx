import React from 'react'
import { ShieldCheck, MessageSquare, ArrowUp, Laptop, MapPin, CheckCircle2 } from 'lucide-react'

export const Footer: React.FC = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const basePhone = '5511996795882'

  return (
    <footer className="border-t border-slate-200 bg-slate-50 py-16 px-6 relative z-10 text-xs text-slate-600">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
        {/* Brand */}
        <div className="md:col-span-2 space-y-3">
          <div className="flex flex-col">
            <span className="text-base font-extrabold tracking-tight text-slate-900">
              Breno Roncaglione
            </span>
            <span className="text-xs font-mono tracking-wider text-amber-700 uppercase font-bold">
              Professor de Inglês • Aulas Particulares
            </span>
          </div>

          <p className="text-slate-600 text-xs leading-relaxed max-w-md">
            Inglês de verdade, no seu ritmo e com um plano sob medida para o seu objetivo. Metodologia ativa focada em conversação e resultados práticos para sua carreira.
          </p>

          <div className="flex flex-wrap items-center gap-2 pt-2 text-slate-700">
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-white border border-slate-200 shadow-2xs">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Atendimento Personalizado
            </span>
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-white border border-slate-200 shadow-2xs">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-700" /> Pagamento ao Final (Presencial)
            </span>
          </div>
        </div>

        {/* Links */}
        <div className="space-y-3">
          <h5 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] font-mono">
            Modalidades
          </h5>
          <ul className="space-y-2.5">
            <li>
              <a href="#modalidades" className="hover:text-slate-900 transition-colors flex items-center gap-1.5">
                <Laptop className="w-3.5 h-3.5 text-blue-600" /> Aulas Online (Global)
              </a>
            </li>
            <li>
              <a href="#modalidades" className="hover:text-slate-900 transition-colors flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-amber-700" /> Aulas Presenciais (Após 18h)
              </a>
            </li>
            <li>
              <a href="#metodo" className="hover:text-slate-900 transition-colors">
                Metodologia Própria
              </a>
            </li>
            <li>
              <a href="#audio-lab" className="hover:text-slate-900 transition-colors">
                Laboratório de Pronúncia
              </a>
            </li>
          </ul>
        </div>

        {/* Contact info */}
        <div className="space-y-3">
          <h5 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] font-mono">
            Contato Oficial
          </h5>
          <p className="text-slate-600">
            Fale diretamente com o professor para tirar dúvidas ou agendar nivelamento:
          </p>
          <a
            href={`https://wa.me/${basePhone}?text=${encodeURIComponent('Olá Breno! Gostaria de mais informações sobre suas aulas.')}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold transition-all shadow-sm"
          >
            <MessageSquare className="w-4 h-4 fill-current" />
            (11) 99679-5882
          </a>
          <p className="text-[11px] text-slate-500">
            São Paulo - SP • Atendimento Online para todo o Brasil e Exterior
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-[11px] text-slate-500">
          © {new Date().getFullYear()} Breno Roncaglione. Todos os direitos reservados.
        </p>

        <button
          onClick={scrollToTop}
          className="flex items-center gap-1.5 text-slate-500 hover:text-slate-900 transition-colors text-xs p-1 cursor-pointer"
        >
          <span>Voltar ao topo</span>
          <ArrowUp className="w-4 h-4" />
        </button>
      </div>
    </footer>
  )
}
