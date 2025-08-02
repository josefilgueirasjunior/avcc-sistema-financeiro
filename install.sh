#!/bin/bash

echo "=== Sistema Financeiro AVCC - Instalação Docker ==="
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

echo "✅ Docker e Docker Compose encontrados"
echo ""

# Parar containers existentes (se houver)
echo "🔄 Parando containers existentes..."
docker-compose down 2>/dev/null || true

# Construir e iniciar o sistema
echo "🏗️  Construindo e iniciando o sistema..."
docker-compose up -d --build

# Aguardar o sistema inicializar
echo "⏳ Aguardando sistema inicializar..."
sleep 10

# Verificar se está rodando
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "🎉 Sistema instalado com sucesso!"
    echo ""
    echo "📋 Informações de acesso:"
    echo "   URL: http://localhost:8080"
    echo "   Usuário: admin"
    echo "   Senha: admin123"
    echo ""
    echo "🔧 Comandos úteis:"
    echo "   Parar: docker-compose down"
    echo "   Iniciar: docker-compose up -d"
    echo "   Logs: docker-compose logs -f"
    echo "   Reiniciar: docker-compose restart"
    echo ""
else
    echo "❌ Erro na instalação. Verifique os logs:"
    echo "   docker-compose logs"
fi

