import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_client() -> Client:
    """Returns a cached Supabase client built from Streamlit secrets.

    Requires SUPABASE_URL and SUPABASE_KEY to be set in .streamlit/secrets.toml
    locally, or in the app's Secrets panel on Streamlit Community Cloud.
    """
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)