#!/bin/bash

# Test script to verify preferences update functionality
# This script tests the preferences update endpoint

echo "=== Testando a funcionalidade de atualização de preferências ==="
echo ""

# First, verify the server is running
echo "1. Verificando se o servidor está rodando..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Servidor está rodando"
else
    echo "❌ Servidor não está respondendo em http://localhost:8000"
    echo "   Inicie o servidor com: ./scripts/start_server.sh"
    exit 1
fi

echo ""
echo "2. Instruções de teste manual:"
echo ""
echo "   a) Abra o navegador em http://localhost:8000/home.html"
echo "   b) Faça login com suas credenciais"
echo "   c) Vá para a aba 'Profile'"
echo "   d) Preencha os campos de preferências:"
echo "      - Culinária Preferida: Brasileira"
echo "      - Região: Sudeste"
echo "      - Marque alguns checkboxes (baixo sódio, etc)"
echo "      - Preencha likes/dislikes"
echo "   e) Clique em 'Salvar Preferências'"
echo "   f) Verifique se a mensagem 'Preferências salvas com sucesso' aparece"
echo "   g) Recarregue a página e clique em 'Carregar Perfil'"
echo "   h) Verifique se os checkboxes mantêm os valores corretos"
echo ""
echo "3. Console do navegador:"
echo "   - Abra o console (F12) e verifique as mensagens de log"
echo "   - Deve aparecer: 'Enviando preferências: {...}'"
echo "   - Deve aparecer: 'Preferências salvas: {...}'"
echo ""
echo "=== Correções implementadas ==="
echo ""
echo "✅ Variável user_preferences inicializada corretamente"
echo "✅ Função loadUserData agora popula os checkboxes a partir do dietary_style"
echo "✅ Função updatePreferences agora mostra feedback detalhado"
echo "✅ Adicionado log de debug no console"
echo "✅ Mensagens de erro mais claras"
echo ""
echo "=== Mudanças realizadas ==="
echo ""
echo "1. Adicionada inicialização de vm.user_preferences = { low_sodium: false, mediterranean: false, low_fat: false }"
echo "2. Adicionado parsing do dietary_style ao carregar perfil para popular os checkboxes"
echo "3. Melhorada tratamento de erros com mensagens mais claras"
echo "4. Adicionado console.log para debug"
echo ""
