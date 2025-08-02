#!/usr/bin/env python3
"""
Script para inicializar o banco de dados com dados de exemplo
"""

from backend.database import engine, SessionLocal, create_tables
from backend import database, auth, schemas
from datetime import date, datetime

def init_database():
    """Inicializar banco de dados com dados de exemplo"""
    
    # Criar tabelas
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Verificar se já existem dados
        existing_user = db.query(database.Usuario).first()
        if existing_user:
            print("Banco de dados já inicializado.")
            return
        
        # Criar usuário administrador padrão
        admin_user = schemas.UsuarioCreate(
            username="admin",
            email="admin@associacao.org",
            password="admin123"
        )
        
        db_user = auth.create_user(db, admin_user)
        print(f"Usuário administrador criado: {db_user.username}")
        
        # Criar contas de exemplo
        conta_caixa = database.Conta(
            nome_conta="Caixa Principal",
            tipo="Caixa",
            observacao="Conta principal da associação"
        )
        db.add(conta_caixa)
        
        conta_banco = database.Conta(
            nome_conta="Banco do Brasil - CC 12345-6",
            tipo="Banco",
            observacao="Conta corrente principal"
        )
        db.add(conta_banco)
        
        db.commit()
        db.refresh(conta_caixa)
        db.refresh(conta_banco)
        
        # Criar fornecedores/doadores de exemplo
        fornecedor1 = database.FornecedorDoador(
            tipo="Fornecedor",
            nome_razao="Supermercado Exemplo Ltda",
            cpf_cnpj="12.345.678/0001-90",
            cidade="São Paulo",
            estado="SP",
            telefone="(11) 1234-5678",
            observacao="Fornecedor de alimentos"
        )
        db.add(fornecedor1)
        
        doador1 = database.FornecedorDoador(
            tipo="Doador",
            nome_razao="João Silva",
            cpf_cnpj="123.456.789-00",
            cidade="São Paulo",
            estado="SP",
            whatsapp="(11) 98765-4321",
            observacao="Doador regular"
        )
        db.add(doador1)
        
        db.commit()
        db.refresh(fornecedor1)
        db.refresh(doador1)
        
        # Criar beneficiários de exemplo
        beneficiario1 = database.Beneficiario(
            nome="Maria Santos",
            cpf="987.654.321-00",
            cidade="São Paulo",
            estado="SP",
            nome_responsavel="Maria Santos",
            whatsapp_responsavel="(11) 91234-5678",
            categoria_ajuda="Cesta Básica",
            observacao="Família de 4 pessoas"
        )
        db.add(beneficiario1)
        
        db.commit()
        
        # Criar contas a pagar de exemplo
        conta_pagar1 = database.ContaPagar(
            fornecedor_id=fornecedor1.id,
            status="Pendente",
            categoria="Alimentação",
            conta_id=conta_banco.id,
            data_emissao=date.today(),
            data_vencimento=date(2025, 7, 20),
            valor=500.00,
            tipo_pagamento="Boleto",
            observacao="Compra de alimentos para cestas básicas"
        )
        db.add(conta_pagar1)
        
        # Criar contas a receber de exemplo
        conta_receber1 = database.ContaReceber(
            origem="Outro",
            nome_razao="Prefeitura Municipal",
            status="Pendente",
            categoria="Subvenção",
            conta_id=conta_banco.id,
            data_emissao=date.today(),
            data_vencimento=date(2025, 7, 25),
            valor=2000.00,
            observacao="Subvenção mensal da prefeitura"
        )
        db.add(conta_receber1)
        
        # Criar doações avulsas de exemplo
        doacao1 = database.DoacaoAvulsa(
            nome_doador="Ana Costa",
            whatsapp="(11) 99999-8888",
            valor=100.00,
            conta_id=conta_caixa.id,
            data=date.today(),
            observacao="Doação em dinheiro",
            recebido=True
        )
        db.add(doacao1)
        
        db.commit()
        
        print("Dados de exemplo criados com sucesso!")
        print("\nCredenciais de acesso:")
        print("Usuário: admin")
        print("Senha: admin123")
        
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()

