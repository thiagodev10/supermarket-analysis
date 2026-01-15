import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Dashboard Executivo - Supermercado", layout="wide", page_icon="📊")

# ============================================================================
# CONFIGURAÇÃO E CARREGAMENTO
# ============================================================================

REQUIRED = ["sales", "profit", "quantity", "category", "discount", "region"]
ALIASES = {
    "vendas": "sales", "sales": "sales",
    "lucro": "profit", "profit": "profit",
    "quantidade": "quantity", "quantity": "quantity",
    "categoria": "category", "category": "category",
    "desconto": "discount", "discount": "discount",
    "regiao": "region", "região": "region", "region": "region",
}

def _normalize_cols(cols):
    return (
        pd.Index(cols)
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace("\ufeff", "", regex=False)
        .str.replace(" ", "_", regex=False)
    )

@st.cache_data(show_spinner=False)
def load_data(csv_path: str) -> pd.DataFrame:
    encodings_to_try = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]
    seps_to_try = [",", ";", "\t", "|"]
    
    best_df = None
    for enc in encodings_to_try:
        for sep_val in seps_to_try:
            try:
                df_try = pd.read_csv(csv_path, encoding=enc, sep=sep_val, engine='python', on_bad_lines='skip')
                if df_try.shape[1] > 1:
                    df_try.columns = _normalize_cols(df_try.columns)
                    best_df = df_try
                    break
            except:
                continue
        if best_df is not None:
            break
    
    if best_df is None:
        st.error("Erro ao ler o CSV. Por favor, verifique o formato do arquivo.")
        st.stop()
    
    rename_map = {c: ALIASES[c] for c in best_df.columns if c in ALIASES}
    df_local = best_df.rename(columns=rename_map)
    
    for c in ["sales", "profit", "quantity", "discount"]:
        if c in df_local.columns:
            df_local[c] = pd.to_numeric(df_local[c], errors="coerce")
    
    for c in ["region", "category"]:
        if c in df_local.columns:
            df_local[c] = df_local[c].astype(str).str.strip()
    
    return df_local

def format_brl(val: float) -> str:
    if pd.isna(val):
        return "R$ 0"
    txt = "{:,.0f}".format(float(val))
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + txt

# ============================================================================
# ANÁLISES EXECUTIVAS - VERSÃO QUE MOSTRA A VERDADE
# ============================================================================

