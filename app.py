# Rewrite app.py to a more robust Streamlit app using Plotly, with caching, sidebar filters, and column validation.
from pathlib import Path

new_app_code = '''import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Supermercado - Análise", layout="wide")

REQUIRED_COLS = [
    "sales",
    "profit",
    "quantity",
    "category",
    "discount",
    "region",
]

@st.cache_data(show_spinner=False)
def load_data(csv_path: str) -> pd.DataFrame:
    df_local = pd.read_csv(csv_path)
    df_local.columns = (
        df_local.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    # Coerções defensivas (evita quebrar por tipo estranho)
    for col_name in ["sales", "profit", "quantity", "discount"]:
        if col_name in df_local.columns:
            df_local[col_name] = pd.to_numeric(df_local[col_name], errors="coerce")

    return df_local


def require_columns(df_local: pd.DataFrame, required_cols: list[str]) -> bool:
    missing_cols = [c for c in required_cols if c not in df_local.columns]
    if len(missing_cols) > 0:
        st.error("O CSV não tem as colunas obrigatórias: " + ", ".join(missing_cols))
        st.info("Colunas encontradas: " + ", ".join(list(df_local.columns)))
        return False
    return True


def format_brl(val: float) -> str:
    if pd.isna(val):
        return "R$ 0"
    # Formato simples estilo BR (sem depender de locale do SO)
    txt = "{:,.0f}".format(float(val))
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + txt


# ======================
# LOAD
# ======================
st.title("Análise de Vendas do Supermercado")

with st.spinner("Carregando dados..."):
    df = load_data("supermarket.csv")

if not require_columns(df, REQUIRED_COLS):
    st.stop()

# ======================
# SIDEBAR
# ======================
st.sidebar.header("Filtros")

debug_mode = st.sidebar.toggle("Modo debug", value=False)

if debug_mode:
    st.sidebar.caption("Colunas carregadas")
    st.sidebar.write(list(df.columns))

region_vals = sorted([x for x in df["region"].dropna().unique().tolist()])
category_vals = sorted([x for x in df["category"].dropna().unique().tolist()])

selected_regions = st.sidebar.multiselect(
    "Regiões",
    options=region_vals,
    default=region_vals,
)

selected_categories = st.sidebar.multiselect(
    "Categorias",
    options=category_vals,
    default=category_vals,
)

# Desconto
min_disc = float(df["discount"].min()) if df["discount"].notna().any() else 0.0
max_disc = float(df["discount"].max()) if df["discount"].notna().any() else 0.0
if min_disc > max_disc:
    min_disc = 0.0
    max_disc = 0.0

disc_range = st.sidebar.slider(
    "Faixa de desconto",
    min_value=float(min_disc),
    max_value=float(max_disc),
    value=(float(min_disc), float(max_disc)),
)

# ======================
# FILTER
# ======================
df_f = df.copy()

df_f = df_f[df_f["region"].isin(selected_regions)]
df_f = df_f[df_f["category"].isin(selected_categories)]
df_f = df_f[df_f["discount"].between(disc_range[0], disc_range[1], inclusive="both")]

df_f = df_f.dropna(subset=["sales", "profit", "quantity", "discount", "category", "region"])

if df_f.shape[0] == 0:
    st.warning("Sem dados para os filtros selecionados.")
    st.stop()

# ======================
# KPIs
# ======================
st.subheader("Indicadores gerais")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Vendas totais", format_brl(df_f["sales"].sum()))
kpi2.metric("Lucro total", format_brl(df_f["profit"].sum()))
kpi3.metric("Quantidade vendida", "{:,.0f}".format(df_f["quantity"].sum()).replace(",", "."))
kpi4.metric("Margem (lucro/vendas)", "{:.1%}".format((df_f["profit"].sum() / df_f["sales"].sum()) if df_f["sales"].sum() else 0.0))

# ======================
# CHARTS
# ======================
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Lucro por categoria")
    lucro_categoria = (
        df_f.groupby("category", as_index=False)["profit"].sum()
        .sort_values("profit", ascending=False)
    )
    fig_cat = px.bar(
        lucro_categoria,
        x="category",
        y="profit",
        title=None,
        labels={"category": "Categoria", "profit": "Lucro"},
    )
    fig_cat.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_cat, use_container_width=True)

with right_col:
    st.subheader("Lucro por região")
    lucro_regiao = (
        df_f.groupby("region", as_index=False)["profit"].sum()
        .sort_values("profit", ascending=False)
    )
    fig_reg = px.bar(
        lucro_regiao,
        x="region",
        y="profit",
        title=None,
        labels={"region": "Região", "profit": "Lucro"},
    )
    fig_reg.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_reg, use_container_width=True)

st.subheader("Desconto vs lucro")

fig_scatter = px.scatter(
    df_f,
    x="discount",
    y="profit",
    color="category",
    hover_data=["region", "sales", "quantity"],
    opacity=0.7,
    labels={"discount": "Desconto", "profit": "Lucro"},
    trendline="ols",
)
fig_scatter.update_layout(margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_scatter, use_container_width=True)

# ======================
# TABLE (optional)
# ======================
with st.expander("Ver dados filtrados"):
    st.dataframe(df_f, use_container_width=True)

# ======================
# CONCLUSÕES
# ======================
st.subheader("Conclusões")

st.success(
    "\
".join(
        [
            "- Existem categorias mais rentáveis que outras",
            "- Descontos altos tendem a pressionar o lucro (veja a tendência no gráfico)",
            "- Regiões têm desempenho distinto",
            "- Filtros ajudam a encontrar onde o lucro está sendo perdido",
        ]
    )
)
'''

Path('app.py').write_text(new_app_code, encoding='utf-8')
print('app.py')
