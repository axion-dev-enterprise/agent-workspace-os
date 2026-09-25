---
name: react-native-expo
description: >-
  Operational skill for cross-platform mobile app development with Expo Router, React Native, native modules, push notifications, and EAS builds.
---

# React Native & Expo Mobile Skill

Skill operacional para desenvolvimento de aplicativos móveis nativos para iOS e Android com Expo.

## 1. Melhores Práticas
- **Expo Router**: Roteamento baseado em arquivos nativo similar ao Next.js App Router (`app/(tabs)/index.tsx`).
- **Performance de Listas**: Utilizar `@shopify/flash-list` em vez de `FlatList` padrão para renderização de listas longas a 60/120 FPS.
- **Safe Area & Teclado**: Sempre envolver telas em `SafeAreaView` e gerenciar teclado com `KeyboardAvoidingView`.
