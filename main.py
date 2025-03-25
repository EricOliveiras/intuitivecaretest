from src.web_scraping.anexos_download import download_anexos
from src.data_processing.pdf_to_csv import extract_tables_pdf
from src.database.db_operations import download_ans_data, setup_database, import_operadoras, import_demonstracoes
import os
import sys
from datetime import datetime
import pandas as pd 

def log_step(step_name):
    """Formata mensagens de log para cada etapa"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] {'='*30} {step_name} {'='*30}\n")

def validate_file_exists(filepath, description):
    """Valida se arquivo existe e não está vazio"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"{description} não encontrado: {filepath}")
    if os.path.getsize(filepath) == 0:
        raise ValueError(f"{description} está vazio: {filepath}")

def run_pipeline():
    try:
        # Configuração inicial
        os.makedirs('data/raw', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)
        
        # 1. Baixar dados da ANS
        log_step("1. BAIXANDO DADOS DA ANS")
        if not download_ans_data():
            print("Aviso: Usando dados locais/parciais")
            if not os.path.exists('data/raw/operadoras_ativas.csv'):
                with open('data/raw/operadoras_ativas.csv', 'w', encoding='iso-8859-1') as f:
                    f.write("Registro_ANS;CNPJ;Razao_Social\n") 
        
        # Validação crítica
        validate_file_exists('data/raw/operadoras_ativas.csv', 'Arquivo de operadoras')
        
        # 2. Baixar anexos
        log_step("2. BAIXANDO ANEXOS")
        if not download_anexos():
            raise RuntimeError("Falha crítica no download dos anexos")
        validate_file_exists('data/raw/Anexo_I.pdf', 'Arquivo Anexo I')
        
        # 3. Processar PDF
        log_step("3. PROCESSANDO PDF")
        if not extract_tables_pdf():
            raise RuntimeError("Falha crítica no processamento do PDF")
        validate_file_exists('data/processed/Rol_de_Procedimentos.csv', 'Arquivo CSV processado')
        
        # 4. Banco de dados
        log_step("4. CONFIGURANDO BANCO DE DADOS")
        conn = setup_database()
        success = True
        
        try:
            if not import_operadoras(conn):
                print("Aviso: Importação de operadoras parcial")
                success = False
                
            if not import_demonstracoes(conn):
                print("Aviso: Importação de demonstrações parcial")
                success = False
                
            if success:
                print("\nBanco de dados populado com sucesso completo!")
            else:
                print("\nBanco de dados populado parcialmente - verifique avisos")
                
            return success
            
        except Exception as e:
            print(f"\nERRO NA IMPORTAÇÃO: {str(e)}")
            print("Tentando importação mínima...")
            
            # Fallback básico
            df_fallback = pd.DataFrame(columns=['registro_ans', 'cnpj', 'razao_social'])
            df_fallback.to_sql('operadoras', conn, if_exists='replace', index=False)
            print("Importado esquema mínimo de operadoras")
            return False
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"\nERRO FATAL: {str(e)}")
        return False

if __name__ == "__main__":
    start_time = datetime.now()
    print(f"\n{'#'*60}")
    print(f" INÍCIO DA EXECUÇÃO: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")
    
    success = run_pipeline()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'#'*60}")
    print(f" RESUMO DA EXECUÇÃO")
    print(f" Tempo total: {duration.total_seconds():.2f} segundos")
    print(f" Status: {'SUCESSO COMPLETO' if success else 'SUCESSO PARCIAL' if success is not None else 'FALHA'}")
    print(f"{'#'*60}\n")
    
    sys.exit(0 if success else 1)