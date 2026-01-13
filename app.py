import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(page_title="Supermercado - Análise", layout="wide")

# Carregar dados
df = pd.read_csv("supermarket.csv")
df.columns = df.columns.str.strip()

# Título
st.title("📊 Análise de Vendas do Supermercado")

st.markdown("""
Este painel apresenta uma análise simples e objetiva
para apoio à tomada de decisão.
""")

# ======================
# KPIs
# ======================
st.subheader("📌 Indicadores Gerais")

col1, col2, col3 = st.columns(3)

col1.metric("💰 Vendas Totais", f"R$ {df['Sales'].sum():,.0f}")
col2.metric("📈 Lucro Total", f"R$ {df['Profit'].sum():,.0f}")
col3.metric("📦 Quantidade Vendida", int(df['Quantity'].sum()))

# ======================
# LUCRO POR CATEGORIA
# ======================
st.subheader("💰 Lucro por Categoria")

lucro_categoria = df.groupby("Category")["Profit"].sum()

fig, ax = plt.subplots()
lucro_categoria.plot(kind="bar", ax=ax)
ax.set_ylabel("Lucro")
st.pyplot(fig)

# ======================
# DESCONTO x LUCRO
# ======================
st.subheader("🎯 Relação entre Desconto e Lucro")

fig2, ax2 = plt.subplots()
ax2.scatter(df["Discount"], df["Profit"])
ax2.axhline(0)
ax2.set_xlabel("Desconto")
ax2.set_ylabel("Lucro")
st.pyplot(fig2)

# ======================
# REGIÕES
# ======================
st.subheader("🌍 Lucro por Região")

lucro_regiao = df.groupby("Region")["Profit"].sum()

fig3, ax3 = plt.subplots()
lucro_regiao.plot(kind="bar", ax=ax3)
ax3.set_ylabel("Lucro")
st.pyplot(fig3)

# ======================
# CONCLUSÃO
# ======================
st.subheader("📌 Conclusões")

st.success("""
- Categorias possuem desempenho financeiro distinto  
- Descontos excessivos reduzem o lucro  
- Algumas regiões são mais rentáveis que outras  
- Monitorar lucro é essencial para decisões estratégicas  
""")
