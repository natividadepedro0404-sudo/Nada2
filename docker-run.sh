#!/bin/bash
# Script para testar o Docker localmente

echo "🐳 Construindo imagem Docker..."
docker build -t cc-checker-test .

echo ""
echo "🚀 Iniciando container..."
docker run -p 4000:4000 \
  -e RENDER=true \
  -e PORT=4000 \
  -e SUPABASE_URL="https://yyqvpykqoqiygdinbcbj.supabase.co" \
  -e SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl5cXZweWtxb3FpeWdkaW5iY2JqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI0MDQyNDIsImV4cCI6MjA4Nzk4MDI0Mn0.zfTy2x0mrj3j2TpMhKCz-P8QdnL3bw-V9zWKfwtQpYc" \
  -e MISTICPAY_CLIENT_ID="ci_libdweclsjyry50" \
  -e MISTICPAY_CLIENT_SECRET="cs_kknlfy76fe2ir4nqjydf8ebee" \
  -e WEBHOOK_URL="http://localhost:4000/api/webhook/misticpay" \
  -e DOMINOS_EMAIL="p808409@gmail.com" \
  -e DOMINOS_PASSWORD="@P808409p10" \
  cc-checker-test

echo ""
echo "✅ Container rodando em http://localhost:4000"
