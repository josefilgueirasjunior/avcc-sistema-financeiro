# Sistema Financeiro AVCC Coronel Macedo

Sistema de controle financeiro desenvolvido em FastAPI para gestão de associações.

## Funcionalidades

- Dashboard com transparência financeira
- Gestão de fornecedores/doadores
- Controle de beneficiários
- Contas a pagar e receber
- Doações avulsas
- Gestão de usuários e categorias
- Relatórios por categoria e beneficiário

## Instalação com Docker

### Opção 1: Docker Compose (Recomendado)

```bash
# 1. Extrair o arquivo
tar -xzf sistema-financeiro-completo.tar.gz
cd sistema-financeiro

# 2. Executar com Docker Compose
docker-compose up -d

# 3. Acessar o sistema
# http://localhost:8080
```

### Opção 2: Docker Manual

```bash
# 1. Construir a imagem
docker build -t sistema-financeiro .

# 2. Executar o container
docker run -d -p 8000:8000 --name sistema-financeiro sistema-financeiro

# 3. Acessar o sistema
# http://localhost:8080
```

## Credenciais Padrão

- **Usuário:** admin
- **Senha:** admin123

## Estrutura do Projeto

```
sistema-financeiro/
├── backend/           # Código do backend FastAPI
├── templates/         # Templates HTML
├── static/           # Arquivos estáticos (CSS, JS, imagens)
├── requirements.txt  # Dependências Python
├── Dockerfile       # Configuração Docker
├── docker-compose.yml # Configuração Docker Compose
├── main.py          # Arquivo principal
├── create_admin_user.py # Script para criar usuário admin
├── init_db.py       # Script de inicialização do banco
└── financeiro.db    # Banco de dados SQLite
```

## Configuração

O sistema usa SQLite como banco de dados e já vem com dados de exemplo.

### Criar Novo Usuário Admin

```bash
# Dentro do container
docker exec -it sistema-financeiro python create_admin_user.py
```

### Reinicializar Banco de Dados

```bash
# Dentro do container
docker exec -it sistema-financeiro python init_db.py
```

## Desenvolvimento

Para desenvolvimento local:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar o servidor
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Acessar
# http://localhost:8080
```

## Tecnologias Utilizadas

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Autenticação:** JWT
- **Containerização:** Docker

## Suporte

Sistema desenvolvido para a Associação de Voluntários no Combate ao Câncer de Coronel Macedo.

Para suporte técnico, consulte a documentação ou entre em contato com o desenvolvedor.

