import streamlit as st
import pandas as pd
import os
import sys

# Configuração da página
st.set_page_config(
    page_title="Dashboard Supermercado",
    page_icon="🛒",
    layout="wide"
)

st.title("📊 Dashboard de Análise de Vendas")

# Verificar pacotes instalados
st.sidebar.header("🛠️ Diagnóstico")
st.sidebar.write(f"Python: {sys.version}")

# Listar pacotes instalados (para diagnóstico)
try:
    import pkg_resources
    installed_packages = [pkg.key for pkg in pkg_resources.working_set]
    st.sidebar.write(f"Pacotes: {len(installed_packages)}")
    
    # Verificar pacotes específicos
    for pkg in ['streamlit', 'pandas', 'plotly', 'numpy']:
        if pkg in installed_packages:
            st.sidebar.success(f"✅ {pkg} instalado")
        else:
            st.sidebar.error(f"❌ {pkg} NÃO instalado")
except:
    pass

# Carregar dados
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('supermarket.csv')
        st.success(f"✅ Dados carregados: {len(df)} registros")
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar: {str(e)}")
        return None

df = load_data()

if df is not None:
    # ========== MÉTRICAS ==========
    st.subheader("📈 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Vendas Totais", f"R$ {df['vendas'].sum():,.0f}")
    
    with col2:
        st.metric("💵 Lucro Total", f"R$ {df['lucro'].sum():,.0f}")
    
    with col3:
        margem = df['margem'].mean() * 100
        st.metric("📊 Margem Média", f"{margem:.1f}%")
    
    with col4:
        st.metric("🛒 Transações", f"{len(df):,}")
    
    # ========== VERIFICAR PLOTLY ==========
    st.markdown("---")
    
    # Tentar importar Plotly de forma mais robusta
    plotly_available = False
    try:
        import plotly
        import plotly.express as px
        import plotly.graph_objects as go
        
        plotly_version = plotly.__version__
        st.success(f"✅ Plotly detectado (versão {plotly_version})")
        plotly_available = True
        
    except ImportError as e:
        st.error(f"❌ Plotly não disponível: {str(e)}")
        st.info("""
        **Solução:**
        1. Verifique se `requirements.txt` contém `plotly`
        2. No Streamlit Cloud: Settings → Clear cache → Redeploy
        3. Aguarde alguns minutos para reinstalação
        """)
        plotly_available = False
    
    # ========== VISUALIZAÇÕES ==========
    if plotly_available:
        st.subheader("📊 Gráficos Interativos com Plotly")
        
        # Gráfico 1: Vendas por Categoria
        vendas_cat = df.groupby('categoria')['vendas'].sum().reset_index()
        fig1 = px.bar(
            vendas_cat,
            x='categoria',
            y='vendas',
            title='Vendas por Categoria',
            color='categoria'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Gráfico 2: Lucro por Segmento
        lucro_seg = df.groupby('segmento')['lucro'].sum().reset_index()
        fig2 = px.pie(
            lucro_seg,
            values='lucro',
            names='segmento',
            title='Lucro por Segmento'
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Gráfico 3: Vendas vs Lucro
        fig3 = px.scatter(
            df,
            x='vendas',
            y='lucro',
            color='categoria',
            title='Vendas vs Lucro',
            hover_data=['subcategoria', 'regiao']
        )
        st.plotly_chart(fig3, use_container_width=True)
        
    else:
        # Visualizações alternativas
        st.subheader("📋 Visualizações em Tabela")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Vendas por Categoria:**")
            vendas_table = df.groupby('categoria').agg({
                'vendas': ['sum', 'mean', 'count'],
                'lucro': 'sum',
                'margem': 'mean'
            }).round(2)
            st.dataframe(vendas_table)
        
        with col2:
            st.write("**Top 10 Produtos:**")
            top_produtos = df.groupby('subcategoria')['vendas'].sum().nlargest(10)
            st.dataframe(top_produtos)
    
    # ========== DADOS DETALHADOS ==========
    st.markdown("---")
    st.subheader("📋 Dados Completos")
    
    with st.expander("Ver todos os dados"):
        st.dataframe(df)
    
    # ========== DOWNLOAD ==========
    import datetime
    csv = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Baixar CSV completo",
        data=csv,
        file_name=f"supermarket_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.error("Não foi possível carregar os dados.")
