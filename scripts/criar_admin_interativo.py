"""
Script INTERATIVO para criar e excluir administradores de barbearias
O script pergunta os dados e cria/exclui o admin
"""
import sqlite3
import os
import sys
import getpass
from werkzeug.security import generate_password_hash, check_password_hash
import logging, sys as _sys

# Logger para scripts interativos
logger = logging.getLogger('projeto_barber.scripts.criar_admin_interativo')
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(_sys.stdout)
_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(_handler)

# Definir caminho fixo do banco de dados (onde o script está originalmente)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'meubanco.db')

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def listar_barbearias():
    """Lista e retorna todas as barbearias disponíveis"""
    if not os.path.exists(DB_PATH):
        logger.error(f"Erro: Banco de dados não encontrado em: {DB_PATH}")
        logger.info("Execute este script da pasta do projeto")
        logger.info(f"   {SCRIPT_DIR}")
        input("Pressione ENTER para sair...")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, slug, nome, ativa FROM barbearia ORDER BY nome")
        barbearias = cursor.fetchall()
        return barbearias
    finally:
        conn.close()

def criar_admin_interativo():
    """Cria um admin de forma interativa"""
    limpar_tela()
    logger.info("" + "=" * 70)
    logger.info("CRIAÇÃO INTERATIVA DE ADMINISTRADOR DE BARBEARIA")
    logger.info("" + "=" * 70)
    logger.info("")
    
    # Verificar autenticação do super admin
    if not verificar_super_admin():
        logger.error('Credenciais inválidas — acesso negado')
        return

    logger.info('Autenticado com sucesso')
    
    # 1. Listar e selecionar barbearia
    logger.info('BARBEARIAS DISPONÍVEIS:')
    logger.info('-' * 70)
    barbearias = listar_barbearias()
    
    for idx, (id, slug, nome, ativa) in enumerate(barbearias, 1):
        status = "ATIVA" if ativa else "INATIVA"
        logger.info(f"{idx}. {status} {nome} ({slug})")
    print("-" * 70)
    print()
    
    while True:
        try:
            escolha = input("Digite o número da barbearia: ").strip()
            idx = int(escolha) - 1
            if 0 <= idx < len(barbearias):
                barbearia_id, barbearia_slug, barbearia_nome, _ = barbearias[idx]
                break
            else:
                    logger.warning('Número inválido! Tente novamente.')
        except ValueError:
                logger.warning('Digite apenas números!')
    
    logger.info(f"Barbearia selecionada: {barbearia_nome}")
    
    # 2. Coletar dados do admin
    logger.info('DADOS DO ADMINISTRADOR:')
    logger.info('-' * 70)
    
    nome = input("Nome completo: ").strip()
    while not nome:
        logger.warning('Nome é obrigatório!')
        nome = input("Nome completo: ").strip()
    
    username = input("Username (para login): ").strip()
    while not username:
        logger.warning('Username é obrigatório!')
        username = input("Username (para login): ").strip()
    
    senha = getpass.getpass("Senha: ")
    while not senha:
        logger.warning('Senha é obrigatória!')
        senha = getpass.getpass("Senha: ")
    
    email = input("Email (deixe vazio para gerar automaticamente): ").strip()
    if not email:
        email = f"{username}@{barbearia_slug}.com"
    
    telefone = input("Telefone (opcional): ").strip() or None
    
    # 3. Confirmar dados
    logger.info('=' * 70)
    logger.info('CONFIRME OS DADOS:')
    logger.info('=' * 70)
    logger.info(f"Barbearia: {barbearia_nome}")
    logger.info(f"Nome: {nome}")
    logger.info(f"Username: {username}")
    logger.info(f"Senha: {senha}")
    logger.info(f"Email: {email}")
    logger.info(f"Telefone: {telefone or 'Não informado'}")
    logger.info('=' * 70)
    logger.info('')
    
    confirma = input("Confirma a criação? (S/N): ").strip().upper()
    if confirma != 'S':
        logger.info('Operação cancelada pelo usuário')
        return
    
    # 4. Criar no banco de dados
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar se username já existe
        cursor.execute("SELECT id FROM usuario WHERE username = ?", (username,))
        if cursor.fetchone():
            logger.error(f"Username '{username}' já está em uso")
            return
        
        # Verificar se email já existe
        cursor.execute("SELECT id FROM usuario WHERE email = ?", (email,))
        if cursor.fetchone():
            logger.error(f"Email '{email}' já está em uso")
            return
        
        # Criar o usuário
        senha_hash = generate_password_hash(senha)
        cursor.execute("""
            INSERT INTO usuario (nome, email, username, senha, telefone, tipo_conta, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome, email, username, senha_hash, telefone, 'admin_barbearia', 1))
        
        usuario_id = cursor.lastrowid
        
        # Vincular à barbearia com role 'admin'
        cursor.execute("""
            INSERT INTO usuario_barbearia (usuario_id, barbearia_id, role, ativo)
            VALUES (?, ?, ?, ?)
        """, (usuario_id, barbearia_id, 'admin', 1))
        
        conn.commit()
        
        logger.info('=' * 70)
        logger.info('ADMINISTRADOR CRIADO COM SUCESSO')
        logger.info('=' * 70)
        logger.info('Credenciais de Acesso:')
        logger.info(f"   Barbearia: {barbearia_nome}")
        logger.info(f"   Username: {username}")
        logger.info(f"   Senha: {senha}")
        logger.info(f"   Email: {email}")
        logger.info(f"   http://localhost:5000/{barbearia_slug}/login")
        logger.info('=' * 70)
        logger.info('')
        
    except Exception as e:
        logger.exception('Erro ao criar admin')
        conn.rollback()
    finally:
        conn.close()

def verificar_super_admin():
    """Verifica credenciais do super admin"""
    logger.info('AUTENTICAÇÃO DO SUPER ADMIN')
    logger.info('-' * 70)
    username = input("Username do Super Admin: ").strip()
    senha = getpass.getpass("Senha do Super Admin: ")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT senha FROM usuario 
            WHERE (username = ? OR email = ?) 
            AND tipo_conta = 'super_admin' 
            AND ativo = 1
        """, (username, username))
        
        resultado = cursor.fetchone()
        if resultado and check_password_hash(resultado[0], senha):
            return True
        return False
    finally:
        conn.close()

