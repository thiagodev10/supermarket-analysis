import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Supermercado - Análise", layout="wide")

# ======================
# CARREGAR CSV
# ======================
df = pd.read_csv("supermarket.csv")

# Padronizar nomes das colunas
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# DEBUG VISUAL (IMPORTANTE)
st.write("📄 Colunas carregadas:", df.columns.tolist())

# ======================
# TÍTULO
# ======================
st.title("📊 Análise de Vendas do Supermercado")

# ======================
# KPIs
# ======================
st.subheader("📌 Indicadores Gerais")

col1, col2, col3 = st.columns(3)

col1.metric("💰 Vendas Totais", f"R$ {df['sales'].sum():,.0f}")
col2.metric("📈 Lucro Total", f"R$ {df['profit'].sum():,.0f}")
col3.metric("📦 Quantidade Vendida", int(df['quantity'].sum()))

# ======================
# LUCRO POR CATEGORIA
# ======================
st.subheader("💰 Lucro por Categoria")

lucro_categoria = df.groupby("category")["profit"].sum()

fig, ax = plt.subplots()
lucro_categoria.plot(kind="bar", ax=ax)
ax.set_ylabel("Lucro")
st.pyplot(fig)

# ======================
# DESCONTO x LUCRO
# ======================
st.subheader("🎯 Desconto vs Lucro")

fig2, ax2 = plt.subplots()
ax2.scatter(df["discount"], df["profit"])
ax2.axhline(0)
ax2.set_xlabel("Desconto")
ax2.set_ylabel("Lucro")
st.pyplot(fig2)

# ======================
# REGIÕES
# ======================
st.subheader("🌍 Lucro por Região")

lucro_regiao = df.groupby("region")["profit"].sum()

fig3, ax3 = plt.subplots()
lucro_regiao.plot(kind="bar", ax=ax3)
ax3.set_ylabel("Lucro")
st.pyplot(fig3)

# ======================
# CONCLUSÃO
# ======================
st.subheader("📌 Conclusões")

st.success("""
- Existem categorias mais rentáveis que outras  
- Descontos elevados impactam negativamente o lucro  
- Regiões possuem comportamentos distintos  
- Monitorar indicadores evita prejuízo recorrente  
""")
