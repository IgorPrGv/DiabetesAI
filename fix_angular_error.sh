#!/bin/bash

echo "=========================================="
echo "CORREÇÃO: Erro de Sintaxe Angular"
echo "=========================================="
echo ""

echo "✅ Arquivo home.html corrigido:"
echo "   - Removido código duplicado no final"
echo "   - Removidas linhas vazias após </html>"
echo "   - Total de linhas: $(wc -l < frontend/home.html)"
echo ""

echo "Para resolver o erro no navegador:"
echo ""
echo "1. LIMPAR CACHE DO NAVEGADOR:"
echo "   - Pressione Ctrl+Shift+Delete"
echo "   - Ou vá em Configurações → Privacidade → Limpar dados"
echo "   - Marque 'Cache' e 'Cookies'"
echo "   - Limpe apenas da última hora"
echo ""
echo "2. RECARREGAR A PÁGINA:"
echo "   - Pressione Ctrl+Shift+R (hard reload)"
echo "   - Ou Ctrl+F5"
echo ""
echo "3. VERIFICAR CONSOLE:"
echo "   - Pressione F12"
echo "   - Vá para aba Console"
echo "   - Deve aparecer:"
echo "     ✅ AngularJS carregado, versão: 1.8.2"
echo "     ✅ Módulo diabetesApp criado"
echo "     ✅ MainCtrl inicializado"
echo ""
echo "4. SE O ERRO PERSISTIR:"
echo "   - Feche TODAS as abas do navegador"
echo "   - Abra uma nova janela"
echo "   - Acesse http://localhost:8000/home.html"
echo ""

echo "=========================================="
echo "TESTE RÁPIDO"
echo "=========================================="
echo ""

# Verificar se o servidor está rodando
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Servidor está rodando"
    echo ""
    echo "Acessehttp://localhost:8000/home.html no navegador"
    echo "e pressione Ctrl+Shift+R para recarregar"
else
    echo "❌ Servidor não está rodando"
    echo ""
    echo "Inicie o servidor com:"
    echo "  ./scripts/start_server.sh"
fi

echo ""
echo "=========================================="
