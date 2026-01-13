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

# Remover espaços invisíveis (segurança)
df.columns = df.columns.str.strip()

# ======================
# TÍTULO
# ======================
st.title("📊 Análise Estratégica de Vendas — Supermercado")

st.markdown("""
Dashboard executivo para análise de **lucro, descontos,
categorias e desempenho regional**.
""")

# ======================
# KPIs
# ======================
st.subheader("📌 Visão Geral")

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
st.pyplot(fig)

st.info("📌 **Decisão:** Priorizar categorias mais rentáveis.")

# ======================
# SUBCATEGORIAS COM PREJUÍZO
# ======================
st.subheader("🚨 Subcategorias com Prejuízo")

prejuizo = (
    df[df["Profit"] < 0]
    .groupby("Sub-Category")[["Profit", "Quantity"]]
    .sum()
    .sort_values("Profit")
)

st.dataframe(prejuizo.head(10))

st.warning("❗ **Ação:** Reavaliar produtos com prejuízo recorrente.")

# ======================
# DESCONTO x LUCRO
# ======================
st.subheader("🎯 Impacto dos Descontos")

fig, ax = plt.subplots()
ax.scatter(df["Discount"], df["Profit"], alpha=0.5)
ax.axhline(0)
ax.set_xlabel("Desconto")
ax.set_ylabel("Lucro")
st.pyplot(fig)

st.error("📉 **Decisão:** Limitar descontos por categoria.")

# ======================
# LUCRO POR REGIÃO
# ======================
st.subheader("🌍 Lucro por Região")

lucro_regiao = df.groupby("Region")["Profit"].sum()

fig, ax = plt.subplots()
lucro_regiao.plot(kind="bar", ax=ax)
ax.set_ylabel("Lucro")
st.pyplot(fig)

st.info("📍 **Decisão:** Estratégias regionais de precificação.")

# ======================
# ALERTA
# ======================
st.subheader("🚨 Alerta Financeiro")

prejuizo_total = df[df["Profit"] < 0]["Profit"].sum()

if prejuizo_total < -50000:
    st.error(f"🚨 Prejuízo acumulado: R$ {prejuizo_total:,.0f}")
else:
