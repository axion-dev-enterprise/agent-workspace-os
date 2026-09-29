import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Image as ImageIcon, CheckCircle, Layers } from 'lucide-react'

interface OriginalFlyerModalProps {
  isOpen: boolean
  onClose: () => void
}

export const OriginalFlyerModal: React.FC<OriginalFlyerModalProps> = ({ isOpen, onClose }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
          />

          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="relative w-full max-w-3xl max-h-[90vh] rounded-3xl border border-slate-200 bg-white shadow-2xl p-6 sm:p-8 z-10 flex flex-col overflow-hidden text-slate-900"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 shrink-0">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-5 h-5 text-amber-700" />
                <h4 className="text-sm font-bold text-slate-900">
                  Criativo Original dos Stories (@blackcatcalls)
                </h4>
              </div>
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                aria-label="Fechar"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content Body */}
            <div className="overflow-y-auto py-4 space-y-6 flex-1 pr-1">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                <div className="flex justify-center bg-slate-100 p-2 rounded-2xl border border-slate-200">
                  <img
                    src="/flyer-original.png"
                    alt="Story Original Breno Roncaglione"
                    className="max-h-[60vh] object-contain rounded-xl shadow-lg border border-slate-200"
                  />
                </div>

                <div className="space-y-4 text-xs sm:text-sm text-slate-700">
                  <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900">
                    <p className="font-bold flex items-center gap-1.5 mb-1 text-amber-950 font-mono text-xs">
                      <Layers className="w-4 h-4 text-amber-700" />
                      Fidelidade Visual & Arquitetura
                    </p>
                    Esta aplicação recria e expande a oferta comercial e os diferenciais do criativo oficial para um formato web responsivo de alta conversão.
                  </div>

                  <div className="space-y-2.5">
                    <h5 className="font-bold text-slate-900 uppercase tracking-wider text-xs">
                      Elementos Mapeados do Flyer:
                    </h5>
                    <ul className="space-y-2 text-slate-600 text-xs">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span><strong>Autoridade:</strong> Breno Roncaglione — Professor de Inglês.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span><strong>Modalidade Online:</strong> Estude de onde estiver, flexibilidade, material incluso, foco no objetivo.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span><strong>Modalidade Presencial:</strong> Após as 18h, passagem inclusa, dias combinados, pagamento ao final.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span><strong>Metodologia Própria:</strong> Aulas práticas, dinâmicas e focadas em resultados.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span><strong>Canal de Conversão:</strong> WhatsApp oficial (11) 99679-5882.</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
