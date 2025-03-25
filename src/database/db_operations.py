import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pandas as pd
import zipfile
import sqlite3
import sys
import time

def setup_database():
    """Cria e conecta ao banco de dados SQLite"""
    try:
        os.makedirs('data/processed', exist_ok=True)
        db_path = 'data/processed/ans.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Criação das tabelas com IF NOT EXISTS
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS operadoras (
            registro_ans TEXT PRIMARY KEY,
            cnpj TEXT,
            razao_social TEXT,
            nome_fantasia TEXT,
            modalidade TEXT,
            data_registro TEXT
        )''')
        
        cursor.execute('''
      CREATE TABLE IF NOT EXISTS demonstracoes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          data DATE NOT NULL,
          registro_ans TEXT NOT NULL,
          codigo_conta TEXT NOT NULL,
          descricao TEXT NOT NULL,
          valor DECIMAL(15,2) NOT NULL,
          ano INTEGER NOT NULL,
          trimestre TEXT NOT NULL,
          FOREIGN KEY (registro_ans) REFERENCES operadoras(registro_ans),
          CONSTRAINT unq_demonstracoes UNIQUE (data, registro_ans, codigo_conta)
      )''')
        
        conn.commit()
        print("Banco de dados configurado com sucesso")
        return conn
        
    except Exception as e:
        print(f"Erro ao configurar banco de dados: {str(e)}")
        raise

def download_file_with_retry(url, destination, max_retries=3):
    """Baixa um arquivo com mecanismo de retentativa"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(destination, 'wb') as f:
                f.write(response.content)
            return True
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Tentativa {attempt + 1} falhou, aguardando para tentar novamente...")
            time.sleep(5 * (attempt + 1))
    return False

def download_demonstracoes_contabeis():
    """Baixa arquivos trimestrais das demonstrações contábeis"""
    base_url = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
    current_year = datetime.now().year
    years_to_download = [current_year - 1, current_year - 2]  # 2024 e 2023 em 2025
    downloaded_files = []
    
    for year in years_to_download:
        print(f"\nProcessando ano {year}...")
        url = f"{base_url}{year}/"
        
        try:
            # Obter lista de arquivos no diretório
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.zip')]
            
            if not links:
                print(f"Nenhum arquivo ZIP encontrado para {year}")
                continue
                
            # Baixar cada arquivo trimestral
            for file in links:
                if any(q in file for q in ['1T', '2T', '3T', '4T']):
                    file_url = f"{url}{file}"
                    dest_dir = f'data/raw/demonstracoes/{year}'
                    os.makedirs(dest_dir, exist_ok=True)
                    file_path = f'{dest_dir}/{file}'
                    
                    print(f"Baixando {file}...")
                    if download_file_with_retry(file_url, file_path):
                        downloaded_files.append(file_path)
                    
        except Exception as e:
            print(f"Erro ao processar {year}: {str(e)}")
            continue
    
    return downloaded_files

def extrair_arquivos_zip(downloaded_files):
    """Extrai arquivos ZIP baixados"""
    for zip_path in downloaded_files:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_path = os.path.splitext(zip_path)[0]  # Remove .zip
                os.makedirs(extract_path, exist_ok=True)
                zip_ref.extractall(extract_path)
                print(f"Arquivos extraídos em {extract_path}")
        except Exception as e:
            print(f"Erro ao extrair {zip_path}: {str(e)}")
            continue

def import_operadoras(conn):
    try:
        file_path = 'data/raw/operadoras_ativas.csv'
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo {file_path} não encontrado")
        
        # Verifica o cabeçalho real do arquivo
        with open(file_path, 'r', encoding='iso-8859-1') as f:
            first_line = f.readline().strip()
        
        # Mapeamento de colunas (nomes no arquivo -> nomes no banco)
        column_mapping = {
            'Registro_ANS': 'registro_ans',
            'CNPJ': 'cnpj',
            'Razao_Social': 'razao_social',
            'Nome_Fantasia': 'nome_fantasia',
            'Modalidade': 'modalidade',
            'Data_Registro_ANS': 'data_registro'
        }
        
        # Encontra as colunas disponíveis que queremos importar
        available_cols = [col.strip() for col in first_line.split(';')]
        cols_to_import = [col for col in column_mapping.keys() if col in available_cols]
        
        if not cols_to_import:
            raise ValueError("Nenhuma coluna válida encontrada no arquivo")
        
        # Leitura do CSV
        df = pd.read_csv(
            file_path,
            sep=';',
            encoding='iso-8859-1',
            usecols=cols_to_import
        )
        
        # Renomeia colunas para o padrão do banco
        df = df.rename(columns=column_mapping)
        
        # Limpeza básica dos dados
        df = df.dropna(subset=['registro_ans']).drop_duplicates(subset=['registro_ans'])
        
        # Conversão de datas
        if 'data_registro' in df.columns:
            df['data_registro'] = pd.to_datetime(df['data_registro'], errors='coerce')
        
        # Importação para o banco
        df.to_sql('operadoras', conn, if_exists='replace', index=False)
        print(f"Operadoras importadas: {len(df)} registros")
        return True
        
    except Exception as e:
        print(f"Erro na importação de operadoras: {str(e)}")
        raise

def import_demonstracoes(conn):
    try:
        base_dir = 'data/raw/demonstracoes'
        if not os.path.exists(base_dir):
            print("Aviso: Nenhum dado de demonstrações encontrado")
            return False
        
        total_imported = 0
        processed_files = 0
        
        # Processa todos os arquivos baixados
        for year in os.listdir(base_dir):
            year_dir = os.path.join(base_dir, year)
            if not os.path.isdir(year_dir):
                continue
                
            for quarter_file in os.listdir(year_dir):
                if not quarter_file.endswith('.zip'):
                    continue
                    
                quarter = quarter_file[:2]  # Pega '1T', '2T', etc
                quarter_dir = os.path.join(year_dir, quarter_file.replace('.zip', ''))
                
                # Processa cada arquivo CSV dentro do diretório do trimestre
                for root, _, files in os.walk(quarter_dir):
                    for file in files:
                        if file.lower().endswith('.csv'):
                            file_path = os.path.join(root, file)
                            try:
                                # Leitura do arquivo CSV
                                df = pd.read_csv(
                                    file_path, 
                                    sep=';', 
                                    encoding='iso-8859-1',
                                    dtype={'REG_ANS': str, 'CD_CONTA_CONTABIL': str},
                                    parse_dates=['DATA']
                                )
                                
                                # Padroniza colunas
                                df.columns = [col.lower() for col in df.columns]
                                
                                # Filtra apenas colunas relevantes
                                df = df[['data', 'reg_ans', 'cd_conta_contabil', 'descricao', 'vl_saldo_final']]
                                
                                # Renomeia colunas para o padrão do banco
                                df = df.rename(columns={
                                    'data': 'data',
                                    'reg_ans': 'registro_ans',
                                    'cd_conta_contabil': 'codigo_conta',
                                    'descricao': 'descricao',
                                    'vl_saldo_final': 'valor'
                                })
                                
                                # Adiciona metadados
                                df['ano'] = year
                                df['trimestre'] = quarter
                                
                                # Remove linhas com valores zerados ou inválidos
                                df = df[df['valor'] != 0]
                                df = df.dropna(subset=['valor'])
                                
                                # Importa para o banco
                                if not df.empty:
                                    df.to_sql(
                                        'demonstracoes', 
                                        conn, 
                                        if_exists='append', 
                                        index=False,
                                        method='multi',  # Insere em lotes para performance
                                        chunksize=1000
                                    )
                                    total_imported += len(df)
                                    processed_files += 1
                                    print(f"Processado {file}: {len(df)} registros")
                                
                            except Exception as e:
                                print(f"Aviso: Erro ao processar {file}: {str(e)}")
                                continue
        
        print(f"\nResumo Demonstrações Contábeis:")
        print(f"- Total de registros importados: {total_imported}")
        print(f"- Arquivos processados: {processed_files}")
        
        return total_imported > 0  # Retorna True se pelo menos um registro foi importado
        
    except Exception as e:
        print(f"Erro fatal na importação de demonstrações: {str(e)}")
        return False

def download_ans_data():
    """Função principal para download de todos os dados"""
    try:
        os.makedirs('data/raw', exist_ok=True)
        
        # 1. Baixar operadoras ativas
        operadoras_url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"
        print("\nBaixando operadoras ativas...")
        if not download_file_with_retry(operadoras_url, 'data/raw/operadoras_ativas.csv'):
            raise Exception("Falha ao baixar operadoras ativas")
        
        # 2. Baixar demonstrações contábeis
        downloaded_files = download_demonstracoes_contabeis()
        
        # 3. Extrair arquivos ZIP
        if downloaded_files:
            extrair_arquivos_zip(downloaded_files)
        
        print("\nDownloads concluídos com sucesso!")
        return True
        
    except Exception as e:
        print(f"\nErro geral no download: {str(e)}")
        # Cria arquivo vazio para permitir continuidade
        with open('data/raw/operadoras_ativas.csv', 'w') as f:
            f.write("Registro ANS;CNPJ;Razão Social\n")
        return False

if __name__ == "__main__":
    try:
        # 1. Baixar dados
        if not download_ans_data():
            print("Alguns downloads falharam")
        
        # 2. Configurar banco de dados
        conn = setup_database()
        
        # 3. Importar dados
        import_operadoras(conn)
        import_demonstracoes(conn)
        
        conn.close()
        sys.exit(0)
        
    except Exception as e:
        print(f"Erro fatal: {str(e)}")
        sys.exit(1)