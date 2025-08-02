from datetime import datetime

# Informações de versão do sistema
VERSION = "1.5.1"
RELEASE_DATE = "2025-01-28"
BUILD_NUMBER = "20250128005"
ENVIRONMENT = "development"  # development, staging, production

# Changelog das versões
CHANGELOG = {
    "1.5.1": {
        "date": "2025-01-28",
        "features": [
            "Melhorias de responsividade em todas as tabelas do sistema",
            "Correção de sobreposição de cabeçalhos em dispositivos móveis",
            "Botões de ação organizados lado a lado em modo responsivo",
            "Cabeçalhos de tabela otimizados: 'Responsável' e 'Ven/Valor'",
            "Layout de botões reorganizado em contas a receber",
            "Scroll horizontal implementado em doações avulsas para telas pequenas",
            "Larguras de colunas ajustadas para melhor distribuição do espaço",
            "Consistência visual entre beneficiários, contas a pagar e doações avulsas"
        ],
        "fixes": [
            "Corrigido corte de botões em dispositivos móveis",
            "Resolvido problema de cabeçalhos sobrepostos em tablets",
            "Ajustada largura da coluna de ações para evitar truncamento"
        ]
    },
    "1.5.0": {
        "date": "2025-01-28",
        "features": [
            "Filtro de busca por WhatsApp implementado em beneficiários",
            "Campo de filtro de beneficiários em contas a pagar convertido para busca por texto",
            "Layout otimizado dos campos de filtro em contas a pagar e receber",
            "Versão do sistema movida para sidebar (parte inferior)",
            "Busca inteligente de WhatsApp com remoção automática de formatação",
            "Redistribuição de espaço nos filtros para melhor usabilidade"
        ],
        "fixes": [
            "Filtro de WhatsApp agora funciona com números sem formatação",
            "Remoção do modal de seleção de beneficiários em contas a pagar",
            "Campo de fornecedor ampliado para melhor digitação",
            "Campos de status e período redimensionados proporcionalmente",
            "Versão do sistema posicionada discretamente no sidebar"
        ]
    },
    "1.4.0": {
        "date": "2025-01-28",
        "features": [
            "Sistema de validação de senhas robusto implementado",
            "Paginação responsiva inteligente em todas as páginas",
            "Melhorias significativas na responsividade mobile",
            "Script de população de dados fake para testes",
            "Otimização de layout de tabelas e colunas",
            "Sistema de truncamento inteligente de texto",
            "Navegação adaptativa com ellipses em paginação"
        ],
        "fixes": [
            "Ajustes de largura de colunas em tabelas",
            "Correção de cores em elementos small",
            "Melhorias na experiência mobile",
            "Otimização de espaçamento e layout responsivo"
        ]
    },
    "1.3.0": {
        "date": "2025-01-28",
        "features": [
            "Sistema de sessão única implementado",
            "Controle rigoroso de autenticação",
            "Invalidação automática de sessões múltiplas",
            "Endpoint dedicado para verificação de sessão",
            "Verificação periódica de sessão no frontend"
        ],
        "fixes": [
            "Problema de múltiplos logins simultâneos resolvido",
            "Detecção automática de sessões invalidadas",
            "Arquitetura de autenticação robusta implementada"
        ]
    },
    "1.2.0": {
        "date": "2025-01-28",
        "features": [
            "Rate limiting implementado",
            "Paginação melhorada",
            "Índices de banco para performance",
            "Correções de serialização"
        ],
        "fixes": [
            "Erro de serialização do Pydantic corrigido",
            "Problema de autenticação JWT resolvido",
            "Compatibilidade com estrutura paginada"
        ]
    },
    "1.1.0": {
        "date": "2025-01-27",
        "features": [
            "Sistema de autenticação JWT",
            "CRUD completo para todas entidades",
            "Dashboard financeiro",
            "Gestão de contas e movimentações"
        ],
        "fixes": [
            "Validações de entrada implementadas",
            "Correções de CORS"
        ]
    },
    "1.0.0": {
        "date": "2025-01-26",
        "features": [
            "Versão inicial do sistema",
            "Estrutura básica do banco de dados",
            "Interface web responsiva"
        ],
        "fixes": []
    }
}

def get_version_info():
    """Retorna informações completas da versão"""
    return {
        "version": VERSION,
        "release_date": RELEASE_DATE,
        "build_number": BUILD_NUMBER,
        "environment": ENVIRONMENT,
        "current_time": datetime.now().isoformat(),
        "changelog": CHANGELOG.get(VERSION, {})
    }

def get_version_string():
    """Retorna string simples da versão"""
    return f"v{VERSION} ({BUILD_NUMBER})"