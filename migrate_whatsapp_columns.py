#!/usr/bin/env python3
"""
Script de migração para adicionar colunas WhatsApp
Versão 1.5.0 - Estruturas necessárias para funcionalidades implementadas
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

def verificar_coluna_existe(conn, tabela, coluna):
    """Verifica se uma coluna existe em uma tabela"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({tabela})")
        colunas = cursor.fetchall()
        colunas_existentes = [col[1] for col in colunas]
        return coluna in colunas_existentes
    except sqlite3.Error:
        return False

def adicionar_coluna(conn, tabela, coluna, tipo):
    """Adiciona uma coluna a uma tabela"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar coluna {coluna} em {tabela}: {e}")
        return False

def verificar_tabela_existe(conn, tabela):
    """Verifica se uma tabela existe"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabela,))
        return cursor.fetchone() is not None
    except sqlite3.Error:
        return False

def executar_migracoes():
    """Executa todas as migrações necessárias"""
    
    # Definir as colunas que precisam ser adicionadas
    migracoes = [
        {
            'tabela': 'fornecedor_doador',
            'colunas': [
                ('whatsapp', 'TEXT')
            ]
        },
        {
            'tabela': 'beneficiarios', 
            'colunas': [
                ('whatsapp', 'TEXT'),
                ('whatsapp_responsavel', 'TEXT')
            ]
        },
        {
            'tabela': 'doacoes_avulsas',
            'colunas': [
                ('whatsapp', 'TEXT')
            ]
        },
        {
            'tabela': 'usuarios',
            'colunas': [
                ('nome_completo', 'TEXT')
            ]
        }
    ]
    
    conn = conectar_banco()
    if not conn:
        return False
    
    try:
        mudancas_realizadas = []
        
        print("🔍 VERIFICANDO ESTRUTURAS NECESSÁRIAS...")
        print("=" * 50)
        
        for migracao in migracoes:
            tabela = migracao['tabela']
            colunas = migracao['colunas']
            
            print(f"\n📊 Verificando tabela '{tabela}'...")
            
            # Verificar se a tabela existe
            if not verificar_tabela_existe(conn, tabela):
                print(f"⚠️  Tabela '{tabela}' não encontrada - pulando...")
                continue
            
            # Verificar cada coluna
            for nome_coluna, tipo_coluna in colunas:
                if verificar_coluna_existe(conn, tabela, nome_coluna):
                    print(f"✅ Coluna '{nome_coluna}' já existe em '{tabela}'")
                else:
                    print(f"➕ Adicionando coluna '{nome_coluna}' em '{tabela}'...")
                    if adicionar_coluna(conn, tabela, nome_coluna, tipo_coluna):
                        print(f"✅ Coluna '{nome_coluna}' adicionada com sucesso!")
                        mudancas_realizadas.append(f"{tabela}.{nome_coluna}")
                    else:
                        print(f"❌ Falha ao adicionar coluna '{nome_coluna}'")
                        return False
        
        print("\n" + "=" * 50)
        
        if mudancas_realizadas:
            print("✅ MIGRAÇÕES CONCLUÍDAS COM SUCESSO!")
            print("\n📋 Colunas adicionadas:")
            for mudanca in mudancas_realizadas:
                print(f"   • {mudanca}")
        else:
            print("✅ TODAS AS COLUNAS JÁ EXISTEM!")
            print("\n📋 Nenhuma migração necessária.")
        
        print("\n🔄 Próximos passos:")
        print("   1. Reiniciar o servidor: python main.py")
        print("   2. Testar funcionalidades de WhatsApp")
        print("   3. Verificar filtros nos beneficiários")
        print("   4. Confirmar busca por WhatsApp")
        
        return True
        
    finally:
        conn.close()

def verificar_estruturas_finais():
    """Verifica as estruturas finais após migração"""
    conn = conectar_banco()
    if not conn:
        return False
    
    try:
        print("\n🔍 VERIFICAÇÃO FINAL DAS ESTRUTURAS:")
        print("=" * 40)
        
        tabelas_verificar = {
            'fornecedor_doador': ['whatsapp'],
            'beneficiarios': ['whatsapp', 'whatsapp_responsavel'],
            'doacoes_avulsas': ['whatsapp'],
            'usuarios': ['nome_completo']
        }
        
        for tabela, colunas_esperadas in tabelas_verificar.items():
            if verificar_tabela_existe(conn, tabela):
                print(f"\n📊 {tabela}:")
                for coluna in colunas_esperadas:
                    existe = verificar_coluna_existe(conn, tabela, coluna)
                    status = "✅" if existe else "❌"
                    print(f"   {status} {coluna}")
            else:
                print(f"\n⚠️  {tabela}: tabela não encontrada")
        
        return True
        
    finally:
        conn.close()

def main():
    """Função principal"""
    print("🚀 MIGRAÇÃO DE COLUNAS WHATSAPP - VERSÃO 1.5.0")
    print("=" * 50)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Este script irá:")
    print("• Adicionar colunas WhatsApp nas tabelas necessárias")
    print("• Verificar coluna nome_completo em usuários")
    print("• Validar estruturas finais")
    print()
    
    input("Pressione ENTER para continuar ou Ctrl+C para cancelar...")
    print()
    
    # Executar migrações
    if not executar_migracoes():
        print("❌ FALHA NAS MIGRAÇÕES!")
        return False
    
    # Verificar estruturas finais
    verificar_estruturas_finais()
    
    print("\n" + "=" * 50)
    print("🎉 MIGRAÇÃO CONCLUÍDA!")
    print("\nAgora o banco está preparado para:")
    print("   • Busca por WhatsApp em beneficiários")
    print("   • Filtros de WhatsApp em doações")
    print("   • Campos WhatsApp em fornecedores")
    print("   • Nome completo em usuários")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migração cancelada pelo usuário.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        exit(1)