def analyze_financial_health(df):
    """1. Saúde Financeira Geral - VERSÃO HONESTA"""
    st.subheader("📈 Saúde Financeira REAL")
    
    total_sales = df['sales'].sum()
    total_profit = df['profit'].sum()
    avg_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0
    
    # Análise mais profunda
    profit_stats = df['profit'].describe()
    negative_profits = (df['profit'] < 0).sum()
    zero_profits = (df['profit'] == 0).sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vendas Totais", format_brl(total_sales))
    with col2:
        profit_color = "normal" if total_profit > 0 else "inverse"
        st.metric("Lucro Total", format_brl(total_profit), delta_color=profit_color)
    with col3:
        margin_status = "normal" if avg_margin > 10 else "off" if avg_margin > 0 else "inverse"
        st.metric("Margem Média", f"{avg_margin:.1f}%", delta_color=margin_status)
    with col4:
        st.metric("Transações Negativas", f"{negative_profits:,}", 
                 help="Número de transações com prejuízo")
    
    # Mostrar estatísticas REAIS
    with st.expander("📊 Estatísticas Detalhadas"):
        cols = st.columns(4)
        with cols[0]:
            st.metric("Lucro Mínimo", format_brl(profit_stats['min']))
        with cols[1]:
            st.metric("Lucro Máximo", format_brl(profit_stats['max']))
        with cols[2]:
            st.metric("Lucro Médio", format_brl(profit_stats['mean']))
        with cols[3]:
            st.metric("Transações Neutras", f"{zero_profits:,}")
    
    # Distribuição REAL de Margem por Categoria
    profit_margin_by_category = df.groupby('category').apply(
        lambda x: (x['profit'].sum() / x['sales'].sum()) * 100 if x['sales'].sum() > 0 else 0
    ).sort_values()
    
    # Colorir baseado na realidade
    colors = []
    for margin in profit_margin_by_category.values:
        if margin < 0:
            colors.append('red')
        elif margin < 5:
            colors.append('orange')
        elif margin < 10:
            colors.append('yellow')
        else:
            colors.append('green')
    
    fig = go.Figure(data=[
        go.Bar(
            x=profit_margin_by_category.index,
            y=profit_margin_by_category.values,
            marker_color=colors,
            text=[f"{x:.1f}%" for x in profit_margin_by_category.values],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Margem REAL por Categoria (%) - Ordenado do Pior ao Melhor",
        xaxis_title="Categoria",
        yaxis_title="Margem %",
        showlegend=False,
        height=500
    )
    
    # Adicionar linhas de referência
    fig.add_hline(y=10, line_dash="dash", line_color="green", annotation_text="Meta: 10%")
    fig.add_hline(y=5, line_dash="dash", line_color="orange", annotation_text="Mínimo Aceitável: 5%")
    fig.add_hline(y=0, line_dash="solid", line_color="red", annotation_text="Prejuízo")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análise crítica
    if avg_margin < 5:
        st.error(f"🚨 **ALERTA CRÍTICO:** Margem média de {avg_margin:.1f}% está abaixo do mínimo aceitável de 5%!")
    elif avg_margin < 10:
        st.warning(f"⚠️ **ATENÇÃO:** Margem média de {avg_margin:.1f}% está abaixo da meta de 10%")
    
    if negative_profits > len(df) * 0.1:  # Mais de 10% das transações com prejuízo
        st.error(f"🚨 **PROBLEMA GRAVE:** {negative_profits:,} transações ({negative_profits/len(df)*100:.1f}%) estão dando prejuízo!")
    
    return total_sales, total_profit, avg_margin

def analyze_profit_sources(df):
    """2. Onde o lucro está sendo gerado - VERSÃO HONESTA"""
    st.subheader("💰 Análise REAL das Fontes de Lucro")
    
    # Análise por categoria
    category_analysis = df.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'count'
    })
    category_analysis['margin'] = (category_analysis['profit'] / category_analysis['sales']) * 100
    category_analysis['profit_per_transaction'] = category_analysis['profit'] / category_analysis['quantity']
    
    # Análise por região
    region_analysis = df.groupby('region').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'count'
    })
    region_analysis['margin'] = (region_analysis['profit'] / region_analysis['sales']) * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Top e Bottom Categorias")
        
        # Top 3 categorias
        top_categories = category_analysis.nlargest(3, 'profit')
        st.write("**🏆 Top 3 Categorias (Lucro Absoluto):**")
        for i, (cat, row) in enumerate(top_categories.iterrows(), 1):
            st.write(f"{i}. **{cat}**: {format_brl(row['profit'])} (Margem: {row['margin']:.1f}%)")
        
        # Bottom 3 categorias
        bottom_categories = category_analysis.nsmallest(3, 'profit')
        st.write("**📉 Bottom 3 Categorias (Lucro Absoluto):**")
        for i, (cat, row) in enumerate(bottom_categories.iterrows(), 1):
            color = "🔴" if row['profit'] < 0 else "🟡" if row['margin'] < 5 else "🟠"
            st.write(f"{i}. {color} **{cat}**: {format_brl(row['profit'])} (Margem: {row['margin']:.1f}%)")
        
        # Gráfico de pizza mostrando concentração
        fig = px.pie(
            values=category_analysis['profit'].abs(),
            names=category_analysis.index,
            title="Concentração do Lucro por Categoria",
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("### 🌍 Análise Regional")
        
        # Top 3 regiões
        top_regions = region_analysis.nlargest(3, 'profit')
        st.write("**🏆 Top 3 Regiões:**")
        for i, (reg, row) in enumerate(top_regions.iterrows(), 1):
            st.write(f"{i}. **{reg}**: {format_brl(row['profit'])} (Margem: {row['margin']:.1f}%)")
        
        # Bottom 3 regiões
        bottom_regions = region_analysis.nsmallest(3, 'profit')
        st.write("**📉 Bottom 3 Regiões:**")
        for i, (reg, row) in enumerate(bottom_regions.iterrows(), 1):
            color = "🔴" if row['profit'] < 0 else "🟡" if row['margin'] < 5 else "🟠"
            st.write(f"{i}. {color} **{reg}**: {format_brl(row['profit'])} (Margem: {row['margin']:.1f}%)")
        
        # Gráfico de barras comparativo
        fig = px.bar(
            x=region_analysis.index,
            y=region_analysis['margin'],
            title="Margem por Região",
            labels={'x': 'Região', 'y': 'Margem %'},
            color=region_analysis['margin'],
            color_continuous_scale='RdYlGn',
            text=[f"{x:.1f}%" for x in region_analysis['margin']]
        )
        fig.update_traces(textposition='outside')
        fig.add_hline(y=0, line_dash="solid", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    
    # Análise de concentração de risco
    st.write("### ⚖️ Análise de Concentração e Risco")
    
    total_profit = category_analysis['profit'].sum()
    top_category_profit = top_categories['profit'].sum()
    concentration_ratio = (top_category_profit / total_profit * 100) if total_profit != 0 else 0
    
    cols = st.columns(3)
    with cols[0]:
        st.metric("Concentração Top 3", f"{concentration_ratio:.1f}%",
                 help="% do lucro total vindo das top 3 categorias")
    with cols[1]:
        risky_categories = len(category_analysis[category_analysis['margin'] < 5])
        total_categories = len(category_analysis)
        st.metric("Categorias de Risco", f"{risky_categories}/{total_categories}")
    with cols[2]:
        negative_categories = len(category_analysis[category_analysis['profit'] < 0])
        st.metric("Categorias Negativas", f"{negative_categories}/{total_categories}")

def analyze_loss_sources(df):
    """3. Análise REAL de Performance - Mostra a VERDADE"""
    st.subheader("🔍 Análise REAL de Performance")
    
    # ANÁLISE 1: Margens por categoria (VERDADEIRA)
    st.write("### 📊 Margens Reais por Categoria")
    
    category_analysis = df.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'count'
    }).reset_index()
    
    category_analysis['margin_pct'] = (category_analysis['profit'] / category_analysis['sales']) * 100
    category_analysis['profit_per_transaction'] = category_analysis['profit'] / category_analysis['quantity']
    
    # Ordenar por margem (do pior para o melhor)
    category_analysis = category_analysis.sort_values('margin_pct')
    
    # Criar gráfico HONESTO
    fig = px.bar(
        category_analysis,
        x='category',
        y='margin_pct',
        title="Margem REAL por Categoria (%) - Do Pior ao Melhor",
        labels={'category': 'Categoria', 'margin_pct': 'Margem %'},
        color='margin_pct',
        color_continuous_scale='RdYlGn',
        text=['{:.1f}%'.format(x) for x in category_analysis['margin_pct']]
    )
    fig.update_traces(textposition='outside')
    fig.add_hline(y=0, line_dash="solid", line_color="red", annotation_text="Linha de Equilíbrio")
    fig.add_hline(y=10, line_dash="dash", line_color="orange", annotation_text="Meta: 10%")
    st.plotly_chart(fig, use_container_width=True)
    
    # TABELA DETALHADA - A VERDADE NUMA E CRUA
    st.write("### 📈 Detalhamento por Categoria")
    
    # Preparar dados para tabela
    detailed_table = category_analysis.copy()
    detailed_table['sales'] = [format_brl(x) for x in detailed_table['sales']]
    detailed_table['profit'] = [format_brl(x) for x in detailed_table['profit']]
    detailed_table['profit_per_transaction'] = [format_brl(x) for x in detailed_table['profit_per_transaction']]
    detailed_table['margin_pct'] = ['{:.1f}%'.format(x) for x in detailed_table['margin_pct']]
    
    # Adicionar classificação REAL
    conditions = [
        category_analysis['margin_pct'] < 0,
        category_analysis['margin_pct'] < 5,
        category_analysis['margin_pct'] < 10,
        category_analysis['margin_pct'] >= 10
    ]
    choices = ['🔴 CRÍTICO', '🟡 ATENÇÃO', '🟠 BAIXO', '🟢 BOM']
    detailed_table['status'] = np.select(conditions, choices, default='⚪ INDEFINIDO')
    
    # Mostrar tabela
    st.dataframe(
        detailed_table[['category', 'sales', 'profit', 'margin_pct', 'profit_per_transaction', 'status']]
        .rename(columns={
            'category': 'Categoria',
            'sales': 'Vendas Totais',
            'profit': 'Lucro Total',
            'margin_pct': 'Margem %',
            'profit_per_transaction': 'Lucro/Transação',
            'status': 'Status'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # ANÁLISE 2: REGIÕES PROBLEMÁTICAS
    st.write("### 🌍 Análise Regional Detalhada")
    
    region_analysis = df.groupby('region').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'count'
    }).reset_index()
    
    region_analysis['margin_pct'] = (region_analysis['profit'] / region_analysis['sales']) * 100
    region_analysis = region_analysis.sort_values('margin_pct')
    
    # Gráfico regional
    fig2 = px.bar(
        region_analysis,
        x='region',
        y='margin_pct',
        title="Margem por Região (%) - REAL",
        labels={'region': 'Região', 'margin_pct': 'Margem %'},
        color='margin_pct',
        color_continuous_scale='RdYlGn',
        text=['{:.1f}%'.format(x) for x in region_analysis['margin_pct']]
    )
    fig2.update_traces(textposition='outside')
    fig2.add_hline(y=0, line_dash="solid", line_color="red")
    st.plotly_chart(fig2, use_container_width=True)
    
    # ANÁLISE 3: IDENTIFICAR VERDADEIROS PROBLEMAS
    st.write("### ⚠️ Pontos Críticos Identificados")
    
    # Categorias com margem negativa ou muito baixa
    problematic_categories = category_analysis[
        (category_analysis['margin_pct'] < 5) | 
        (category_analysis['profit'] < 0)
    ]
    
    if len(problematic_categories) > 0:
        st.error(f"🚨 **ALERTA:** {len(problematic_categories)} categorias com problemas!")
        
        for _, row in problematic_categories.iterrows():
            with st.expander(f"🔴 {row['category']} - Margem: {row['margin_pct']:.1f}%"):
                st.write(f"**Vendas:** {format_brl(row['sales'])}")
                st.write(f"**Lucro:** {format_brl(row['profit'])}")
                st.write(f"**Transações:** {row['quantity']:,}")
                st.write(f"**Lucro por transação:** {format_brl(row['profit_per_transaction'])}")
                
                # Análise mais profunda
                cat_data = df[df['category'] == row['category']]
                if len(cat_data) > 0:
                    worst_region = cat_data.groupby('region')['profit'].sum().idxmin()
                    worst_region_profit = cat_data.groupby('region')['profit'].sum().min()
                    
                    if worst_region_profit < 0:
                        st.warning(f"📌 **Pior região:** {worst_region} (Prejuízo: {format_brl(abs(worst_region_profit))})")
                    
                    # Top 3 produtos/transações com maior prejuízo
                    if 'profit' in cat_data.columns and len(cat_data) > 0:
                        worst_transactions = cat_data.nsmallest(3, 'profit')
                        st.write("**📉 Top 3 transações com maior prejuízo:**")
                        for idx, trans in worst_transactions.iterrows():
                            st.write(f"- Prejuízo: {format_brl(abs(trans['profit']))} | Região: {trans.get('region', 'N/A')}")
    else:
        st.success("✅ **ÓTIMO:** Nenhuma categoria crítica identificada!")
        
        # Mostrar as 3 piores categorias mesmo assim
        worst_3 = category_analysis.head(3)
        st.info(f"📉 **Categorias com menor margem:**")
        for _, row in worst_3.iterrows():
            st.write(f"• {row['category']}: {row['margin_pct']:.1f}% de margem")
    
    # ANÁLISE 4: DESCONTOS QUE PREJUDICAM
    st.write("### 💸 Impacto REAL dos Descontos")
    
    # Correlação descontos vs lucro por categoria
    correlation_by_category = []
    for cat in df['category'].unique():
        cat_data = df[df['category'] == cat]
        if len(cat_data) > 5:  # Precisa de dados suficientes
            corr = cat_data['discount'].corr(cat_data['profit'])
            correlation_by_category.append({
                'category': cat,
                'correlation': corr,
                'avg_discount': cat_data['discount'].mean(),
                'avg_profit': cat_data['profit'].mean()
            })
    
    if correlation_by_category:
        corr_df = pd.DataFrame(correlation_by_category)
        corr_df = corr_df.sort_values('correlation')
        
        # Identificar onde descontos estão matando o lucro
        harmful_discounts = corr_df[corr_df['correlation'] < -0.3]
        if len(harmful_discounts) > 0:
            st.warning("🚨 **CUIDADO:** Descontos estão prejudicando o lucro nestas categorias:")
            for _, row in harmful_discounts.iterrows():
                st.write(f"• {row['category']}: Correlação {row['correlation']:.2f} (Desconto médio: {row['avg_discount']:.1f}%)")
        else:
            st.info("✅ Descontos não estão correlacionados negativamente com lucro nas categorias")
    
    # RESUMO EXECUTIVO HONESTO
    st.write("### 📋 Resumo Executivo HONESTO")
    
    total_sales = df['sales'].sum()
    total_profit = df['profit'].sum()
    avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Margem Média REAL", f"{avg_margin:.1f}%")
    with col2:
        # Percentual de categorias com margem abaixo de 5%
        low_margin_cats = len(category_analysis[category_analysis['margin_pct'] < 5])
        total_cats = len(category_analysis)
        low_margin_pct = (low_margin_cats / total_cats * 100) if total_cats > 0 else 0
        st.metric("Categorias de Risco", f"{low_margin_pct:.0f}%")
    with col3:
        # Região com pior desempenho
        worst_region = region_analysis.iloc[0]
        st.metric("Pior Região", f"{worst_region['region']}", 
                 delta=f"{worst_region['margin_pct']:.1f}%")

def analyze_discount_impact(df):
    """4. Descontos: vilão ou aliado? - ANÁLISE REAL"""
    st.subheader("🎯 Impacto REAL dos Descontos")
    
    # Segmentar por faixa de desconto
    df['discount_range'] = pd.cut(df['discount'], 
                                  bins=[-1, 0, 10, 20, 30, 100], 
                                  labels=['0%', '1-10%', '11-20%', '21-30%', '>30%'])
    
    discount_analysis = df.groupby('discount_range').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'sum',
        'discount': 'count'
    }).reset_index()
    
    discount_analysis['margin'] = (discount_analysis['profit'] / discount_analysis['sales']) * 100
    discount_analysis['transactions'] = discount_analysis['discount']
    discount_analysis['avg_profit_per_transaction'] = discount_analysis['profit'] / discount_analysis['transactions']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de margem por faixa de desconto
        fig = px.bar(
            discount_analysis,
            x='discount_range',
            y='margin',
            title="Margem REAL por Faixa de Desconto",
            labels={'discount_range': 'Faixa de Desconto', 'margin': 'Margem %'},
            color='margin',
            color_continuous_scale='RdYlGn',
            text=['{:.1f}%'.format(x) for x in discount_analysis['margin']]
        )
        fig.update_traces(textposition='outside')
        fig.add_hline(y=0, line_dash="solid", line_color="red", annotation_text="Prejuízo")
        fig.add_hline(y=10, line_dash="dash", line_color="orange", annotation_text="Meta: 10%")
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise crítica
        negative_margin_ranges = discount_analysis[discount_analysis['margin'] < 0]
        if len(negative_margin_ranges) > 0:
            st.error(f"🚨 **ALERTA:** {len(negative_margin_ranges)} faixas de desconto estão dando prejuízo!")
            for _, row in negative_margin_ranges.iterrows():
                st.write(f"• {row['discount_range']}: Margem de {row['margin']:.1f}%")
    
    with col2:
        # Análise de correlação GLOBAL
        correlation = df['discount'].corr(df['profit'])
        
        st.metric("Correlação Global", f"{correlation:.2f}")
        
        if correlation < -0.5:
            st.error("🚨 **CRÍTICO:** Descontos têm forte correlação NEGATIVA com lucro!")
        elif correlation < -0.3:
            st.error("⚠️ **PERIGO:** Descontos correlacionam com menor lucro")
        elif correlation < 0:
            st.warning("📉 **ATENÇÃO:** Descontos tendem a reduzir lucro")
        elif correlation > 0.3:
            st.success("✅ **ÓTIMO:** Descontos correlacionam com maior lucro")
        elif correlation > 0.1:
            st.success("📈 **BOM:** Descontos ajudam no lucro")
        else:
            st.info("📊 **NEUTRO:** Descontos não têm correlação clara com lucro")
        
        # Scatter plot com amostra real
        sample_size = min(1000, len(df))
        fig = px.scatter(
            df.sample(sample_size, random_state=42),
            x='discount',
            y='profit',
            size='quantity',
            color='category',
            title="Relação REAL Desconto vs Lucro",
            opacity=0.7,
            hover_data=['region', 'sales']
        )
        
        # Adicionar linha de tendência manual (simples)
        if len(df) > 10:
            x = df['discount'].values[:sample_size]
            y = df['profit'].values[:sample_size]
            if not np.isnan(x).all() and not np.isnan(y).all():
                try:
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    fig.add_trace(go.Scatter(
                        x=x, 
                        y=p(x),
                        mode='lines',
                        name='Tendência',
                        line=dict(color='red', dash='dash')
                    ))
                except:
                    pass
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ANÁLISE DETALHADA POR CATEGORIA
    st.write("### 📊 Análise por Categoria")
    
    # Tabela de correlação por categoria
    category_correlations = []
    for cat in df['category'].unique():
        cat_data = df[df['category'] == cat]
        if len(cat_data) > 10:
            corr = cat_data['discount'].corr(cat_data['profit'])
            avg_discount = cat_data['discount'].mean()
            avg_profit = cat_data['profit'].mean()
            category_correlations.append({
                'Categoria': cat,
                'Correlação': corr,
                'Desconto Médio': f"{avg_discount:.1f}%",
                'Lucro Médio': format_brl(avg_profit),
                'Interpretação': "🟢 Boa" if corr > 0.3 else 
                               "🟡 OK" if corr > 0 else 
                               "🟠 Ruim" if corr > -0.3 else 
                               "🔴 Crítico"
            })
    
    if category_correlations:
        corr_df = pd.DataFrame(category_correlations).sort_values('Correlação')
        st.dataframe(corr_df, use_container_width=True, hide_index=True)
    
    # RECOMENDAÇÕES BASEADAS EM DADOS
    st.write("### 🎯 Recomendações Baseadas em Dados")
    
    # Encontrar faixa de desconto ideal
    optimal_range = discount_analysis.loc[discount_analysis['margin'].idxmax()]
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Faixa de desconto mais lucrativa:** {optimal_range['discount_range']}")
        st.write(f"Margem: {optimal_range['margin']:.1f}%")
        st.write(f"Lucro total: {format_brl(optimal_range['profit'])}")
        st.write(f"Transações: {optimal_range['transactions']:,}")
    
    with col2:
        # Faixa com pior desempenho
        worst_range = discount_analysis.loc[discount_analysis['margin'].idxmin()]
        st.warning(f"**Faixa de desconto problemática:** {worst_range['discount_range']}")
        st.write(f"Margem: {worst_range['margin']:.1f}%")
        st.write(f"Lucro total: {format_brl(worst_range['profit'])}")

