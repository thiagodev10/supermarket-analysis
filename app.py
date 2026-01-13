import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard Estratégico - Análise de Vendas",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .section-header {
        font-size: 1.8rem;
        color: #0F4C75;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #0F4C75;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .negative-metric {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .positive-metric {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .insight-box {
        background-color: #F0F9FF;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #F59E0B;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">📈 Dashboard Estratégico - Análise de Vendas</h1>', unsafe_allow_html=True)
st.markdown("### Análises direcionadas para tomada de decisão executiva")

# Carregar dados
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('supermarket.csv')
        # Criar colunas auxiliares
        df['lucro_percentual'] = (df['lucro'] / df['vendas']) * 100
        df['desconto_percentual'] = (df['desconto'] / df['vendas']) * 100
        df['e_prejuizo'] = df['lucro'] < 0
        df['margem_bruta'] = df['margem'] * 100
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

df = load_data()

if df is not None:
    # ========== BARRA LATERAL ==========
    st.sidebar.header("⚙️ Configurações do Dashboard")
    
    # Filtro de data (simulado)
    st.sidebar.subheader("📅 Período de Análise")
    periodo = st.sidebar.selectbox(
        "Selecione o período:",
        ["Últimos 3 meses", "Últimos 6 meses", "Último ano", "Todos os dados"]
    )
    
    # Filtro por valor mínimo de vendas
    min_vendas = st.sidebar.slider(
        "Vendas mínimas (R$):",
        min_value=0,
        max_value=int(df['vendas'].max()),
        value=0,
        step=100
    )
    
    # Aplicar filtros
    df_filtrado = df[df['vendas'] >= min_vendas]
    
    # Métricas rápidas na sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Métricas Rápidas")
    st.sidebar.metric("Total Clientes", f"{len(df_filtrado):,}")
    st.sidebar.metric("Regiões", f"{df_filtrado['regiao'].nunique()}")
    st.sidebar.metric("Categorias", f"{df_filtrado['categoria'].nunique()}")
    
    # ========== QUESTÃO 1: CONTEXTO DO NEGÓCIO ==========
    st.markdown('<h2 class="section-header">1. 🏢 Contexto do Negócio</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Volume Total", f"R$ {df_filtrado['vendas'].sum():,.0f}", 
                 delta=f"{len(df_filtrado):,} transações")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="positive-metric">', unsafe_allow_html=True)
        lucro_total = df_filtrado['lucro'].sum()
        st.metric("Lucro Total", f"R$ {lucro_total:,.0f}", 
                 delta=f"{df_filtrado['lucro'].mean():,.0f} médio")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        margem_media = df_filtrado['margem'].mean() * 100
        st.metric("Margem Média", f"{margem_media:.1f}%", 
                 delta=f"{(df_filtrado['margem'] > 0).mean()*100:.1f}% positivas")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        ticket_medio = df_filtrado['vendas'].sum() / len(df_filtrado)
        st.metric("Ticket Médio", f"R$ {ticket_medio:,.1f}", 
                 delta=f"{df_filtrado['quantidade'].sum():,} itens")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Insights do contexto
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("**📊 Segmentos de Clientes:**")
        segmento_dist = df_filtrado['segmento'].value_counts()
        for seg, count in segmento_dist.items():
            percent = (count / len(df_filtrado)) * 100
            st.markdown(f"- **{seg}**: {count:,} ({percent:.1f}%)")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("**🌎 Presença Geográfica:**")
        regiao_dist = df_filtrado['regiao'].value_counts()
        for reg, count in regiao_dist.items():
            percent = (count / len(df_filtrado)) * 100
            vendas_reg = df_filtrado[df_filtrado['regiao'] == reg]['vendas'].sum()
            st.markdown(f"- **{reg}**: R$ {vendas_reg:,.0f} ({percent:.1f}% transações)")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== QUESTÃO 2: SAÚDE FINANCEIRA GERAL ==========
    st.markdown('<h2 class="section-header">2. 💰 Saúde Financeira Geral</h2>', unsafe_allow_html=True)
    
    # KPIs de saúde financeira
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Taxa de lucratividade
        transacoes_lucrativas = (df_filtrado['lucro'] > 0).sum()
        taxa_lucratividade = (transacoes_lucrativas / len(df_filtrado)) * 100
        st.metric("Taxa de Lucratividade", f"{taxa_lucratividade:.1f}%", 
                 delta=f"{transacoes_lucrativas:,} transações")
    
    with col2:
        # ROI médio
        roi_medio = (df_filtrado['lucro'].sum() / df_filtrado['vendas'].sum()) * 100
        st.metric("ROI Médio", f"{roi_medio:.1f}%")
    
    with col3:
        # Variabilidade do lucro
        cv_lucro = (df_filtrado['lucro'].std() / abs(df_filtrado['lucro'].mean())) * 100
        st.metric("Volatilidade do Lucro", f"{cv_lucro:.1f}%")
    
    with col4:
        # Eficiência operacional
        lucro_por_transacao = df_filtrado['lucro'].sum() / len(df_filtrado)
        st.metric("Lucro por Transação", f"R$ {lucro_por_transacao:,.2f}")
    
    # Análise de distribuição
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("**📈 Distribuição de Rentabilidade:**")
        
        # Categorizar por nível de rentabilidade
        df_filtrado['faixa_rentabilidade'] = pd.cut(
            df_filtrado['margem_bruta'],
            bins=[-1000, -50, -10, 0, 10, 30, 50, 1000],
            labels=['Crítico (<-50%)', 'Alto Prejuízo', 'Prejuízo Leve', 
                   'Margem Zero', 'Baixa Margem', 'Boa Margem', 'Excelente Margem']
        )
        
        dist_rent = df_filtrado['faixa_rentabilidade'].value_counts().sort_index()
        for faixa, count in dist_rent.items():
            percent = (count / len(df_filtrado)) * 100
            st.markdown(f"- **{faixa}**: {percent:.1f}% ({count:,} transações)")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**⚠️ Alertas Financeiros:**")
        
        # Identificar problemas
        transacoes_prejuizo = df_filtrado[df_filtrado['lucro'] < 0]
        if len(transacoes_prejuizo) > 0:
            prejuizo_total = abs(transacoes_prejuizo['lucro'].sum())
            percent_prejuizo = (len(transacoes_prejuizo) / len(df_filtrado)) * 100
            
            st.markdown(f"- **Transações com prejuízo**: {len(transacoes_prejuizo):,} ({percent_prejuizo:.1f}%)")
            st.markdown(f"- **Prejuízo acumulado**: R$ {prejuizo_total:,.0f}")
            st.markdown(f"- **Prejuízo médio**: R$ {transacoes_prejuizo['lucro'].mean():,.2f}")
            
            # Maior prejuízo único
            maior_prejuizo = transacoes_prejuizo['lucro'].min()
            st.markdown(f"- **Maior prejuízo**: R$ {maior_prejuizo:,.2f}")
        else:
            st.markdown("✅ Nenhuma transação com prejuízo identificada")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== QUESTÃO 3: ONDE O LUCRO ESTÁ SENDO GERADO ==========
    st.markdown('<h2 class="section-header">3. 📈 Fontes de Lucro</h2>', unsafe_allow_html=True)
    
    # Análise multidimensional do lucro
    tabs = st.tabs(["📦 Por Categoria", "👥 Por Segmento", "🌎 Por Região", "🏷️ Por Produto"])
    
    with tabs[0]:
        # Por Categoria
        lucro_categoria = df_filtrado.groupby('categoria').agg({
            'lucro': ['sum', 'mean', 'count'],
            'vendas': 'sum',
            'margem_bruta': 'mean'
        }).round(2)
        
        lucro_categoria.columns = ['Lucro Total', 'Lucro Médio', 'Qtd Transações', 
                                  'Vendas Totais', 'Margem Média %']
        lucro_categoria = lucro_categoria.sort_values('Lucro Total', ascending=False)
        
        st.dataframe(lucro_categoria.style.background_gradient(subset=['Lucro Total'], cmap='Greens'))
        
        # Insights
        top_categoria = lucro_categoria.index[0]
        st.markdown(f'<div class="success-box">', unsafe_allow_html=True)
        st.markdown(f"**🏆 Maior Gerador de Lucro:** **{top_categoria}**")
        st.markdown(f"- Contribui com R$ {lucro_categoria.iloc[0]['Lucro Total']:,.0f}")
        st.markdown(f"- Representa {(lucro_categoria.iloc[0]['Lucro Total']/lucro_total)*100:.1f}% do lucro total")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tabs[1]:
        # Por Segmento
        lucro_segmento = df_filtrado.groupby('segmento').agg({
            'lucro': ['sum', 'mean'],
            'vendas': 'sum',
            'margem_bruta': 'mean',
            'quantidade': 'sum'
        }).round(2)
        
        lucro_segmento.columns = ['Lucro Total', 'Lucro Médio', 'Vendas Totais', 
                                 'Margem Média %', 'Qtd Itens']
        lucro_segmento = lucro_segmento.sort_values('Lucro Total', ascending=False)
        
        st.dataframe(lucro_segmento.style.background_gradient(subset=['Lucro Total'], cmap='Blues'))
    
    with tabs[2]:
        # Por Região
        lucro_regiao = df_filtrado.groupby('regiao').agg({
            'lucro': ['sum', 'mean'],
            'vendas': 'sum',
            'margem_bruta': 'mean',
            'quantidade': 'sum'
        }).round(2)
        
        lucro_regiao.columns = ['Lucro Total', 'Lucro Médio', 'Vendas Totais', 
                               'Margem Média %', 'Qtd Itens']
        lucro_regiao = lucro_regiao.sort_values('Lucro Total', ascending=False)
        
        st.dataframe(lucro_regiao.style.background_gradient(subset=['Lucro Total'], cmap='Purples'))
    
    with tabs[3]:
        # Por Produto (Top 20)
        lucro_produto = df_filtrado.groupby('subcategoria').agg({
            'lucro': ['sum', 'mean'],
            'vendas': 'sum',
            'margem_bruta': 'mean',
            'quantidade': 'sum'
        }).round(2)
        
        lucro_produto.columns = ['Lucro Total', 'Lucro Médio', 'Vendas Totais', 
                                'Margem Média %', 'Qtd Itens']
        lucro_produto = lucro_produto.sort_values('Lucro Total', ascending=False).head(20)
        
        st.dataframe(lucro_produto.style.background_gradient(subset=['Lucro Total'], cmap='Oranges'))
    
    # ========== QUESTÃO 4: ONDE O PREJUÍZO ESTÁ ACONTECENDO ==========
    st.markdown('<h2 class="section-header">4. ⚠️ Pontos de Prejuízo</h2>', unsafe_allow_html=True)
    
    # Filtrar apenas transações com prejuízo
    df_prejuizo = df_filtrado[df_filtrado['lucro'] < 0].copy()
    
    if len(df_prejuizo) > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="negative-metric">', unsafe_allow_html=True)
            prejuizo_total = abs(df_prejuizo['lucro'].sum())
            st.metric("Prejuízo Total", f"R$ {prejuizo_total:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="negative-metric">', unsafe_allow_html=True)
            prejuizo_medio = df_prejuizo['lucro'].mean()
            st.metric("Prejuízo Médio", f"R$ {prejuizo_medio:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="negative-metric">', unsafe_allow_html=True)
            percent_prejuizo = (len(df_prejuizo) / len(df_filtrado)) * 100
            st.metric("Taxa de Prejuízo", f"{percent_prejuizo:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Análise detalhada do prejuízo
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Prejuízo por Categoria:**")
            prejuizo_cat = df_prejuizo.groupby('categoria')['lucro'].sum().sort_values()
            st.bar_chart(abs(prejuizo_cat))
            
            # Tabela detalhada
            st.dataframe(
                df_prejuizo.groupby('categoria').agg({
                    'lucro': ['sum', 'mean', 'count'],
                    'vendas': 'sum',
                    'margem_bruta': 'mean'
                }).round(2).sort_values(('lucro', 'sum'))
            )
        
        with col2:
            st.markdown("**🌎 Prejuízo por Região:**")
            prejuizo_reg = df_prejuizo.groupby('regiao')['lucro'].sum().sort_values()
            st.bar_chart(abs(prejuizo_reg))
            
            # Identificar piores produtos
            st.markdown("**📦 Top 10 Produtos com Maior Prejuízo:**")
            top_prejuizo_prod = df_prejuizo.groupby('subcategoria')['lucro'].sum().nsmallest(10)
            for produto, valor in top_prejuizo_prod.items():
                st.markdown(f"- **{produto}**: R$ {valor:,.2f}")
        
        # Análise de causa raiz
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**🔍 Análise de Causa Raiz:**")
        
        # Verificar relação com desconto
        if 'desconto' in df_prejuizo.columns and df_prejuizo['desconto'].sum() > 0:
            st.markdown("**Possível causa: Descontos agressivos**")
            st.markdown(f"- Desconto médio nas transações com prejuízo: {df_prejuizo['desconto'].mean():.2f}%")
            st.markdown(f"- Correlação desconto-prejuízo: {df_prejuizo['desconto'].corr(df_prejuizo['lucro']):.2f}")
        else:
            st.markdown("**Possível causa: Margens de produto insuficientes**")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.success("✅ Excelente! Não há transações com prejuízo no período analisado.")
    
    # ========== QUESTÃO 5: DESCONTOS: VILÃO OU ALIADO? ==========
    st.markdown('<h2 class="section-header">5. 🎯 Impacto dos Descontos</h2>', unsafe_allow_html=True)
    
    # Análise do impacto dos descontos
    df_com_desconto = df_filtrado[df_filtrado['desconto'] > 0]
    df_sem_desconto = df_filtrado[df_filtrado['desconto'] == 0]
    
    if len(df_com_desconto) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            percent_com_desconto = (len(df_com_desconto) / len(df_filtrado)) * 100
            st.metric("Transações c/ Desconto", f"{percent_com_desconto:.1f}%", 
                     delta=f"{len(df_com_desconto):,} transações")
        
        with col2:
            desconto_medio = df_com_desconto['desconto'].mean()
            st.metric("Desconto Médio", f"{desconto_medio:.1f}%")
        
        with col3:
            # Comparar margens
            margem_com_desconto = df_com_desconto['margem_bruta'].mean()
            margem_sem_desconto = df_sem_desconto['margem_bruta'].mean()
            diferenca_margem = margem_com_desconto - margem_sem_desconto
            st.metric("Margem c/ Desconto", f"{margem_com_desconto:.1f}%", 
                     delta=f"{diferenca_margem:+.1f}% vs sem desconto")
        
        with col4:
            # Volume gerado por desconto
            volume_com_desconto = df_com_desconto['vendas'].sum()
            volume_total = df_filtrado['vendas'].sum()
            percent_volume = (volume_com_desconto / volume_total) * 100
            st.metric("Volume c/ Desconto", f"{percent_volume:.1f}%", 
                     delta=f"R$ {volume_com_desconto:,.0f}")
        
        # Análise detalhada
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 Eficácia do Desconto por Categoria:**")
            
            eficacia_desconto = []
            for categoria in df_filtrado['categoria'].unique():
                df_cat = df_filtrado[df_filtrado['categoria'] == categoria]
                com_desc = df_cat[df_cat['desconto'] > 0]
                sem_desc = df_cat[df_cat['desconto'] == 0]
                
                if len(com_desc) > 0 and len(sem_desc) > 0:
                    lucro_medio_com = com_desc['lucro'].mean()
                    lucro_medio_sem = sem_desc['lucro'].mean()
                    diferenca = lucro_medio_com - lucro_medio_sem
                    
                    eficacia_desconto.append({
                        'Categoria': categoria,
                        'Lucro Médio c/ Desconto': lucro_medio_com,
                        'Lucro Médio s/ Desconto': lucro_medio_sem,
                        'Diferença': diferenca,
                        'Eficaz': 'SIM' if diferenca > 0 else 'NÃO'
                    })
            
            if eficacia_desconto:
                df_eficacia = pd.DataFrame(eficacia_desconto)
                st.dataframe(df_eficacia.sort_values('Diferença', ascending=False))
        
        with col2:
            st.markdown("**📊 Relação Desconto vs Lucro:**")
            
            # Criar faixas de desconto
            df_filtrado['faixa_desconto'] = pd.cut(
                df_filtrado['desconto_percentual'],
                bins=[0, 10, 20, 30, 40, 50, 100],
                labels=['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '>50%']
            )
            
            analise_faixa = df_filtrado.groupby('faixa_desconto').agg({
                'lucro': 'mean',
                'vendas': 'mean',
                'quantidade': 'mean',
                'margem_bruta': 'mean'
            }).round(2)
            
            st.dataframe(analise_faixa)
        
        # Conclusão sobre descontos
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("**🎯 Conclusão: Descontos são...**")
        
        # Determinar se desconto é vilão ou aliado
        lucro_total_com_desc = df_com_desconto['lucro'].sum()
        lucro_total_sem_desc = df_sem_desconto['lucro'].sum()
        
        if lucro_total_com_desc > 0 and (lucro_total_com_desc / len(df_com_desconto)) > (lucro_total_sem_desc / len(df_sem_desconto)):
            st.markdown("✅ **ALIADO** - Descontos estão gerando valor positivo")
            st.markdown(f"- Lucro por transação com desconto: R$ {df_com_desconto['lucro'].mean():.2f}")
            st.markdown(f"- Lucro por transação sem desconto: R$ {df_sem_desconto['lucro'].mean():.2f}")
        else:
            st.markdown("⚠️ **VILÃO** - Descontos estão destruindo valor")
            st.markdown(f"- Prejuízo por transação com desconto: R$ {df_com_desconto['lucro'].mean():.2f}")
            st.markdown(f"- Recomendação: Revisar política de descontos")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.info("ℹ️ Não há transações com desconto no período analisado")
    
    # ========== QUESTÃO 6: DIFERENÇAS REGIONAIS ==========
    st.markdown('<h2 class="section-header">6. 🌎 Análise Regional</h2>', unsafe_allow_html=True)
    
    # Comparativo regional
    analise_regional = df_filtrado.groupby('regiao').agg({
        'vendas': ['sum', 'mean', 'count'],
        'lucro': ['sum', 'mean'],
        'margem_bruta': 'mean',
        'quantidade': 'sum',
        'desconto': 'mean'
    }).round(2)
    
    analise_regional.columns = ['Vendas Totais', 'Ticket Médio', 'Qtd Transações',
                               'Lucro Total', 'Lucro Médio', 'Margem Média %',
                               'Qtd Itens', 'Desconto Médio %']
    
    # Adicionar rankings
    analise_regional['Rank Vendas'] = analise_regional['Vendas Totais'].rank(ascending=False, method='dense')
    analise_regional['Rank Lucro'] = analise_regional['Lucro Total'].rank(ascending=False, method='dense')
    analise_regional['Rank Margem'] = analise_regional['Margem Média %'].rank(ascending=False, method='dense')
    
    st.dataframe(
        analise_regional.sort_values('Vendas Totais', ascending=False)
        .style.background_gradient(subset=['Vendas Totais', 'Lucro Total'], cmap='YlOrRd')
    )
    
    # Insights regionais
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("**🏆 Melhor Desempenho Regional:**")
        
        melhor_lucro = analise_regional['Lucro Total'].idxmax()
        melhor_margem = analise_regional['Margem Média %'].idxmax()
        
        st.markdown(f"- **Maior lucro**: {melhor_lucro} (R$ {analise_regional.loc[melhor_lucro, 'Lucro Total']:,.0f})")
        st.markdown(f"- **Maior margem**: {melhor_margem} ({analise_regional.loc[melhor_margem, 'Margem Média %']:.1f}%)")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**📉 Oportunidades Regionais:**")
        
        pior_lucro = analise_regional['Lucro Total'].idxmin()
        pior_margem = analise_regional['Margem Média %'].idxmin()
        
        st.markdown(f"- **Menor lucro**: {pior_lucro} (R$ {analise_regional.loc[pior_lucro, 'Lucro Total']:,.0f})")
        st.markdown(f"- **Menor margem**: {pior_margem} ({analise_regional.loc[pior_margem, 'Margem Média %']:.1f}%)")
        
        # Sugestão de ação
        if analise_regional.loc[pior_lucro, 'Desconto Médio %'] > analise_regional['Desconto Médio %'].mean():
            st.markdown(f"🔍 **Sugestão**: Reduzir descontos em {pior_lucro} (atual: {analise_regional.loc[pior_lucro, 'Desconto Médio %']:.1f}%)")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== QUESTÃO 7: RECOMENDAÇÕES EXECUTIVAS ==========
    st.markdown('<h2 class="section-header">7. 🎯 Recomendações Executivas</h2>', unsafe_allow_html=True)
    
    # Gerar recomendações baseadas nos dados
    recomendacoes = []
    
    # 1. Baseado na saúde financeira
    if taxa_lucratividade < 70:
        recomendacoes.append({
            'Prioridade': 'ALTA',
            'Área': 'Saúde Financeira',
            'Recomendação': f'Aumentar taxa de lucratividade (atual: {taxa_lucratividade:.1f}%)',
            'Ação': 'Revisar preços e custos das transações não lucrativas'
        })
    
    # 2. Baseado no prejuízo
    if len(df_prejuizo) > 0:
        maior_causa_prejuizo = df_prejuizo.groupby('categoria')['lucro'].sum().idxmin()
        recomendacoes.append({
            'Prioridade': 'ALTA',
            'Área': 'Controle de Prejuízos',
            'Recomendação': f'Investigar prejuízos em {maior_causa_prejuizo}',
            'Ação': 'Auditar custos e preços desta categoria'
        })
    
    # 3. Baseado em descontos
    if 'desconto' in df_filtrado.columns:
        if df_com_desconto['margem_bruta'].mean() < df_sem_desconto['margem_bruta'].mean():
            recomendacoes.append({
                'Prioridade': 'MÉDIA',
                'Área': 'Gestão de Descontos',
                'Recomendação': 'Revisar política de descontos',
                'Ação': 'Implementar limites de desconto por categoria'
            })
    
    # 4. Baseado em diferenças regionais
    dif_lucro_regioes = analise_regional['Lucro Total'].max() - analise_regional['Lucro Total'].min()
    if dif_lucro_regioes > (analise_regional['Lucro Total'].mean() * 0.5):
        recomendacoes.append({
            'Prioridade': 'MÉDIA',
            'Área': 'Expansão Regional',
            'Recomendação': 'Reduzir disparidades regionais',
            'Ação': 'Replicar boas práticas da região de melhor desempenho'
        })
    
    # 5. Baseado em segmentos
    lucro_por_segmento = df_filtrado.groupby('segmento')['lucro'].sum()
    if len(lucro_por_segmento) > 1:
        segmento_mais_lucrativo = lucro_por_segmento.idxmax()
        segmento_menos_lucrativo = lucro_por_segmento.idxmin()
        
        if lucro_por_segmento[segmento_mais_lucrativo] > 2 * lucro_por_segmento[segmento_menos_lucrativo]:
            recomendacoes.append({
                'Prioridade': 'BAIXA',
                'Área': 'Desenvolvimento de Segmentos',
                'Recomendação': f'Focar em {segmento_mais_lucrativo}',
                'Ação': 'Aumentar investimento em marketing para este segmento'
            })
    
    # Exibir recomendações
    if recomendacoes:
        df_recomendacoes = pd.DataFrame(recomendacoes)
        
        # Colorir por prioridade
        def color_priority(val):
            if val == 'ALTA':
                return 'background-color: #FECACA; color: #991B1B'
            elif val == 'MÉDIA':
                return 'background-color: #FEF3C7; color: #92400E'
            else:
                return 'background-color: #D1FAE5; color: #065F46'
        
        st.dataframe(
            df_recomendacoes.style.applymap(color_priority, subset=['Prioridade'])
        )
    else:
        st.success("✅ Todas as métricas estão dentro dos parâmetros esperados!")
    
    # ========== DOWNLOAD DO RELATÓRIO ==========
    st.markdown("---")
    st.subheader("📥 Exportar Relatório")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Resumo executivo para download
        resumo_executivo = f"""
        RELATÓRIO EXECUTIVO - ANÁLISE DE VENDAS
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        
        1. CONTEXTO DO NEGÓCIO
        - Volume total: R$ {df_filtrado['vendas'].sum():,.0f}
        - Lucro total: R$ {df_filtrado['lucro'].sum():,.0f}
        - Margem média: {df_filtrado['margem_bruta'].mean():.1f}%
        
        2. SAÚDE FINANCEIRA
        - Taxa de lucratividade: {taxa_lucratividade:.1f}%
        - ROI médio: {roi_medio:.1f}%
        
        3. FONTES DE LUCRO
        - Maior categoria: {top_categoria if 'top_categoria' in locals() else 'N/A'}
        - Melhor região: {melhor_lucro if 'melhor_lucro' in locals() else 'N/A'}
        
        4. PONTOS DE ATENÇÃO
        - Transações com prejuízo: {len(df_prejuizo) if 'df_prejuizo' in locals() else 0}
        - Prejuízo total: R$ {prejuizo_total if 'prejuizo_total' in locals() else 0:,.0f}
        
        5. IMPACTO DOS DESCONTOS
        - {percent_com_desconto if 'percent_com_desconto' in locals() else 0:.1f}% das transações com desconto
        - Eficácia: {'POSITIVA' if 'lucro_total_com_desc' in locals() and lucro_total_com_desc > 0 else 'NEGATIVA'}
        
        """
        
        st.download_button(
            label="📄 Baixar Resumo Executivo (TXT)",
            data=resumo_executivo,
            file_name=f"resumo_executivo_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    
    with col2:
        # Dados completos
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Baixar Dados Completos (CSV)",
            data=csv,
            file_name=f"dados_analise_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

else:
    st.error("❌ Não foi possível carregar os dados. Verifique o arquivo CSV.")

# ========== RODAPÉ ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6B7280; font-size: 0.9rem; padding: 1rem;'>
    📊 Dashboard Estratégico | Desenvolvido com Streamlit | 
    Última atualização: {}
</div>
""".format(datetime.now().strftime('%d/%m/%Y %H:%M:%S')), unsafe_allow_html=True)
