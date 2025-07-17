import json
import pandas as pd
import streamlit as st
from openai import OpenAI
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"]

# Load OpenAI API key
# with open("data/secret/openai_key.json") as f:
#     OPENAI_API_KEY = json.load(f)["API_KEY"]
# client = OpenAI(api_key=OPENAI_API_KEY)

# Load internal prompt
with open("data/prompts/WEBSITE_FINDER_PROMPT.txt", "r", encoding="utf-8") as f:
    WEBSITE_FINDER_PROMPT = f.read()

# Function to batch-query GPT for domains
def find_domains(names, batch_size=50, model="gpt-4o-mini", prompt="data/prompts/WEBSITE_FINDER_PROMPT"):
    results = {}
    for i in range(0, len(names), batch_size):
        batch = names[i : i + batch_size]
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(batch, ensure_ascii=False)}
            ],
            temperature=0,
            top_p=1.0,
            n=1
        )
        raw = resp.choices[0].message.content.strip()
        try:
            container = json.loads(raw)
        except json.JSONDecodeError:
            st.error("Invalid JSON received from model:")
            st.code(raw)
            return {}
        for entry in container.get("results", []):
            results[entry.get("name")] = entry.get("domain")
    return results

# Streamlit UI
st.set_page_config(
    page_title="Company Domain Finder",  # Browser tab title
    page_icon=":rocket:",               # Favicon emoji (or use a file path like "🚀.png")
    # layout="wide"                       # Optional: "centered" or "wide"
)
st.title("Company Domain Finder")

uploaded_file = st.file_uploader("Upload CSV/Excel file", type=["csv", "xlsx"])
batch_size = st.number_input("Batch size", min_value=1, max_value=200, value=50)

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success(f"Loaded {len(df)} rows.")
        if st.button("Find Domains"):
            if "Company Name" not in df.columns:
                st.error("CSV/Excel must have a 'Company Name' column.")
            else:
                names = df["Company Name"].dropna().astype(str).tolist()
                with st.spinner("Querying GPT..."):
                    name_to_domain = find_domains(names, batch_size)
                df["Company Domain"] = df["Company Name"].map(name_to_domain).fillna("")
                st.success("Domains fetched!")
                fmt = st.selectbox("Download format", ["Excel (.xlsx)", "CSV (.csv)"])
                if fmt.startswith("Excel"):
                    towrite = pd.ExcelWriter("results.xlsx", engine='openpyxl')
                    df.to_excel(towrite, index=False)
                    towrite.save()
                    st.download_button(
                        label="Download Excel",
                        data=open("results.xlsx", "rb"),
                        file_name="domain_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    csv_bytes = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv_bytes,
                        file_name="domain_results.csv",
                        mime="text/csv"
                    )
    except Exception as e:
        st.error(f"Error reading file: {e}")

