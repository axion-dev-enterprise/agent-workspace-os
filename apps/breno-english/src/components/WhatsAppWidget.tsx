import React, { useState } from 'react'
import { X, Send, CheckCircle2, Clock, GraduationCap } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { WhatsAppIcon } from './WhatsAppIcon'

interface WhatsAppWidgetProps {
  onOpenQuiz: () => void
}

export const WhatsAppWidget: React.FC<WhatsAppWidgetProps> = ({ onOpenQuiz }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [customMsg, setCustomMsg] = useState('')

  const basePhone = '5511996795882'
  const displayPhone = '(11) 99679-5882'

  const quickMessages = [
    { label: '💻 Tenho interesse nas Aulas Online', text: 'Olá Breno! Gostaria de saber mais sobre as Aulas Online de inglês.' },
    { label: '📍 Quero aulas Presenciais (após 18h)', text: 'Olá Breno! Tenho interesse nas aulas presenciais noturnas (após 18h).' },
    { label: '🎯 Agendar conversa de nivelamento', text: 'Olá Breno! Vi sua página e gostaria de agendar um bate-papo de nivelamento.' }
  ]

  const handleSendWhatsApp = (textToSend: string) => {
    const encoded = encodeURIComponent(textToSend)
    window.open(`https://wa.me/${basePhone}?text=${encoded}`, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="mb-4 w-96 max-w-[calc(100vw-2rem)] rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="bg-[#25D366] p-4 flex items-center justify-between text-white">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <img
                    src="/breno-portrait.png"
                    alt="Breno Roncaglione"
                    className="w-12 h-12 rounded-full object-cover border-2 border-white/90 shadow-sm"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none'
                    }}
                  />
                  <span className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-white border-2 border-[#25D366] rounded-full flex items-center justify-center">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-bold flex items-center gap-1.5">
                    Breno Roncaglione
                    <CheckCircle2 className="w-4 h-4 text-white inline" />
                  </h4>
                  <p className="text-xs text-white/90 font-medium flex items-center gap-1">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-white" />
                    Online agora • Resposta rápida
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-white/80 hover:text-white transition-colors p-1 rounded-lg hover:bg-black/10 cursor-pointer"
                aria-label="Fechar chat"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="p-4 space-y-3 bg-white">
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3 text-xs text-slate-700 leading-relaxed">
                <p className="font-bold text-amber-800 mb-1">Teacher Breno:</p>
                Olá! Como posso ajudar você com seu inglês hoje? Escolha uma opção rápida abaixo ou envie sua mensagem:
              </div>

              {/* Quick suggestions */}
              <div className="space-y-1.5 pt-1">
                {quickMessages.map((msg, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendWhatsApp(msg.text)}
                    className="w-full text-left px-3.5 py-2.5 rounded-xl bg-slate-50 hover:bg-emerald-50 hover:border-emerald-300 border border-slate-200 text-xs text-slate-800 font-medium transition-all flex items-center justify-between group cursor-pointer"
                  >
                    <span>{msg.label}</span>
                    <Send className="w-3.5 h-3.5 text-slate-400 group-hover:text-emerald-600 transition-colors" />
                  </button>
                ))}
              </div>

              <div className="pt-2 border-t border-slate-100">
                <button
                  onClick={() => {
                    setIsOpen(false)
                    onOpenQuiz()
                  }}
                  type="button"
                  className="btn-tactile w-full py-2.5 px-3 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200 text-xs text-amber-900 font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <GraduationCap className="w-4 h-4 text-amber-700" />
                  Fazer Diagnóstico de Nível (1 min)
                </button>
              </div>

              {/* Custom Input */}
              <div className="pt-2 flex gap-2">
                <input
                  type="text"
                  placeholder="Escreva sua dúvida..."
                  value={customMsg}
                  onChange={(e) => setCustomMsg(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && customMsg.trim()) {
                      handleSendWhatsApp(customMsg)
                      setCustomMsg('')
                    }
                  }}
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-[#25D366]"
                />
                <button
                  onClick={() => {
                    if (customMsg.trim()) {
                      handleSendWhatsApp(customMsg)
                      setCustomMsg('')
                    }
                  }}
                  className="p-2.5 rounded-xl bg-[#25D366] hover:bg-[#20ba59] text-white transition-colors cursor-pointer"
                  aria-label="Enviar mensagem"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Atendimento ágil
                </span>
                <span className="font-mono text-slate-700 font-semibold">{displayPhone}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Trigger Button with pulsating ring and official icon */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="relative group flex items-center gap-3 bg-[#25D366] hover:bg-[#20ba59] text-white px-5 py-3.5 rounded-full shadow-[0_8px_25px_rgba(37,211,102,0.4)] hover:shadow-[0_12px_35px_rgba(37,211,102,0.6)] transition-all font-bold text-sm cursor-pointer"
        aria-label="Abrir conversa no WhatsApp"
      >
        <span className="absolute -inset-1 rounded-full bg-[#25D366] opacity-30 group-hover:opacity-75 animate-ping pointer-events-none" />
        <WhatsAppIcon className="w-5 h-5 fill-white relative z-10" />
        <span className="hidden sm:inline relative z-10">Falar no WhatsApp</span>
        <span className="sm:hidden font-mono relative z-10">11 99679-5882</span>
      </motion.button>
    </div>
  )
}
