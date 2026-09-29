import React, { useState, useEffect, useRef } from 'react'
import { Play, Pause, UserCheck, Volume2, ShieldCheck } from 'lucide-react'
import { motion } from 'framer-motion'

interface Scenario {
  id: string
  title: string
  category: string
  phraseEn: string
  phrasePt: string
  tip: string
  audioSpeed: number
}

const scenarios: Scenario[] = [
  {
    id: 'interview',
    title: 'Entrevista Internacional',
    category: 'Carreira & Contratação',
    phraseEn: "Could you walk me through your decision-making process during that architectural migration?",
    phrasePt: "Você poderia me guiar pelo seu processo de tomada de decisão durante aquela migração de arquitetura?",
    tip: "O Breno treina com você conectores de alta autoridade ('First and foremost', 'Ultimately', 'From my standpoint').",
    audioSpeed: 0.95
  },
  {
    id: 'negotiation',
    title: 'Negociação Salarial',
    category: 'Business English',
    phraseEn: "Given the scope of this role and market benchmarks, I'm targeting a base compensation of 110k.",
    phrasePt: "Dado o escopo desta função e os padrões de mercado, estou buscando uma remuneração base de 110k.",
    tip: "Prática de postura vocal assertiva e pausas estratégicas, sem hesitações ('uhms' e 'ahs').",
    audioSpeed: 0.9
  },
  {
    id: 'meeting',
    title: 'Reunião de Alinhamento',
    category: 'Daily Standup & Sync',
    phraseEn: "Let's circle back to this point once we review the analytics report by Friday.",
    phrasePt: "Vamos retomar esse ponto assim que revisarmos o relatório de métricas até sexta-feira.",
    tip: "Expressões corporativas comuns ('circle back', 'by Friday') usadas de forma idiomática e natural.",
    audioSpeed: 1.0
  },
  {
    id: 'travel',
    title: 'Viagens & Autonomia',
    category: 'Situações Reais',
    phraseEn: "Excuse me, could you let me know if this express train connects directly to downtown?",
    phrasePt: "Com licença, você saberia me dizer se este trem expresso faz conexão direta com o centro?",
    tip: "Entonação educada e ritmo calmo para resolver imprevistos no exterior sem insegurança.",
    audioSpeed: 0.95
  }
]

