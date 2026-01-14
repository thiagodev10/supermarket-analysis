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
# ANÁLISES EXECUTIVAS (ATUALIZADAS SEM MATPLOTLIB)
# ============================================================================

def analyze_financial_health(df):
    """1. Saúde Financeira Geral"""
    st.subheader("📈 Saúde Financeira Geral")
    
    total_sales = df['sales'].sum()
    total_profit = df['profit'].sum()
    avg_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0
    profit_margin_by_category = df.groupby('category').apply(
        lambda x: (x['profit'].sum() / x['sales'].sum()) * 100 if x['sales'].sum() > 0 else 0
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vendas Totais", format_brl(total_sales))
    with col2:
        profit_color = "normal" if total_profit > 0 else "inverse"
        st.metric("Lucro Total", format_brl(total_profit), delta_color=profit_color)
    with col3:
        margin_status = "normal" if avg_margin > 10 else "off" if avg_margin > 0 else "inverse"
        st.metric("Margem Média", f"{avg_margin:.1f}%", delta_color=margin_status)
    
    # Distribuição de Margem por Categoria
    fig = px.bar(
        x=profit_margin_by_category.index,
        y=profit_margin_by_category.values,
        title="Margem por Categoria (%)",
        labels={'x': 'Categoria', 'y': 'Margem %'},
        color=profit_margin_by_category.values,
        color_continuous_scale='RdYlGn',
        range_color=[-20, 40]
    )
    fig.add_hline(y=10, line_dash="dash", line_color="orange", annotation_text="Meta: 10%")
    fig.add_hline(y=0, line_dash="solid", line_color="red")
    st.plotly_chart(fig, use_container_width=True)
    
    return total_sales, total_profit, avg_margin

def analyze_profit_sources(df):
    """2. Onde o lucro está sendo gerado"""
    st.subheader("💰 Fontes de Lucro")
    
    profit_by_category = df.groupby('category')['profit'].sum().sort_values(ascending=False)
    profit_by_region = df.groupby('region')['profit'].sum().sort_values(ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top 3 Categorias Lucrativas:**")
        for i, (cat, profit) in enumerate(profit_by_category.head(3).items(), 1):
            margin = (df[df['category'] == cat]['profit'].sum() / 
                     df[df['category'] == cat]['sales'].sum()) * 100
            st.write(f"{i}. {cat}: {format_brl(profit)} (Margem: {margin:.1f}%)")
        
        fig = px.pie(
            values=profit_by_category.values,
            names=profit_by_category.index,
            title="Distribuição do Lucro por Categoria",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**Top 3 Regiões Lucrativas:**")
        for i, (reg, profit) in enumerate(profit_by_region.head(3).items(), 1):
            region_margin = (df[df['region'] == reg]['profit'].sum() / 
                           df[df['region'] == reg]['sales'].sum()) * 100
            st.write(f"{i}. {reg}: {format_brl(profit)} (Margem: {region_margin:.1f}%)")
        
        fig = px.bar(
            x=profit_by_region.index,
            y=profit_by_region.values,
            title="Lucro por Região",
            labels={'x': 'Região', 'y': 'Lucro'},
            color=profit_by_region.values,
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)

def analyze_loss_sources(df):
    """3. Onde o prejuízo está acontecendo"""
    st.subheader("⚠️ Pontos de Atenção (Prejuízos)")
    
    loss_categories = df.groupby('category').filter(lambda x: x['profit'].sum() < 0)
    loss_regions = df.groupby('region').filter(lambda x: x['profit'].sum() < 0)
    
    if not loss_categories.empty:
        st.warning(f"**Categorias com Prejuízo:** {len(loss_categories['category'].unique())}")
        loss_by_cat = loss_categories.groupby('category')['profit'].sum().sort_values()
        
        fig = px.bar(
            x=loss_by_cat.index,
            y=loss_by_cat.values,
            title="Prejuízo por Categoria",
            labels={'x': 'Categoria', 'y': 'Prejuízo'},
            color=loss_by_cat.values,
            color_continuous_scale='Reds_r'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if not loss_regions.empty:
        st.error(f"**Regiões com Prejuízo:** {len(loss_regions['region'].unique())}")
        loss_by_reg = loss_regions.groupby('region')['profit'].sum().sort_values()
        
        for reg, loss in loss_by_reg.items():
            st.write(f"• **{reg}**: Prejuízo de {format_brl(abs(loss))}")
            
            # Análise detalhada da região problemática
            reg_data = df[df['region'] == reg]
            problematic_cats = reg_data.groupby('category').filter(lambda x: x['profit'].sum() < 0)
            if not problematic_cats.empty:
                st.caption(f"  Categorias problemáticas em {reg}: {', '.join(problematic_cats['category'].unique())}")

def analyze_discount_impact(df):
    """4. Descontos: vilão ou aliado?"""
    st.subheader("🎯 Impacto dos Descontos")
    
    # Segmentar por faixa de desconto
    df['discount_range'] = pd.cut(df['discount'], 
                                  bins=[-1, 0, 10, 20, 30, 100], 
                                  labels=['0%', '1-10%', '11-20%', '21-30%', '>30%'])
    
    discount_analysis = df.groupby('discount_range').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    discount_analysis['margin'] = (discount_analysis['profit'] / discount_analysis['sales']) * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            discount_analysis,
            x='discount_range',
            y='margin',
            title="Margem por Faixa de Desconto",
            labels={'discount_range': 'Faixa de Desconto', 'margin': 'Margem %'},
            color='margin',
            color_continuous_scale='RdYlGn',
            range_color=[-20, 40]
        )
        fig.add_hline(y=0, line_dash="solid", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Análise de correlação
        correlation = df['discount'].corr(df['profit'])
        
        st.metric("Correlação Desconto-Lucro", f"{correlation:.2f}")
        
        if correlation < -0.3:
            st.error("⚠️ Descontos altos correlacionam com menor lucro")
        elif correlation > 0.1:
            st.success("✅ Descontos correlacionam com maior lucro")
        else:
            st.info("ℹ️ Descontos têm correlação neutra com lucro")
        
        # Scatter plot sem trendline (evita statsmodels)
        fig = px.scatter(
            df.sample(min(1000, len(df))),
            x='discount',
            y='profit',
            size='quantity',
            color='category',
            title="Relação Desconto vs Lucro",
            opacity=0.6
        )
        st.plotly_chart(fig, use_container_width=True)

def analyze_regional_differences(df):
    """5. Diferenças regionais (CORRIGIDO - sem matplotlib)"""
    st.subheader("🌍 Análise Regional Comparativa")
    
    regional_stats = df.groupby('region').agg({
        'sales': ['sum', 'mean'],
        'profit': ['sum', 'mean'],
        'quantity': 'sum',
        'discount': 'mean'
    }).round(2)
    
    regional_stats['margin'] = (regional_stats[('profit', 'sum')] / 
                               regional_stats[('sales', 'sum')]) * 100
    
    # Simplificar o MultiIndex para exibição
    regional_stats.columns = ['_'.join(col).strip() for col in regional_stats.columns.values]
    regional_stats = regional_stats.reset_index()
    
    # Renomear colunas para melhor legibilidade
    rename_dict = {
        'sales_sum': 'Vendas Totais',
        'sales_mean': 'Venda Média',
        'profit_sum': 'Lucro Total',
        'profit_mean': 'Lucro Médio',
        'quantity_sum': 'Quantidade Total',
        'discount_mean': 'Desconto Médio',
        'margin': 'Margem %'
    }
    
    display_df = regional_stats.rename(columns=rename_dict)
    
    # Criar visualização com Plotly em vez de estilo do pandas
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(display_df.columns),
            fill_color='lightblue',
            align='left',
            font=dict(size=12)
        ),
        cells=dict(
            values=[display_df[col] for col in display_df.columns],
            fill_color='white',
            align='left',
            # Formatar valores
            format=[
                None,  # Região
                [None, format_brl(x) for x in display_df['Vendas Totais']],  # Vendas
                [None, format_brl(x) for x in display_df['Venda Média']],  # Venda média
                [None, format_brl(x) for x in display_df['Lucro Total']],  # Lucro
                [None, format_brl(x) for x in display_df['Lucro Médio']],  # Lucro médio
                [None, '{:,.0f}'.format(x).replace(',', '.') for x in display_df['Quantidade Total']],  # Quantidade
                [None, '{:.1f}%'.format(x) for x in display_df['Desconto Médio']],  # Desconto
                [None, ['🟢 {:.1f}%'.format(x) if x > 10 else 
                        '🟡 {:.1f}%'.format(x) if x > 0 else 
                        '🔴 {:.1f}%'.format(x) for x in display_df['Margem %']]]  # Margem com cores
            ],
            font=dict(size=11)
        )
    )])
    
    fig.update_layout(title="Comparativo Regional", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Mapa de calor regional
    pivot_table = df.pivot_table(
        values='profit',
        index='category',
        columns='region',
        aggfunc='sum',
        fill_value=0
    )
    
    fig = px.imshow(
        pivot_table,
        title="Mapa de Calor: Lucro por Categoria x Região",
        labels=dict(x="Região", y="Categoria", color="Lucro"),
        color_continuous_scale='RdYlGn',
        aspect="auto"
    )
    st.plotly_chart(fig, use_container_width=True)

def generate_executive_recommendations(df, total_profit, avg_margin):
    """6. Recomendações Executivas"""
    st.subheader("🚀 Recomendações Estratégicas")
    
    recommendations = []
    
    # 1. Análise de margem
    if avg_margin < 10:
        recommendations.append({
            "priority": "ALTA",
            "title": "Melhorar Margem Geral",
            "description": f"A margem atual ({avg_margin:.1f}%) está abaixo do ideal (10%+).",
            "action": "Revisar estrutura de custos e precificação"
        })
    
    # 2. Categorias problemáticas
    loss_cats = df.groupby('category').filter(lambda x: x['profit'].sum() < 0)
    if not loss_cats.empty:
        cat_list = loss_cats['category'].unique()[:3]
        recommendations.append({
            "priority": "ALTA",
            "title": "Revisar Categorias Deficientes",
            "description": f"Categorias com prejuízo: {', '.join(cat_list)}",
            "action": "Considerar descontinuar ou reformular"
        })
    
    # 3. Descontos eficazes
    discount_analysis = df.groupby(pd.cut(df['discount'], [0, 10, 20, 100])).agg({
        'profit': 'sum',
        'quantity': 'sum'
    })
    if not discount_analysis.empty:
        optimal_discount = discount_analysis['profit'].idxmax()
        if isinstance(optimal_discount, pd.Interval):
            recommendations.append({
                "priority": "MÉDIA",
                "title": "Otimizar Estratégia de Descontos",
                "description": f"Faixa de desconto mais lucrativa: {optimal_discount.left:.0f}-{optimal_discount.right:.0f}%",
                "action": "Focar promoções nesta faixa"
            })
    
    # 4. Melhores performers
    top_category = df.groupby('category')['profit'].sum().idxmax()
    top_region = df.groupby('region')['profit'].sum().idxmax()
    
    recommendations.append({
        "priority": "BAIXA",
        "title": "Expandir Sucessos",
        "description": f"Melhor categoria: {top_category}, Melhor região: {top_region}",
        "action": "Replicar estratégias bem-sucedidas"
    })
    
    # 5. Se houver poucas recomendações, adicionar padrão
    if len(recommendations) < 3:
        recommendations.append({
            "priority": "MÉDIA",
            "title": "Monitorar Performance",
            "description": "Manter acompanhamento contínuo dos KPIs",
            "action": "Estabelecer reuniões semanais de análise"
        })
    
    # Exibir recomendações
    for i, rec in enumerate(recommendations, 1):
        with st.container():
            cols = st.columns([1, 5, 10])
            with cols[0]:
                color = {"ALTA": "🔴", "MÉDIA": "🟡", "BAIXA": "🟢"}[rec['priority']]
                st.write(f"**{color}**")
            with cols[1]:
                st.write(f"**{rec['priority']}**")
            with cols[2]:
                st.write(f"**{rec['title']}**")
                st.caption(rec['description'])
                st.write(f"*Ação sugerida:* {rec['action']}")
            st.divider()

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    st.title("📊 Dashboard Executivo - Supermercado")
    st.markdown("### Análise Estratégica para Acionistas")
    
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
    
    with st.spinner("Analisando dados..."):
        df = load_data(csv_path)
    
    # Verificar colunas obrigatórias
    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        st.error(f"Colunas faltantes: {', '.join(missing_cols)}")
        st.info("Colunas disponíveis: " + ", ".join(df.columns.tolist()))
        st.stop()
    
    # Filtros
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
    
    # Aplicar filtros
    filtered_df = df[
        df['region'].isin(selected_regions) & 
        df['category'].isin(selected_categories)
    ].copy()
    
    if filtered_df.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
        st.stop()
    
    # Menu de navegação
    st.sidebar.divider()
    st.sidebar.subheader("📋 Análises")
    
    analysis_options = {
        "1️⃣ Saúde Financeira Geral": "health",
        "2️⃣ Fontes de Lucro": "profit_sources",
        "3️⃣ Pontos de Prejuízo": "loss_sources",
        "4️⃣ Impacto dos Descontos": "discounts",
        "5️⃣ Diferenças Regionais": "regional",
        "6️⃣ Recomendações Executivas": "recommendations",
        "📈 Visualização Completa": "all"
    }
    
    selected_analysis = st.sidebar.radio(
        "Selecione a análise:",
        list(analysis_options.keys())
    )
    
    # Resumo executivo
    with st.expander("📋 Resumo Executivo", expanded=True):
        cols = st.columns(4)
        total_sales = filtered_df['sales'].sum()
        total_profit = filtered_df['profit'].sum()
        avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        with cols[0]:
            st.metric("Vendas Totais", format_brl(total_sales))
        with cols[1]:
            st.metric("Lucro Total", format_brl(total_profit))
        with cols[2]:
            st.metric("Margem Média", f"{avg_margin:.1f}%")
        with cols[3]:
            st.metric("Transações", f"{len(filtered_df):,}")
    
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
    if st.sidebar.checkbox("Mostrar dados brutos"):
        with st.expander("📊 Dados Filtrados"):
            st.dataframe(filtered_df, use_container_width=True)
    
    # Rodapé
    st.divider()
    st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.caption(f"📊 Dados analisados: {len(filtered_df):,} transações | {len(selected_regions)} regiões | {len(selected_categories)} categorias")

if __name__ == "__main__":
    main()
