# Dashboard no Power BI

Guia para montar o painel a partir dos arquivos gerados em `dados/tratados/`.

## 1. Importar os dados

Em **Obter dados > Texto/CSV**, importe os três arquivos. Como eles usam `;` como separador e `,` como decimal, o Power BI em português reconhece os tipos sem ajustes. Confira só se a coluna `data` ficou como **Data**.

| Tabela | Conteúdo |
|---|---|
| `cotacao_diaria` | Uma linha por dia útil: cotação, variação diária e médias móveis |
| `resumo_mensal` | Uma linha por mês: abertura, fechamento, média, mínima, máxima, variação e volatilidade |
| `dim_calendario` | Todas as datas dos anos cobertos, com ano, trimestre, mês e dia da semana |

## 2. Modelo de dados

- Relacione `dim_calendario[data]` (1) → `cotacao_diaria[data]` (*).
- Marque `dim_calendario` como **tabela de datas** (Ferramentas da tabela > Marcar como tabela de datas).
- Classifique `mes_nome` pela coluna `mes_numero`, para os meses não aparecerem em ordem alfabética.
- Use sempre as colunas de `dim_calendario` nos eixos e filtros.

## 3. Medidas DAX

```dax
Cotação Média = AVERAGE ( cotacao_diaria[cotacao] )

Cotação Máxima = MAX ( cotacao_diaria[cotacao] )

Cotação Mínima = MIN ( cotacao_diaria[cotacao] )

-- Última cotação disponível dentro do filtro atual
Última Cotação =
LASTNONBLANKVALUE ( dim_calendario[data], MAX ( cotacao_diaria[cotacao] ) )

Primeira Cotação =
FIRSTNONBLANKVALUE ( dim_calendario[data], MAX ( cotacao_diaria[cotacao] ) )

-- Quanto o dólar subiu ou caiu no período selecionado
Variação % no Período =
DIVIDE ( [Última Cotação] - [Primeira Cotação], [Primeira Cotação] )

Cotação Média Ano Anterior =
CALCULATE ( [Cotação Média], SAMEPERIODLASTYEAR ( dim_calendario[data] ) )

Variação % vs Ano Anterior =
DIVIDE ( [Cotação Média] - [Cotação Média Ano Anterior], [Cotação Média Ano Anterior] )

Dias de Alta =
CALCULATE ( COUNTROWS ( cotacao_diaria ), cotacao_diaria[variacao_diaria_pct] > 0 )

% Dias de Alta =
DIVIDE ( [Dias de Alta], COUNTROWS ( cotacao_diaria ) )

-- Desvio padrão da variação diária: quanto maior, mais instável o período
Volatilidade Diária = STDEV.S ( cotacao_diaria[variacao_diaria_pct] )
```

Formate `Variação % no Período`, `Variação % vs Ano Anterior` e `% Dias de Alta` como **Porcentagem**, e as cotações como **Moeda (R$)** com 4 casas decimais.

## 4. Layout sugerido

1. **Linha de cartões no topo:** Última Cotação, Variação % no Período, Cotação Máxima e Volatilidade Diária.
2. **Gráfico de linhas:** `dim_calendario[data]` no eixo, com `cotacao` e `media_movel_63d`.
3. **Gráfico de colunas:** variação mensal (`resumo_mensal[variacao_mes_pct]` por mês), com formatação condicional para alta e queda.
4. **Matriz ano × mês:** `Cotação Média` com escala de cor, para ver de relance os períodos de dólar alto.
5. **Segmentação de dados:** ano e trimestre, alinhados acima dos visuais.

Depois de montar, salve o arquivo como `powerbi/dashboard_dolar.pbix` e coloque um print em `imagens/dashboard.png` para ele aparecer no README.
