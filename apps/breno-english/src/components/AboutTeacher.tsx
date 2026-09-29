import React from 'react'
import { Award, Check, MessageSquare, ArrowRight, ShieldCheck, HeartHandshake } from 'lucide-react'

interface AboutTeacherProps {
  onOpenQuiz: () => void
}

export const AboutTeacher: React.FC<AboutTeacherProps> = ({ onOpenQuiz }) => {
  const basePhone = '5511996795882'

  return (
    <section id="sobre" className="py-24 px-6 max-w-6xl mx-auto relative z-10">
      <div className="rounded-3xl border border-slate-200 bg-slate-50/80 p-8 sm:p-14 overflow-hidden relative">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Photo Column */}
          <div className="lg:col-span-5 flex flex-col items-center">
            <div className="relative w-full max-w-sm rounded-3xl overflow-hidden border border-slate-200 bg-white p-2 shadow-lg">
              <div className="rounded-2xl overflow-hidden bg-slate-900">
                <img
                  src="/breno-portrait.png"
                  alt="Breno Roncaglione - Professor de Inglês"
                  className="w-full h-auto object-cover object-top"
                />
              </div>
              <div className="p-4 text-center">
                <p className="font-bold text-sm text-slate-900">Breno Roncaglione</p>
                <p className="text-xs text-amber-700 font-semibold">Professor de Inglês Particular</p>
              </div>
            </div>

            <div className="flex items-center gap-6 mt-5 text-xs text-slate-600 font-medium">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" /> Acompanhamento 1-on-1
              </span>
              <span className="flex items-center gap-1.5">
                <HeartHandshake className="w-4 h-4 text-amber-700" /> Ritmo Individual
              </span>
            </div>
          </div>

          {/* Bio Column */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 border border-amber-300 text-amber-900 text-xs font-bold">
              <Award className="w-3.5 h-3.5" />
              Ensino com Foco no Aluno
            </div>

            <h3 className="text-2xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
              "Inglês de verdade, no seu ritmo e com um plano para o seu objetivo."
            </h3>

            <p className="text-slate-700 text-sm leading-relaxed">
              Olá! Sou o <strong>Breno Roncaglione</strong>. Minha atuação como professor é desenhada para adultos e profissionais que já tentaram métodos tradicionais ou aplicativos, mas continuam travando na hora de falar em reuniões, viagens ou entrevistas.
            </p>

            <p className="text-slate-600 text-xs sm:text-sm leading-relaxed">
              Nas minhas aulas particulares — sejam online ou presenciais em São Paulo — nós eliminamos a vergonha do erro e construímos um vocabulário útil para o seu dia a dia. Você ganha confiança para conduzir conversas sem precisar traduzir palavra por palavra na cabeça.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-2xl border border-slate-200 bg-white">
                <h5 className="text-xs font-bold text-slate-900 flex items-center gap-1.5 mb-1">
                  <Check className="w-4 h-4 text-emerald-600" /> Zero Julgamento
                </h5>
                <p className="text-xs text-slate-600">Ambiente seguro onde errar faz parte natural da evolução da fala.</p>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 bg-white">
                <h5 className="text-xs font-bold text-slate-900 flex items-center gap-1.5 mb-1">
                  <Check className="w-4 h-4 text-amber-600" /> Horários Flexíveis
                </h5>
                <p className="text-xs text-slate-600">Possibilidade de alternar horários e ajustar o plano à sua rotina real.</p>
              </div>
            </div>

            <div className="pt-4 flex flex-wrap gap-4 items-center">
              <a
                href={`https://wa.me/${basePhone}?text=${encodeURIComponent('Olá Breno! Gostaria de conversar sobre as aulas particulares.')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-all flex items-center gap-2 cursor-pointer shadow-sm hover:shadow"
              >
                <MessageSquare className="w-4 h-4 fill-current" />
                Conversar com o Breno no WhatsApp
              </a>

              <button
                onClick={onOpenQuiz}
                className="px-6 py-3.5 rounded-full border border-slate-300 hover:bg-slate-100 text-slate-800 font-bold text-xs transition-all flex items-center gap-2 cursor-pointer"
              >
                <span>Diagnóstico de Nível</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
