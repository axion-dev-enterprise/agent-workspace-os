import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  GraduationCap,
  ArrowRight,
  ShieldCheck,
  Check,
  Calendar,
  Clock,
  MapPin,
  Laptop,
  Image as ImageIcon
} from 'lucide-react'

import { ThreeBackground } from './components/ThreeBackground'
import { Header } from './components/Header'
import { ModalitiesSection } from './components/ModalitiesSection'
import { ConversationPlayer } from './components/ConversationPlayer'
import { MethodologySection } from './components/MethodologySection'
import { AboutTeacher } from './components/AboutTeacher'
import { TestimonialsSection } from './components/TestimonialsSection'
import { FaqSection } from './components/FaqSection'
import { Footer } from './components/Footer'
import { WhatsAppWidget } from './components/WhatsAppWidget'
import { LevelQuizModal } from './components/LevelQuizModal'
import { OriginalFlyerModal } from './components/OriginalFlyerModal'
import { WhatsAppIcon } from './components/WhatsAppIcon'
import { TiltCard } from './components/TiltCard'

export function App() {
  const [quizOpen, setQuizOpen] = useState(false)
  const [flyerOpen, setFlyerOpen] = useState(false)

  // Booking schedule state for final conversion section
  const [selectedFormat, setSelectedFormat] = useState('Aulas Presenciais (SP)')
  const [selectedPeriod, setSelectedPeriod] = useState('Noturno (Após as 18h)')

  const basePhone = '5511996795882'
  const displayPhone = '11 99679-5882'

  const handleMainWhatsApp = () => {
    const text = encodeURIComponent(
      'Olá Breno! Vi sua página e gostaria de informações sobre as aulas particulares de inglês.'
    )
    window.open(`https://wa.me/${basePhone}?text=${text}`, '_blank', 'noopener,noreferrer')
  }

  const handleBookingWhatsApp = () => {
    const text = encodeURIComponent(
      `Olá Breno! Gostaria de agendar uma conversa inicial de nivelamento.%0A%0A` +
      `📌 *Modalidade de interesse:* ${selectedFormat}%0A` +
      `⏰ *Período preferido:* ${selectedPeriod}`
    )
    window.open(`https://wa.me/${basePhone}?text=${text}`, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="relative min-h-[100dvh] bg-white text-slate-900 selection:bg-amber-100 selection:text-amber-900">
      {/* Interactive WebGL Ambient Canvas */}
      <ThreeBackground />

      {/* Navigation */}
      <Header
        onOpenQuiz={() => setQuizOpen(true)}
        onOpenFlyer={() => setFlyerOpen(true)}
      />

      <main className="relative z-10">
        {/* HERO SECTION */}
        <section className="relative pt-12 pb-20 md:pt-20 md:pb-28 px-6 max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-center">
            {/* Left Content Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="lg:col-span-7 space-y-6"
            >
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-100 border border-slate-200">
                <span className="w-2 h-2 rounded-full bg-[#25D366] animate-pulse" />
                <span className="text-xs font-semibold text-slate-800">
                  Vagas Abertas • Aulas Particulares Individuais
                </span>
              </div>

              {/* Title & Headline with high-end editorial typography */}
              <div className="space-y-3">
                <p className="text-xs font-mono uppercase tracking-widest text-amber-800 font-bold">
                  Aulas de Inglês • Online & Presencial (SP)
                </p>

                <h1 className="font-editorial text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-slate-900 leading-[1.08]">
                  Inglês de verdade, no seu ritmo e com plano para o{' '}
                  <span className="text-amber-800 underline decoration-amber-300 decoration-wavy decoration-2 underline-offset-8">
                    seu objetivo.
                  </span>
                </h1>
              </div>

              {/* Value Proposition */}
              <p className="text-sm sm:text-base text-slate-600 leading-relaxed max-w-xl">
                Metodologia prática e humanizada com o <strong>Professor Breno Roncaglione</strong>. Destrave sua fala para reuniões globais, entrevistas internacionais e viagens, com acompanhamento 1-on-1 próximo.
              </p>

              {/* Offer highlights */}
              <div className="space-y-3 pt-1 text-xs sm:text-sm text-slate-700">
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
                    <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                  </div>
                  <span><strong>Aulas Online:</strong> Estude de onde estiver com horários adaptáveis à sua rotina semanal.</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded-full bg-amber-100 text-amber-900 flex items-center justify-center shrink-0">
                    <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                  </div>
                  <span><strong>Aulas Presenciais:</strong> Turno noturno após 18h no seu endereço (SP), passagem inclusa e <strong>pagamento ao final</strong>.</span>
                </div>
              </div>

              {/* Call to Action Buttons with official pulsating WhatsApp */}
              <div className="pt-4 flex flex-col sm:flex-row gap-3.5 max-w-md">
                <button
                  onClick={handleMainWhatsApp}
                  type="button"
                  className="btn-tactile relative group py-4 px-7 rounded-full bg-[#25D366] hover:bg-[#20ba59] text-white font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-3 shadow-[0_8px_25px_rgba(37,211,102,0.35)] hover:shadow-[0_12px_35px_rgba(37,211,102,0.5)] cursor-pointer"
                >
                  <span className="absolute -inset-0.5 rounded-full bg-[#25D366] opacity-30 group-hover:opacity-75 animate-ping pointer-events-none" />
                  <WhatsAppIcon className="w-5 h-5 fill-white relative z-10" />
                  <span className="relative z-10">Falar no WhatsApp ({displayPhone})</span>
                </button>

                <button
                  onClick={() => setQuizOpen(true)}
                  type="button"
                  className="btn-tactile py-4 px-5 rounded-full bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-800 font-bold text-xs sm:text-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <GraduationCap className="w-4 h-4 text-amber-700" />
                  <span>Diagnóstico de Nível</span>
                </button>
              </div>

              {/* Trust Indicators */}
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
                <span>• Material didático incluso</span>
                <span>• Sem taxa de matrícula</span>
                <span>• Acompanhamento individual</span>
              </div>
            </motion.div>

            {/* Right Visual Column (3D Tilt Card with Inpainted Portrait) */}
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7 }}
              className="lg:col-span-5 flex justify-center"
            >
              <div className="w-full max-w-md">
                <TiltCard tiltAmount={10}>
                  <div className="rounded-3xl border border-slate-200 bg-white p-3 shadow-2xl">
                    <div className="rounded-2xl overflow-hidden bg-slate-900">
                      <img
                        src="/breno-portrait.png"
                        alt="Breno Roncaglione - Professor de Inglês"
                        className="w-full h-auto object-cover object-top"
                      />
                    </div>
                    <div className="p-4 sm:p-5 bg-white flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">Breno Roncaglione</h4>
                        <p className="text-xs text-amber-700 font-semibold">Professor de Inglês Particular</p>
                      </div>

                      <button
                        onClick={() => setFlyerOpen(true)}
                        className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1.5 transition-colors cursor-pointer"
                        title="Ver story original de referência"
                      >
                        <ImageIcon className="w-3.5 h-3.5 text-amber-700" />
                        <span>Ver Criativo</span>
                      </button>
                    </div>
                  </div>
                </TiltCard>
              </div>
            </motion.div>
          </div>
        </section>

        {/* MODALITIES (ONLINE & PRESENCIAL) */}
        <ModalitiesSection />

        {/* INTERACTIVE SPEAKING & AUDIO LAB */}
        <section id="audio-lab" className="py-24 px-6 max-w-6xl mx-auto">
          <ConversationPlayer />
        </section>

        {/* METHODOLOGY & FUNCTIONAL MATRIX */}
        <MethodologySection />

        {/* ABOUT TEACHER BRENO */}
        <AboutTeacher onOpenQuiz={() => setQuizOpen(true)} />

        {/* SOCIAL PROOF & TESTIMONIALS */}
        <TestimonialsSection />

        {/* FAQ ACCORDION */}
        <FaqSection />

        {/* FINAL CONVERSION HUB (FUNCTIONAL SCHEDULER & WHATSAPP) */}
        <section className="py-24 px-6 max-w-5xl mx-auto relative z-10">
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-8 sm:p-14 shadow-sm relative overflow-hidden">
            <div className="text-center max-w-2xl mx-auto mb-10 space-y-3">
              <span className="text-xs font-mono uppercase tracking-widest text-[#25D366] font-bold px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 inline-block">
                Início Imediato • Vagas Limitadas
              </span>

              <h3 className="font-editorial text-2xl sm:text-4xl font-bold text-slate-900 tracking-tight">
                Agende Sua Conversa de Alinhamento
              </h3>

              <p className="text-slate-600 text-xs sm:text-sm leading-relaxed">
                Personalize sua preferência abaixo e fale diretamente com o Professor Breno pelo WhatsApp. Sem burocracia e sem compromisso.
              </p>
            </div>

            {/* Interactive Schedule Selector */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 max-w-2xl mx-auto space-y-6 shadow-2xs">
              {/* Modality Selector */}
              <div>
                <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-2">
                  1. Escolha a Modalidade:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { id: 'Aulas Presenciais (SP)', label: 'Aulas Presenciais (SP)', desc: 'Após 18h no seu endereço com pagamento ao final' },
                    { id: 'Aulas Online (Global)', label: 'Aulas Online (Global)', desc: 'Estude de onde estiver com horários flexíveis' }
                  ].map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setSelectedFormat(m.id)}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                        selectedFormat === m.id
                          ? 'border-amber-400 bg-amber-50/50 shadow-2xs'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <p className="text-xs font-bold text-slate-900">{m.label}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">{m.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Period Selector */}
              <div>
                <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-2">
                  2. Horário de Preferência:
                </label>
                <div className="grid grid-cols-3 gap-2.5">
                  {[
                    'Manhã (07h às 12h)',
                    'Tarde (13h às 18h)',
                    'Noturno (Após as 18h)'
                  ].map((p) => (
                    <button
                      key={p}
                      onClick={() => setSelectedPeriod(p)}
                      className={`p-2.5 rounded-xl border text-center text-xs font-semibold transition-all cursor-pointer ${
                        selectedPeriod === p
                          ? 'border-emerald-500 bg-emerald-50 text-emerald-900 font-bold'
                          : 'border-slate-200 text-slate-600 hover:border-slate-300'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-2">
                <button
                  onClick={handleBookingWhatsApp}
                  type="button"
                  className="btn-tactile relative group w-full py-4 px-6 rounded-full bg-[#25D366] hover:bg-[#20ba59] text-white font-bold text-sm sm:text-base transition-all flex items-center justify-center gap-3 shadow-[0_8px_25px_rgba(37,211,102,0.4)] hover:shadow-[0_12px_35px_rgba(37,211,102,0.6)] cursor-pointer"
                >
                  <span className="absolute -inset-0.5 rounded-full bg-[#25D366] opacity-30 group-hover:opacity-75 animate-ping pointer-events-none" />
                  <WhatsAppIcon className="w-5 h-5 fill-white relative z-10" />
                  <span className="relative z-10">Confirmar e Chamar no WhatsApp ({displayPhone})</span>
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-6 text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  Pagamento ao final (presencial)
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-amber-700" />
                  Resposta em menos de 15 minutos
                </span>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer & Floating Widgets */}
      <Footer />
      <WhatsAppWidget onOpenQuiz={() => setQuizOpen(true)} />
      <LevelQuizModal isOpen={quizOpen} onClose={() => setQuizOpen(false)} />
      <OriginalFlyerModal isOpen={flyerOpen} onClose={() => setFlyerOpen(false)} />
    </div>
  )
}
export default App
