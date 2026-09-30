import streamlit as st
import requests

st.set_page_config(
    page_title="Text-to-SQL RAG System",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Text-to-SQL RAG System")

API_URL = "http://127.0.0.1:8000/ask"

token = st.text_input(
    "Authentication Token",
    type="password"
)

question = st.text_area(
    "Ask your question",
    placeholder="Example: How many customers are there?"
)

if st.button("Ask"):

    if not token.strip():
        st.warning("Please enter an authentication token.")

    elif not question.strip():
        st.warning("Please enter a question.")

    else:
        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "question": question
                }
            )

            data = response.json()

            if response.status_code != 200:
                st.error(data.get("detail", "Something went wrong."))

            else:
                st.subheader("Answer")
                st.write(data["answer"])

                # Admin and Analyst responses contain these fields.
                # Viewer receives only the answer.
                if "sql" in data:

                    st.subheader("Generated SQL")
                    st.code(data["sql"], language="sql")

                    st.subheader("Schema")
                    st.code(data["schema"], language="sql")

                    st.subheader("Result")
                    st.json(data["result"])

        except requests.exceptions.ConnectionError:
            st.error(
                "Could not connect to backend. "
                "Make sure FastAPI is running on port 8000."
            )