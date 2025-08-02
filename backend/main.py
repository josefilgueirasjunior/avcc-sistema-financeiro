from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timedelta, date
from typing import List, Optional
import calendar
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import database, schemas, auth
from .version import get_version_info, get_version_string

# Configuração do Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Sistema Financeiro Associação")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://painel.avcccelmacedo.xyz", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Criar tabelas do banco
database.create_tables()

# Rotas de autenticação
@app.post("/api/token", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Invalidar todas as sessões ativas do usuário antes de criar uma nova
    auth.invalidate_all_user_sessions(db, user.id)
    
    # Criar nova sessão do usuário
    session_token = auth.create_user_session(db, user.id, request)
    
    # Criar token JWT que inclui o session_token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "session_token": session_token.session_token}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/register", response_model=schemas.Usuario)
def register_user(user: schemas.UsuarioCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_user = auth.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return auth.create_user(db=db, user=user)

# Rotas para Fornecedores/Doadores
@app.get("/api/fornecedores-doadores", response_model=schemas.PaginatedResponse)
def read_fornecedores_doadores(
    page: int = 1, 
    size: int = 20, 
    db: Session = Depends(database.get_db), 
    current_user: database.Usuario = Depends(auth.get_current_user)
):
    pagination = schemas.PaginationParams(page=page, size=size)
    
    total = db.query(func.count(database.FornecedorDoador.id)).scalar()
    db_items = db.query(database.FornecedorDoador).offset(pagination.skip).limit(pagination.limit).all()
    
    # Converter objetos SQLAlchemy para schemas Pydantic
    items = [schemas.FornecedorDoador.from_orm(item) for item in db_items]
    
    return schemas.PaginatedResponse.create(items, total, pagination)

@app.post("/api/fornecedores-doadores", response_model=schemas.FornecedorDoador)
def create_fornecedor_doador(
    fornecedor: schemas.FornecedorDoadorCreate, 
    db: Session = Depends(database.get_db), 
    current_user: database.Usuario = Depends(auth.get_current_user)
):
    db_fornecedor = database.FornecedorDoador(**fornecedor.dict())
    db.add(db_fornecedor)
    db.commit()
    db.refresh(db_fornecedor)
    
    # Log de auditoria removido
    
    return db_fornecedor

@app.get("/api/fornecedores-doadores/{fornecedor_id}", response_model=schemas.FornecedorDoador)
def read_fornecedor_doador(fornecedor_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_fornecedor = db.query(database.FornecedorDoador).filter(database.FornecedorDoador.id == fornecedor_id).first()
    if db_fornecedor is None:
        raise HTTPException(status_code=404, detail="Fornecedor/Doador not found")
    return db_fornecedor

@app.put("/api/fornecedores-doadores/{fornecedor_id}", response_model=schemas.FornecedorDoador)
def update_fornecedor_doador(fornecedor_id: int, fornecedor: schemas.FornecedorDoadorCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_fornecedor = db.query(database.FornecedorDoador).filter(database.FornecedorDoador.id == fornecedor_id).first()
    if db_fornecedor is None:
        raise HTTPException(status_code=404, detail="Fornecedor/Doador not found")
    
    for key, value in fornecedor.dict().items():
        setattr(db_fornecedor, key, value)
    
    db.commit()
    db.refresh(db_fornecedor)
    return db_fornecedor

@app.delete("/api/fornecedores-doadores/{fornecedor_id}")
def delete_fornecedor_doador(fornecedor_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_fornecedor = db.query(database.FornecedorDoador).filter(database.FornecedorDoador.id == fornecedor_id).first()
    if db_fornecedor is None:
        raise HTTPException(status_code=404, detail="Fornecedor/Doador not found")
    
    db.delete(db_fornecedor)
    db.commit()
    return {"message": "Fornecedor/Doador deleted successfully"}

# Rotas para Beneficiários
@app.get("/api/beneficiarios", response_model=List[schemas.Beneficiario])
def read_beneficiarios(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.Beneficiario).offset(skip).limit(limit).all()

@app.post("/api/beneficiarios", response_model=schemas.Beneficiario)
def create_beneficiario(beneficiario: schemas.BeneficiarioCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_beneficiario = database.Beneficiario(**beneficiario.dict())
    db.add(db_beneficiario)
    db.commit()
    db.refresh(db_beneficiario)
    return db_beneficiario

@app.get("/api/beneficiarios/{beneficiario_id}", response_model=schemas.Beneficiario)
def read_beneficiario(beneficiario_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_beneficiario = db.query(database.Beneficiario).filter(database.Beneficiario.id == beneficiario_id).first()
    if db_beneficiario is None:
        raise HTTPException(status_code=404, detail="Beneficiário not found")
    return db_beneficiario

@app.put("/api/beneficiarios/{beneficiario_id}", response_model=schemas.Beneficiario)
def update_beneficiario(beneficiario_id: int, beneficiario: schemas.BeneficiarioCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_beneficiario = db.query(database.Beneficiario).filter(database.Beneficiario.id == beneficiario_id).first()
    if db_beneficiario is None:
        raise HTTPException(status_code=404, detail="Beneficiário not found")
    
    for key, value in beneficiario.dict().items():
        setattr(db_beneficiario, key, value)
    
    db.commit()
    db.refresh(db_beneficiario)
    return db_beneficiario

@app.delete("/api/beneficiarios/{beneficiario_id}")
def delete_beneficiario(beneficiario_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_beneficiario = db.query(database.Beneficiario).filter(database.Beneficiario.id == beneficiario_id).first()
    if db_beneficiario is None:
        raise HTTPException(status_code=404, detail="Beneficiário not found")
    
    db.delete(db_beneficiario)
    db.commit()
    return {"message": "Beneficiário deleted successfully"}

# Rotas para Contas
@app.get("/api/contas", response_model=List[schemas.Conta])
def read_contas(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.Conta).offset(skip).limit(limit).all()

@app.post("/api/contas", response_model=schemas.Conta)
def create_conta(conta: schemas.ContaCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = database.Conta(**conta.dict())
    db.add(db_conta)
    db.commit()
    db.refresh(db_conta)
    return db_conta

@app.get("/api/contas/{conta_id}", response_model=schemas.Conta)
def read_conta(conta_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.Conta).filter(database.Conta.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta not found")
    return db_conta

@app.put("/api/contas/{conta_id}", response_model=schemas.Conta)
def update_conta(conta_id: int, conta: schemas.ContaCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.Conta).filter(database.Conta.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta not found")
    
    for key, value in conta.dict().items():
        setattr(db_conta, key, value)
    
    db.commit()
    db.refresh(db_conta)
    return db_conta

@app.delete("/api/contas/{conta_id}")
def delete_conta(conta_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.Conta).filter(database.Conta.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta not found")
    
    db.delete(db_conta)
    db.commit()
    return {"message": "Conta deleted successfully"}

# Rotas para Contas a Pagar
@app.get("/api/contas-pagar", response_model=List[schemas.ContaPagar])
def read_contas_pagar(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.ContaPagar).offset(skip).limit(limit).all()

@app.post("/api/contas-pagar", response_model=schemas.ContaPagar)
def create_conta_pagar(conta: schemas.ContaPagarCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    import uuid
    
    # Gerar ID único para o grupo de recorrência se for recorrente
    grupo_recorrencia = None
    if conta.recorrente and conta.meses_repetir and conta.meses_repetir > 1:
        grupo_recorrencia = str(uuid.uuid4())
    
    # Criar a conta principal com informações de parcela
    conta_data = conta.model_dump()
    conta_data['parcela_numero'] = 1
    conta_data['parcela_total'] = conta.meses_repetir if conta.recorrente and conta.meses_repetir else 1
    conta_data['grupo_recorrencia'] = grupo_recorrencia
    
    db_conta = database.ContaPagar(**conta_data)
    db.add(db_conta)
    db.commit()
    db.refresh(db_conta)
    
    # Se foi criada como "Pago", criar movimentação imediatamente
    if conta.status == "Pago":
        # Definir data_pagamento como hoje se não foi definida
        if not db_conta.data_pagamento:
            db_conta.data_pagamento = datetime.utcnow().date()
            
        # Buscar nome do fornecedor (sempre obrigatório)
        fornecedor = db.query(database.FornecedorDoador).filter(database.FornecedorDoador.id == conta.fornecedor_id).first()
        nome_fornecedor = fornecedor.nome_razao if fornecedor else "Fornecedor"
        
        # Se tem beneficiário, incluir no descritivo
        if conta.beneficiario_id:
            beneficiario = db.query(database.Beneficiario).filter(database.Beneficiario.id == conta.beneficiario_id).first()
            nome_beneficiario = beneficiario.nome if beneficiario else "Beneficiário"
            descricao = f"Pagamento - {nome_fornecedor} (para {nome_beneficiario})"
        else:
            descricao = f"Pagamento - {nome_fornecedor}"
        
        # Criar movimentação de saída
        movimentacao = database.MovimentacaoFinanceira(
            conta_id=conta.conta_id,
            tipo_movimentacao="SAIDA",
            valor=conta.valor,
            data_movimentacao=datetime.utcnow(),
            descricao=descricao,
            categoria=conta.categoria,
            origem_tipo="CONTA_PAGAR",
            origem_id=db_conta.id,
            usuario_id=current_user.id,
            observacao=conta.observacao
        )
        db.add(movimentacao)
        
        # Atualizar saldo da conta
        conta_obj = db.query(database.Conta).filter(database.Conta.id == conta.conta_id).first()
        if conta_obj:
            conta_obj.saldo_atual = conta_obj.saldo_atual - conta.valor
        
        db.commit()
    
    # Se for recorrente, criar as parcelas futuras (meses_repetir - 1 parcelas adicionais)
    if conta.recorrente and conta.meses_repetir and conta.meses_repetir > 1:
        for i in range(2, conta.meses_repetir + 1):  # Começar do 2 porque a primeira já foi criada
            nova_data_vencimento = conta.data_vencimento + relativedelta(months=i-1)
            nova_data_emissao = conta.data_emissao + relativedelta(months=i-1)
            
            # Criar nova conta recorrente
            nova_conta_data = conta.model_dump()
            nova_conta_data['data_vencimento'] = nova_data_vencimento
            nova_conta_data['data_emissao'] = nova_data_emissao
            nova_conta_data['data_pagamento'] = None  # Resetar data de pagamento
            nova_conta_data['status'] = 'Pendente'  # Sempre pendente para parcelas futuras
            nova_conta_data['parcela_numero'] = i
            nova_conta_data['parcela_total'] = conta.meses_repetir
            nova_conta_data['grupo_recorrencia'] = grupo_recorrencia
            
            nova_conta = database.ContaPagar(**nova_conta_data)
            db.add(nova_conta)
        
        db.commit()
    
    return db_conta

@app.get("/api/contas-pagar/{conta_id}", response_model=schemas.ContaPagar)
def read_conta_pagar(conta_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.ContaPagar).filter(database.ContaPagar.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta a Pagar not found")
    return db_conta

@app.put("/api/contas-pagar/{conta_id}", response_model=schemas.ContaPagar)
def update_conta_pagar(conta_id: int, conta: schemas.ContaPagarCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.ContaPagar).filter(database.ContaPagar.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta a Pagar not found")
    
    # Verificar se o status está mudando para "Pago"
    status_anterior = db_conta.status
    
    for key, value in conta.dict().items():
        setattr(db_conta, key, value)
    
       # Se mudou para pago e não era pago antes, criar movimentação
    if conta.status == "Pago" and status_anterior != "Pago":
        # Definir data_pagamento como hoje se não foi definida
        if not db_conta.data_pagamento:
            db_conta.data_pagamento = datetime.utcnow().date()
            
        # Buscar nome do fornecedor (sempre obrigatório)
        fornecedor = db.query(database.FornecedorDoador).filter(database.FornecedorDoador.id == conta.fornecedor_id).first()
        nome_fornecedor = fornecedor.nome_razao if fornecedor else "Fornecedor"
        
        # Se tem beneficiário, incluir no descritivo
        if conta.beneficiario_id:
            beneficiario = db.query(database.Beneficiario).filter(database.Beneficiario.id == conta.beneficiario_id).first()
            nome_beneficiario = beneficiario.nome if beneficiario else "Beneficiário"
            descricao = f"Pagamento - {nome_fornecedor} (para {nome_beneficiario})"
        else:
            descricao = f"Pagamento - {nome_fornecedor}"
        
        # Criar movimentação de saída
        movimentacao = database.MovimentacaoFinanceira(
            conta_id=conta.conta_id,
            tipo_movimentacao="SAIDA",
            valor=conta.valor,
            data_movimentacao=datetime.utcnow(),
            descricao=descricao,
            categoria=conta.categoria,
            origem_tipo="CONTA_PAGAR",
            origem_id=conta_id,
            usuario_id=current_user.id,
            observacao=conta.observacao
        )
        db.add(movimentacao)
        
        # Atualizar saldo da conta
        conta_obj = db.query(database.Conta).filter(database.Conta.id == conta.conta_id).first()
        if conta_obj:
            conta_obj.saldo_atual = conta_obj.saldo_atual - conta.valor
    
    db.commit()
    db.refresh(db_conta)
    return db_conta

@app.delete("/api/contas-pagar/{conta_id}")
def delete_conta_pagar(conta_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.ContaPagar).filter(database.ContaPagar.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta a Pagar not found")
    
    # Se a conta estava paga, remover movimentação e ajustar saldo
    if db_conta.status == "Pago":
        # Buscar movimentação relacionada
        movimentacao = db.query(database.MovimentacaoFinanceira).filter(
            database.MovimentacaoFinanceira.origem_tipo == "CONTA_PAGAR",
            database.MovimentacaoFinanceira.origem_id == conta_id
        ).first()
        
        if movimentacao:
            # Reverter saldo da conta (adicionar de volta o valor que foi subtraído)
            conta_obj = db.query(database.Conta).filter(database.Conta.id == db_conta.conta_id).first()
            if conta_obj:
                conta_obj.saldo_atual = conta_obj.saldo_atual + db_conta.valor
            
            # Remover movimentação
            db.delete(movimentacao)
    
    # Remover conta a pagar
    db.delete(db_conta)
    db.commit()
    return {"message": "Conta a Pagar deleted successfully"}

# Rotas para Contas a Receber
@app.get("/api/contas-receber", response_model=List[schemas.ContaReceber])
def read_contas_receber(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.ContaReceber).options(
        joinedload(database.ContaReceber.fornecedor_doador),
        joinedload(database.ContaReceber.conta)
    ).offset(skip).limit(limit).all()

@app.post("/api/contas-receber", response_model=schemas.ContaReceber)
def create_conta_receber(conta: schemas.ContaReceberCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    import uuid
    
    # Gerar ID único para o grupo de recorrência se for recorrente
    grupo_recorrencia = None
    if conta.recorrente and conta.meses_repetir and conta.meses_repetir > 1:
        grupo_recorrencia = str(uuid.uuid4())
    
    # Criar a conta principal com informações de parcela
    conta_data = conta.model_dump()
    conta_data['parcela_numero'] = 1
    conta_data['parcela_total'] = conta.meses_repetir if conta.recorrente and conta.meses_repetir else 1
    conta_data['grupo_recorrencia'] = grupo_recorrencia
    
    db_conta = database.ContaReceber(**conta_data)
    db.add(db_conta)
    db.commit()
    db.refresh(db_conta)
    
    # Se for recorrente, criar as parcelas futuras (meses_repetir - 1 parcelas adicionais)
    if conta.recorrente and conta.meses_repetir and conta.meses_repetir > 1:
        for i in range(2, conta.meses_repetir + 1):  # Começar do 2 porque a primeira já foi criada
            nova_data_vencimento = conta.data_vencimento + relativedelta(months=i-1)
            nova_data_emissao = conta.data_emissao + relativedelta(months=i-1)
            
            # Criar nova conta recorrente
            nova_conta_data = conta.model_dump()
            nova_conta_data['data_vencimento'] = nova_data_vencimento
            nova_conta_data['data_emissao'] = nova_data_emissao
            nova_conta_data['data_recebimento'] = None  # Resetar data de recebimento
            nova_conta_data['status'] = 'Pendente'  # Sempre pendente para parcelas futuras
            nova_conta_data['parcela_numero'] = i
            nova_conta_data['parcela_total'] = conta.meses_repetir
            nova_conta_data['grupo_recorrencia'] = grupo_recorrencia
            
            nova_conta = database.ContaReceber(**nova_conta_data)
            db.add(nova_conta)
        
        db.commit()
    
    return db_conta

@app.get("/api/contas-receber/{conta_id}", response_model=schemas.ContaReceber)
def read_conta_receber(conta_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.ContaReceber).options(
        joinedload(database.ContaReceber.fornecedor_doador),
        joinedload(database.ContaReceber.conta)
    ).filter(database.ContaReceber.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta a Receber not found")
    return db_conta

@app.put("/api/contas-receber/{conta_id}", response_model=schemas.ContaReceber)
def update_conta_receber(conta_id: int, conta: schemas.ContaReceberCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.ContaReceber).filter(database.ContaReceber.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta a Receber not found")
    
    # Verificar se o status está mudando para "Recebido"
    status_anterior = db_conta.status
    
    for key, value in conta.dict().items():
        setattr(db_conta, key, value)
    
    # Se mudou para "Recebido" e não era "Recebido" antes, criar movimentação
    if conta.status == "Recebido" and status_anterior != "Recebido":
        # Criar movimentação de entrada
        movimentacao = database.MovimentacaoFinanceira(
            conta_id=conta.conta_id,
            tipo_movimentacao="ENTRADA",
            valor=conta.valor,
            data_movimentacao=datetime.utcnow(),
            descricao=f"Recebimento - {conta.categoria}",
            categoria=conta.categoria,
            origem_tipo="CONTA_RECEBER",
            origem_id=conta_id,
            usuario_id=current_user.id,
            observacao=conta.observacao
        )
        db.add(movimentacao)
        
        # Atualizar saldo da conta
        conta_obj = db.query(database.Conta).filter(database.Conta.id == conta.conta_id).first()
        if conta_obj:
            conta_obj.saldo_atual = conta_obj.saldo_atual + conta.valor
    
    db.commit()
    db.refresh(db_conta)
    return db_conta

@app.delete("/api/contas-receber/{conta_id}")
def delete_conta_receber(conta_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.ContaReceber).filter(database.ContaReceber.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta a Receber not found")
    
    # Se a conta estava recebida, remover movimentação e ajustar saldo
    if db_conta.status == "Recebido":
        # Buscar movimentação relacionada
        movimentacao = db.query(database.MovimentacaoFinanceira).filter(
            database.MovimentacaoFinanceira.origem_tipo == "CONTA_RECEBER",
            database.MovimentacaoFinanceira.origem_id == conta_id
        ).first()
        
        if movimentacao:
            # Reverter saldo da conta (subtrair de volta o valor que foi adicionado)
            conta_obj = db.query(database.Conta).filter(database.Conta.id == db_conta.conta_id).first()
            if conta_obj:
                conta_obj.saldo_atual = conta_obj.saldo_atual - db_conta.valor
            
            # Remover movimentação
            db.delete(movimentacao)
    
    # Remover conta a receber
    db.delete(db_conta)
    db.commit()
    return {"message": "Conta a Receber deleted successfully"}

# Rotas para Doações Avulsas
@app.get("/api/doacoes-avulsas", response_model=List[schemas.DoacaoAvulsa])
def read_doacoes_avulsas(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.DoacaoAvulsa).offset(skip).limit(limit).all()

@app.post("/api/doacoes-avulsas", response_model=schemas.DoacaoAvulsa)
def create_doacao_avulsa(doacao: schemas.DoacaoAvulsaCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_doacao = database.DoacaoAvulsa(**doacao.dict())
    db.add(db_doacao)
    db.commit()
    db.refresh(db_doacao)
    
    # Se foi criada como recebida, criar movimentação
    if db_doacao.recebido:
        # Criar movimentação de entrada
        movimentacao = database.MovimentacaoFinanceira(
            conta_id=db_doacao.conta_id,
            tipo_movimentacao="ENTRADA",
            valor=db_doacao.valor,
            data_movimentacao=datetime.utcnow(),
            descricao=f"Doação - {db_doacao.nome_doador}",
            categoria="Doação",
            origem_tipo="DOACAO",
            origem_id=db_doacao.id,
            usuario_id=current_user.id,
            observacao=db_doacao.observacao
        )
        db.add(movimentacao)
        
        # Atualizar saldo da conta
        conta_obj = db.query(database.Conta).filter(database.Conta.id == db_doacao.conta_id).first()
        if conta_obj:
            conta_obj.saldo_atual = conta_obj.saldo_atual + db_doacao.valor
        
        db.commit()
    
    return db_doacao

@app.get("/api/doacoes-avulsas/{doacao_id}", response_model=schemas.DoacaoAvulsa)
def read_doacao_avulsa(doacao_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_doacao = db.query(database.DoacaoAvulsa).filter(database.DoacaoAvulsa.id == doacao_id).first()
    if db_doacao is None:
        raise HTTPException(status_code=404, detail="Doação Avulsa not found")
    return db_doacao

@app.put("/api/doacoes-avulsas/{doacao_id}", response_model=schemas.DoacaoAvulsa)
def update_doacao_avulsa(doacao_id: int, doacao: schemas.DoacaoAvulsaCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_doacao = db.query(database.DoacaoAvulsa).filter(database.DoacaoAvulsa.id == doacao_id).first()
    if db_doacao is None:
        raise HTTPException(status_code=404, detail="Doação Avulsa not found")
    
    # Verificar se está mudando para recebido
    recebido_anterior = db_doacao.recebido
    
    for key, value in doacao.dict().items():
        setattr(db_doacao, key, value)
    
    # Se mudou para recebido e não era recebido antes, criar movimentação
    if doacao.recebido and not recebido_anterior:
        # Criar movimentação de entrada
        movimentacao = database.MovimentacaoFinanceira(
            conta_id=doacao.conta_id,
            tipo_movimentacao="ENTRADA",
            valor=doacao.valor,
            data_movimentacao=datetime.utcnow(),
            descricao=f"Doação - {doacao.nome_doador}",
            categoria="Doação",
            origem_tipo="DOACAO",
            origem_id=doacao_id,
            usuario_id=current_user.id,
            observacao=doacao.observacao
        )
        db.add(movimentacao)
        
        # Atualizar saldo da conta
        conta_obj = db.query(database.Conta).filter(database.Conta.id == doacao.conta_id).first()
        if conta_obj:
            conta_obj.saldo_atual = conta_obj.saldo_atual + doacao.valor
    
    db.commit()
    db.refresh(db_doacao)
    return db_doacao

@app.delete("/api/doacoes-avulsas/{doacao_id}")
def delete_doacao_avulsa(doacao_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_doacao = db.query(database.DoacaoAvulsa).filter(database.DoacaoAvulsa.id == doacao_id).first()
    if db_doacao is None:
        raise HTTPException(status_code=404, detail="Doação Avulsa not found")
    
    # Se a doação estava recebida, remover movimentação e ajustar saldo
    if db_doacao.recebido:
        # Buscar movimentação relacionada
        movimentacao = db.query(database.MovimentacaoFinanceira).filter(
            database.MovimentacaoFinanceira.origem_tipo == "DOACAO",
            database.MovimentacaoFinanceira.origem_id == doacao_id
        ).first()
        
        if movimentacao:
            # Reverter saldo da conta (subtrair de volta o valor que foi adicionado)
            conta_obj = db.query(database.Conta).filter(database.Conta.id == db_doacao.conta_id).first()
            if conta_obj:
                conta_obj.saldo_atual = conta_obj.saldo_atual - db_doacao.valor
            
            # Remover movimentação
            db.delete(movimentacao)
    
    # Remover doação
    db.delete(db_doacao)
    db.commit()
    return {"message": "Doação Avulsa deleted successfully"}

# Rotas para Usuários
@app.get("/api/users", response_model=List[schemas.Usuario])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.Usuario).offset(skip).limit(limit).all()

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_user = db.query(database.Usuario).filter(database.Usuario.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    db.delete(db_user)
    db.commit()
    return {"message": "Usuário excluído com sucesso"}

# Rotas para Categorias de Ajuda
@app.get("/api/categorias-ajuda", response_model=List[schemas.CategoriaAjuda])
def read_categorias_ajuda(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.CategoriaAjuda).filter(database.CategoriaAjuda.ativo == True).offset(skip).limit(limit).all()

@app.post("/api/categorias-ajuda", response_model=schemas.CategoriaAjuda)
def create_categoria_ajuda(categoria: schemas.CategoriaAjudaCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_categoria = database.CategoriaAjuda(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@app.delete("/api/categorias-ajuda/{categoria_id}")
def delete_categoria_ajuda(categoria_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_categoria = db.query(database.CategoriaAjuda).filter(database.CategoriaAjuda.id == categoria_id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    db_categoria.ativo = False
    db.commit()
    return {"message": "Categoria desativada com sucesso"}

# Rotas para Categorias de Pagar
@app.get("/api/categorias-pagar", response_model=List[schemas.CategoriaPagar])
def read_categorias_pagar(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.CategoriaPagar).filter(database.CategoriaPagar.ativo == True).offset(skip).limit(limit).all()

@app.post("/api/categorias-pagar", response_model=schemas.CategoriaPagar)
def create_categoria_pagar(categoria: schemas.CategoriaPagarCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_categoria = database.CategoriaPagar(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@app.delete("/api/categorias-pagar/{categoria_id}")
def delete_categoria_pagar(categoria_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_categoria = db.query(database.CategoriaPagar).filter(database.CategoriaPagar.id == categoria_id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    db_categoria.ativo = False
    db.commit()
    return {"message": "Categoria desativada com sucesso"}

# Rotas para Tipos de Pagamento
@app.get("/api/tipos-pagamento", response_model=List[schemas.TipoPagamento])
def read_tipos_pagamento(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.TipoPagamento).filter(database.TipoPagamento.ativo == True).offset(skip).limit(limit).all()

@app.post("/api/tipos-pagamento", response_model=schemas.TipoPagamento)
def create_tipo_pagamento(tipo: schemas.TipoPagamentoCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_tipo = database.TipoPagamento(**tipo.dict())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

@app.delete("/api/tipos-pagamento/{tipo_id}")
def delete_tipo_pagamento(tipo_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_tipo = db.query(database.TipoPagamento).filter(database.TipoPagamento.id == tipo_id).first()
    if db_tipo is None:
        raise HTTPException(status_code=404, detail="Tipo de pagamento não encontrado")
    
    db_tipo.ativo = False
    db.commit()
    return {"message": "Tipo de pagamento desativado com sucesso"}

# Rotas para Categorias de Receber
@app.get("/api/categorias-receber", response_model=List[schemas.CategoriaReceber])
def read_categorias_receber(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.CategoriaReceber).filter(database.CategoriaReceber.ativo == True).offset(skip).limit(limit).all()

@app.post("/api/categorias-receber", response_model=schemas.CategoriaReceber)
def create_categoria_receber(categoria: schemas.CategoriaReceberCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_categoria = database.CategoriaReceber(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@app.delete("/api/categorias-receber/{categoria_id}")
def delete_categoria_receber(categoria_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_categoria = db.query(database.CategoriaReceber).filter(database.CategoriaReceber.id == categoria_id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    db_categoria.ativo = False
    db.commit()
    return {"message": "Categoria desativada com sucesso"}

# Rotas para Origens de Receber
@app.get("/api/origens-receber", response_model=List[schemas.OrigemReceber])
def read_origens_receber(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    return db.query(database.OrigemReceber).filter(database.OrigemReceber.ativo == True).offset(skip).limit(limit).all()

@app.post("/api/origens-receber", response_model=schemas.OrigemReceber)
def create_origem_receber(origem: schemas.OrigemReceberCreate, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_origem = database.OrigemReceber(**origem.dict())
    db.add(db_origem)
    db.commit()
    db.refresh(db_origem)
    return db_origem

@app.delete("/api/origens-receber/{origem_id}")
def delete_origem_receber(origem_id: int, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_origem = db.query(database.OrigemReceber).filter(database.OrigemReceber.id == origem_id).first()
    if db_origem is None:
        raise HTTPException(status_code=404, detail="Origem não encontrada")
    
    db_origem.ativo = False
    db.commit()
    return {"message": "Origem desativada com sucesso"}

# Rota para Dashboard
@app.get("/api/dashboard", response_model=schemas.DashboardData)
def get_dashboard_data(db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    fim_mes = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
    
    # Total a pagar hoje
    total_pagar_hoje = db.query(database.ContaPagar).filter(
        database.ContaPagar.data_vencimento == hoje,
        database.ContaPagar.status == "Pendente"
    ).with_entities(database.ContaPagar.valor).all()
    total_pagar_hoje = sum([x[0] for x in total_pagar_hoje]) if total_pagar_hoje else 0
    
    # Total a pagar no mês
    total_pagar_mes = db.query(database.ContaPagar).filter(
        database.ContaPagar.data_vencimento >= inicio_mes,
        database.ContaPagar.data_vencimento <= fim_mes,
        database.ContaPagar.status == "Pendente"
    ).with_entities(database.ContaPagar.valor).all()
    total_pagar_mes = sum([x[0] for x in total_pagar_mes]) if total_pagar_mes else 0
    
    # Total a receber hoje
    total_receber_hoje = db.query(database.ContaReceber).filter(
        database.ContaReceber.data_vencimento == hoje,
        database.ContaReceber.status == "Pendente"
    ).with_entities(database.ContaReceber.valor).all()
    total_receber_hoje = sum([x[0] for x in total_receber_hoje]) if total_receber_hoje else 0
    
    # Total a receber no mês
    total_receber_mes = db.query(database.ContaReceber).filter(
        database.ContaReceber.data_vencimento >= inicio_mes,
        database.ContaReceber.data_vencimento <= fim_mes,
        database.ContaReceber.status == "Pendente"
    ).with_entities(database.ContaReceber.valor).all()
    total_receber_mes = sum([x[0] for x in total_receber_mes]) if total_receber_mes else 0
    
    # Total de doações no mês
    total_doacoes_mes = db.query(database.DoacaoAvulsa).filter(
        database.DoacaoAvulsa.data >= inicio_mes,
        database.DoacaoAvulsa.data <= fim_mes,
        database.DoacaoAvulsa.recebido == True
    ).with_entities(database.DoacaoAvulsa.valor).all()
    total_doacoes_mes = sum([x[0] for x in total_doacoes_mes]) if total_doacoes_mes else 0
    
    # Saldos por conta (simplificado)
    contas = db.query(database.Conta).all()
    saldos_contas = []
    for conta in contas:
        saldos_contas.append({
            "nome_conta": conta.nome_conta,
            "saldo": conta.saldo_atual
        })
    
    return {
        "total_pagar_hoje": total_pagar_hoje,
        "total_pagar_mes": total_pagar_mes,
        "total_receber_hoje": total_receber_hoje,
        "total_receber_mes": total_receber_mes,
        "total_doacoes_mes": total_doacoes_mes,
        "saldos_contas": saldos_contas,
        "previsao_futura": {}
    }

# Rotas para servir o frontend
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/fornecedores-doadores", response_class=HTMLResponse)
async def fornecedores_doadores_page(request: Request):
    return templates.TemplateResponse("fornecedores-doadores.html", {"request": request})

@app.get("/beneficiarios", response_class=HTMLResponse)
async def beneficiarios_page(request: Request):
    return templates.TemplateResponse("beneficiarios.html", {"request": request})

@app.get("/contas", response_class=HTMLResponse)
async def contas_page(request: Request):
    return templates.TemplateResponse("contas.html", {"request": request})

@app.get("/contas-pagar", response_class=HTMLResponse)
async def contas_pagar_page(request: Request):
    return templates.TemplateResponse("contas-pagar.html", {"request": request})

@app.get("/contas-receber", response_class=HTMLResponse)
async def contas_receber_page(request: Request):
    return templates.TemplateResponse("contas-receber.html", {"request": request})

@app.get("/doacoes-avulsas", response_class=HTMLResponse)
async def doacoes_avulsas_page(request: Request):
    return templates.TemplateResponse("doacoes-avulsas.html", {"request": request})

@app.get("/usuarios", response_class=HTMLResponse)
async def usuarios_page(request: Request):
    return templates.TemplateResponse("usuarios.html", {"request": request})

@app.get("/categorias", response_class=HTMLResponse)
async def categorias_page(request: Request):
    return templates.TemplateResponse("categorias.html", {"request": request})

# Rota para healthcheck (para verificação de saúde do container)
@app.get("/health")
def healthcheck():
    return {"status": "ok"}

@app.get("/api/auth/check")
def check_auth(current_user: database.Usuario = Depends(auth.get_current_user)):
    """Endpoint simples para verificar se a autenticação ainda é válida"""
    return {"valid": True, "user_id": current_user.id}

@app.get("/api/version")
def get_version():
    """Endpoint para consultar informações de versão do sistema"""
    return get_version_info()

@app.get("/api/version/simple")
def get_version_simple():
    """Endpoint para consultar versão simples"""
    return {"version": get_version_string()}

# Endpoint para logs de auditoria
@app.get("/api/audit-logs", response_model=schemas.PaginatedResponse)
def get_audit_logs(
    page: int = 1,
    size: int = 20,
    tabela: Optional[str] = None,
    acao: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: database.Usuario = Depends(auth.get_current_user)
):
    """Consultar logs de auditoria (apenas para administradores)"""
    pagination = schemas.PaginationParams(page=page, size=size)
    
    query = db.query(database.AuditLog)
    
    if tabela:
        query = query.filter(database.AuditLog.tabela == tabela)
    if acao:
        query = query.filter(database.AuditLog.acao == acao)
    
    total = query.count()
    db_items = query.order_by(database.AuditLog.timestamp.desc()).offset(pagination.skip).limit(pagination.limit).all()
    
    # Converter objetos SQLAlchemy para schemas Pydantic
    items = [schemas.AuditLog.from_orm(item) for item in db_items]
    
    return schemas.PaginatedResponse.create(items, total, pagination)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Endpoint para resetar saldos das contas (remover todas as movimentações)
@app.post("/api/contas/reset-saldos")
def reset_saldos_contas(db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    """
    Remove todas as movimentações financeiras e zera completamente os saldos das contas
    """
    try:
        # Remover todas as movimentações
        movimentacoes_removidas = db.query(database.MovimentacaoFinanceira).count()
        db.query(database.MovimentacaoFinanceira).delete()
        
        # Zerar completamente os saldos de todas as contas (inicial e atual)
        contas = db.query(database.Conta).all()
        for conta in contas:
            conta.saldo_inicial = 0.0
            conta.saldo_atual = 0.0
        
        db.commit()
        
        return {
            "message": "Saldos resetados completamente para zero", 
            "contas_atualizadas": len(contas),
            "movimentacoes_removidas": movimentacoes_removidas
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao resetar saldos: {str(e)}")


# Rotas para adicionar e retirar saldo das contas
@app.post("/api/contas/{conta_id}/adicionar_saldo")
def adicionar_saldo(conta_id: int, request: schemas.SaldoRequest, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.Conta).filter(database.Conta.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta not found")
    
    # Atualizar saldo atual
    if db_conta.saldo_atual is None:
        db_conta.saldo_atual = 0
    db_conta.saldo_atual += request.valor
    
    # Criar movimentação
    movimentacao = database.MovimentacaoConta(
        conta_id=conta_id,
        tipo="Entrada",
        valor=request.valor,
        data=date.today(),
        observacao=request.observacao or f"Adição de saldo - {request.valor}"
    )
    db.add(movimentacao)
    
    db.commit()
    db.refresh(db_conta)
    
    return {"message": "Saldo adicionado com sucesso", "novo_saldo": db_conta.saldo_atual}

@app.post("/api/contas/{conta_id}/retirar_saldo")
def retirar_saldo(conta_id: int, request: schemas.SaldoRequest, db: Session = Depends(database.get_db), current_user: database.Usuario = Depends(auth.get_current_user)):
    db_conta = db.query(database.Conta).filter(database.Conta.id == conta_id).first()
    if db_conta is None:
        raise HTTPException(status_code=404, detail="Conta not found")
    
    # Verificar se há saldo suficiente
    if db_conta.saldo_atual is None:
        db_conta.saldo_atual = 0
    
    if db_conta.saldo_atual < request.valor:
        raise HTTPException(
            status_code=400, 
            detail=f"Saldo insuficiente. Saldo atual: R$ {db_conta.saldo_atual:.2f}, Valor solicitado: R$ {request.valor:.2f}"
        )
    
    # Atualizar saldo atual
    db_conta.saldo_atual -= request.valor
    
    # Criar movimentação
    movimentacao = database.MovimentacaoConta(
        conta_id=conta_id,
        tipo="Saída",
        valor=request.valor,
        data=date.today(),
        observacao=request.observacao or f"Retirada de saldo - {request.valor}"
    )
    db.add(movimentacao)
    
    db.commit()
    db.refresh(db_conta)
    
    return {"message": "Saldo retirado com sucesso", "novo_saldo": db_conta.saldo_atual}

