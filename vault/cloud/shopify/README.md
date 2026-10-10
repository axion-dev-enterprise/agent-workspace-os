# Shopify — SPA Pharma Brasil

Credencial temporária atualizada em 2026-10-02 pelo operador para autenticação da conta Shopify. O login anterior foi substituído; os valores vigentes ficam exclusivamente no arquivo .env ignorado pelo Git.
Valores exclusivamente no arquivo .env ignorado pelo Git. Nunca incluir senha em relatórios.
Consumo programático: scripts.vault_loader.load_vault(). Não há serviço automático configurado.
O titular pode rotacionar a senha nas configurações de segurança da conta Shopify ou usar a recuperação oficial; alterações de senha devem ser realizadas pelo titular.
Revogar sessões temporárias após o trabalho, conforme decisão do titular.
Auditoria: python scripts/vault_loader.py audit.
Código de uso único solicitado pela Shopify permanece pendente; não persistir códigos transitórios.

O app `n8n SpaPharma (SERVIDOR)` possui credenciais próprias no Dev Dashboard. A chave de cliente e qualquer token efêmero ficam apenas neste `.env`. Não revele, rotacione, desinstale ou reutilize a integração sem validação do token e autorização para mudanças. O token de acesso, quando emitido, expira conforme o fluxo da Shopify e deve ser renovado programaticamente.

A variável `SPAPHARMA_OPS_KEY` autentica exclusivamente rotas operacionais de finalidade fixa no bridge Vercel. Rotacione-a se houver suspeita de exposição; ela nunca deve ser enviada ao navegador ou registrada em logs.
