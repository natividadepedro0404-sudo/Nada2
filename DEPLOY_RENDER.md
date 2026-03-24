# Guia de Deploy no Render

## Opção 1: Deploy com Docker (Recomendado para CC Checker)

O CC Checker precisa do Chrome/Chromium para funcionar. O Dockerfile já está configurado para instalar todas as dependências.

### Passos:

1. **Faça push do seu repositório para o GitHub**
   ```bash
   git add .
   git commit -m "Add Docker support for Render deployment"
   git push
   ```

2. **Acesse Render.com**
   - Crie uma conta em https://render.com
   - Conecte seu repositório GitHub

3. **Crie um novo Web Service**
   - Clique em "New +" → "Web Service"
   - Conecte seu repositório GitHub
   - Configure:
     - **Runtime**: Docker
     - **Build Command**: (deixe vazio, Docker monta automaticamente)
     - **Start Command**: (deixe vazio, Docker usa CMD do Dockerfile)
     - **Port**: 4000

4. **Configure as Environment Variables**
   No painel do Render, vá para "Environment" e adicione:
   
   ```
   PORT=4000
   RENDER=true
   SUPABASE_URL=https://yyqvpykqoqiygdinbcbj.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   MISTICPAY_CLIENT_ID=ci_libdweclsjyry50
   MISTICPAY_CLIENT_SECRET=cs_kknlfy76fe2ir4nqjydf8ebee
   WEBHOOK_URL=https://seu-render-url.onrender.com/api/webhook/misticpay
   DOMINOS_EMAIL=seu_email@gmail.com
   DOMINOS_PASSWORD=sua_senha
   ```

5. **Deploy**
   - Clique em "Create Web Service"
   - O Render fará o build do Docker automaticamente
   - Isso pode levar 5-10 minutos na primeira vez

### Problemas Comuns:

**Erro: "Chrome instance exited"**
- ✅ Resolvido: O Dockerfile agora instala o Chromium corretamente
- Se persistir, verifique se o Render tem memória suficiente (use o plano Standard ou acima)

**Erro: "chromedriver not found"**
- ✅ Resolvido: O Dockerfile instala chromium-driver

**Build demora muito**
- Normal na primeira vez. Renders subsequentes são mais rápidos.

---

## Opção 2: Deploy com Python Direto (Não Recomendado)

Se quiser tentar sem Docker (menos confiável):
1. Crie um Web Service Python
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python app.py`
4. ⚠️ Aviso: O Chrome ainda pode não funcionar sem o Docker

---

## Testando Localmente com Docker

```bash
# Build local
docker build -t cc-checker .

# Executar local
docker run -p 4000:4000 \
  -e SUPABASE_URL="https://..." \
  -e SUPABASE_KEY="..." \
  -e MISTICPAY_CLIENT_ID="..." \
  cc-checker
```

Acesse: http://localhost:4000

---

## Monitorando Logs

No Render Dashboard:
- Vá para seu Web Service
- Clique em "Logs"
- Veja logs em tempo real do que está rolando

---

## URLs Importantes

- **App URL**: `https://seu-app.onrender.com`
- **Webhook URL**: `https://seu-app.onrender.com/api/webhook/misticpay`
- Atualize a variável `WEBHOOK_URL` com a URL gerada

---

## Removendo Cache de Build

Se o build ficar preso:
1. Vá para Settings
2. Clique "Clear Build Cache"
3. Tentei um novo deploy

---

## Custo e Planos

- **Free**: Pode funcionar, mas app entra em sleep
- **Standard**: Recomendado - alwayson, melhor performance
- Chrome/Selenium precisa de recursos, então Free pode ter timeout
