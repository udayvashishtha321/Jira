"""
st.title("Jira Automation Tool")

# -----------------------------
# INPUT FIELDS
# -----------------------------
email = st.text_input("Email")
url = st.text_input("Jira URL")
token = st.text_input("API Token", type="password")
project_key = st.text_input("Project Key")

req_file = st.file_uploader("Upload Requirement PDF", type=["pdf"])
person_file = st.file_uploader("Upload Employees PDF", type=["pdf"])

# -----------------------------
# SUBMIT BUTTON
# -----------------------------
if st.button("Submit"):

    if not req_file or not person_file:
        st.error("Please upload both files")
    
    else:
        try:
            # -----------------------------
            # PREPARE FILES
            # -----------------------------
            files = {
                "req_file": ("requirements.pdf", req_file.getvalue()),
                "person_file": ("employees.pdf", person_file.getvalue())
            }

            # -----------------------------
            # PREPARE DATA
            # -----------------------------
            data = {
                "email": email,
                "url": url,
                "api_token": token,
                "project_key": project_key
            }

            # -----------------------------
            # API CALL
            # -----------------------------
            response = requests.post(
                "http://127.0.0.1:8000/send-data",
                data=data,
                files=files
            )

            # -----------------------------
            # HANDLE RESPONSE
            # -----------------------------
            if response.status_code == 200:
                result = response.json()
                
                st.success("Task Created Successfully!")
                st.json(result)

            else:
                st.error(f"Error: {response.text}")

        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")


st.title("📊 Jira Status Dashboard")

if st.button("Load Status Summary"):

    dataa = {
        "email": email,
        "url": url,
        "api_token": token,
        "project_key": project_key
    }
    print(dataa)
    response = requests.post(
        "http://127.0.0.1:8000/get-status-summary",
        data=dataa
    )
    print(response)
    if response.status_code != 200:
        st.error(f"API Error: {response.text}")
        st.stop()

    data = response.json()
    print(data)

    # ✅ extract safely
    stat = data.get("status_summary", {})

    statuses = list(stat.keys())
    counts = list(stat.values())

    # ❗ IMPORTANT: columns MUST be inside button block
    col1, col2 = st.columns(2)

    # 🥧 PIE CHART
    with col1:
        fig1, ax1 = plt.subplots(figsize=(5, 5))
        ax1.pie(counts, labels=statuses, autopct='%1.1f%%')
        st.subheader("Status Distribution")
        st.pyplot(fig1)

    # 📊 BAR CHART
    with col2:
        fig2, ax2 = plt.subplots(figsize=(5, 5))
        ax2.bar(statuses, counts)
        ax2.set_xlabel("Status")
        ax2.set_ylabel("Number of Tasks")
        ax2.set_title("Jira Status Count")
        st.subheader("Status Count")
        st.pyplot(fig2)

    
    
st.title("📊 Jira Dashboard - Assignee Report")

# 🔘 Button
if st.button("Get Assignee Report"):
    
    dataa ={
                "email": email,
                "url": url,
                "api_token": token,
                "project_key": project_key
            }

    # 🔗 Call backend API (NO data parameter needed for GET)
    response = requests.post("http://localhost:8000/assignee-summary",data=dataa)

    if response.status_code != 200:
        st.error("Failed to fetch data from backend")
        st.stop()

    data = response.json()
    
    names = list(data.keys())
    values = list(data.values())

    st.title("Jira Assignee Dashboard")

# Create two columns
    col1, col2 = st.columns(2)

# ---------------- PIE CHART ----------------
    with col1:
       st.subheader("Pie Chart")

       fig1, ax1 = plt.subplots()
       ax1.pie(values, labels=names, autopct='%1.1f%%')
       ax1.axis("equal")  # circle shape

       st.pyplot(fig1)


# ---------------- BAR CHART ----------------
    with col2:
        st.subheader("Bar Chart")

        fig2, ax2 = plt.subplots()
        ax2.bar(names, values)

        plt.xticks(rotation=45)

        st.pyplot(fig2)
"""