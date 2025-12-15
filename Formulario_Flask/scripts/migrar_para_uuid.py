"""
Script de Migração: Adicionar UUIDs aos Registros Existentes
Este script gera UUIDs únicos para todos os registros existentes no banco de dados.
"""
import sys
import os
from pathlib import Path
import uuid as uuid_lib

# Adicionar o diretório pai ao path para importar os módulos
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from app import app, db, Barbearia, Usuario, Servico, Reserva, DisponibilidadeSemanal

def gerar_uuids():
    """Gera UUIDs para todos os registros que não têm"""
    with app.app_context():
        print("=" * 60)
        print("MIGRAÇÃO: Gerando UUIDs para registros existentes")
        print("=" * 60)
        
        # Contadores
        total_atualizados = 0
        
        # 1. Barbearias
        print("\n[1/5] Processando Barbearias...")
        barbearias = Barbearia.query.filter(
            (Barbearia.uuid == None) | (Barbearia.uuid == '')
        ).all()
        for barbearia in barbearias:
            barbearia.uuid = str(uuid_lib.uuid4())
            print(f"  ✓ Barbearia '{barbearia.nome}' -> UUID: {barbearia.uuid}")
        if barbearias:
            db.session.commit()
            total_atualizados += len(barbearias)
            print(f"  Total: {len(barbearias)} barbearias atualizadas")
        else:
            print("  ✓ Todas as barbearias já possuem UUID")
        
        # 2. Usuários
        print("\n[2/5] Processando Usuários...")
        usuarios = Usuario.query.filter(
            (Usuario.uuid == None) | (Usuario.uuid == '')
        ).all()
        for usuario in usuarios:
            usuario.uuid = str(uuid_lib.uuid4())
            print(f"  ✓ Usuário '{usuario.nome}' ({usuario.email}) -> UUID: {usuario.uuid}")
        if usuarios:
            db.session.commit()
            total_atualizados += len(usuarios)
            print(f"  Total: {len(usuarios)} usuários atualizados")
        else:
            print("  ✓ Todos os usuários já possuem UUID")
        
        # 3. Serviços
        print("\n[3/5] Processando Serviços...")
        servicos = Servico.query.filter(
            (Servico.uuid == None) | (Servico.uuid == '')
        ).all()
        for servico in servicos:
            servico.uuid = str(uuid_lib.uuid4())
            print(f"  ✓ Serviço '{servico.nome}' -> UUID: {servico.uuid}")
        if servicos:
            db.session.commit()
            total_atualizados += len(servicos)
            print(f"  Total: {len(servicos)} serviços atualizados")
        else:
            print("  ✓ Todos os serviços já possuem UUID")
        
        # 4. Reservas
        print("\n[4/5] Processando Reservas...")
        reservas = Reserva.query.filter(
            (Reserva.uuid == None) | (Reserva.uuid == '')
        ).all()
        for reserva in reservas:
            reserva.uuid = str(uuid_lib.uuid4())
            print(f"  ✓ Reserva (ID: {reserva.id}) -> UUID: {reserva.uuid}")
        if reservas:
            db.session.commit()
            total_atualizados += len(reservas)
            print(f"  Total: {len(reservas)} reservas atualizadas")
        else:
            print("  ✓ Todas as reservas já possuem UUID")
        
        # 5. Disponibilidades Semanais
        print("\n[5/5] Processando Disponibilidades Semanais...")
        disponibilidades = DisponibilidadeSemanal.query.filter(
            (DisponibilidadeSemanal.uuid == None) | (DisponibilidadeSemanal.uuid == '')
        ).all()
        for disp in disponibilidades:
            disp.uuid = str(uuid_lib.uuid4())
            print(f"  ✓ Disponibilidade (ID: {disp.id}) -> UUID: {disp.uuid}")
        if disponibilidades:
            db.session.commit()
            total_atualizados += len(disponibilidades)
            print(f"  Total: {len(disponibilidades)} disponibilidades atualizadas")
        else:
            print("  ✓ Todas as disponibilidades já possuem UUID")
        
        # Resumo
        print("\n" + "=" * 60)
        print(f"MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"Total de registros atualizados: {total_atualizados}")
        print("=" * 60)
        
        # Verificação final
        print("\n" + "=" * 60)
        print("VERIFICAÇÃO FINAL")
        print("=" * 60)
        
        verificacoes = [
            ("Barbearias", Barbearia.query.filter((Barbearia.uuid == None) | (Barbearia.uuid == '')).count()),
            ("Usuários", Usuario.query.filter((Usuario.uuid == None) | (Usuario.uuid == '')).count()),
            ("Serviços", Servico.query.filter((Servico.uuid == None) | (Servico.uuid == '')).count()),
            ("Reservas", Reserva.query.filter((Reserva.uuid == None) | (Reserva.uuid == '')).count()),
            ("Disponibilidades", DisponibilidadeSemanal.query.filter((DisponibilidadeSemanal.uuid == None) | (DisponibilidadeSemanal.uuid == '')).count()),
        ]
        
        todos_ok = True
        for nome, count in verificacoes:
            if count > 0:
                print(f"  ⚠ {nome}: {count} registros ainda sem UUID!")
                todos_ok = False
            else:
                print(f"  ✓ {nome}: Todos os registros possuem UUID")
        
        if todos_ok:
            print("\n✅ Verificação OK: Todos os registros possuem UUID!")
        else:
            print("\n⚠ ATENÇÃO: Ainda existem registros sem UUID!")
        
        print("=" * 60)

if __name__ == '__main__':
    try:
        gerar_uuids()
    except Exception as e:
        print(f"\n❌ ERRO durante a migração: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
