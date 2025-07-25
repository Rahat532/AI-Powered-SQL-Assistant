import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
from db_utils import save_csv_to_db

# ----- Page Config -----
st.set_page_config(
    page_title="AI SQL Assistant",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="expanded"
)

import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
from db_utils import save_csv_to_db
from sql_agent import ask_query
import json

# ----- Page Config -----
st.set_page_config(
    page_title="AI SQL Assistant",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="expanded"
)

# ----- Custom CSS for Modern Styling -----
st.markdown("""
    <style>
    .stApp {
        background-color: #616161;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .title {
        color: #000000;
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5em;
    }
    .subtitle {
        color: #000000;
        font-size: 1.5em;
        text-align: center;
        font-weight: semi-bold;
        margin-bottom: 1em;
    }
    .section-header {
        color: #000000;
        font-size: 1.5em;
        font-weight: 600;
        margin-top: 1em;
        margin-bottom: 0.5em;
    }
    .stButton>button {
        background-color: #000000;
        color: white;
        border-radius: 8px;
        padding: 0.5em 1em;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        color: white;
    }
    .stSelectbox, .stTextInput {
        background-color: white;
        border-radius: 8px;
        padding: 0.5em;
    }
    .stSpinner {
        color: #1a73e8;
    }
    .chat-message {
        background-color: white;
        border-radius: 8px;
        padding: 1em;
        margin-bottom: 1em;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .sidebar .stButton>button {
        width: 100%;
        margin-bottom: 1em;
    }
    </style>
""", unsafe_allow_html=True)

# ----- Sidebar for Settings and Navigation -----
with st.sidebar:
    st.header("⚙️ Settings")
    theme = st.selectbox("Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("""
            <style>
            .stApp {
                background-color: #1e1e1e;
                color: white;
            }
            .section-header, .title, .subtitle {
                color: #8ab4f8;
            }
            .stSelectbox, .stTextInput {
                background-color: #2d2d2d;
                color: white;
            }
            .chat-message {
                background-color: #2d2d2d;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("ℹ️ Help")
    st.write("Upload a CSV file to start. Ask questions in plain English, like 'Show total number of data.'")
    if st.button("🗑️ Reset App"):
        st.session_state.clear()
        st.rerun()

# ----- Title and Description -----
st.markdown('<div class="title">🧠 AI-Powered SQL Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a CSV file and explore your data with natural language queries.</div>', unsafe_allow_html=True)

# ----- File Upload Section -----
st.markdown('<div class="section-header">📤 Upload Data</div>', unsafe_allow_html=True)
col1, col2 = st.columns([2, 3])
with col1:
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], help="Upload a CSV file to analyze.")
with col2:
    if uploaded_file:
        st.write(f"**File Uploaded:** {uploaded_file.name}")

