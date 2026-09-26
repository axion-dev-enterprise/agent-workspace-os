# Diretrizes de Contribuição — AXION Enterprise

Bem-vindo ao repositório AXION! Agradecemos o interesse em contribuir para o ecossistema de engenharia e agentes autônomos.

---

## 1. Fluxo de Trabalho e Branches

1. **Branch de Trabalho**:
   - Todo desenvolvimento deve ocorrer em branches de funcionalidade (`feat/<nome>`, `fix/<nome>`).
   - É expressamente proibido comitar diretamente na branch `main`.
2. **Branch Operacional (`axion`) vs. Whitelabel (`main`)**:
   - O desenvolvimento local ocorre na branch corporativa `axion`.
   - A promoção para a branch pública `main` deve ser realizada exclusivamente via `python scripts/export_whitelabel_release.py`.

---

## 2. Padrões de Código e Qualidade

- **Verificação Empírica**: Todo PR deve incluir evidências de testes executados com sucesso.
- **Tipagem Estrita**: Código TypeScript e Python deve cumprir validação estrita sem supressões indiscriminadas de erro.
- **Zero Segredos**: Nunca comite chaves de API, arquivos `.env` ou credenciais privadas.

---

## 3. Padrão de Commits

Adotamos a especificação **Conventional Commits**:
- `feat(módulo): descrição clara`
- `fix(módulo): correção pontual`
- `docs(módulo): alterações em documentação`
- `refactor(módulo): refatoração sem alteração de comportamento`
- `test(módulo): adição ou correção de testes`
