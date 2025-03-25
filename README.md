# 📊 Teste IntuitiveCare

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Projeto para coleta, processamento e análise de dados abertos da Agência Nacional de Saúde Suplementar (ANS).

## 📦 Pré-requisitos

- Python 3.8+
- Java Runtime Environment (para tabula-py)
- Git (opcional)

## 🛠️ Instalação

### 1. Clonar o repositório
```bash
git clone https://github.com/EricOliveiras/intuitivecaretest.git
cd intuitivecaretest
```
### 2. Configurar ambiente virtual
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/MacOS:
source venv/bin/activate
```
### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

## ▶️ Execução
```bash
python main.py
```

# 📡 API

Documentação completa para utilização da API Flask de consulta aos dados das operadoras de saúde.

## 🔌 Endpoints Disponíveis

### GET `/api/operadoras`
Consulta paginada de operadoras de planos de saúde

## 🛠️ Como Utilizar

### 1. Iniciar o Servidor Flask

```bash
python src/api/app.py
```
Servidor estará disponível em: http://localhost:5000

### 2. Consultas Básicas

Busca simples:
```bash
curl "http://localhost:5000/api/operadoras?q=saude"
```

```bash
curl "http://localhost:5000/api/operadoras?q=12345678"
```

```bash
curl "http://localhost:5000/api/operadoras"
```

### 3. Paginação

Paginação básica:

```bash
curl "http://localhost:5000/api/operadoras?page=2"
```
Customizar itens por página:
```bash
curl "http://localhost:5000/api/operadoras?page=1&per_page=5"
```
### 4. Filtros Avançados

Filtrar por modalidade:

```bash
curl "http://localhost:5000/api/operadoras?modalidade=Odontologico"
```
Combinação de filtros:
```bash
curl "http://localhost:5000/api/operadoras?q=saude&modalidade=Medicina&page=2"
```

## 📋 Parâmetros da API

| Parâmetro  | Tipo    | Descrição                          | Valor Padrão |
|------------|---------|------------------------------------|--------------|
| `q`        | string  | Termo de busca geral               | `""`         |
| `page`     | integer | Número da página                   | `1`          |
| `per_page` | integer | Itens por página                   | `10`         |
| `modalidade` | string | Filtrar por tipo de plano          | `null`       |

```json
{
  "data": [
    {
      "registro_ans": "12345",
      "cnpj": "12.345.678/0001-90",
      "razao_social": "OPERADORA SAUDE EXEMPLO LTDA",
      "nome_fantasia": "SAUDE EXEMPLO",
      "modalidade": "Medicina",
      "data_registro": "2020-01-15"
    }
  ],
  "pagination": {
    "total": 150,
    "pages": 15,
    "current_page": 1,
    "per_page": 10
  }
}
```

## 🚨 Códigos de Status
| Código | Descrição                     |
|--------|-------------------------------|
| 200    | ✅ Consulta realizada com sucesso |
| 400    | ❌ Parâmetros inválidos          |
| 404    | 🔍 Página não encontrada         |
| 500    | 💥 Erro interno do servidor      |