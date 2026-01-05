#!/usr/bin/env python3
"""
Serviço de sincronização automática de chamados
Executa periodicamente para manter status sincronizados com API externa
"""

import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime
import requests
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sincronizacao_chamados.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

current_dir = Path(__file__).resolve().parent.parent
app_file = current_dir / 'app.py'

if not app_file.exists():
    logging.error("ERRO: Execute este script da pasta raiz do projeto")
    sys.exit(1)

sys.path.insert(0, str(current_dir))

try:
    from app import app, db, Chamado
    logging.info("✅ Módulos importados com sucesso")
except ImportError as e:
    logging.error(f"ERRO ao importar módulos: {e}")
    sys.exit(1)

class SincronizadorChamados:
    """Classe para gerenciar sincronização de chamados"""

    def __init__(self):
        self.api_base_url = "http://localhost:5001"
        self.api_headers = {"X-API-Key": "barber-connect-api-key-2025"}
        self.intervalo_verificacao = 300  # 5 minutos por padrão

    def verificar_conectividade_api(self):
        """Verifica se a API externa está acessível"""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/suporte",
                                  headers=self.api_headers, timeout=10)
            return response.status_code in [200, 405]  # 405 é OK (método não permitido, mas API responde)
        except Exception as e:
            logging.warning(f"API não acessível: {e}")
            return False

    def verificar_status_chamado_api(self, api_chamado_id):
        """Verifica o status de um chamado na API externa"""
        if not api_chamado_id:
            return None, None

        # Tentar diferentes endpoints
        endpoints = [
            f"{self.api_base_url}/api/v1/suporte/{api_chamado_id}",
            f"{self.api_base_url}/api/v1/chamados/{api_chamado_id}",
            f"{self.api_base_url}/api/chamados/{api_chamado_id}"
        ]

        for url in endpoints:
            try:
                response = requests.get(url, headers=self.api_headers, timeout=5)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data.get('status'), data
                    except json.JSONDecodeError:
                        logging.warning(f"Resposta JSON inválida da API: {url}")
                        continue
                elif response.status_code == 404:
                    # Chamado não existe mais na API
                    return 'deletado', None
            except requests.exceptions.Timeout:
                logging.warning(f"Timeout ao verificar {url}")
                continue
            except Exception as e:
                logging.warning(f"Erro ao verificar {url}: {e}")
                continue

        return None, None

    def sincronizar_chamados(self):
        """Sincroniza todos os chamados com a API externa"""
        logging.info("🔄 Iniciando sincronização de chamados...")

        with app.app_context():
            # Verificar conectividade da API
            if not self.verificar_conectividade_api():
                logging.error("❌ API externa não está acessível. Abortando sincronização.")
                return False

            # Buscar chamados que têm api_chamado_id
            chamados = Chamado.query.filter(Chamado.api_chamado_id.isnot(None)).all()

            if not chamados:
                logging.info("⚠️  Nenhum chamado com ID da API encontrado")
                return True

            atualizados = 0
            deletados = 0
            erros = 0

            for chamado in chamados:
                try:
                    logging.info(f"📋 Verificando: {chamado.numero_chamado} (API ID: {chamado.api_chamado_id})")

                    status_api, dados_api = self.verificar_status_chamado_api(chamado.api_chamado_id)

                    if status_api == 'deletado':
                        # Chamado foi removido da API
                        if chamado.status != 'cancelado':
                            chamado.status = 'cancelado'
                            chamado.data_atualizacao = datetime.utcnow()
                            deletados += 1
                            logging.info(f"   🗑️  Marcado como CANCELADO (removido da API)")
                        else:
                            logging.info(f"   ✅ Já estava marcado como CANCELADO")

                    elif status_api and status_api != chamado.status:
                        # Status diferente - atualizar
                        status_anterior = chamado.status
                        chamado.status = status_api
                        chamado.data_atualizacao = datetime.utcnow()
                        atualizados += 1
                        logging.info(f"   🔄 Status atualizado: {status_anterior} → {status_api}")

                    elif status_api == chamado.status:
                        logging.debug(f"   ✅ Status já está sincronizado: {status_api}")

                    else:
                        logging.warning(f"   ❓ Não foi possível verificar status na API")

                except Exception as e:
                    erros += 1
                    logging.error(f"   ❌ Erro ao processar {chamado.numero_chamado}: {e}")

            # Commit das alterações
            try:
                if atualizados > 0 or deletados > 0:
                    db.session.commit()
                    logging.info("✅ Sincronização concluída com sucesso!")
                    logging.info(f"   📊 Chamados atualizados: {atualizados}")
                    logging.info(f"   🗑️  Chamados marcados como cancelados: {deletados}")
                    if erros > 0:
                        logging.warning(f"   ⚠️  Erros encontrados: {erros}")
                else:
                    logging.info("✅ Todos os chamados já estão sincronizados")
                    db.session.rollback()  # Nada para commitar
            except Exception as e:
                logging.error(f"❌ Erro ao salvar alterações: {e}")
                db.session.rollback()
                return False

            return True

    def executar_sincronizacao_unica(self):
        """Executa uma única sincronização"""
        logging.info("=" * 60)
        logging.info("🚀 SINCRONIZAÇÃO MANUAL DE CHAMADOS")
        logging.info("=" * 60)

        sucesso = self.sincronizar_chamados()

        if sucesso:
            logging.info("✅ Sincronização manual concluída com sucesso")
        else:
            logging.error("❌ Sincronização manual falhou")

        return sucesso

    def iniciar_monitoramento_continuo(self, intervalo_segundos=None):
        """Inicia monitoramento contínuo em loop"""
        if intervalo_segundos:
            self.intervalo_verificacao = intervalo_segundos

        logging.info("=" * 60)
        logging.info("🔄 INICIANDO MONITORAMENTO CONTÍNUO DE CHAMADOS")
        logging.info(f"   Intervalo: {self.intervalo_verificacao} segundos")
        logging.info("=" * 60)

        ciclo = 1
        while True:
            try:
                logging.info(f"🔄 Ciclo #{ciclo} - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

                sucesso = self.sincronizar_chamados()

                if sucesso:
                    logging.info(f"✅ Ciclo #{ciclo} concluído com sucesso")
                else:
                    logging.warning(f"⚠️  Ciclo #{ciclo} teve problemas")

                ciclo += 1

                # Aguardar próximo ciclo
                logging.info(f"⏰ Aguardando {self.intervalo_verificacao} segundos para próximo ciclo...")
                time.sleep(self.intervalo_verificacao)

            except KeyboardInterrupt:
                logging.info("🛑 Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logging.error(f"❌ Erro crítico no ciclo #{ciclo}: {e}")
                logging.info("⏰ Aguardando 60 segundos antes de tentar novamente...")
                time.sleep(60)

def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Sincronização automática de chamados')
    parser.add_argument('--modo', choices=['unico', 'continuo'],
                       default='unico', help='Modo de execução')
    parser.add_argument('--intervalo', type=int, default=300,
                       help='Intervalo em segundos para modo contínuo (padrão: 300)')

    args = parser.parse_args()

    sincronizador = SincronizadorChamados()

    if args.modo == 'continuo':
        sincronizador.iniciar_monitoramento_continuo(args.intervalo)
    else:
        sincronizador.executar_sincronizacao_unica()

if __name__ == "__main__":
    main()