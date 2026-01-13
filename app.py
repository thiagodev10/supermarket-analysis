# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Dashboard Supermercado",
    page_icon="🛒",
    layout="wide"
)

# Título
st.title("📊 Dashboard de Vendas - Supermercado")

# Carregar dados
@st.cache_data
def load_data():
    # Certifique-se que o arquivo está na mesma pasta
    df = pd.read_csv('supermarket.csv')
    return df

try:
    df = load_data()
    
    # Mostrar dados brutos (opcional)
    with st.expander("👀 Visualizar Dados Brutos"):
        st.dataframe(df)
    
    # Métricas principais
    st.subheader("📈 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # CORREÇÃO AQUI: usar nomes corretos das colunas
    with col1:
        # Usar 'vendas' em vez de 'sales'
        total_vendas = df['vendas'].sum()
        st.metric("💰 Vendas Totais", f"R$ {total_vendas:,.2f}")
    
    with col2:
        # Usar 'lucro' em vez de 'profit'
        total_lucro = df['lucro'].sum()
        st.metric("💵 Lucro Total", f"R$ {total_lucro:,.2f}")
    
    with col3:
        # Calcular margem média
        margem_media = df['margem'].mean() * 100
        st.metric("📊 Margem Média", f"{margem_media:.1f}%")
    
    with col4:
        total_transacoes = len(df)
        st.metric("🛒 Total de Transações", f"{total_transacoes:,}")
    
    # Gráficos
    st.subheader("📊 Análise por Categoria")
    
    # 1. Vendas por Categoria
    fig1 = px.bar(
        df.groupby('categoria')['vendas'].sum().reset_index(),
        x='categoria',
        y='vendas',
        title='Vendas por Categoria',
        color='categoria'
    )
    
    # 2. Lucro por Segmento
    fig2 = px.pie(
        df.groupby('segmento')['lucro'].sum().reset_index(),
        values='lucro',
        names='segmento',
        title='Distribuição de Lucro por Segmento'
    )
    
    # 3. Vendas por Região
    fig3 = px.treemap(
        df,
        path=['regiao', 'estado', 'cidade'],
        values='vendas',
        title='Vendas por Localização (Região > Estado > Cidade)'
    )
    
    # 4. Margem vs Vendas
    fig4 = px.scatter(
        df,
        x='vendas',
        y='lucro',
        color='categoria',
        size='quantidade',
        hover_data=['subcategoria'],
        title='Relação entre Vendas e Lucro'
    )
    
    # Layout dos gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig4, use_container_width=True)
    
    # Filtros interativos
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por região
    regioes = df['regiao'].unique()
    regiao_selecionada = st.sidebar.multiselect(
        "Selecione a Região",
        options=regioes,
        default=regioes
    )
    
    # Filtro por categoria
    categorias = df['categoria'].unique()
    categoria_selecionada = st.sidebar.multiselect(
        "Selecione a Categoria",
        options=categorias,
        default=categorias
    )
    
    # Filtro por segmento
    segmentos = df['segmento'].unique()
    segmento_selecionado = st.sidebar.multiselect(
        "Selecione o Segmento",
        options=segmentos,
        default=segmentos
    )
    
    # Aplicar filtros
    if regiao_selecionada:
        df_filtrado = df[df['regiao'].isin(regiao_selecionada)]
    else:
        df_filtrado = df.copy()
    
    if categoria_selecionada:
        df_filtrado = df_filtrado[df_filtrado['categoria'].isin(categoria_selecionada)]
    
    if segmento_selecionado:
        df_filtrado = df_filtrado[df_filtrado['segmento'].isin(segmento_selecionado)]
    
    # Tabela com dados filtrados
    st.subheader("📋 Dados Filtrados")
    st.dataframe(df_filtrado)
    
    # Resumo estatístico
    st.subheader("📊 Estatísticas Descritivas")
    st.dataframe(df_filtrado[['vendas', 'lucro', 'margem', 'quantidade']].describe())
    
except FileNotFoundError:
    st.error("❌ Arquivo 'supermarket.csv' não encontrado!")
    st.info("Certifique-se de que o arquivo está na mesma pasta que o app.py")
except KeyError as e:
    st.error(f"❌ Erro: Coluna não encontrada - {e}")
    st.info("Verifique os nomes das colunas no arquivo CSV. As colunas devem ser:")
    st.code("modo_envio, segmento, pais, cidade, estado, cep, regiao, categoria, subcategoria, vendas, quantidade, desconto, lucro, margem")
except Exception as e:
    st.error(f"❌ Ocorreu um erro: {e}")
