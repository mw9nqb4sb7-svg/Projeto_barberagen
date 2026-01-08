#!/usr/bin/env python3
"""
Script para implementar sincronização de status dos chamados
Verifica se chamados foram marcados como cancelados/deletados na API externa
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import requests
import json

current_dir = Path(__file__).resolve().parent.parent
app_file = current_dir / 'app.py'

if not app_file.exists():
    print("❌ ERRO: Execute este script da pasta raiz do projeto")
    sys.exit(1)

sys.path.insert(0, str(current_dir))

try:
    from app import app, db, Chamado
except ImportError as e:
    print(f"❌ ERRO ao importar: {e}")
    sys.exit(1)

def verificar_status_chamado_api(api_chamado_id):
    """Verifica o status de um chamado na API externa"""
    if not api_chamado_id:
        return None, None

    try:
        # Tentar diferentes endpoints para consultar o chamado
        endpoints = [
            f"http://localhost:5001/api/v1/suporte/{api_chamado_id}",
            f"http://localhost:5001/api/v1/chamados/{api_chamado_id}",
            f"http://localhost:5001/api/chamados/{api_chamado_id}"
        ]

        headers = {"X-API-Key": "barber-connect-api-key-2025"}

        for url in endpoints:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # A API retorna {"success": true, "ticket": {...}}
                        if data.get('success') and 'ticket' in data:
                            ticket = data['ticket']
                            # Mapear status da API para status local
                            status_api = ticket.get('status', 'novo')
                            status_mapeado = mapear_status_api(status_api)
                            return status_mapeado, ticket
                        else:
                            # Formato diferente, tentar ler diretamente
                            status_api = data.get('status')
                            if status_api:
                                status_mapeado = mapear_status_api(status_api)
                                return status_mapeado, data
                    except json.JSONDecodeError:
                        logging.warning(f"Resposta JSON inválida da API: {url}")
                        continue
                elif response.status_code == 404:
                    # Chamado não existe mais na API
                    return 'deletado', None
            except:
                continue

        return None, None

    except Exception as e:
        print(f"❌ Erro ao verificar status na API: {e}")
        return None, None

def mapear_status_api(status_api):
    """Mapeia status da API externa para status local"""
    mapeamento = {
        'novo': 'enviado',
        'recebido': 'enviado',
        'em_andamento': 'em_andamento',
        'atendimento': 'em_andamento',
        'em_atendimento': 'em_andamento',
        'resolvido': 'resolvido',
        'finalizado': 'fechado',
        'fechado': 'fechado',
        'cancelado': 'cancelado',
        'deletado': 'cancelado'
    }

    return mapeamento.get(status_api.lower(), 'enviado')

def sincronizar_status_chamados():
    """Sincroniza o status dos chamados locais com a API externa"""
    with app.app_context():
        print("🔄 Sincronizando status dos chamados...")

        # Buscar chamados que têm api_chamado_id
        chamados = Chamado.query.filter(Chamado.api_chamado_id.isnot(None)).all()

        if not chamados:
            print("⚠️  Nenhum chamado com ID da API encontrado")
            return

        atualizados = 0
        deletados = 0

        for chamado in chamados:
            print(f"📋 Verificando: {chamado.numero_chamado} (API ID: {chamado.api_chamado_id})")

            status_api, dados_api = verificar_status_chamado_api(chamado.api_chamado_id)

            if status_api == 'deletado':
                # Chamado foi removido da API - marcar como cancelado localmente
                chamado.status = 'cancelado'
                chamado.data_atualizacao = datetime.utcnow()
                deletados += 1
                print(f"   🗑️  Marcado como CANCELADO (removido da API)")

            elif status_api and status_api != chamado.status:
                # Status diferente - atualizar
                chamado.status = status_api
                chamado.data_atualizacao = datetime.utcnow()
                atualizados += 1
                print(f"   🔄 Status atualizado: {chamado.status} → {status_api}")

            elif status_api == chamado.status:
                print(f"   ✅ Status já está sincronizado: {status_api}")

            else:
                print(f"   ❓ Não foi possível verificar status na API")

        # Commit das alterações
        if atualizados > 0 or deletados > 0:
            db.session.commit()
            print(f"\n✅ Sincronização concluída!")
            print(f"   📊 Chamados atualizados: {atualizados}")
            print(f"   🗑️  Chamados marcados como cancelados: {deletados}")
        else:
            print("\n✅ Todos os chamados já estão sincronizados")

def mostrar_status_atual():
    """Mostra o status atual de todos os chamados"""
    with app.app_context():
        chamados = Chamado.query.order_by(Chamado.data_criacao.desc()).all()

        if not chamados:
            print("📭 Nenhum chamado encontrado")
            return

        print(f"📊 Status atual dos chamados ({len(chamados)} total):")
        print("-" * 60)

        for chamado in chamados:
            api_status = "Sim" if chamado.api_chamado_id else "Não"
            print(f"📋 {chamado.numero_chamado}: {chamado.status.upper()}")
            print(f"   📅 Criado: {chamado.data_criacao.strftime('%d/%m/%Y %H:%M')}")
            print(f"   🔗 API ID: {chamado.api_chamado_id or 'N/A'}")
            print(f"   📝 Assunto: {chamado.assunto[:50]}...")
            print()

if __name__ == "__main__":
    print("🔄 SINCRONIZAÇÃO DE STATUS DOS CHAMADOS")
    print("=" * 50)

    print("\n1. Status atual antes da sincronização:")
    mostrar_status_atual()

    print("\n2. Executando sincronização...")
    sincronizar_status_chamados()

    print("\n3. Status após sincronização:")
    mostrar_status_atual()

    print("\n💡 Dica: Execute este script periodicamente para manter os status sincronizados")
    print("   Ou configure como tarefa agendada no servidor")