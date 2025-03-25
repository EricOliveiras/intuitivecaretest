import tabula
import pandas as pd
import zipfile
import os
from datetime import datetime

def extract_tables_pdf():
    """
    Extrai tabelas do PDF do Anexo I e gera arquivos CSV e ZIP
    Retorna:
        str: Nome do arquivo ZIP gerado ou None em caso de falha
    """
    try:
        # Configurações
        pdf_path = "data/raw/Anexo_I.pdf"
        csv_path = "data/processed/Rol_de_Procedimentos.csv"
        zip_name = "Teste_Eric_Nascimento.zip"  

        # Verificação do arquivo
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Arquivo {pdf_path} não encontrado")

        # Extração das tabelas
        print(f"{datetime.now().strftime('%H:%M:%S')} - Extraindo tabelas do PDF...")
        tables = tabula.read_pdf(
            pdf_path,
            pages='all',
            multiple_tables=True,
            lattice=True,
            pandas_options={'header': None},
            silent=True
        )

        if not tables:
            raise ValueError("Nenhuma tabela encontrada no PDF")

        # Processamento dos dados
        df = pd.concat(tables).reset_index(drop=True)
        
        # Substituição das abreviações 
        df = df.replace({
            'OD': 'Odontológico',
            'AMB': 'Ambulatorial'
        })

        # Geração do CSV (item 2.2)
        os.makedirs('data/processed', exist_ok=True)
        df.to_csv(csv_path, sep=';', index=False, encoding='utf-8-sig')
        print(f"{datetime.now().strftime('%H:%M:%S')} - CSV gerado em {csv_path}")

        # Criação do ZIP (itens 1.3 e 2.3)
        with zipfile.ZipFile(zip_name, 'w') as zipf:
            zipf.write(csv_path, os.path.basename(csv_path))
        print(f"{datetime.now().strftime('%H:%M:%S')} - Arquivo ZIP criado: {zip_name}")

        return True

    except Exception as e:
        print(f"Erro na extração de tabelas: {str(e)}")
        return False