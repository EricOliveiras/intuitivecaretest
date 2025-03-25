-- QUERIES ANALÍTICAS PARA DEMONSTRAÇÕES CONTÁBEIS

-- 1. Query para as 10 operadoras com maiores despesas no último trimestre
WITH ultimo_trimestre AS (
    SELECT MAX(data) as data_final 
    FROM demonstracoes
)
SELECT 
    o.razao_social,
    SUM(d.valor) as total_despesas,
    COUNT(d.id) as quantidade_registros,
    MAX(d.data) as data_mais_recente
FROM 
    demonstracoes d
JOIN 
    operadoras o ON d.registro_ans = o.registro_ans
WHERE 
    d.descricao LIKE '%EVENTOS/%SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR%'
    AND d.data >= DATE_SUB((SELECT data_final FROM ultimo_trimestre), INTERVAL 3 MONTH)
GROUP BY 
    o.razao_social
ORDER BY 
    total_despesas DESC
LIMIT 10;

-- 2. Query para as 10 operadoras com maiores despesas no último ano
WITH ultimo_ano AS (
    SELECT MAX(data) as data_final 
    FROM demonstracoes
)
SELECT 
    o.razao_social,
    SUM(d.valor) as total_despesas,
    COUNT(d.id) as quantidade_registros,
    MIN(d.data) as data_mais_antiga,
    MAX(d.data) as data_mais_recente
FROM 
    demonstracoes d
JOIN 
    operadoras o ON d.registro_ans = o.registro_ans
WHERE 
    d.descricao LIKE '%EVENTOS/%SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR%'
    AND d.data >= DATE_SUB((SELECT data_final FROM ultimo_ano), INTERVAL 1 YEAR)
GROUP BY 
    o.razao_social
ORDER BY 
    total_despesas DESC
LIMIT 10;