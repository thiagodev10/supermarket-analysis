# Write a fully corrected app.py with robust CSV reading (encoding + delimiter), PT-BR column mapping, and safer parsing.
from pathlib import Path

app_code_fixed = '''import os
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Supermercado - Análise", layout="wide")

# Canonical columns used internally by the app
REQUIRED = ["sales", "profit", "quantity", "category", "discount", "region"]

# PT-BR + EN aliases (normalized form: lower, stripped, spaces->underscore)
ALIASES = {
    # sales
    "vendas": "sales",
    "sales": "sales",

    # profit
    "lucro": "profit",
    "profit": "profit",

    # quantity
    "quantidade": "quantity",
    "quantity": "quantity",

    # category
    "categoria": "category",
    "category": "category",

    # discount
    "desconto": "discount",
    "discount": "discount",

    # region
    "regiao": "region",
    "região": "region",
    "region": "region",
}


def _normalize_cols(cols):
    return (
        pd.Index(cols)
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace("\ufeff", "", regex=False)
        .str.replace(" ", "_", regex=False)
    )


def _looks_mojibake(df_local: pd.DataFrame) -> bool:
    # Heuristic: if many cells contain typical mojibake markers.
    text_cols = [c for c in df_local.columns if df_local[c].dtype == object]
    if len(text_cols) == 0:
        return False
    sample = df_local[text_cols].head(50).astype(str)
    joined = " ".join(sample.fillna("").to_numpy().ravel().tolist())
    bad_markers = ["Ã", "Â", "�"]
    score = sum(joined.count(m) for m in bad_markers)
    return score >= 5


@st.cache_data(show_spinner=False)
def load_data(csv_path: str) -> pd.DataFrame:
    # Try common encodings and delimiters
    encodings_to_try = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    seps_to_try = [",", ";", "\	"]

    best_df = None
    best_score = None

    for enc in encodings_to_try:
        for sep_val in seps_to_try:
            try:
                df_try = pd.read_csv(csv_path, encoding=enc, sep=sep_val)
                if df_try.shape[1] <= 1:
                    continue

                # Normalize headers early
                df_try.columns = _normalize_cols(df_try.columns)

                # Prefer frames that contain more required/aliased columns
                cols = set(df_try.columns.tolist())
                aliased = set([ALIASES[c] for c in cols if c in ALIASES])
                required_hit = len([c for c in REQUIRED if c in aliased or c in cols])

                # Penalize obvious mojibake
                mojibake_penalty = 1 if _looks_mojibake(df_try) else 0

                score = (required_hit * 10) - mojibake_penalty

                if best_score is None or score > best_score:
                    best_score = score
                    best_df = df_try
            except Exception:
                continue

    if best_df is None:
        st.error("Não consegui ler o CSV. Verifique o arquivo e tente salvar como CSV UTF-8.")
        st.stop()

    # Auto-rename columns using aliases
    rename_map = {}
    for c in best_df.columns:
        if c in ALIASES:
            rename_map[c] = ALIASES[c]
    df_local = best_df.rename(columns=rename_map)

    # Coerce numeric columns
    for c in ["sales", "profit", "quantity", "discount"]:
        if c in df_local.columns:
            df_local[c] = pd.to_numeric(df_local[c], errors="coerce")

    # Clean strings (helps reduce stray spaces)
    for c in ["region", "category"]:
        if c in df_local.columns:
            df_local[c] = df_local[c].astype(str).str.strip()

    return df_local


def require_columns(df_local: pd.DataFrame) -> None:
    missing_cols = [c for c in REQUIRED if c not in df_local.columns]
    if len(missing_cols) > 0:
        st.error("O CSV não tem as colunas obrigatórias (após mapear PT-BR -> padrão): " + ", ".join(missing_cols))
        st.info("Colunas encontradas: " + ", ".join(list(df_local.columns)))
        st.info("Esperado (PT-BR ou EN): vendas/lucro/quantidade/desconto/categoria/regiao (ou sales/profit/quantity/discount/category/region)")
        st.stop()


def format_brl(val: float) -> str:
    if pd.isna(val):
        return "R$ 0"
    txt = "{:,.0f}".format(float(val))
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + txt


st.title("Análise de Vendas do Supermercado")

csv_candidates = ["supermarket.csv", "Supermarket.csv", "dados.csv", "data.csv"]
csv_path = None
for fp in csv_candidates:
    if os.path.exists(fp):
        csv_path = fp
        break

if csv_path is None:
    st.error("Não encontrei o arquivo CSV. Coloque um arquivo chamado supermarket.csv na mesma pasta do app.")
    st.stop()

with st.spinner("Carregando dados..."):
    df = load_data(csv_path)

require_columns(df)

st.sidebar.header("Filtros")
debug_mode = st.sidebar.toggle("Modo debug", value=False)
if debug_mode:
    st.sidebar.caption("Arquivo")
    st.sidebar.write(csv_path)
    st.sidebar.caption("Colunas carregadas")
    st.sidebar.write(list(df.columns))

region_vals = sorted([x for x in df["region"].dropna().unique().tolist()])
category_vals = sorted([x for x in df["category"].dropna().unique().tolist()])

selected_regions = st.sidebar.multiselect("Regiões", options=region_vals, default=region_vals)
selected_categories = st.sidebar.multiselect("Categorias", options=category_vals, default=category_vals)

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

# Apply filters
f = df.copy()
f = f[f["region"].isin(selected_regions)]
f = f[f["category"].isin(selected_categories)]
f = f[f["discount"].between(disc_range[0], disc_range[1], inclusive="both")]

# Keep only valid rows for computations
f = f.dropna(subset=["sales", "profit", "quantity", "discount", "category", "region"])
if f.shape[0] == 0:
    st.warning("Sem dados para os filtros selecionados.")
    st.stop()

# KPIs
st.subheader("Indicadores gerais")
k1, k2, k3, k4 = st.columns(4)

k1.metric("Vendas totais", format_brl(f["sales"].sum()))
k2.metric("Lucro total", format_brl(f["profit"].sum()))
k3.metric("Quantidade vendida", "{:,.0f}".format(f["quantity"].sum()).replace(",", "."))
margin_val = (f["profit"].sum() / f["sales"].sum()) if f["sales"].sum() else 0.0
k4.metric("Margem (lucro/vendas)", "{:.1%}".format(margin_val))

# Charts
c1, c2 = st.columns(2)

with c1:
    st.subheader("Lucro por categoria")
    lucro_categoria = f.groupby("category", as_index=False)["profit"].sum().sort_values("profit", ascending=False)
    fig_cat = px.bar(lucro_categoria, x="category", y="profit", labels={"category": "Categoria", "profit": "Lucro"})
    fig_cat.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_cat, use_container_width=True)

with c2:
    st.subheader("Lucro por região")
    lucro_regiao = f.groupby("region", as_index=False)["profit"].sum().sort_values("profit", ascending=False)
    fig_reg = px.bar(lucro_regiao, x="region", y="profit", labels={"region": "Região", "profit": "Lucro"})
    fig_reg.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_reg, use_container_width=True)

st.subheader("Desconto vs lucro")
fig_scatter = px.scatter(
    f,
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

with st.expander("Ver dados filtrados"):
    st.dataframe(f, use_container_width=True)
'''

Path('app.py').write_text(app_code_fixed, encoding='utf-8')
print('app.py')
