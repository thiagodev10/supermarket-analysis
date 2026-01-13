import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Supermercado",
    page_icon="🛒",
    layout="wide"
)

# Título com estilo
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📊 Dashboard de Análise de Vendas</h1>', unsafe_allow_html=True)

# Carregar dados com verificação
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('supermarket.csv')
        
        # Verificar colunas necessárias
        required_columns = ['vendas', 'lucro', 'margem', 'quantidade', 'categoria', 'segmento']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Colunas ausentes no CSV: {missing_columns}")
            return None
            
        return df
    except FileNotFoundError:
        st.error("❌ Arquivo 'supermarket.csv' não encontrado!")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return None

# Carregar dados
df = load_data()

if df is not None:
    # ========== SIDEBAR ==========
    st.sidebar.header("⚙️ Configurações")
    
    # Filtros
    st.sidebar.subheader("🔍 Filtros")
    
    # Filtro por região
    regioes = sorted(df['regiao'].unique().tolist())
    regiao_selecionada = st.sidebar.multiselect(
        "Selecione as Regiões:",
        options=regioes,
        default=regioes
    )
    
    # Filtro por categoria
    categorias = sorted(df['categoria'].unique().tolist())
    categoria_selecionada = st.sidebar.multiselect(
        "Selecione as Categorias:",
        options=categorias,
        default=categorias
    )
    
    # Filtro por segmento
    segmentos = sorted(df['segmento'].unique().tolist())
    segmento_selecionado = st.sidebar.multiselect(
        "Selecione os Segmentos:",
        options=segmentos,
        default=segmentos
    )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if regiao_selecionada:
        df_filtrado = df_filtrado[df_filtrado['regiao'].isin(regiao_selecionada)]
    
    if categoria_selecionada:
        df_filtrado = df_filtrado[df_filtrado['categoria'].isin(categoria_selecionada)]
    
    if segmento_selecionado:
        df_filtrado = df_filtrado[df_filtrado['segmento'].isin(segmento_selecionado)]
    
    # ========== MÉTRICAS PRINCIPAIS ==========
    st.markdown("---")
    st.subheader("📊 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_vendas = df_filtrado['vendas'].sum()
        st.metric(
            label="💰 Vendas Totais",
            value=f"R$ {total_vendas:,.0f}",
            delta=f"{len(df_filtrado):,} transações"
        )
    
    with col2:
        total_lucro = df_filtrado['lucro'].sum()
        lucro_medio = df_filtrado['lucro'].mean()
        st.metric(
            label="💵 Lucro Total",
            value=f"R$ {total_lucro:,.0f}",
            delta=f"R$ {lucro_medio:,.1f} médio"
        )
    
    with col3:
        margem_media = df_filtrado['margem'].mean() * 100
        margem_positiva = (df_filtrado['margem'] > 0).sum() / len(df_filtrado) * 100
        st.metric(
            label="📈 Margem Média",
            value=f"{margem_media:.1f}%",
            delta=f"{margem_positiva:.1f}% positivas"
        )
    
    with col4:
        quantidade_total = df_filtrado['quantidade'].sum()
        ticket_medio = total_vendas / len(df_filtrado)
        st.metric(
            label="🛒 Volume de Vendas",
            value=f"{quantidade_total:,} itens",
            delta=f"R$ {ticket_medio:,.1f} ticket médio"
        )
    
    # ========== VISUALIZAÇÕES ==========
    st.markdown("---")
    
    # Tentar carregar Plotly, mas funcionar sem ele
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Layout em abas para gráficos
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Vendas", "💰 Lucro", "🌎 Geografia", "📦 Produtos"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de vendas por categoria
                vendas_cat = df_filtrado.groupby('categoria')['vendas'].sum().reset_index()
                fig1 = px.bar(
                    vendas_cat,
                    x='categoria',
                    y='vendas',
                    title='Vendas por Categoria',
                    color='categoria',
                    text_auto='.2s'
                )
                fig1.update_layout(showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Gráfico de pizza para segmento
                vendas_seg = df_filtrado.groupby('segmento')['vendas'].sum().reset_index()
                fig2 = px.pie(
                    vendas_seg,
                    values='vendas',
                    names='segmento',
                    title='Distribuição de Vendas por Segmento',
                    hole=0.3
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                # Scatter plot: Vendas vs Lucro
                fig3 = px.scatter(
                    df_filtrado,
                    x='vendas',
                    y='lucro',
                    color='categoria',
                    size='quantidade',
                    hover_data=['subcategoria', 'regiao'],
                    title='Relação entre Vendas e Lucro',
                    labels={'vendas': 'Vendas (R$)', 'lucro': 'Lucro (R$)'}
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                # Lucro por região
                lucro_regiao = df_filtrado.groupby('regiao')['lucro'].sum().reset_index()
                fig4 = px.bar(
                    lucro_regiao,
                    x='regiao',
                    y='lucro',
                    title='Lucro por Região',
                    color='lucro',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig4, use_container_width=True)
        
        with tab3:
            # Mapa de calor por estado
            try:
                vendas_estado = df_filtrado.groupby('estado')['vendas'].sum().reset_index()
                fig5 = px.choropleth(
                    vendas_estado,
                    locations='estado',
                    locationmode="USA-states",
                    color='vendas',
                    scope="usa",
                    title='Vendas por Estado (EUA)',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig5, use_container_width=True)
            except:
                st.info("Mapa disponível apenas para dados dos EUA")
                
                # Alternativa: tabela
                st.dataframe(
                    df_filtrado.groupby(['regiao', 'estado'])['vendas']
                    .agg(['sum', 'count', 'mean'])
                    .round(2)
                    .sort_values('sum', ascending=False)
                    .head(20)
                )
        
        with tab4:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top 10 subcategorias
                top_produtos = df_filtrado.groupby('subcategoria')['vendas'].sum().nlargest(10)
                fig6 = px.bar(
                    top_produtos.reset_index(),
                    x='subcategoria',
                    y='vendas',
                    title='Top 10 Produtos (por vendas)',
                    color='vendas',
                    color_continuous_scale='thermal'
                )
                fig6.update_xaxes(tickangle=45)
                st.plotly_chart(fig6, use_container_width=True)
            
            with col2:
                # Margem por categoria
                margem_cat = df_filtrado.groupby('categoria')['margem'].mean() * 100
                fig7 = px.bar(
                    margem_cat.reset_index(),
                    x='categoria',
                    y='margem',
                    title='Margem Média por Categoria (%)',
                    text_auto='.1f'
                )
                st.plotly_chart(fig7, use_container_width=True)
    
    except ImportError:
        st.warning("⚠️ Plotly não disponível. Mostrando dados em tabelas...")
        
        # Visualizações alternativas sem Plotly
        st.subheader("📊 Dados em Tabela")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Vendas por Categoria:**")
            st.dataframe(
                df_filtrado.groupby('categoria')['vendas']
                .agg(['sum', 'count', 'mean', 'std'])
                .round(2)
                .sort_values('sum', ascending=False)
            )
        
        with col2:
            st.write("**Lucro por Segmento:**")
            st.dataframe(
                df_filtrado.groupby('segmento')['lucro']
                .agg(['sum', 'count', 'mean', 'std'])
                .round(2)
                .sort_values('sum', ascending=False)
            )
    
    # ========== TABELA DETALHADA ==========
    st.markdown("---")
    st.subheader("📋 Dados Detalhados")
    
    # Opções de visualização
    view_option = st.radio(
        "Visualizar:",
        ["Todos os dados", "Apenas transações com prejuízo", "Top 50 transações"],
        horizontal=True
    )
    
    if view_option == "Apenas transações com prejuízo":
        df_display = df_filtrado[df_filtrado['lucro'] < 0]
    elif view_option == "Top 50 transações":
        df_display = df_filtrado.nlargest(50, 'vendas')
    else:
        df_display = df_filtrado
    
    st.dataframe(
        df_display.sort_values('vendas', ascending=False),
        height=400,
        use_container_width=True
    )
    
    # ========== DOWNLOAD ==========
    st.markdown("---")
    st.subheader("💾 Exportar Dados")
    
    # Converter para CSV
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Baixar dados filtrados (CSV)",
        data=csv,
        file_name=f"supermarket_filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # ========== RESUMO ESTATÍSTICO ==========
    with st.expander("📊 Estatísticas Detalhadas"):
        st.write("**Estatísticas Descritivas:**")
        st.dataframe(df_filtrado[['vendas', 'lucro', 'margem', 'quantidade']].describe().round(2))
        
        st.write("**Correlações:**")
        corr_matrix = df_filtrado[['vendas', 'lucro', 'margem', 'quantidade', 'desconto']].corr()
        st.dataframe(corr_matrix.style.background_gradient(cmap='coolwarm', axis=None))
    
else:
    st.error("Não foi possível carregar os dados. Verifique o arquivo CSV.")

# ========== RODAPÉ ==========
st.markdown("---")
st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.caption("Dashboard desenvolvido com Streamlit | Dados: supermarket.csv")
