from fastapi import FastAPI, UploadFile, File, Form
from fastapi import FastAPI, Request
from test import send_data
import os
import shutil
from collections import Counter
from collections import defaultdict
from jira import JIRA

app = FastAPI()


@app.post("/send-data")
async def receive_data(
    request: Request,   
    email: str = Form(...),
    url: str = Form(...),
    api_token: str = Form(...),
    project_key: str = Form(...),
    req_file: UploadFile = File(...),
    person_file: UploadFile = File(...)
):
    try:
    
        form_data = await request.form()
        print("FORM DATA RECEIVED:", form_data)

        print("EMAIL:", email)
        print("PROJECT KEY:", project_key)

        
        if not email or not project_key:
            return {"status": "error", "message": "Missing email or project_key"}

        if not req_file or not person_file:
            return {"status": "error", "message": "Files missing"}

        print("✅ Request reached backend")

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        UPLOAD_DIR = os.path.join(BASE_DIR, "neww")

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        req_path = os.path.join(UPLOAD_DIR, "requirements.pdf")
        person_path = os.path.join(UPLOAD_DIR, "employees.pdf")

        
        with open(req_path, "wb") as f:
            shutil.copyfileobj(req_file.file, f)

        with open(person_path, "wb") as f:
            shutil.copyfileobj(person_file.file, f)

        print("✅ Files saved")

        # call your function
        send_data(
            email,
            url,
            api_token,
            project_key,
            req_path,
            person_path
        )

        return {"status": "success"}

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {
            "status": "error",
            "message": str(e)
        }
        

@app.post("/get-status-summary")
async def get_status_summary(
    email: str = Form(...),
    url: str = Form(...),
    api_token: str = Form(...),
    project_key: str = Form(...)
):
    
    
    try:
        
        print("data is comiing")
        jira = JIRA(
            server=url,
            basic_auth=(email, api_token)
        )

        # 🔹 Fetch all issues
        issues = jira.search_issues(
            f'project={project_key}',
            maxResults=100
        )

        # 🔹 Extract statuses
        status_list = [issue.fields.status.name for issue in issues]

        # 🔹 Count each status
        status_counts = Counter(status_list)
        
        print("sc ",status_counts)
        # 🔹 Return clean JSON
        return {
            "status_summary": dict(status_counts)
        }

    except Exception as e:
        return {"error": str(e)}
    






@app.post("/assignee-summary")
def get_assignee_summary(
    email: str = Form(...),
    url: str = Form(...),
    api_token: str = Form(...),
    project_key: str = Form(...)
):

    # create jira connection
    jira = JIRA(
        server=url,
        basic_auth=(email, api_token)
    )

    issues = jira.search_issues(
        f'project={project_key}',
        maxResults=100,
        fields="assignee"
    )
    print("TOTAL ISSUES:", len(issues))
    assignee_count = defaultdict(int)
    for issue in issues:
        assignee = issue.fields.assignee

        if assignee:
           name = getattr(assignee, "displayName", None) or getattr(assignee, "accountId", "unknown")
        else:
           name = "Unassigned"

        assignee_count[name] += 1

    return (dict(assignee_count))