import React from 'react'
import { Laptop, MapPin, Check, ArrowRight, Shield } from 'lucide-react'

export const ModalitiesSection: React.FC = () => {
  const basePhone = '5511996795882'

  const handleWhatsApp = (mode: string) => {
    const text = encodeURIComponent(
      `Olá Breno! Gostaria de saber mais sobre as *${mode}* de inglês (valores e disponibilidade).`
    )
    window.open(`https://wa.me/${basePhone}?text=${text}`, '_blank', 'noopener,noreferrer')
  }

  return (
    <section id="modalidades" className="py-24 px-6 max-w-6xl mx-auto relative z-10">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
        <p className="text-xs font-bold uppercase tracking-wider text-amber-700 font-mono">
          Formatos Sob Medida
        </p>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
          Aulas Online ou Presenciais
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
          Sem contratos engessados e sem método genérico de cursinho tradicional. Escolha a conveniência do online ou o atendimento presencial noturno no seu endereço.
        </p>
      </div>

      {/* Two Modality Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10 items-stretch">
        {/* Card 1: Online */}
        <div className="rounded-3xl border border-slate-200 bg-white p-8 sm:p-10 flex flex-col justify-between hover:border-slate-300 transition-all shadow-sm hover:shadow-md relative group">
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-200/80 flex items-center justify-center text-blue-600">
                <Laptop className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-bold tracking-wide uppercase px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200/80">
                Estude de Onde Estiver
              </span>
            </div>

            <h3 className="text-2xl font-bold text-slate-900 mb-2">
              Aulas Online
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed mb-6">
              Ideal para executivos, quem trabalha em home office ou viaja frequentemente e busca máxima flexibilidade de agenda sem perda de tempo com trânsito.
            </p>

            {/* Feature Checklist from Flyer */}
            <ul className="space-y-4 mb-8 border-t border-slate-100 pt-6">
              {[
                { title: 'Flexibilidade de horários', desc: 'Ajuste seus encontros conforme seus compromissos e fuso horário da semana.' },
                { title: 'Aulas 100% personalizadas', desc: 'Foco exclusivo nos seus temas de trabalho, reuniões e entrevistas.' },
                { title: 'Material didático incluso', desc: 'Zero cobrança de livros caros ou taxas de matrícula ocultas.' },
                { title: 'Foco no seu objetivo', desc: 'Do destravamento básico até liderança e negociações globais de alta complexidade.' }
              ].map((item, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                  </div>
                  <div>
                    <span className="text-sm font-bold text-slate-900 block">{item.title}</span>
                    <span className="text-xs text-slate-600 block">{item.desc}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <button
            onClick={() => handleWhatsApp('Aulas Online')}
            className="w-full py-4 px-6 rounded-2xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer shadow-sm hover:shadow"
          >
            <span>Consultar Horários Online</span>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
          </button>
        </div>

        {/* Card 2: Presencial (Highlighted) */}
        <div className="rounded-3xl border-2 border-amber-400 bg-amber-50/30 p-8 sm:p-10 flex flex-col justify-between hover:border-amber-500 transition-all shadow-md hover:shadow-lg relative group">
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="w-12 h-12 rounded-2xl bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-800">
                <MapPin className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-bold tracking-wide uppercase px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
                Mais Praticidade Para Você
              </span>
            </div>

            <h3 className="text-2xl font-bold text-slate-900 mb-2">
              Aulas Presenciais
            </h3>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed mb-6">
              O professor vai até sua casa, escritório ou coworking em São Paulo para uma experiência imersiva e humana após o seu horário de trabalho.
            </p>

            {/* Feature Checklist from Flyer */}
            <ul className="space-y-4 mb-8 border-t border-amber-200/60 pt-6">
              {[
                { title: 'Após as 18h (Turno Noturno)', desc: 'Perfeito para quem trabalha em horário comercial e quer evoluir à noite com calma.' },
                { title: 'Passagem inclusa', desc: 'Deslocamento do professor coberto integralmente, sem taxas surpresa.' },
                { title: 'Dias combinados', desc: 'Alinhamento flexível e direto de calendário entre você e o Breno.' },
                { title: 'Pagamento ao final', desc: 'Risco zero e confiança mútua: você só realiza o acerto financeiro após as aulas concluídas.' }
              ].map((item, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-amber-200 text-amber-900 flex items-center justify-center shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                  </div>
                  <div>
                    <span className="text-sm font-bold text-slate-900 block">{item.title}</span>
                    <span className="text-xs text-slate-700 block">{item.desc}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <button
            onClick={() => handleWhatsApp('Aulas Presenciais')}
            className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white font-bold text-xs transition-all flex items-center justify-center gap-2 shadow-sm hover:shadow cursor-pointer"
          >
            <span>Consultar Disponibilidade Presencial</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Trust reassurance banner */}
      <div className="mt-12 rounded-2xl border border-slate-200 bg-slate-50 p-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-600">
        <div className="flex items-center gap-3">
          <Shield className="w-5 h-5 text-amber-600 shrink-0" />
          <span>
            <strong>Flexibilidade total:</strong> Você pode alternar entre aulas online e presenciais conforme sua agenda exigir.
          </span>
        </div>
        <button
          onClick={() => handleWhatsApp('Tirar dúvidas sobre a região de atendimento em SP')}
          className="text-amber-700 hover:text-amber-800 font-bold underline underline-offset-4 shrink-0 cursor-pointer"
        >
          Consultar bairros atendidos em SP
        </button>
      </div>
    </section>
  )
}