export const ConversationPlayer: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<Scenario>(scenarios[0])
  const [isPlaying, setIsPlaying] = useState(false)
  const [audioBars, setAudioBars] = useState<number[]>([12, 28, 45, 18, 35, 60, 42, 25, 55, 30, 15, 40])
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      audioRef.current = null
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    setIsPlaying(false)
  }

  const playAudio = () => {
    stopAudio()

    // 1. Primary: Use pre-rendered studio neural audio file (100% native US English voice)
    const audioSrc = `/audio/${selectedScenario.id}.mp3`
    const audio = new Audio(audioSrc)
    audioRef.current = audio

    audio.onplay = () => setIsPlaying(true)
    audio.onended = () => {
      setIsPlaying(false)
      audioRef.current = null
    }
    audio.onerror = () => {
      // 2. Fallback to Web Speech API with STRICT English voice enforcement
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel()
        const utterance = new SpeechSynthesisUtterance(selectedScenario.phraseEn)
        utterance.lang = 'en-US'
        utterance.rate = selectedScenario.audioSpeed

        const voices = window.speechSynthesis.getVoices()
        const enVoice =
          voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Christopher') || v.name.includes('Guy') || v.name.includes('Aria') || v.name.includes('David') || v.name.includes('Jenny'))) ||
          voices.find(v => v.lang.startsWith('en'))
        if (enVoice) utterance.voice = enVoice

        utterance.onstart = () => setIsPlaying(true)
        utterance.onend = () => setIsPlaying(false)
        utterance.onerror = () => setIsPlaying(false)

        window.speechSynthesis.speak(utterance)
      } else {
        setIsPlaying(false)
      }
    }

    audio.play().catch(() => {
      // If browser blocked autoplay, fallback to speech synthesis
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel()
        const utterance = new SpeechSynthesisUtterance(selectedScenario.phraseEn)
        utterance.lang = 'en-US'
        utterance.rate = selectedScenario.audioSpeed
        const voices = window.speechSynthesis.getVoices()
        const enVoice = voices.find(v => v.lang.startsWith('en'))
        if (enVoice) utterance.voice = enVoice
        utterance.onstart = () => setIsPlaying(true)
        utterance.onend = () => setIsPlaying(false)
        utterance.onerror = () => setIsPlaying(false)
        window.speechSynthesis.speak(utterance)
      }
    })
  }

  // Cleanup on unmount or scenario change
  useEffect(() => {
    return () => {
      stopAudio()
    }
  }, [selectedScenario])

  useEffect(() => {
    let interval: any
    if (isPlaying) {
      interval = setInterval(() => {
        setAudioBars(
          Array.from({ length: 14 }, () => Math.floor(Math.random() * 45) + 10)
        )
      }, 100)
    } else {
      setAudioBars([14, 22, 38, 18, 28, 44, 32, 20, 36, 24, 16, 30, 18, 24])
    }
    return () => clearInterval(interval)
  }, [isPlaying])

  return (
    <div className="w-full rounded-3xl border border-slate-200 bg-white p-6 sm:p-10 shadow-sm relative overflow-hidden">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-8 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono uppercase tracking-wider text-amber-800 font-bold">
              Laboratório de Pronúncia
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
              <Volume2 className="w-3 h-3 text-emerald-600" />
              Voz Nativa Americana (en-US)
            </span>
          </div>
          <h3 className="font-editorial text-xl sm:text-2xl font-bold text-slate-900 mt-1">
            Ouça a Dinâmica Prática das Aulas
          </h3>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            Exemplos de frases reais treinadas pelo Professor Breno com dicção natural e entonação profissional.
          </p>
        </div>

        {/* Tab selection */}
        <div className="flex flex-wrap gap-1.5 bg-slate-100 p-1.5 rounded-xl border border-slate-200">
          {scenarios.map((sc) => (
            <button
              key={sc.id}
              type="button"
              onClick={() => {
                stopAudio()
                setSelectedScenario(sc)
              }}
              className={`btn-tactile px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedScenario.id === sc.id
                  ? 'bg-white text-slate-900 shadow-sm border border-slate-200/60'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {sc.title}
            </button>
          ))}
        </div>
      </div>

      {/* Main Player Display */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-8 items-center">
        {/* Left: Phrase card */}
        <div className="lg:col-span-8 space-y-5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-700 font-semibold">
              {selectedScenario.category}
            </span>
          </div>

          <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-6 sm:p-7">
            <p className="text-lg sm:text-2xl font-bold text-slate-900 leading-relaxed">
              "{selectedScenario.phraseEn}"
            </p>
            <p className="text-xs sm:text-sm text-slate-600 mt-3 font-medium">
              {selectedScenario.phrasePt}
            </p>

            <div className="mt-5 pt-4 border-t border-slate-200 text-xs text-slate-700 leading-relaxed">
              <strong className="text-amber-800 font-bold">Como o Breno orienta: </strong>
              {selectedScenario.tip}
            </div>
          </div>

          {/* Audio Visualizer Waves */}
          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200 flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5 h-10 flex-1 px-2">
              {audioBars.map((height, i) => (
                <motion.div
                  key={i}
                  animate={{ height: `${height}px` }}
                  transition={{ duration: 0.1 }}
                  className={`w-1.5 rounded-full transition-colors ${
                    isPlaying ? 'bg-amber-600' : 'bg-slate-300'
                  }`}
                />
              ))}
            </div>

            <button
              onClick={isPlaying ? stopAudio : playAudio}
              type="button"
              className="btn-tactile px-5 py-2.5 rounded-xl bg-amber-700 hover:bg-amber-800 text-white font-bold text-xs transition-all flex items-center gap-2 shadow-sm shrink-0 cursor-pointer"
            >
              {isPlaying ? (
                <>
                  <Pause className="w-4 h-4 fill-current" /> Pausar
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" /> Ouvir Pronúncia
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: How lessons actually work */}
        <div className="lg:col-span-4 bg-slate-50 border border-slate-200 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-200">
            <UserCheck className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Como Funciona na Prática
            </span>
          </div>

          <div className="space-y-3.5 text-xs text-slate-700 leading-relaxed">
            <div className="flex items-start gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-600 mt-1.5 shrink-0" />
              <span><strong>Sem interrupções traumáticas:</strong> o Breno anota suas pronúncias e termos e faz a revisão em momentos estratégicos.</span>
            </div>
            <div className="flex items-start gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-600 mt-1.5 shrink-0" />
              <span><strong>Gravações para comparação:</strong> você percebe claramente a evolução da dicção e a perda da inibição ao longo dos meses.</span>
            </div>
            <div className="flex items-start gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-600 mt-1.5 shrink-0" />
              <span><strong>Vocabulário vivo:</strong> focado nas expressões que você realmente precisa no seu setor de atuação.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