def listar_admins():
    """Lista todos os admins de barbearias"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.id, u.nome, u.username, u.email, b.nome as barbearia_nome, b.slug
            FROM usuario u
            JOIN usuario_barbearia ub ON u.id = ub.usuario_id
            JOIN barbearia b ON ub.barbearia_id = b.id
            WHERE u.tipo_conta = 'admin_barbearia' AND u.ativo = 1 AND ub.role = 'admin'
            ORDER BY b.nome, u.nome
        """)
        
        admins = cursor.fetchall()
        return admins
    finally:
        conn.close()

def excluir_admin_interativo():
    """Exclui um admin de forma interativa (requer autenticação super admin)"""
    limpar_tela()
    print("=" * 70)
    print("🗑️  EXCLUIR ADMINISTRADOR DE BARBEARIA")
    print("=" * 70)
    print()
    
    # Verificar autenticação do super admin
    if not verificar_super_admin():
        print("\n❌ Credenciais inválidas! Acesso negado.")
        return
    
    print("\n✅ Autenticado com sucesso!\n")
    
    # Listar admins existentes
    print("📋 ADMINISTRADORES CADASTRADOS:")
    print("-" * 70)
    admins = listar_admins()
    
    if not admins:
        print("Nenhum administrador encontrado.")
        return
    
    for idx, (id, nome, username, email, barbearia, slug) in enumerate(admins, 1):
        print(f"{idx}. {nome} (@{username}) - {barbearia}")
        print(f"   Email: {email}")
    print("-" * 70)
    print()
    
    # Selecionar admin para excluir
    while True:
        try:
            escolha = input("Digite o número do admin para excluir (0 para cancelar): ").strip()
            if escolha == '0':
                print("\n❌ Operação cancelada!")
                return
            
            idx = int(escolha) - 1
            if 0 <= idx < len(admins):
                admin_id, admin_nome, admin_username, admin_email, barbearia, slug = admins[idx]
                break
            else:
                print("❌ Número inválido! Tente novamente.")
        except ValueError:
            print("❌ Digite apenas números!")
    
    # Confirmar exclusão
    print()
    print("=" * 70)
    print("⚠️  CONFIRME A EXCLUSÃO:")
    print("=" * 70)
    print(f"Nome: {admin_nome}")
    print(f"Username: {admin_username}")
    print(f"Email: {admin_email}")
    print(f"Barbearia: {barbearia}")
    print("=" * 70)
    print()
    
    confirma = input("⚠️  CONFIRMA A EXCLUSÃO? (Digite 'EXCLUIR' para confirmar): ").strip()
    if confirma != 'EXCLUIR':
        print("\n❌ Operação cancelada!")
        return
    
    # Excluir do banco de dados
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Desativar usuário ao invés de deletar (para manter histórico)
        cursor.execute("UPDATE usuario SET ativo = 0 WHERE id = ?", (admin_id,))
        cursor.execute("UPDATE usuario_barbearia SET ativo = 0 WHERE usuario_id = ?", (admin_id,))
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ ADMINISTRADOR EXCLUÍDO COM SUCESSO!")
        print("=" * 70)
        print(f"\nAdmin '{admin_nome}' foi desativado e não poderá mais fazer login.")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\n❌ Erro ao excluir admin: {e}")
        conn.rollback()
    finally:
        conn.close()

def menu_principal():
    """Menu principal do script"""
    limpar_tela()
    print("=" * 70)
    print("🎯 GERENCIAR ADMINISTRADORES DE BARBEARIAS")
    print("=" * 70)
    print()
    print("1. ➕ Criar novo administrador (requer super admin)")
    print("2. 🗑️  Excluir administrador (requer super admin)")
    print("0. ❌ Sair")
    print()
    print("=" * 70)
    
    escolha = input("\nEscolha uma opção: ").strip()
    return escolha

def main():
    try:
        while True:
            opcao = menu_principal()
            
            if opcao == '1':
                criar_admin_interativo()
                input("\nPressione ENTER para continuar...")
            elif opcao == '2':
                excluir_admin_interativo()
                input("\nPressione ENTER para continuar...")
            elif opcao == '0':
                print("\n👋 Até logo!")
                break
            else:
                print("\n❌ Opção inválida!")
                input("\nPressione ENTER para continuar...")
                
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == '__main__':
    main()
