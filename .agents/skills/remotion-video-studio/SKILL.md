---
name: remotion-video-studio
description: >-
  Comprehensive operational skill for programmatic video creation, rendering, and animation with Remotion and React.
  Covers composition architecture, React markup, audio/video synchronization, captions, Remotion Studio preview,
  SSR rendering (CLI/Lambda), and dynamic asset pipelines.
---

# Remotion Video Studio -- Master Engineering Skill

Skill operacional canonica e unificada para producao programatica de videos, animacoes graficas e composicoes audiovisuais em React utilizando o ecossistema **Remotion**.

---

## 1. Arquitetura Fundamental do Remotion

Um video no Remotion e uma funcao pura do estado e do tempo (`frame` atual).

### 1.1 Anatomia de uma Composicao Canônica
```tsx
import { Composition } from 'remotion';
import { MainVideo } from './components/MainVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MainHeroVideo"
      component={MainVideo}
      durationInFrames={300} // 10 segundos a 30fps
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: 'Bem-vindo ao AXION',
        themeColor: '#00f0ff',
      }}
    />
  );
};
```

### 1.2 Regras de Ouro de Animacao e Tempo
- **Nunca use `useState` ou timers do browser (`setTimeout`, `setInterval`) para animar**: Toda mudanca visual deve derivar de `useCurrentFrame()` e `useVideoConfig()`.
- **Interpolacao Suave**: Use `interpolate()` com `extrapolateLeft: 'clamp'` e `extrapolateRight: 'clamp'`:
  ```tsx
  import { useCurrentFrame, interpolate } from 'remotion';

  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  ```
- **Fisica com Spring**: Use `spring()` para dinamica de aceleracao natural sem curvas manuais:
  ```tsx
  import { spring, useCurrentFrame, useVideoConfig } from 'remotion';

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, mass: 0.5 } });
  ```

---

## 2. Estruturacao de Cenas e Sequenciamento

Utilize `<Sequence>` e `<Series>` para compartimentar o tempo sem calcular offsets manuais:

```tsx
import { Series } from 'remotion';
import { IntroScene } from './scenes/IntroScene';
import { FeatureScene } from './scenes/FeatureScene';
import { OutroScene } from './scenes/OutroScene';

export const MainVideo: React.FC = () => {
  return (
    <Series>
      <Series.Sequence durationInFrames={90}>
        <IntroScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={150}>
        <FeatureScene />
      </Series.Sequence>
      <Series.Sequence durationInFrames={60}>
        <OutroScene />
      </Series.Sequence>
    </Series>
  );
};
```

---

## 3. Audio, Trilhas Sonoras e Legendas Dinamicas

### 3.1 Sincronizacao de Audio e Efeitos (SFX)
```tsx
import { Audio, staticFile } from 'remotion';

export const SoundTrack: React.FC = () => {
  return (
    <>
      <Audio src={staticFile('audio/ambient_beat.mp3')} volume={0.6} />
      <Audio src={staticFile('audio/whoosh.wav')} startFrom={0} volume={0.9} />
    </>
  );
};
```

### 3.2 Legendas Temporizadas (Captions)
Toda legenda deve seguir o tipo oficial `Caption` com timestamps em milissegundos:
```tsx
import { useCurrentFrame, useVideoConfig } from 'remotion';

interface WordCaption {
  text: string;
  startMs: number;
  endMs: number;
}

export const AnimatedCaptions: React.FC<{ words: WordCaption[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;

  return (
    <div className="absolute bottom-20 w-full text-center text-3xl font-bold text-white">
      {words.map((w, idx) => {
        const isActive = currentMs >= w.startMs && currentMs <= w.endMs;
        return (
          <span key={idx} style={{ color: isActive ? '#00f0ff' : '#ffffff', opacity: isActive ? 1 : 0.6, margin: '0 4px' }}>
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
```

---

## 4. Utilitario CLI Standalone (`scripts/remotion_cli_helper.py`)

A skill inclui um executor CLI que valida o ambiente Node, detecta composicoes no projeto e roda renders e preview sem complexidade:

```bash
# Diagnosticar projeto Remotion e listar composicoes
python .agents/skills/remotion-video-studio/scripts/remotion_cli_helper.py --dir apps/my-video --info

# Iniciar o Remotion Studio interativo
python .agents/skills/remotion-video-studio/scripts/remotion_cli_helper.py --dir apps/my-video --studio

# Executar render headless de MP4 com aceleracao de hardware
python .agents/skills/remotion-video-studio/scripts/remotion_cli_helper.py --dir apps/my-video --render MainHeroVideo --out dist/video.mp4
```

---

## 5. Portao de Verificacao (Verification Gate)

Antes de aprovar qualquer video em Remotion:
1. Execute `npm run build` ou `npx remotion bundle` para garantir ausencia de erros de tipo em TypeScript.
2. Inspecione o render headless de teste dos primeiros 30 frames:
   ```bash
   npx remotion render src/index.ts MainHeroVideo out/test.mp4 --frames=0-30
   ```
3. Verifique se o arquivo MP4 gerado tem tamanho > 0 bytes e codec H.264/AAC valido via `ffprobe`.