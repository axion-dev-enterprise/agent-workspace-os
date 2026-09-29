import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ArrowRight, CheckCircle2, Compass, MessageSquare, Award, Laptop, MapPin } from 'lucide-react'
import confetti from 'canvas-confetti'

interface LevelQuizModalProps {
  isOpen: boolean
  onClose: () => void
}

export const LevelQuizModal: React.FC<LevelQuizModalProps> = ({ isOpen, onClose }) => {
  const [step, setStep] = useState(1)
  const [level, setLevel] = useState<string>('')
  const [goal, setGoal] = useState<string>('')
  const [format, setFormat] = useState<string>('')

  const handleFinish = () => {
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 }
    })
    setStep(4)
  }

  const handleSendToWhatsApp = () => {
    const text = `Olá Breno! Fiz o diagnóstico de nível na sua página:%0A%0A` +
      `📊 *Meu Nível Atual:* ${encodeURIComponent(level)}%0A` +
      `🎯 *Meu Objetivo:* ${encodeURIComponent(goal)}%0A` +
      `📍 *Formato Preferido:* ${encodeURIComponent(format)}%0A%0A` +
      `Gostaria de agendar uma conversa com base nesse plano!`

    window.open(`https://wa.me/5511996795882?text=${text}`, '_blank', 'noopener,noreferrer')
    onClose()
  }

  const resetAndClose = () => {
    setStep(1)
    setLevel('')
    setGoal('')
    setFormat('')
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={resetAndClose}
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
          />

          {/* Dialog Container */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 15 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 15 }}
            className="relative w-full max-w-xl rounded-3xl border border-slate-200 bg-white shadow-2xl p-6 sm:p-8 z-10 overflow-hidden text-slate-900"
          >
            {/* Top decorative solid bar */}
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-amber-600" />

            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-amber-700" />
                <span className="text-xs font-bold uppercase tracking-wider text-amber-800 font-mono">
                  Diagnóstico de Fluência & Objetivos
                </span>
              </div>
              <button
                onClick={resetAndClose}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                aria-label="Fechar modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Step 1: Level */}
            {step === 1 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="pt-6 space-y-4"
              >
                <div>
                  <span className="text-xs text-slate-500 font-mono font-bold">Passo 1 de 3</span>
                  <h3 className="text-lg sm:text-xl font-bold text-slate-900 mt-1">
                    Como você avalia seu inglês hoje?
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Seja sincero. As aulas adaptam-se ao seu ponto exato de partida.
                  </p>
                </div>

                <div className="space-y-2.5 pt-2">
                  {[
                    { id: 'Iniciante do Zero', desc: 'Nunca estudei ou sei apenas palavras básicas e isoladas.' },
                    { id: 'Bloqueado na Fala', desc: 'Entendo bem leitura e séries, mas travo na hora de falar em voz alta.' },
                    { id: 'Intermediário Operacional', desc: 'Consigo me virar, mas faltam vocabulário avançado e fluência natural.' },
                    { id: 'Avançado / Executivo', desc: 'Já falo bem, preciso de refinamento para liderança global e negociações.' }
                  ].map((item) => (
                    <button
                      key={item.id}
                      onClick={() => {
                        setLevel(item.id)
                        setStep(2)
                      }}
                      className="w-full text-left p-4 rounded-2xl border border-slate-200 hover:border-amber-400 bg-slate-50 hover:bg-amber-50/40 transition-all flex items-start justify-between group cursor-pointer"
                    >
                      <div>
                        <p className="text-sm font-bold text-slate-900 group-hover:text-amber-800 transition-colors">
                          {item.id}
                        </p>
                        <p className="text-xs text-slate-600 mt-0.5">{item.desc}</p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-700 mt-1 group-hover:translate-x-1 transition-all" />
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Step 2: Goal */}
            {step === 2 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="pt-6 space-y-4"
              >
                <div>
                  <span className="text-xs text-slate-500 font-mono font-bold">Passo 2 de 3</span>
                  <h3 className="text-lg sm:text-xl font-bold text-slate-900 mt-1">
                    Qual é a sua principal meta com o inglês?
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    O plano pedagógico será estruturado em torno dessa prioridade.
                  </p>
                </div>

                <div className="space-y-2.5 pt-2">
                  {[
                    { id: 'Carreira & Reuniões Globais', desc: 'Liderar reuniões, falar com equipes de fora e destravar promoções.' },
                    { id: 'Entrevistas de Emprego em Inglês', desc: 'Passar em processos seletivos e concorrer a vagas internacionais.' },
                    { id: 'Viagens & Autonomia', desc: 'Viajar com autonomia total, sem medo de aeroportos, hotéis e imprevistos.' },
                    { id: 'Fluência Geral & Conversação Livre', desc: 'Conversar com confiança sobre qualquer assunto sem traduzir mentalmente.' }
                  ].map((item) => (
                    <button
                      key={item.id}
                      onClick={() => {
                        setGoal(item.id)
                        setStep(3)
                      }}
                      className="w-full text-left p-4 rounded-2xl border border-slate-200 hover:border-amber-400 bg-slate-50 hover:bg-amber-50/40 transition-all flex items-start justify-between group cursor-pointer"
                    >
                      <div>
                        <p className="text-sm font-bold text-slate-900 group-hover:text-amber-800 transition-colors">
                          {item.id}
                        </p>
                        <p className="text-xs text-slate-600 mt-0.5">{item.desc}</p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-700 mt-1 group-hover:translate-x-1 transition-all" />
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Step 3: Format */}
            {step === 3 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="pt-6 space-y-4"
              >
                <div>
                  <span className="text-xs text-slate-500 font-mono font-bold">Passo 3 de 3</span>
                  <h3 className="text-lg sm:text-xl font-bold text-slate-900 mt-1">
                    Qual formato se adapta melhor à sua rotina?
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Ambas as modalidades contam com acompanhamento individual.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                  <button
                    onClick={() => {
                      setFormat('Aulas Online (Estude de onde estiver)')
                      handleFinish()
                    }}
                    className="p-5 rounded-2xl border border-slate-200 hover:border-blue-400 bg-slate-50 hover:bg-blue-50/40 text-left transition-all group cursor-pointer"
                  >
                    <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center mb-3">
                      <Laptop className="w-5 h-5" />
                    </div>
                    <p className="font-bold text-sm text-slate-900 group-hover:text-blue-800">
                      Aulas Online
                    </p>
                    <p className="text-xs text-slate-600 mt-1">
                      Máxima flexibilidade de horários, material incluso e chamadas interativas 1-on-1.
                    </p>
                  </button>

                  <button
                    onClick={() => {
                      setFormat('Aulas Presenciais (Após 18h com pagamento ao final)')
                      handleFinish()
                    }}
                    className="p-5 rounded-2xl border border-slate-200 hover:border-amber-400 bg-slate-50 hover:bg-amber-50/40 text-left transition-all group cursor-pointer"
                  >
                    <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center mb-3">
                      <MapPin className="w-5 h-5" />
                    </div>
                    <p className="font-bold text-sm text-slate-900 group-hover:text-amber-800">
                      Aulas Presenciais
                    </p>
                    <p className="text-xs text-slate-600 mt-1">
                      Noite (após 18h), passagem inclusa e pagamento ao final do ciclo de aulas.
                    </p>
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 4: Diagnostic Completed */}
            {step === 4 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="pt-6 space-y-5 text-center"
              >
                <div className="w-14 h-14 mx-auto rounded-full bg-emerald-100 border border-emerald-200 flex items-center justify-center text-emerald-600">
                  <CheckCircle2 className="w-8 h-8" />
                </div>

                <div>
                  <h3 className="text-xl font-bold text-slate-900">
                    Seu Diagnóstico Está Pronto!
                  </h3>
                  <p className="text-xs text-slate-600 max-w-sm mx-auto mt-1">
                    Cruzamos seu nível e objetivo para desenhar um roteiro de evolução direto com o Breno.
                  </p>
                </div>

                {/* Summary box */}
                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-left space-y-2 text-xs">
                  <div className="flex justify-between border-b border-slate-200/80 pb-2">
                    <span className="text-slate-500">Ponto de partida:</span>
                    <span className="font-bold text-amber-800">{level}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-200/80 pb-2">
                    <span className="text-slate-500">Objetivo foco:</span>
                    <span className="font-bold text-slate-900">{goal}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Modalidade:</span>
                    <span className="font-bold text-emerald-700">{format}</span>
                  </div>
                </div>

                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center gap-2 text-left">
                  <Award className="w-5 h-5 shrink-0 text-amber-700" />
                  <span>
                    <strong>Bônus:</strong> Sua primeira conversa de alinhamento e nivelamento prático é gratuita.
                  </span>
                </div>

                <button
                  onClick={handleSendToWhatsApp}
                  className="w-full py-4 px-6 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <MessageSquare className="w-4 h-4 fill-current" />
                  Enviar Diagnóstico para o WhatsApp do Breno
                </button>
              </motion.div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
