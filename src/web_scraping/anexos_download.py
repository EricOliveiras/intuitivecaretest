import requests
from bs4 import BeautifulSoup
import zipfile
import os
import shutil
from datetime import datetime

def download_anexos():
    """
    Versão definitiva com correção do problema de caminhos
    """
    try:
        # Configurações de caminhos
        base_dir = "data"
        raw_dir = os.path.join(base_dir, "raw")
        backup_dir = os.path.join(base_dir, "backup_anexos")
        
        # Garante a estrutura de diretórios
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(backup_dir, exist_ok=True)

        print(f"{datetime.now().strftime('%H:%M:%S')} - Iniciando download dos anexos...")

        # 1. Busca dos anexos no portal ANS
        url = "https://www.gov.br/ans/pt-br/acesso-a-informacao/participacao-da-sociedade/atualizacao-do-rol-de-procedimentos"
        session = requests.Session()
        response = session.get(url, timeout=60)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Mapeamento de anexos
        anexos = {
            'Anexo_I.pdf': None,
            'Anexo_II.pdf': None
        }

        # Estratégia de busca flexível
        for link in soup.find_all('a', href=True):
            lower_text = link.get_text().lower()
            lower_href = link['href'].lower()
            
            if not anexos['Anexo_I.pdf'] and ('anexo i' in lower_text or 'anexoi' in lower_href or 'rol' in lower_href):
                if lower_href.endswith('.pdf'):
                    anexos['Anexo_I.pdf'] = link['href']
                    
            if not anexos['Anexo_II.pdf'] and ('anexo ii' in lower_text or 'anexoii' in lower_href or 'anexo2' in lower_href):
                if lower_href.endswith('.pdf'):
                    anexos['Anexo_II.pdf'] = link['href']

        # Validação
        if None in anexos.values():
            raise ValueError(f"Links não encontrados para: {[k for k, v in anexos.items() if v is None]}")

        # 2. Download dos arquivos
        downloaded_files = []
        for nome, url in anexos.items():
            file_path = os.path.join(raw_dir, nome)
            backup_path = os.path.join(backup_dir, nome)
            
            print(f"{datetime.now().strftime('%H:%M:%S')} - Baixando {nome}...")
            
            # Download com verificação
            response = session.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            # Salva na pasta raw e no backup
            with open(file_path, 'wb') as f, open(backup_path, 'wb') as bf:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bf.write(chunk)
            
            downloaded_files.append(file_path)
            print(f"{datetime.now().strftime('%H:%M:%S')} - {nome} salvo em {file_path}")

        # 3. Criação do ZIP (mantém os arquivos originais)
        zip_path = os.path.join(raw_dir, "Anexos.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in downloaded_files:
                zipf.write(file_path, os.path.basename(file_path))
                print(f"{datetime.now().strftime('%H:%M:%S')} - {os.path.basename(file_path)} adicionado ao ZIP")

        print(f"{datetime.now().strftime('%H:%M:%S')} - Processo concluído com sucesso!")
        return True

    except Exception as e:
        print(f"{datetime.now().strftime('%H:%M:%S')} - ERRO CRÍTICO: {str(e)}")
        return False