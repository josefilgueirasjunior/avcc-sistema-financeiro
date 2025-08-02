#!/usr/bin/env python3
"""
Script para visualizar estrutura das tabelas do banco de dados
"""

import sqlite3
import os
from datetime import datetime

def conectar_banco():
    """Conecta ao banco de dados"""
    db_path = "./financeiro.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

def listar_tabelas(conn):
    """Lista todas as tabelas do banco"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tabelas = cursor.fetchall()
        return [tabela[0] for tabela in tabelas]
    except sqlite3.Error as e:
        print(f"❌ Erro ao listar tabelas: {e}")
        return []

def mostrar_estrutura_tabela(conn, nome_tabela):
    """Mostra a estrutura de uma tabela específica"""
    try:
        cursor = conn.cursor()
        
        # Obter informações das colunas
        cursor.execute(f"PRAGMA table_info({nome_tabela})")
        colunas = cursor.fetchall()
        
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
        total_registros = cursor.fetchone()[0]
        
        print(f"\n📊 TABELA: {nome_tabela}")
        print(f"📋 Total de registros: {total_registros}")
        print("─" * 60)
        print(f"{'Coluna':<25} {'Tipo':<15} {'Null':<8} {'Chave':<8}")
        print("─" * 60)
        
        for coluna in colunas:
            cid, nome, tipo, notnull, default, pk = coluna
            null_str = "NÃO" if notnull else "SIM"
            pk_str = "PK" if pk else ""
            print(f"{nome:<25} {tipo:<15} {null_str:<8} {pk_str:<8}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao mostrar estrutura da tabela {nome_tabela}: {e}")
        return False

def mostrar_dados_exemplo(conn, nome_tabela, limite=3):
    """Mostra alguns registros de exemplo de uma tabela"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {nome_tabela} LIMIT {limite}")
        registros = cursor.fetchall()
        
        if registros:
            print(f"\n📝 Exemplos de dados (primeiros {len(registros)} registros):")
            for i, registro in enumerate(registros, 1):
                print(f"   {i}. {registro}")
        else:
            print("\n📝 Nenhum dado encontrado na tabela.")
            
    except sqlite3.Error as e:
        print(f"❌ Erro ao mostrar dados de exemplo: {e}")

def main():
    """Função principal"""
    print("🔍 VISUALIZADOR DE TABELAS DO BANCO DE DADOS")
    print("=" * 50)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Conectar ao banco
    conn = conectar_banco()
    if not conn:
        return False
    
    try:
        # Listar todas as tabelas
        tabelas = listar_tabelas(conn)
        
        if not tabelas:
            print("❌ Nenhuma tabela encontrada no banco de dados.")
            return False
        
        print(f"📋 TABELAS ENCONTRADAS ({len(tabelas)}):")
        for i, tabela in enumerate(tabelas, 1):
            print(f"   {i}. {tabela}")
        
        print("\n" + "=" * 50)
        
        # Mostrar estrutura de cada tabela
        for tabela in tabelas:
            mostrar_estrutura_tabela(conn, tabela)
            
            # Mostrar dados de exemplo apenas para tabelas principais
            if tabela in ['usuarios', 'fornecedores_doadores', 'beneficiarios', 'contas']:
                mostrar_dados_exemplo(conn, tabela)
        
        print("\n" + "=" * 50)
        print("✅ Visualização concluída!")
        
        return True
        
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        exit(1)