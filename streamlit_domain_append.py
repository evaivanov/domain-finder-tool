import json
import pandas as pd
import streamlit as st
import requests
import os

st.title("Company Domain Finder")

ENDPOINT_URL = os.getenv("ENDPOINT_URL") or st.secrets["ENDPOINT_URL"]
AUTH_TOKEN   = st.secrets["AUTH_TOKEN"]


def find_domains(names: list[str], batch_size: int = 25) -> dict[str,str]:
    """
    Sends names in batches of `batch_size` to your endpoint, which expects
    a single JSON payload with a newline/tab‑delimited string of lines like:
      1\tNameA
      2\tNameB
    and returns something like:
      { "ReturnDomainList": [
         "{\"name\":\"NameA\",\"domain\":\"namea.com\"}",
         …
      ]}
    """
    results = {}
    for i in range(0, len(names), batch_size):
        batch = names[i : i + batch_size]
        # Build the tab‑delimited payload string
        payload_str = "\r\n".join(f"{idx+1}\t{name}" for idx, name in enumerate(batch))
        # Mirror your example: build the JSON‑body dict
        payload = {"ListOfCompanies": payload_str}
        # And send it with the auth header
        response = requests.post(
            ENDPOINT_URL,
            headers={"auth": AUTH_TOKEN},
            json=payload,
            timeout=60
        )
        if response.status_code != 200:
            raise ValueError(f"API call failed ({response.status_code}): {response.text}")
        # Pull out the array of JSON‑strings
        ret = response.json().get("ReturnDomainList", [])
        for item in ret:
            obj = json.loads(item)
            results[obj["name"]] = obj["domain"]
    return results

st.set_page_config(
    page_title="Company Domain Finder", 
    page_icon=":rocket:",               
    # layout="wide"                       
)

uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv","xlsx"])
if uploaded_file and st.button("Find Domains"):
    df = (pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv")
          else pd.read_excel(uploaded_file))
    names = df["Company Name"].dropna().astype(str).tolist()
    with st.spinner("Calling endpoint…"):
        mapping = find_domains(names)
    df["Company Domain"] = df["Company Name"].map(mapping).fillna("")
    st.dataframe(df)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv_bytes, file_name="domains.csv")