def analyze_regional_differences(df):
    """5. Diferenças regionais - ANÁLISE REAL"""
    st.subheader("🌍 Análise Regional COMPARATIVA")
    
    regional_stats = df.groupby('region').agg({
        'sales': ['sum', 'mean', 'std'],
        'profit': ['sum', 'mean', 'std'],
        'quantity': ['sum', 'mean'],
        'discount': ['mean', 'std']
    }).round(2)
    
    regional_stats['margin'] = (regional_stats[('profit', 'sum')] / 
                               regional_stats[('sales', 'sum')]) * 100
    
    regional_stats['profitability_score'] = regional_stats['margin'] * np.log1p(regional_stats[('profit', 'sum')])
    
    # Simplificar o MultiIndex
    regional_stats.columns = ['_'.join(col).strip() for col in regional_stats.columns.values]
    regional_stats = regional_stats.reset_index()
    
    # Renomear colunas
    rename_dict = {
        'sales_sum': 'Vendas Totais',
        'sales_mean': 'Venda Média',
        'sales_std': 'Desvio Vendas',
        'profit_sum': 'Lucro Total',
        'profit_mean': 'Lucro Médio',
        'profit_std': 'Desvio Lucro',
        'quantity_sum': 'Quantidade Total',
        'quantity_mean': 'Quantidade Média',
        'discount_mean': 'Desconto Médio',
        'discount_std': 'Desvio Desconto',
        'margin': 'Margem %',
        'profitability_score': 'Score Rentabilidade'
    }
    
    display_df = regional_stats.rename(columns=rename_dict).copy()
    
    # Preparar valores formatados
    formatted_values = []
    for col in display_df.columns:
        if col == 'region':
            formatted_values.append(display_df[col].tolist())
        elif 'Vendas' in col or 'Lucro' in col:
            if 'Total' in col or 'Médio' in col:
                formatted_values.append([format_brl(x) for x in display_df[col]])
            else:
                formatted_values.append([f"{x:.0f}" for x in display_df[col]])
        elif 'Margem' in col:
            margin_cells = []
            for x in display_df[col]:
                if x > 15:
                    margin_cells.append(f'🟢 {x:.1f}%')
                elif x > 10:
                    margin_cells.append(f'🟡 {x:.1f}%')
                elif x > 5:
                    margin_cells.append(f'🟠 {x:.1f}%')
                elif x > 0:
                    margin_cells.append(f'🔴 {x:.1f}%')
                else:
                    margin_cells.append(f'💀 {x:.1f}%')
            formatted_values.append(margin_cells)
        elif 'Desconto' in col:
            formatted_values.append([f"{x:.1f}%" for x in display_df[col]])
        elif 'Score' in col:
            formatted_values.append([f"{x:.0f}" for x in display_df[col]])
        else:
            formatted_values.append(display_df[col].tolist())
    
    # Criar tabela interativa
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(display_df.columns),
            fill_color='lightblue',
            align='center',
            font=dict(size=11, color='black')
        ),
        cells=dict(
            values=formatted_values,
            fill_color='white',
            align='center',
            font=dict(size=10, color='black'),
            height=30
        )
    )])
    
    fig.update_layout(
        title="Comparativo Regional DETALHADO",
        height=450,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # MAPA DE CALOR DETALHADO
    st.write("### 🔥 Mapa de Calor: Lucro por Categoria x Região")
    
    pivot_table = df.pivot_table(
        values='profit',
        index='category',
        columns='region',
        aggfunc='sum',
        fill_value=0
    )
    
    fig = px.imshow(
        pivot_table,
        title="Mapa de Calor: Lucro por Categoria x Região (REAL)",
        labels=dict(x="Região", y="Categoria", color="Lucro"),
        color_continuous_scale='RdYlGn',
        aspect="auto",
        text_auto=True,
        width=800,
        height=500
    )
    
    # Adicionar anotações para valores negativos
    for i in range(len(pivot_table.index)):
        for j in range(len(pivot_table.columns)):
            value = pivot_table.iloc[i, j]
            if value < 0:
                fig.add_annotation(
                    x=j, y=i,
                    text="🔴",
                    showarrow=False,
                    font=dict(size=14)
                )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ANÁLISE DE DESEMPENHO RELATIVO
    st.write("### 📈 Ranking de Performance Regional")
    
    # Calcular scores normalizados
    for col in ['Vendas Totais', 'Lucro Total', 'Margem %', 'Desconto Médio']:
        if col in display_df.columns:
            if col == 'Margem %':
                display_df[f'{col}_score'] = display_df[col] / display_df[col].max() * 100
            else:
                # Extrair valores numéricos
                numeric_values = []
                for val in display_df[col]:
                    if isinstance(val, str) and 'R$' in val:
                        # Remover formatação
                        num = float(val.replace('R$', '').replace('.', '').replace(',', '.').strip())
                        numeric_values.append(num)
                    else:
                        numeric_values.append(float(val))
                
                if numeric_values:
                    max_val = max(numeric_values)
                    if max_val > 0:
                        display_df[f'{col}_score'] = [v/max_val*100 for v in numeric_values]
    
    # Calcular score composto
    score_cols = [col for col in display_df.columns if '_score' in col]
    if score_cols:
        display_df['Score Final'] = display_df[score_cols].mean(axis=1)
        display_df = display_df.sort_values('Score Final', ascending=False)
        
        # Gráfico de radar
        regions_to_show = min(5, len(display_df))
        fig = go.Figure()
        
        for i in range(regions_to_show):
            region_data = display_df.iloc[i]
            scores = [region_data[col] for col in score_cols]
            fig.add_trace(go.Scatterpolar(
                r=scores,
                theta=[col.replace('_score', '') for col in score_cols],
                fill='toself',
                name=region_data['region']
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title=f"Comparativo de Performance - Top {regions_to_show} Regiões"
        )
        st.plotly_chart(fig, use_container_width=True)

def generate_executive_recommendations(df, total_profit, avg_margin):
    """6. Recomendações Executivas - BASEADAS EM DADOS REAIS"""
    st.subheader("🚀 Recomendações Estratégicas BASEADAS EM DADOS")
    
    recommendations = []
    
    # ANÁLISE DE MARGEM
    if avg_margin < 5:
        recommendations.append({
            "priority": "🔴 ALTA",
            "title": "EMERGÊNCIA: Margem Crítica",
            "description": f"A margem média é de apenas {avg_margin:.1f}% (abaixo do mínimo de 5%). Risco de prejuízo operacional.",
            "action": "Revisão URGENTE de custos e precificação. Cortar despesas operacionais."
        })
    elif avg_margin < 10:
        recommendations.append({
            "priority": "🟡 MÉDIA",
            "title": "Margem Abaixo da Meta",
            "description": f"Margem de {avg_margin:.1f}% está abaixo da meta de 10%.",
            "action": "Otimizar mix de produtos. Revisar estratégia de preços."
        })
    
    # CATEGORIAS PROBLEMÁTICAS
    category_margins = df.groupby('category').apply(
        lambda x: (x['profit'].sum() / x['sales'].sum()) * 100 if x['sales'].sum() > 0 else 0
    )
    
    critical_categories = category_margins[category_margins < 0]
    risky_categories = category_margins[(category_margins >= 0) & (category_margins < 5)]
    
    if len(critical_categories) > 0:
        cat_list = ', '.join(critical_categories.index[:3])
        recommendations.append({
            "priority": "🔴 ALTA",
            "title": "Categorias com PREJUÍZO",
            "description": f"{len(critical_categories)} categorias estão dando prejuízo: {cat_list}",
            "action": "Considerar DESCONTINUAÇÃO imediata ou reformulação completa."
        })
    
    if len(risky_categories) > 0:
        cat_list = ', '.join(risky_categories.index[:3])
        recommendations.append({
            "priority": "🟡 MÉDIA",
            "title": "Categorias de Alto Risco",
            "description": f"{len(risky_categories)} categorias com margem abaixo de 5%: {cat_list}",
            "action": "Revisar custos e preços. Reduzir investimentos."
        })
    
    # DESCONTOS
    discount_correlation = df['discount'].corr(df['profit'])
    if discount_correlation < -0.3:
        recommendations.append({
            "priority": "🟡 MÉDIA",
            "title": "Descontos Prejudicando Lucro",
            "description": f"Correlação negativa forte ({discount_correlation:.2f}) entre descontos e lucro.",
            "action": "Reduzir descontos agressivos. Focar em promoções seletivas."
        })
    
    # CONCENTRAÇÃO DE RISCO
    category_profits = df.groupby('category')['profit'].sum()
    top_3_profit = category_profits.nlargest(3).sum()
    concentration = (top_3_profit / category_profits.sum()) * 100 if category_profits.sum() != 0 else 0
    
    if concentration > 70:
        recommendations.append({
            "priority": "🟠 MÉDIA-ALTA",
            "title": "Alta Concentração de Lucro",
            "description": f"{concentration:.0f}% do lucro vem de apenas 3 categorias.",
            "action": "Diversificar portfólio. Desenvolver novas categorias."
        })
    
    # REGIÕES
    region_margins = df.groupby('region').apply(
        lambda x: (x['profit'].sum() / x['sales'].sum()) * 100 if x['sales'].sum() > 0 else 0
    )
    worst_region = region_margins.idxmin()
    worst_margin = region_margins.min()
    
    if worst_margin < 0:
        recommendations.append({
            "priority": "🔴 ALTA",
            "title": f"Região {worst_region} em PREJUÍZO",
            "description": f"Margem de {worst_margin:.1f}%. Operação insustentável.",
            "action": "Intervenção IMEDIATA. Revisar operação ou considerar fechamento."
        })
    elif worst_margin < 3:
        recommendations.append({
            "priority": "🟡 MÉDIA",
            "title": f"Região {worst_region} com Baixa Rentabilidade",
            "description": f"Margem de apenas {worst_margin:.1f}%.",
            "action": "Plano de recuperação. Otimizar operações locais."
        })
    
    # OPORTUNIDADES
    best_category = category_margins.idxmax()
    best_margin = category_margins.max()
    
    if best_margin > 20:
        recommendations.append({
            "priority": "🟢 BAIXA",
            "title": f"OPORTUNIDADE: {best_category}",
            "description": f"Margem excepcional de {best_margin:.1f}%.",
            "action": "Expandir categoria. Aumentar investimento em marketing."
        })
    
    # Se poucas recomendações, adicionar gerais
    if len(recommendations) < 4:
        recommendations.extend([
            {
                "priority": "🟢 BAIXA",
                "title": "Monitoramento Contínuo",
                "description": "Manter acompanhamento rigoroso dos KPIs.",
                "action": "Implementar dashboard diário para equipe gerencial."
            },
            {
                "priority": "🟡 MÉDIA",
                "title": "Treinamento da Equipe",
                "description": "Capacitar equipe em gestão de margens.",
                "action": "Programa de treinamento sobre precificação e custos."
            }
        ])
    
    # Ordenar por prioridade
    priority_order = {"🔴 ALTA": 1, "🟡 MÉDIA": 2, "🟠 MÉDIA-ALTA": 3, "🟢 BAIXA": 4}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 5))
    
    # Exibir recomendações
    for i, rec in enumerate(recommendations, 1):
        with st.container():
            cols = st.columns([1, 3, 8])
            with cols[0]:
                st.markdown(f"### {i}")
            with cols[1]:
                st.markdown(f"**{rec['priority']}**")
            with cols[2]:
                st.markdown(f"#### {rec['title']}")
                st.markdown(f"*{rec['description']}*")
                st.markdown(f"**🎯 Ação Recomendada:** {rec['action']}")
            
            if i < len(recommendations):
                st.divider()

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    st.title("📊 Dashboard Executivo - Supermercado")
    st.markdown("### Análise Estratégica BASEADA EM DADOS REAIS")
    
    # Sidebar
    st.sidebar.header("⚙️ Configurações")
    
    csv_candidates = ["supermarket.csv", "Supermarket.csv", "dados.csv", "data.csv", "vendas.csv"]
    csv_path = None
    for fp in csv_candidates:
        if os.path.exists(fp):
            csv_path = fp
            break
    
    if csv_path is None:
        uploaded_file = st.sidebar.file_uploader("Carregar arquivo CSV", type=['csv'])
        if uploaded_file is not None:
            csv_path = uploaded_file.name
            with open(csv_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
        else:
            st.error("Por favor, carregue um arquivo CSV")
            st.info("Nomes suportados: supermarket.csv, dados.csv, vendas.csv")
            st.stop()
    
    with st.spinner("Analisando dados REALMENTE..."):
        df = load_data(csv_path)
    
    # Verificar colunas obrigatórias
    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        st.error(f"Colunas faltantes: {', '.join(missing_cols)}")
        st.info("Colunas disponíveis: " + ", ".join(df.columns.tolist()))
        st.stop()
    
    # ANÁLISE RÁPIDA DOS DADOS REAIS
    st.sidebar.divider()
    st.sidebar.subheader("🔍 Diagnóstico Rápido")
    
    # Estatísticas básicas
    total_profit = df['profit'].sum()
    negative_count = (df['profit'] < 0).sum()
    negative_pct = (negative_count / len(df)) * 100 if len(df) > 0 else 0
    
    st.sidebar.metric("Registros", f"{len(df):,}")
    st.sidebar.metric("Prejuízos", f"{negative_count:,}", 
                     delta=f"{negative_pct:.1f}%", delta_color="inverse")
    st.sidebar.metric("Lucro Total", format_brl(total_profit))
    
    if negative_count > 0:
        st.sidebar.error(f"{negative_pct:.1f}% das transações com prejuízo!")
    
    # Filtros
    st.sidebar.divider()
    st.sidebar.subheader("🔍 Filtros")
    
    all_regions = sorted(df['region'].dropna().unique().tolist())
    all_categories = sorted(df['category'].dropna().unique().tolist())
    
    selected_regions = st.sidebar.multiselect(
        "Regiões",
        options=all_regions,
        default=all_regions
    )
    
    selected_categories = st.sidebar.multiselect(
        "Categorias",
        options=all_categories,
        default=all_categories
    )
    
    # Filtro de margem
    min_margin = st.sidebar.slider(
        "Filtrar margem mínima (%)",
        min_value=-50.0,
        max_value=50.0,
        value=-50.0,
        step=5.0
    )
    
    # Aplicar filtros
    filtered_df = df[
        df['region'].isin(selected_regions) & 
        df['category'].isin(selected_categories)
    ].copy()
    
    # Calcular margem por transação para filtro
    if len(filtered_df) > 0:
        filtered_df = filtered_df[
            (filtered_df['profit'] / filtered_df['sales'] * 100) >= min_margin
        ]
    
    if filtered_df.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
        st.stop()
    
    # Menu de navegação
    st.sidebar.divider()
    st.sidebar.subheader("📋 Análises")
    
    analysis_options = {
        "1️⃣ Saúde Financeira REAL": "health",
        "2️⃣ Fontes de Lucro REAIS": "profit_sources",
        "3️⃣ Análise REAL de Performance": "loss_sources",
        "4️⃣ Impacto REAL dos Descontos": "discounts",
        "5️⃣ Diferenças Regionais REAIS": "regional",
        "6️⃣ Recomendações BASEADAS EM DADOS": "recommendations",
        "📈 VISUALIZAÇÃO COMPLETA": "all"
    }
    
    selected_analysis = st.sidebar.radio(
        "Selecione a análise:",
        list(analysis_options.keys())
    )
    
    # Resumo executivo HONESTO
    with st.expander("📋 Resumo Executivo HONESTO", expanded=True):
        cols = st.columns(4)
        total_sales = filtered_df['sales'].sum()
        total_profit = filtered_df['profit'].sum()
        avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
        negative_transactions = (filtered_df['profit'] < 0).sum()
        
        with cols[0]:
            st.metric("Vendas Totais", format_brl(total_sales))
        with cols[1]:
            color = "normal" if total_profit > 0 else "inverse"
            st.metric("Lucro Total", format_brl(total_profit), delta_color=color)
        with cols[2]:
            status = "normal" if avg_margin > 10 else "off" if avg_margin > 5 else "inverse"
            st.metric("Margem REAL", f"{avg_margin:.1f}%", delta_color=status)
        with cols[3]:
            st.metric("Transações Negativas", f"{negative_transactions:,}",
                     delta=f"{negative_transactions/len(filtered_df)*100:.1f}%",
                     delta_color="inverse" if negative_transactions > 0 else "normal")
        
        # Alerta se houver problemas
        if negative_transactions > len(filtered_df) * 0.2:  # 20% negativas
            st.error(f"🚨 **ALERTA CRÍTICO:** {negative_transactions/len(filtered_df)*100:.1f}% das transações estão com prejuízo!")
        elif negative_transactions > 0:
            st.warning(f"⚠️ **ATENÇÃO:** {negative_transactions} transações estão com prejuízo")
    
    # Executar análises selecionadas
    analysis_key = analysis_options[selected_analysis]
    
    if analysis_key in ["health", "all"]:
        analyze_financial_health(filtered_df)
    
    if analysis_key in ["profit_sources", "all"]:
        analyze_profit_sources(filtered_df)
    
    if analysis_key in ["loss_sources", "all"]:
        analyze_loss_sources(filtered_df)
    
    if analysis_key in ["discounts", "all"]:
        analyze_discount_impact(filtered_df)
    
    if analysis_key in ["regional", "all"]:
        analyze_regional_differences(filtered_df)
    
    if analysis_key in ["recommendations", "all"]:
        generate_executive_recommendations(filtered_df, total_profit, avg_margin)
    
    # Dados brutos (opcional)
    st.sidebar.divider()
    if st.sidebar.checkbox("Mostrar dados brutos (CRÍTICO)"):
        with st.expander("📊 Dados Filtrados - VERDADE CRUA"):
            st.dataframe(filtered_df, use_container_width=True)
            
            # Estatísticas detalhadas
            st.write("**📈 Estatísticas Detalhadas:**")
            cols = st.columns(5)
            stats = filtered_df['profit'].describe()
            with cols[0]:
                st.metric("Mínimo", format_brl(stats['min']))
            with cols[1]:
                st.metric("Máximo", format_brl(stats['max']))
            with cols[2]:
                st.metric("Média", format_brl(stats['mean']))
            with cols[3]:
                st.metric("Mediana", format_brl(stats['50%']))
            with cols[4]:
                st.metric("Desvio Padrão", format_brl(stats['std']))
    
    # Rodapé
    st.divider()
    st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.caption(f"📊 Dados analisados: {len(filtered_df):,} transações | {len(selected_regions)} regiões | {len(selected_categories)} categorias")
  

if __name__ == "__main__":
    main()
