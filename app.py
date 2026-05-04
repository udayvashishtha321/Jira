import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt


import streamlit as st
import requests
import matplotlib.pyplot as plt

st.set_page_config(page_title="Jira Dashboard", layout="wide")


if "status_data" not in st.session_state:
    st.session_state.status_data = None

if "assignee_data" not in st.session_state:
    st.session_state.assignee_data = None



st.title("📊 Jira Dashboard")

email = st.text_input("Email")
url = st.text_input("Jira URL")
token = st.text_input("API Token", type="password")
project_key = st.text_input("Project Key")

req_file = st.file_uploader("Upload Requirement PDF", type=["pdf"])
person_file = st.file_uploader("Upload Employees PDF", type=["pdf"])


if st.button("Submit"):

    if not req_file or not person_file:
        st.error("Please upload both files")
    
    else:
        try:
          
            files = {
                "req_file": ("requirements.pdf", req_file.getvalue()),
                "person_file": ("employees.pdf", person_file.getvalue())
            }

           
            data = {
                "email": email,
                "url": url,
                "api_token": token,
                "project_key": project_key
            }

           
            response = requests.post(
                "http://127.0.0.1:8000/send-data",
                data=data,
                files=files
            )

           
            if response.status_code == 200:
                result = response.json()
                
                st.success("Task Created Successfully!")
                st.json(result)

            else:
                st.error(f"Error: {response.text}")

        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")



if st.button("Load Status Summary"):

    dataa = {
        "email": email,
        "url": url,
        "api_token": token,
        "project_key": project_key
    }

    response = requests.post(
        "http://127.0.0.1:8000/get-status-summary",
        data=dataa
    )

    if response.status_code != 200:
        st.error(response.text)
        st.stop()

    st.session_state.status_data = response.json()



if st.button("Get Assignee Report"):

    dataa = {
        "email": email,
        "url": url,
        "api_token": token,
        "project_key": project_key
    }

    response = requests.post(
        "http://127.0.0.1:8000/assignee-summary",
        data=dataa
    )

    if response.status_code != 200:
        st.error("Failed to fetch data from backend")
        st.stop()

    st.session_state.assignee_data = response.json()



if st.session_state.status_data:

    st.markdown("---")
    st.subheader("📊 Status Distribution")

    stat = st.session_state.status_data.get("status_summary", {})

    statuses = list(stat.keys())
    counts = list(stat.values())

    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots()
        ax1.pie(counts, labels=statuses, autopct='%1.1f%%')
        ax1.set_title("Status Pie Chart")
        st.pyplot(fig1)

    with col2:
        fig2, ax2 = plt.subplots()
        ax2.bar(statuses, counts)
        ax2.set_title("Status Bar Chart")
        st.pyplot(fig2)



if st.session_state.assignee_data:

    st.markdown("---")
    st.subheader("👤 Assignee Distribution")

    data = st.session_state.assignee_data

    names = list(data.keys())
    values = list(data.values())

    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots()
        ax1.pie(values, labels=names, autopct='%1.1f%%')
        ax1.set_title("Assignee Pie Chart")
        st.pyplot(fig1)

    with col2:
        fig2, ax2 = plt.subplots()
        ax2.bar(names, values)
        ax2.set_title("Assignee Bar Chart")
        plt.xticks(rotation=45)
        st.pyplot(fig2)