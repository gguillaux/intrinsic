# Intrinsic
# Intrinsic 💎 - A Análise Fundamentalista que Revela Valor Oculto! 🚀

Bem-vindo ao **Intrinsic**! Somos o seu guia definitivo para navegar no mercado de ações e descobrir ações subvalorizadas com **forte geração de caixa**! 💰

Nossa missão é cortar o "ruído" do mercado usando **análise fundamentalista rigorosa** para encontrar a verdadeira essência e o valor intrínseco das empresas.

## ✨ Principais Destaques (O que fazemos de melhor)

- **Análise Fundamentalista Profunda:** Mergulhamos nos números para entender a saúde real do negócio. 🤓
- **Foco em Geração de Caixa:** Priorizamos empresas que geram caixa livre robusto. Nada de truques, só dinheiro de verdade! 💵
- **Descoberta de Valor:** Identificamos ações que o mercado ainda não percebeu que são barganhas. 🧐

## 🛠️ Como Usar Este Projeto (Comece a Explorar!)

Para começar a utilizar as ferramentas e análises deste repositório, siga estes passos rápidos:

1. **Instalação de Dependências:**
   Execute no seu terminal:
   \`\`\`bash
   npm install
   \`\`\`
   *(Instala todas as bibliotecas necessárias para rodar nossas análises. 📦)*

2. **Executando a Análise Principal:**
   Para iniciar nosso motor de análise principal (que identifica os candidatos de valor), use:
   \`\`\`bash
   npm run analyze
   \`\`\`
   *(Prepare-se para ver os resultados brutos da nossa busca! 🔥)*

3. **Executando Testes:**
   Sempre verifique a integridade dos nossos modelos:
   \`\`\`bash
   npm test
   \`\`\`
   *(Garantindo que nossos números estão corretos. ✅)*

## 🤝 Contribuições

Se você adora valor intrínseco tanto quanto nós e quer ajudar a aprimorar nossas análises, sinta-se à vontade para abrir uma *Pull Request*! 🌟

*Lembre-se: A paciência e a análise rigorosa são as maiores ferramentas de um investidor.* 🧘‍♂️
## 🧪 Debugging Frontend with Playwright (Local MVP)

Para debugging do frontend Dash embarcado no FastAPI, adicionamos um MVP com Playwright (Python) para abrir o app no navegador, capturar o html, screenshots e console logs.

- Como usar:
  1) Instale dependências: `pip install playwright` e rode `python -m playwright install` para baixar os browsers.
  2) Rode o servidor do app localmente (ex.: `uvicorn app.main:server --host 0.0.0.0 --port 8000`).
  3) Rode o debug local:
     - `make -f Makefile.playwright debug-dash` (ou execute o script diretamente: `python tools/playwright_debug/run_dash_debug.py`).
  4) Verifique a pasta `debug_dash/` para conteúdos HTML, screenshots e logs de console.

Observação: este é um MVP para diagnóstico local. Em produção/CI, recomenda-se integrar com o seu pipeline de CI para capturar falhas automaticamente.

