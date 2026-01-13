import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Análise de Dados - Supermercado", layout="wide")

st.title("📊 Análise de Dados — Supermercado")

df = pd.read_csv("supermarket.csv")

st.subheader("Visão Geral")
st.dataframe(df.head())

st.subheader("Lucro por Categoria")
lucro_categoria = df.groupby("categoria")["lucro"].sum()

fig, ax = plt.subplots()
lucro_categoria.plot(kind="bar", ax=ax)
st.pyplot(fig)
