---
name: react-native-expo
description: >-
  Operational engineering skill for cross-platform mobile development with Expo Router, React Native, FlashList performance, SecureStore credential isolation, and EAS build automation.
---

# React Native & Expo Mobile Engineering Skill

Guia operacional para desenvolvimento de aplicativos móveis de alto desempenho para iOS e Android com Expo Router, tipagem integral, interface nativa fluida a 60/120 FPS e builds via EAS.

---

## 1. Topologia de Roteamento (Expo Router v3/v4)

Utilize a convenção declarativa baseada no sistema de arquivos nativo sob a pasta `app/`:
```
app/
├── _layout.tsx            # Root layout: provedores globais, splash screen, fontes
├── (auth)/                # Grupo de telas públicas de autenticação
│   ├── login.tsx
│   └── register.tsx
└── (tabs)/                # Interface principal com navegação por abas
    ├── _layout.tsx        # Configuração do BottomTabNavigator
    ├── index.tsx          # Tela inicial (Home Feed)
    ├── explore.tsx        # Tela de busca
    └── profile.tsx        # Perfil do usuário
```

### 1.1 Safe Area e Gestão do Teclado
Sempre utilize `SafeAreaProvider` e `useSafeAreaInsets()` para lidar com recortes de tela (Notch / Dynamic Island) e evite sobreposição com o teclado virtual:
```tsx
import { KeyboardAvoidingView, Platform, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export function ScreenContainer({ children }: { children: React.ReactNode }) {
  const insets = useSafeAreaInsets();

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}
    >
      {children}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#09090b' },
});
```

---

## 2. Renderização de Listas de Alto Desempenho

Em coleções longas (mais de 20 itens), o `FlatList` nativo do React Native sofre com retenção de memória e quedas de FPS em scroll rápido.

### 2.1 Padrão FlashList (`@shopify/flash-list`)
Recicla componentes na memória sem recriar nós na ponte nativa:
```tsx
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={feedItems}
  renderItem={({ item }) => <FeedCard item={item} />}
  estimatedItemSize={120} // Obrigatório para cálculo instantâneo da janela de scroll
  keyExtractor={(item) => item.id}
/>
```

---

## 3. Segurança & Armazenamento de Tokens (Regra #4)

> **Regra Mandatória**: NUNCA armazene JWTs, refresh tokens ou dados sensíveis em `AsyncStorage` (ele persiste em texto plano não criptografado).

Utilize exclusivamente `expo-secure-store`, que delega para o **iOS Keychain** e **Android Keystore**:
```typescript
import * as SecureStore from 'expo-secure-store';

export async function saveAuthToken(token: string): Promise<void> {
  await SecureStore.setItemAsync('auth_token', token, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
}

export async function getAuthToken(): Promise<string | null> {
  return SecureStore.getItemAsync('auth_token');
}
```

---

## 4. Otimização de Imagens (`expo-image`)

Substitua o componente `<Image />` legado por `expo-image`:
- Suporte nativo a WebP e AVIF com compressão extrema.
- Caching em disco e memória com chave de hash.
- Transição suave com placeholder em Blurhash:
```tsx
import { Image } from 'expo-image';

<Image
  source={{ uri: user.avatarUrl }}
  placeholder={user.blurhash}
  contentFit="cover"
  transition={200}
  style={{ width: 48, height: 48, borderRadius: 24 }}
/>
```

---

## 5. Ferramental Integrado

Audite projetos Expo e configurações em `app.json` com o linter embutido:
```powershell
python .agents/skills/react-native-expo/scripts/expo_audit_guard.py <pasta-do-app>
```
O linter valida:
- Ausência de `bundleIdentifier` (iOS) ou `package` (Android) para builds EAS.
- Uso inseguro de `AsyncStorage` para credenciais de autenticação.
- Uso de `FlatList` legado em coleções pesadas.
