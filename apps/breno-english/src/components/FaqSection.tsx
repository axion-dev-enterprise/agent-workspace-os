import React, { useState } from 'react'
import { ChevronDown, MessageSquare } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export const FaqSection: React.FC = () => {
  const [openIdx, setOpenIdx] = useState<number | null>(0)

  const faqs = [
    {
      q: 'Como funciona o "Pagamento ao final" nas aulas presenciais?',
      a: 'Com total transparência e relação de confiança mútua. Você agenda o seu ciclo de aulas presenciais e o acerto financeiro é realizado somente após as aulas combinadas terem sido ministradas. Isso garante que você só paga pelo serviço devidamente entregue.'
    },
    {
      q: 'O que significa "Passagem inclusa" nas aulas presenciais?',
      a: 'Significa que o custo de deslocamento do professor até a sua residência, escritório ou coworking já está 100% coberto no valor da aula. Não haverá cobrança adicional de transporte, combustível ou Uber.'
    },
    {
      q: 'Quais regiões são atendidas na modalidade presencial?',
      a: 'O atendimento presencial após as 18h cobre as principais regiões da cidade de São Paulo (SP) e bairros centrais/corporativos (como Faria Lima, Paulista, Itaim Bibi, Pinheiros, Berrini, Moema, etc.). Caso esteja em outra área, você pode consultar a disponibilidade via WhatsApp.'
    },
    {
      q: 'Preciso comprar material didático ou livros caros à parte?',
      a: 'Não. Todo o material didático (apostilas digitais personalizadas, áudios, resumos de vocabulário, simulações e materiais de apoio) já está 100% incluso, sem taxas de matrícula ou anuidades escondidas.'
    },
    {
      q: 'Posso fazer uma aula experimental antes de começar?',
      a: 'Sim! Você pode entrar em contato direto pelo WhatsApp (11 99679-5882) para agendar uma conversa inicial de nivelamento e diagnóstico gratuito, onde alinhamos seus objetivos e definimos o plano de estudos.'
    },
    {
      q: 'Qual a flexibilidade caso eu precise remarcar uma aula?',
      a: 'Sabemos que imprevistos profissionais acontecem. Com aviso prévio com antecedência razoável, sua aula pode ser facilmente remarcada dentro da semana sem qualquer perda pedagógica.'
    }
  ]

  return (
    <section id="faq" className="py-24 px-6 max-w-3xl mx-auto relative z-10">
      <div className="text-center mb-16 space-y-3">
        <p className="text-xs font-mono uppercase tracking-wider text-amber-800 font-bold">
          Dúvidas Frequentes
        </p>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
          Perguntas & Respostas
        </h2>
        <p className="text-slate-600 text-sm">
          Tudo o que você precisa saber sobre o funcionamento das aulas particulares.
        </p>
      </div>

      <div className="space-y-3.5">
        {faqs.map((faq, i) => {
          const isOpen = openIdx === i
          return (
            <div
              key={i}
              className={`rounded-2xl border transition-all overflow-hidden ${
                isOpen
                  ? 'border-amber-300 bg-amber-50/20 shadow-sm'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <button
                onClick={() => setOpenIdx(isOpen ? null : i)}
                className="w-full text-left p-5 sm:p-6 flex items-center justify-between gap-4 font-bold text-sm sm:text-base text-slate-900 cursor-pointer"
              >
                <span>{faq.q}</span>
                <ChevronDown
                  className={`w-4 h-4 text-amber-700 shrink-0 transition-transform duration-200 ${
                    isOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>

              <AnimatePresence>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="px-5 sm:px-6 pb-6 pt-0 text-xs sm:text-sm text-slate-600 leading-relaxed border-t border-slate-100">
                      {faq.a}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>

      <div className="mt-12 p-6 rounded-3xl border border-slate-200 bg-slate-50 text-center space-y-3">
        <p className="text-xs text-slate-600">
          Tem alguma dúvida específica ou gostaria de alinhar sua disponibilidade?
        </p>
        <a
          href="https://wa.me/5511996795882?text=Ol%C3%A1%20Breno%2C%20tenho%20uma%20d%C3%BAvida%20sobre%20as%20aulas%3A"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors cursor-pointer shadow-sm hover:shadow"
        >
          <MessageSquare className="w-3.5 h-3.5 fill-current" />
          Falar Diretamente no WhatsApp (11 99679-5882)
        </a>
      </div>
    </section>
  )
}
