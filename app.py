import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ======================
# CONFIGURAÇÃO DA PÁGINA
# ======================
st.set_page_config(
    page_title="Análise Estratégica - Supermercado",
    layout="wide"
)

# ======================
# CARREGAR DADOS
# ======================
df = pd.read_csv("supermarket.csv")
df.columns = df.columns.str.strip()  # remove espaços invisíveis

# ======================
# TÍTULO
# ======================
st.title("📊 Análise Estratégica de Vendas — Supermercado")

st.markdown("""
Dashboard executivo para apoiar **decisões estratégicas**
sobre **lucro, descontos, categorias e regiões**.
""")

# ======================
# KPIs
# ======================
st.subheader("📌 Visão Geral do Negócio")

c1, c2, c3, c4 = st.columns(4)

c1.metric("💰 Vendas Totais", f"R$ {df['Sales'].sum():,.0f}")
c2.metric("📈 Lucro Total", f"R$ {df['Profit'].sum():,.0f}")
c3.metric("📦 Quantidade Vendida", int(df['Quantity'].sum()))
c4.metric(
    "% Itens com Prejuízo",
    f"{(df[df['Profit'] < 0].shape[0] / df.shape[0]) * 100:.1f}%"
)

# ======================
# LUCRO POR CATEGORIA
# ======================
st.subheader("💰 Lucro por Categoria")

lucro_categoria = df.groupby("Category")["Profit"].sum().sort_values()

fig, ax = plt.subplots()
lucro_categoria.plot(kind="barh", ax=ax)
ax.set_xlabel("Lucro")
ax.set_ylabel("Categoria")
st.pyplot(fig)

st.info("📌 **Decisão:** Priorizar categorias mais rentáveis.")

# ======================
# SUBCATEGORIAS COM PREJUÍZO
# ======================
st.subheader("🚨 Subcategorias com Prejuízo")

prejuizo_sub = (
    df[df["Profit"] < 0]
    .groupby("Sub-Category")[["Profit", "Quantity"]]
    .sum()
    .sort_values("Profit")
)

st.dataframe(prejuizo_s_
