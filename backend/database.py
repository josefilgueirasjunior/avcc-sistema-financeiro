from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, ForeignKey, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, date
from typing import Generator
import sqlite3
import os
import json

# Configuração do banco de dados SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./financeiro.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Modelos de dados
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class FornecedorDoador(Base):
    __tablename__ = "fornecedor_doador"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String)  # Fornecedor ou Doador
    nome_razao = Column(String)
    cpf_cnpj = Column(String)
    cep = Column(String)
    rua = Column(String)
    numero = Column(String)
    bairro = Column(String)
    cidade = Column(String)
    estado = Column(String)
    telefone = Column(String)
    whatsapp = Column(String)
    observacao = Column(String)

class Beneficiario(Base):
    __tablename__ = "beneficiarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    cpf = Column(String)
    whatsapp = Column(String)
    cep = Column(String)
    rua = Column(String)
    numero = Column(String)
    bairro = Column(String)
    cidade = Column(String)
    estado = Column(String)
    nome_responsavel = Column(String)
    whatsapp_responsavel = Column(String)
    observacao = Column(String)

class Conta(Base):
    __tablename__ = "contas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome_conta = Column(String)
    tipo = Column(String)  # Caixa ou Banco
    observacao = Column(String)
    saldo_atual = Column(Float, default=0.0)
    saldo_inicial = Column(Float, default=0.0)
    data_saldo_inicial = Column(Date, default=date.today)

class MovimentacaoFinanceira(Base):
    __tablename__ = "movimentacoes_financeiras"
    
    id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    tipo_movimentacao = Column(String, nullable=False)  # ENTRADA ou SAIDA
    valor = Column(Float, nullable=False)
    data_movimentacao = Column(DateTime, nullable=False, default=datetime.utcnow)
    descricao = Column(String, nullable=False)
    categoria = Column(String)
    origem_tipo = Column(String)  # CONTA_PAGAR, CONTA_RECEBER, DOACAO, AJUSTE
    origem_id = Column(Integer)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    observacao = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    conta = relationship("Conta")
    usuario = relationship("Usuario")

class ContaPagar(Base):
    __tablename__ = "contas_pagar"
    
    id = Column(Integer, primary_key=True, index=True)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor_doador.id"), nullable=False)  # Sempre obrigatório
    beneficiario_id = Column(Integer, ForeignKey("beneficiarios.id"), nullable=True)  # Opcional
    status = Column(String)  # Pendente ou Pago
    categoria = Column(String)  # Categoria unificada
    conta_id = Column(Integer, ForeignKey("contas.id"))
    data_emissao = Column(Date)
    data_vencimento = Column(Date)
    data_pagamento = Column(Date)
    valor = Column(Float)
    tipo_pagamento = Column(String)
    observacao = Column(String)
    recorrente = Column(Boolean, default=False)
    meses_repetir = Column(Integer)
    parcela_numero = Column(Integer, default=1)  # Número da parcela atual
    parcela_total = Column(Integer, default=1)   # Total de parcelas
    grupo_recorrencia = Column(String)           # ID para agrupar parcelas da mesma recorrência
    
    fornecedor = relationship("FornecedorDoador")
    beneficiario = relationship("Beneficiario")
    conta = relationship("Conta")

class ContaReceber(Base):
    __tablename__ = "contas_receber"
    
    id = Column(Integer, primary_key=True, index=True)
    origem = Column(String)  # Fornecedor ou Outro
    fornecedor_doador_id = Column(Integer, ForeignKey("fornecedor_doador.id"), nullable=False)
    status = Column(String)  # Pendente ou Recebido
    categoria = Column(String)
    conta_id = Column(Integer, ForeignKey("contas.id"))
    data_emissao = Column(Date)
    data_vencimento = Column(Date)
    data_recebimento = Column(Date)
    valor = Column(Float)
    observacao = Column(String)
    recorrente = Column(Boolean, default=False)
    meses_repetir = Column(Integer)
    parcela_numero = Column(Integer, default=1)  # Número da parcela atual
    parcela_total = Column(Integer, default=1)   # Total de parcelas
    grupo_recorrencia = Column(String)           # ID para agrupar parcelas da mesma recorrência
    
    fornecedor_doador = relationship("FornecedorDoador")
    conta = relationship("Conta")

class DoacaoAvulsa(Base):
    __tablename__ = "doacoes_avulsas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome_doador = Column(String, nullable=False)
    whatsapp = Column(String)
    valor = Column(Float, nullable=False)
    conta_id = Column(Integer, ForeignKey("contas.id"))
    data = Column(Date, nullable=False)
    observacao = Column(Text)
    recebido = Column(Boolean, default=False)
    
    conta = relationship("Conta", back_populates="doacoes_avulsas")

# Modelos para categorias dinâmicas
class CategoriaAjuda(Base):
    __tablename__ = "categorias_ajuda"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CategoriaPagar(Base):
    __tablename__ = "categorias_pagar"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TipoPagamento(Base):
    __tablename__ = "tipos_pagamento"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CategoriaReceber(Base):
    __tablename__ = "categorias_receber"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OrigemReceber(Base):
    __tablename__ = "origens_receber"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Atualizar relacionamentos
Conta.doacoes_avulsas = relationship("DoacaoAvulsa", back_populates="conta")

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class MovimentacaoConta(Base):
    __tablename__ = "movimentacoes_conta"
    
    id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    tipo = Column(String, nullable=False)  # Entrada ou Saída
    valor = Column(Float, nullable=False)
    data = Column(Date, nullable=False, default=date.today)
    observacao = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    conta = relationship("Conta")



class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    session_token = Column(String, unique=True, nullable=False, index=True)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String)
    device_info = Column(Text)  # JSON com informações do dispositivo
    location = Column(String)  # Localização aproximada
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario")

# Índices para melhorar performance
Index('idx_conta_pagar_vencimento', ContaPagar.data_vencimento)
Index('idx_conta_pagar_status', ContaPagar.status)
Index('idx_conta_receber_vencimento', ContaReceber.data_vencimento)
Index('idx_conta_receber_status', ContaReceber.status)
Index('idx_movimentacao_financeira_data', MovimentacaoFinanceira.data_movimentacao)
Index('idx_movimentacao_financeira_conta', MovimentacaoFinanceira.conta_id)
Index('idx_movimentacao_conta_data', MovimentacaoConta.data)
Index('idx_movimentacao_conta_conta', MovimentacaoConta.conta_id)

Index('idx_user_session_usuario', UserSession.usuario_id)
Index('idx_user_session_token', UserSession.session_token)
Index('idx_user_session_active', UserSession.is_active)
Index('idx_user_session_expires', UserSession.expires_at)

