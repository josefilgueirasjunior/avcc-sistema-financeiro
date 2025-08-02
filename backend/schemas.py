from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

# Schemas para Usuario
class UsuarioBase(BaseModel):
    username: str

class UsuarioCreate(UsuarioBase):
    password: str

class Usuario(UsuarioBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schemas para FornecedorDoador
class FornecedorDoadorBase(BaseModel):
    tipo: str
    nome_razao: str
    cpf_cnpj: Optional[str] = None
    cep: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    observacao: Optional[str] = None

class FornecedorDoadorCreate(FornecedorDoadorBase):
    pass

class FornecedorDoador(FornecedorDoadorBase):
    id: int
    
    class Config:
        from_attributes = True

# Schemas para Beneficiario
class BeneficiarioBase(BaseModel):
    nome: str
    cpf: Optional[str] = None
    whatsapp: Optional[str] = None
    cep: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    nome_responsavel: Optional[str] = None
    whatsapp_responsavel: Optional[str] = None
    observacao: Optional[str] = None

class BeneficiarioCreate(BeneficiarioBase):
    pass

class Beneficiario(BeneficiarioBase):
    id: int
    
    class Config:
        from_attributes = True

# Schemas para Conta
class ContaBase(BaseModel):
    nome_conta: str
    tipo: str
    observacao: Optional[str] = None
    saldo_inicial: Optional[float] = 0.0

class ContaCreate(ContaBase):
    pass

class Conta(ContaBase):
    id: int
    saldo_atual: float
    data_saldo_inicial: Optional[date] = None
    
    class Config:
        from_attributes = True

# Schemas para ContaPagar
class ContaPagarBase(BaseModel):
    fornecedor_id: int  # Sempre obrigatório
    beneficiario_id: Optional[int] = None  # Opcional
    status: str
    categoria: str  # Categoria unificada
    conta_id: int
    data_emissao: date
    data_vencimento: date
    data_pagamento: Optional[date] = None
    valor: float
    tipo_pagamento: Optional[str] = None
    observacao: Optional[str] = None
    recorrente: bool = False
    meses_repetir: Optional[int] = None
    parcela_numero: int = 1
    parcela_total: int = 1
    grupo_recorrencia: Optional[str] = None

class ContaPagarCreate(ContaPagarBase):
    pass

class ContaPagar(ContaPagarBase):
    id: int
    
    class Config:
        from_attributes = True

# Schemas para ContaReceber
class ContaReceberBase(BaseModel):
    origem: str
    fornecedor_doador_id: int
    status: str
    categoria: str
    conta_id: int
    data_emissao: date
    data_vencimento: date
    data_recebimento: Optional[date] = None
    valor: float
    observacao: Optional[str] = None
    recorrente: bool = False
    meses_repetir: Optional[int] = None
    parcela_numero: int = 1
    parcela_total: int = 1
    grupo_recorrencia: Optional[str] = None

class ContaReceberCreate(ContaReceberBase):
    pass

class ContaReceber(ContaReceberBase):
    id: int
    fornecedor_doador: Optional[FornecedorDoador] = None
    
    class Config:
        from_attributes = True

# Schemas para DoacaoAvulsa
class DoacaoAvulsaBase(BaseModel):
    nome_doador: str
    whatsapp: Optional[str] = None
    valor: float
    conta_id: int
    data: date
    observacao: Optional[str] = None
    recebido: bool = False

class DoacaoAvulsaCreate(DoacaoAvulsaBase):
    pass

class DoacaoAvulsa(DoacaoAvulsaBase):
    id: int
    
    class Config:
        from_attributes = True

# Schema para Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Schema para Dashboard
class DashboardData(BaseModel):
    total_pagar_hoje: float
    total_pagar_mes: float
    total_receber_hoje: float
    total_receber_mes: float
    total_doacoes_mes: float
    saldos_contas: list
    previsao_futura: dict

# Schemas para categorias dinâmicas
class CategoriaAjudaBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class CategoriaAjudaCreate(CategoriaAjudaBase):
    pass

class CategoriaAjuda(CategoriaAjudaBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CategoriaPagarBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class CategoriaPagarCreate(CategoriaPagarBase):
    pass

class CategoriaPagar(CategoriaPagarBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TipoPagamentoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class TipoPagamentoCreate(TipoPagamentoBase):
    pass

class TipoPagamento(TipoPagamentoBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CategoriaReceberBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class CategoriaReceberCreate(CategoriaReceberBase):
    pass

class CategoriaReceber(CategoriaReceberBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrigemReceberBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class OrigemReceberCreate(OrigemReceberBase):
    pass

class OrigemReceber(OrigemReceberBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Schemas para MovimentacaoFinanceira
class MovimentacaoFinanceiraBase(BaseModel):
    conta_id: int
    tipo_movimentacao: str  # ENTRADA ou SAIDA
    valor: float
    data_movimentacao: datetime
    descricao: str
    categoria: Optional[str] = None
    origem_tipo: Optional[str] = None
    origem_id: Optional[int] = None
    observacao: Optional[str] = None

class MovimentacaoFinanceiraCreate(MovimentacaoFinanceiraBase):
    usuario_id: int

class MovimentacaoFinanceira(MovimentacaoFinanceiraBase):
    id: int
    usuario_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Schema para operações de saldo
class SaldoRequest(BaseModel):
    valor: float
    observacao: Optional[str] = None



# Schema para paginação melhorada
class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20
    
    def __init__(self, page: int = 1, size: int = 20):
        super().__init__(page=max(1, page), size=min(max(1, size), 100))
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: list, total: int, pagination: PaginationParams):
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )


# Schemas para sessões de usuário
class UserSessionBase(BaseModel):
    session_token: str
    ip_address: str
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    location: Optional[str] = None
    is_active: bool = True
    expires_at: datetime

class UserSessionCreate(UserSessionBase):
    usuario_id: int

class UserSession(UserSessionBase):
    id: int
    usuario_id: int
    last_activity: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

