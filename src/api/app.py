from flask import Flask, request, jsonify
import pandas as pd
import sqlite3
import os
from functools import lru_cache

app = Flask(__name__)

# Configurações
DATABASE_PATH = 'data/processed/ans.db'
CACHE_TIMEOUT = 300  # 5 minutos

@lru_cache(maxsize=128)
def load_operadoras():
    """Carrega dados das operadoras com cache"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        query = """
        SELECT registro_ans, cnpj, razao_social, nome_fantasia, modalidade 
        FROM operadoras
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro ao carregar operadoras: {str(e)}")
        return []

@app.route('/api/operadoras', methods=['GET'])
def search_operadoras():
    """Endpoint para busca de operadoras com tratamento seguro de tipos"""
    try:
        # Parâmetros da busca
        search_term = request.args.get('q', '').lower()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Carrega dados (com cache)
        operadoras = load_operadoras()
        
        # Função auxiliar para conversão segura
        def safe_to_str(value):
            return str(value).lower() if value is not None else ''
        
        # Filtra resultados de forma segura
        if search_term:
            results = []
            for op in operadoras:
                matches = (
                    search_term in safe_to_str(op.get('registro_ans')) or
                    search_term in safe_to_str(op.get('razao_social')) or
                    search_term in safe_to_str(op.get('cnpj')) or
                    search_term in safe_to_str(op.get('nome_fantasia')))
                if matches:
                    results.append(op)
        else:
            results = operadoras
        
        # Paginação
        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = results[start:end]
        
        return jsonify({
            'data': paginated_results,
            'meta': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        app.logger.error(f"Erro na busca: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erro interno no servidor',
            'message': 'Não foi possível processar a requisição'
        }), 500

@app.route('/api/operadoras/<registro_ans>', methods=['GET'])
def get_operadora(registro_ans):
    """Endpoint para detalhes de uma operadora específica"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Busca operadora
        operadora = pd.read_sql(
            "SELECT * FROM operadoras WHERE registro_ans = ?", 
            conn, 
            params=(registro_ans,)
        ).to_dict('records')
        
        if not operadora:
            return jsonify({'message': 'Operadora não encontrada'}), 404
        
        # Busca demonstrações contábeis
        demonstracoes = pd.read_sql(
            """
            SELECT data, descricao, valor 
            FROM demonstracoes 
            WHERE registro_ans = ?
            ORDER BY data DESC
            """,
            conn,
            params=(registro_ans,)
        ).to_dict('records')
        
        conn.close()
        
        return jsonify({
            'operadora': operadora[0],
            'demonstracoes': demonstracoes
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Erro ao buscar operadora'
        }), 500

if __name__ == '__main__':
    # Garante que o diretório existe
    os.makedirs('data/processed', exist_ok=True)
    
    # Configurações do Flask
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSON_AS_ASCII'] = False
    
    app.run(host='0.0.0.0', port=5000, debug=True)