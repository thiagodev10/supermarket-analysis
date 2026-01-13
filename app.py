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

# NORMALIZAÇÃO FORÇADA DAS COLUNAS
df.columns = (
    df.columns
    .astype(str)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("-", "_")
)

# FAILSAFE: garantir nomes esperados
if "sales" not in df.columns:
    df.rename(columns={df.columns[df.columns.str.contains("sale")][0]: "sales"}, inplace=True)

if "profit" not in df.columns:
    df.rename(columns={df.columns[df.columns.str.contains("profit")][0]: "profit"}, inplace=True)

if "quantity" not in df.columns:
    df.rename(columns={df.columns[df.columns.str.contains("quant")][0]: "quantity"}, inplace=True)

if "category" not in df.columns:
    df.rename(columns={df.columns[df.columns.str.contains("category")][0]: "category"}, inplace=True)

if "sub_category" not in df.columns:
    df.rename(columns={df.columns[df.columns.str.contains("sub")][0]: "sub_category"}, inplace=True)

if "region" not in df.columns:
    df.rename(columns={df.columns[df.columns.str.contains("region")][0]: "region"}, inplace=True)

# ======================
# TÍTULO E CONTEXTO
# ======================
st.title("📊 Análise Estratégica de Vendas — Supermercado")

st.markdown("""
Este painel foi desenvolvido para apoiar **decisões estratégicas**
da diretoria, analisando **lucro, descontos, categorias e regiões**.
""")

# ======================
# KPI - VISÃO GERAL
# ======================
st.subheader("📌 Visão Geral do Negócio")

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Vendas Totais", f"R$ {df['sales'].sum():,.0f}")
col2.metric("📈 Lucro Total", f"R$ {df['profit'].sum():,.0f}")
col3.metric("📦 Quantidade Vendida", int(df['quantity'].sum()))
col4.metric(
    "% Itens com Prejuízo",
    f"{(df[df['profit'] < 0].shape[0] / df.shape[0]) * 100:.1f}%"
)

# ======================
# LUCRO POR CATEGORIA
# ======================
st.subheader("💰 Lucro por Categoria")

lucro_categoria = df.groupby("category")["profit"].sum().sort_values()

fig, ax = plt.subplots()
lucro_categoria.plot(kind="barh", ax=ax)
ax.set_xlabel("Lucro")
ax.set_ylabel("Categoria")
st.pyplot(fig)

st.info("""
📌 **Decisão:** Priorizar categorias com maior margem de lucro
e evitar descontos excessivos nessas áreas.
""")

# ======================
# PREJUÍZO POR SUBCATEGORIA
# ======================
st.subheader("🚨 Subcategorias com Prejuízo")

prejuizo_subcat = (
    df[df["profit"] < 0]
    .groupby("sub_category")[["profit", "quantity"]]
    .sum()
    .sort_values("profit")
)

st.dataframe(prejuizo_subcat.head(10))

st.warning("""
❗ **Ação:** Reavaliar produtos com alto volume
e prejuízo recorrente (preço, custo ou desconto).
""")

# ======================
# DESCONTO x LUCRO
# ======================
st.subheader("🎯 Impacto dos Descontos no Lucro")

fig, ax = plt.subplots()
ax.scatter(df["discount"], df["profit"], alpha=0.5)
ax.axhline(0)
ax.set_xlabel("Desconto")
ax.set_ylabel("Lucro")
st.pyplot(fig)

st.error("""
📉 Descontos elevados estão fortemente associados a prejuízo.

➡️ **Decisão:** Revisar política de descontos,
aplicando limites por categoria.
""")

# ======================
# LUCRO POR REGIÃO
# ======================
st.subheader("🌍 Lucro por Região")

lucro_regiao = df.groupby("region")["profit"].sum()

fig, ax = plt.subplots()
lucro_regiao.plot(kind="bar", ax=ax)
ax.set_ylabel("Lucro")
st.pyplot(fig)

st.info("""
📍 **Decisão:** Adotar estratégias regionais
de precificação e desconto por região.
""")

# ======================
# ALERTA DE PREJUÍZO
# ======================
st.subheader("🚨 Monitoramento de Risco")

prejuizo_total = df[df["profit"] < 0]["profit"].sum()

if prejuizo_total < -50000:
    st.error(f"🚨 ALERTA: Prejuízo acumulado de R$ {prejuizo_total:,.0f}")
else:
    st.success("✅ Prejuízo sob controle no período analisado")

# ======================
# CONCLUSÃO
# ======================
st.subheader("📌 Recomendações Executivas")

st.success("""
- Revisar política de descontos por categoria  
- Reavaliar produtos com alto volume e prejuízo  
- Adotar estratégias regionais de precificação  
- Priorizar categorias com maior margem de lucro  
- Monitorar margens mensalmente  
- Criar alertas automáticos de prejuízo  
""")
