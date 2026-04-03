import pandas as pd
import streamlit as st

st.set_page_config(page_title="Job Data Explorer", layout="wide")

st.title("Job Data Explorer")

@st.cache_data
def load_data():
    return pd.read_csv("structured_jobs.csv")

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
companies = st.sidebar.multiselect("Company", sorted(df["company"].dropna().unique()))
remote_vals = sorted(df["remote_type"].dropna().unique())
employment_vals = sorted(df["employment_type"].dropna().unique())
seniority_vals = sorted(df["seniority"].dropna().unique())

remote_type = st.sidebar.multiselect("Remote Type", remote_vals)
employment_type = st.sidebar.multiselect("Employment Type", employment_vals)
seniority = st.sidebar.multiselect("Seniority", seniority_vals)

# Skill search
skill_query = st.sidebar.text_input("Search required_skills")

filtered = df.copy()
if companies:
    filtered = filtered[filtered["company"].isin(companies)]
if remote_type:
    filtered = filtered[filtered["remote_type"].isin(remote_type)]
if employment_type:
    filtered = filtered[filtered["employment_type"].isin(employment_type)]
if seniority:
    filtered = filtered[filtered["seniority"].isin(seniority)]
if skill_query:
    q = skill_query.strip().lower()
    filtered = filtered[filtered["required_skills"].fillna("[]").str.lower().str.contains(q)]

# Counts
st.subheader("Counts")
col1, col2, col3 = st.columns(3)
col1.metric("Total jobs", len(filtered))
col2.write("By remote_type")
col2.write(filtered["remote_type"].value_counts())
col3.write("By employment_type")
col3.write(filtered["employment_type"].value_counts())

# Dataframe
st.subheader("Filtered Jobs")
st.dataframe(filtered, use_container_width=True)

# Selector
st.subheader("Job Details")
selector_mode = st.selectbox("Select by", ["job_id", "title_clean"], index=0)
options = filtered[selector_mode].dropna().astype(str).tolist()
selected = st.selectbox("Job", options) if options else None

if selected:
    row = filtered[filtered[selector_mode].astype(str) == selected].iloc[0]

    st.markdown("**Raw Text**")
    st.text_area("", row.get("raw_text", ""), height=300)

    st.markdown("**Structured Fields**")
    fields = [
        "job_id",
        "company",
        "title_raw",
        "title_clean",
        "location_raw",
        "location_clean",
        "remote_type",
        "employment_type",
        "seniority",
        "department",
        "experience_years_min",
        "experience_years_max",
        "salary_present",
        "salary_text",
        "required_skills",
        "preferred_skills",
        "responsibilities",
        "qualifications",
        "url",
    ]
    detail = pd.DataFrame({"field": fields, "value": [row.get(f, "") for f in fields]})
    st.dataframe(detail, use_container_width=True, hide_index=True)

# Download
st.subheader("Download")
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", csv_bytes, "filtered_jobs.csv", "text/csv")
