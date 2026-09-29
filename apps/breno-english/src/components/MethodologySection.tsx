import React from 'react'
import { Target, MessageSquare, Briefcase, TrendingUp, Globe2, Star, Check, X, ShieldCheck } from 'lucide-react'
import { motion } from 'framer-motion'
import { TiltCard } from './TiltCard'

export const MethodologySection: React.FC = () => {
  const pillars = [
    {
      icon: MessageSquare,
      title: 'Conversação Real',
      desc: 'Nada de preencher lacunas em livros estéreis. Você pratica conversação ativa desde o primeiro encontro, desenvolvendo reflexos rápidos sem tradução mental.'
    },
    {
      icon: Briefcase,
      title: 'Inglês Profissional',
      desc: 'Simulações reais de entrevistas internacionais, apresentações executivas, reuniões globais com nativos e redação precisa de e-mails corporativos.'
    },
    {
      icon: TrendingUp,
      title: 'Acompanhamento Próximo',
      desc: 'Seu mentor individual mapeia exatamente seus pontos de bloqueio na pronúncia e gramática, aplicando correções cirúrgicas semana após semana.'
    }
  ]

  const comparisonRows = [
    {
      feature: 'Atenção e Foco',
      traditional: '15 a 25 alunos disputando o tempo do professor',
      breno: '100% individual e exclusivo para as suas necessidades'
    },
    {
      feature: 'Tempo de Fala Ativa',
      traditional: 'Menos de 3 a 5 minutos de fala real por aula',
      breno: 'Você fala durante mais de 80% do tempo de cada encontro'
    },
    {
      feature: 'Conteúdo das Aulas',
      traditional: 'Apostila genérica e regras gramaticais estéreis',
      breno: 'Focado nos seus desafios de trabalho, reuniões e entrevistas'
    },
    {
      feature: 'Material Didático',
      traditional: 'Livros e taxas de matrícula cobrados à parte',
      breno: 'Material digital 100% incluso sem nenhuma taxa extra'
    },
    {
      feature: 'Garantia e Confiança',
      traditional: 'Contratos anuais com multas de cancelamento',
      breno: 'Pagamento ao final do ciclo no presencial e risco zero'
    }
  ]

  return (
    <section id="metodo" className="py-24 bg-slate-50/70 border-y border-slate-200/80 relative z-10">
      <div className="max-w-6xl mx-auto px-6">
        {/* Section Header with Functional Pill */}
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 border border-amber-300 text-amber-900 text-xs font-bold font-mono">
            <span>[ 02 / METODOLOGIA PRÓPRIA ]</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
            Aulas Práticas, Dinâmicas e Focadas em Resultados
          </h2>

          <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
            Desenvolvida para adultos e executivos que não têm tempo a perder e precisam de autonomia comunicativa imediata no mercado.
          </p>
        </div>

        {/* 3 Pillars with 3D Tilt Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
          {pillars.map((item, idx) => {
            const Icon = item.icon
            return (
              <TiltCard key={idx} tiltAmount={8} className="h-full">
                <div className="h-full rounded-3xl border border-slate-200 bg-white p-8 flex flex-col justify-between hover:border-amber-300 hover:shadow-xl transition-all shadow-sm">
                  <div>
                    <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200 text-amber-700 flex items-center justify-center mb-6 shadow-2xs">
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-2">
                      {item.title}
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                      {item.desc}
                    </p>
                  </div>

                  <div className="mt-8 pt-4 border-t border-slate-100 flex items-center gap-2 text-[11px] text-slate-500 font-mono font-semibold">
                    <span className="w-2 h-2 rounded-full bg-amber-600" />
                    Pilar Fundamental 0{idx + 1}
                  </div>
                </div>
              </TiltCard>
            )
          })}
        </div>

        {/* Functional Matrix Div: Traditional School vs. Breno */}
        <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden mb-16">
          <div className="p-6 sm:p-8 bg-slate-900 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="text-xs font-mono uppercase tracking-wider text-amber-400 font-bold">
                Comparativo Estratégico
              </p>
              <h3 className="text-xl sm:text-2xl font-bold text-white mt-1">
                Por Que o Ensino Particular Supera Cursinhos Tradicionais
              </h3>
            </div>
            <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-xs font-mono font-semibold border border-amber-500/30">
              ROI em Tempo & Aprendizado
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {comparisonRows.map((row, i) => (
              <div
                key={i}
                className="grid grid-cols-1 md:grid-cols-12 p-5 sm:p-6 items-center gap-4 hover:bg-slate-50/50 transition-colors"
              >
                <div className="md:col-span-3 font-bold text-sm text-slate-900">
                  {row.feature}
                </div>

                <div className="md:col-span-4 flex items-start gap-2.5 text-xs sm:text-sm text-slate-500">
                  <X className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                  <span>{row.traditional}</span>
                </div>

                <div className="md:col-span-5 flex items-start gap-2.5 text-xs sm:text-sm text-slate-900 font-semibold bg-emerald-50/60 p-3 rounded-xl border border-emerald-100">
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="text-emerald-950">{row.breno}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 4 Bottom Pillars from Flyer */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-4">
          {[
            { icon: Globe2, label: 'Mais Oportunidades', desc: 'Vagas remotas em moeda forte e expansão de mercado global.' },
            { icon: ShieldCheck, label: 'Confiança para se Comunicar', desc: 'Fim do receio e suor frio antes de reuniões com estrangeiros.' },
            { icon: Briefcase, label: 'Evolução na Carreira', desc: 'Salários substancialmente maiores para profissionais bilíngues.' },
            { icon: Star, label: 'Investimento em Você', desc: 'A competência de maior retorno vitalício para sua autonomia.' }
          ].map((b, i) => {
            const Icon = b.icon
            return (
              <div key={i} className="p-5 rounded-2xl bg-white border border-slate-200 shadow-2xs space-y-2">
                <div className="flex items-center gap-2.5 text-amber-700">
                  <Icon className="w-4 h-4" />
                  <span className="text-xs font-bold text-slate-900 tracking-wide uppercase">
                    {b.label}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {b.desc}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