if uploaded_file:
    try:
        # Try multiple encodings
        encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        df = None
        for encoding in encodings_to_try:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            st.error("❌ Failed to read CSV with common encodings.")
        elif df.empty:
            st.error("❌ The uploaded CSV is empty.")
        else:
            # Clean column names
            df.columns = df.columns.str.replace('[^a-zA-Z0-9_]', '_', regex=True)
            table_name = uploaded_file.name.split('.')[0].lower().replace(' ', '_')
            table_name, columns = save_csv_to_db(df, table_name)

            st.success(f"✅ Table '{table_name}' created with {len(columns)} columns.")
            
            # ----- Table Preview -----
            st.markdown('<div class="section-header">📄 Table Preview</div>', unsafe_allow_html=True)
            st.dataframe(df.head(20), use_container_width=True)
            
            # ----- Download Table Button -----
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Table as CSV",
                data=csv,
                file_name=f"{table_name}.csv",
                mime="text/csv",
            )

            # ----- Chart Selection -----
            if len(df.columns) >= 2:
                st.markdown('<div class="section-header">📊 Data Visualization</div>', unsafe_allow_html=True)
                with st.expander("Customize Chart", expanded=True):
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Area", "Scatter", "Pie"], help="Select the type of chart to display.")
                        x_axis = st.selectbox("X-axis", df.columns, help="Select column for X-axis.")
                    with chart_col2:
                        y_axis = st.selectbox("Y-axis", df.columns, help="Select column for Y-axis (numeric preferred).")
                        chart_color = st.color_picker("Chart Color", "#1a73e8", help="Pick a color for the chart.")

                    try:
                        chart_base = alt.Chart(df).encode(
                            x=alt.X(x_axis, title=x_axis.replace('_', ' ').title()),
                            y=alt.Y(y_axis, title=y_axis.replace('_', ' ').title()),
                            color=alt.value(chart_color)
                        )
                        if chart_type == "Bar":
                            chart = chart_base.mark_bar()
                        elif chart_type == "Line":
                            chart = chart_base.mark_line()
                        elif chart_type == "Area":
                            chart = chart_base.mark_area()
                        elif chart_type == "Scatter":
                            chart = chart_base.mark_circle()
                        elif chart_type == "Pie":
                            chart = chart_base.mark_arc().encode(theta=y_axis, color=x_axis)
                        else:
                            chart = None

                        if chart:
                            st.altair_chart(chart, use_container_width=True)
                        else:
                            st.warning("⚠️ Invalid chart configuration.")
                    except Exception as chart_err:
                        st.warning(f"⚠️ Couldn't generate chart: {chart_err}. Try selecting numeric columns for Y-axis.")
            else:
                st.warning("⚠️ Not enough columns for a chart.")

    except pd.errors.EmptyDataError:
        st.error("❌ The uploaded file appears to be empty.")
    except Exception as e:
        st.error(f"❌ Failed to process the CSV file: {e}")

# ----- AI Chat Interface -----
st.markdown('<div class="section-header">💬 Ask About Your Data</div>', unsafe_allow_html=True)
st.markdown("Example questions: 'What is the total number of data?' or 'Show average by column.'")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Chat input
with st.form(key="query_form", clear_on_submit=True):
    user_question = st.text_input("Ask in plain English:", placeholder="e.g., What is the total number of data?", help="Type your question about the data.")
    submit_button = st.form_submit_button("Submit Query")

if submit_button and user_question:
    with st.spinner("🧠 Processing your question..."):
        try:
            response = ask_query(user_question)
            st.session_state.chat_history.append({"question": user_question, "response": response})
            
            # Display chat history
            for chat in st.session_state.chat_history:
                st.markdown(f'<div class="chat-message"><strong>You:</strong> {chat["question"]}<br><strong>AI:</strong> {chat["response"]}</div>', unsafe_allow_html=True)

            # If response is SQL, execute and visualize
            if "SELECT" in response.upper():
                try:
                    conn = sqlite3.connect("uploaded.db")
                    result_df = pd.read_sql_query(response, conn)
                    conn.close()

                    st.markdown('<div class="section-header">🧾 Query Result</div>', unsafe_allow_html=True)
                    st.dataframe(result_df.head(20), use_container_width=True)
                    
                    # Download query result
                    if not result_df.empty:
                        result_csv = result_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Query Result as CSV",
                            data=result_csv,
                            file_name="query_result.csv",
                            mime="text/csv",
                        )

                    # Visualize query result
                    if not result_df.empty and len(result_df.columns) >= 2:
                        st.markdown('<div class="section-header">📊 Chart from Query</div>', unsafe_allow_html=True)
                        col1, col2 = result_df.columns[:2]
                        chart = alt.Chart(result_df).mark_bar().encode(
                            x=alt.X(col1, title=col1.replace('_', ' ').title()),
                            y=alt.Y(col2, title=col2.replace('_', ' ').title()),
                            color=alt.value("#1a73e8")
                        )
                        st.altair_chart(chart, use_container_width=True)
                except Exception as chart_err:
                    st.warning(f"⚠️ Could not visualize query result: {chart_err}")
        except Exception as query_err:
            st.error(f"❌ Failed to process your question: {query_err}")

# Clear chat history button
if st.session_state.chat_history:
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()