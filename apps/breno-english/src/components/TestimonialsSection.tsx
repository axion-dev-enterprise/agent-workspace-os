import React from 'react'
import { Star } from 'lucide-react'

export const TestimonialsSection: React.FC = () => {
  const testimonials = [
    {
      name: 'Lucas Mendonça',
      role: 'Engenheiro de Software Sênior',
      company: 'Contratado por empresa nos EUA',
      text: 'Eu tinha muito receio de travar nas entrevistas com recrutadores de fora. O Breno preparou cada pergunta técnica e comportamental comigo. Em 3 meses passei para uma vaga remota ganhando em dólar. O método é direto ao ponto.',
      stars: 5,
      modality: 'Aulas Online'
    },
    {
      name: 'Mariana Duarte',
      role: 'Gerente de Produto (Tech Lead)',
      company: 'Multinacional Financeira',
      text: 'O formato presencial após as 18h salvou minha rotina. O Breno vinha até o escritório após o meu expediente, o que eliminava qualquer desculpa de trânsito. A segurança que adquiri para conduzir reuniões com a diretoria global não tem preço.',
      stars: 5,
      modality: 'Aulas Presenciais'
    },
    {
      name: 'Dr. Roberto Vasconcelos',
      role: 'Médico Cirurgião',
      company: 'Apresentação em Congresso em Chicago',
      text: 'Precisava apresentar um painel internacional e meu inglês estava parado há 10 anos. A metodologia prática sem enrolação me deu vocabulário preciso e pronúncia polida. Foi um divisor de águas.',
      stars: 5,
      modality: 'Aulas Online'
    }
  ]

  return (
    <section id="depoimentos" className="py-24 px-6 max-w-6xl mx-auto relative z-10">
      <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
        <p className="text-xs font-mono uppercase tracking-wider text-amber-800 font-bold">
          Depoimentos de Alunos
        </p>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
          Resultados Reais na Carreira
        </h2>
        <p className="text-slate-600 text-sm">
          Profissionais que destravaram sua comunicação profissional com o Professor Breno.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {testimonials.map((t, idx) => (
          <div
            key={idx}
            className="rounded-3xl border border-slate-200 bg-white p-8 flex flex-col justify-between hover:border-slate-300 shadow-sm transition-all"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-1 text-amber-500">
                  {[...Array(t.stars)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-current" />
                  ))}
                </div>
                <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold border border-slate-200">
                  {t.modality}
                </span>
              </div>

              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed mb-6">
                "{t.text}"
              </p>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-800 border border-slate-200 flex items-center justify-center font-bold text-xs shrink-0">
                {t.name.split(' ').map(n => n[0]).join('')}
              </div>
              <div>
                <p className="text-xs font-bold text-slate-900">{t.name}</p>
                <p className="text-[11px] text-slate-500">{t.role}</p>
                <p className="text-[11px] text-amber-700 font-semibold">{t.company}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
