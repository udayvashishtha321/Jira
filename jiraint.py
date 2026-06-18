import re
import json
import requests
from extract import extract_hierarchy
from requests.auth import HTTPBasicAuth
def parse_form_data(data, story_type, user_map):  
    print("Extract top_summary, story_items, subtask_items from your JSON and acceptance criteria")

    top_summary = data["epic"]["summary"] #extract epic summary

    def build_task(task):
        item = {
            "summary":     task["summary"],
            # "description": task.get("description", ""),
            "description": { # basis on the ADF
    "type": "doc",
    "version": 1,
    "content": [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": task.get("description", "")}]
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": "Acceptance Criteria:", "marks": [{"type": "strong"}]}]
        },
        {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": ac}]
                    }]
                }
                for ac in task.get("acceptance_criteria", [])
            ]
        }
    ]
},
            "status":      task.get("status", "TODO"),
            "assignee":    user_map.get(task["assignee"]) if task.get("assignee") else None,
           
        }

        # ── Convert displayName accountId using user_map ──
        assignee_name = task.get("assignee")
        if assignee_name:
            account_id = user_map.get(assignee_name) 
            if account_id:
                item["assignee"] = {"accountId": account_id}
            else:
                print(f"⚠️ Assignee '{assignee_name}' not found in user_map")

        return item

    if story_type is None:
        story_items   = []
        subtask_items = [
            build_task(task)
            for story in data.get("stories", [])
            for task in story.get("tasks", [])
        ]
        
        print("story none me hai")
    else:
        story_items = [
            {
                "summary":     story["summary"],
                "description": story.get("description", ""),
                "subtasks":    [build_task(task) for task in story.get("tasks", [])]
            }
            for story in data.get("stories", [])
        ]
        subtask_items = []
    
    print("story me hai")
    return top_summary, story_items, subtask_items

def create_issues(top_type, story_type, subtask_type, parent_map,
                  project_key, top_summary, story_items, subtask_items,
                  url, headers, auth):
    
    print("create_issue")
    # ──  Create Top (Epic) ────────────────────────────────
    top_payload = {
        "fields": {
            "project":   {"key": project_key},
            "summary":   top_summary,
            "issuetype": {"name": top_type},
        }
    }
    top_res = requests.post(url, json=top_payload, headers=headers, auth=auth)
    if top_res.status_code != 201:
        print(f"Top failed: {top_res.text}")
        return

    top_key = top_res.json()["key"]
    print(f"Top created: {top_key}")

    if story_type is None:
        print(" crate issue story me hai nhi hai")
        # ── 2 LEVEL  subtasks directly under top ───────
        for item in subtask_items:
            subtask_payload = {
                "fields": {
                    "project":   {"key": project_key},
                    "summary":   item["summary"],
                    "issuetype": {"name": subtask_type},
                    "parent":    {"key": top_key},  # top is direct parent
                    "assignee":  item["assignee"],
                }
            }
            sub_res = requests.post(url, json=subtask_payload, headers=headers, auth=auth)
            if sub_res.status_code == 201:
                print(f"  Subtask created: {sub_res.json()['key']} → {item['summary']}")
            else:
                print(f"  Subtask failed: {sub_res.text}")

    else:
        print(" crate issue story me hai")
        # ──  3 LEVEL  stories under top ─────────────────
        for story in story_items:
            story_payload = {
                "fields": {
                    "project":   {"key": project_key},
                    "summary":   story["summary"],
                    "issuetype": {"name": story_type},
                    "parent":    {"key": top_key},  # top is story's parent
                }
            }
            story_res = requests.post(url, json=story_payload, headers=headers, auth=auth)
            if story_res.status_code != 201:
                print(f"  Story failed: {story_res.text}")
                continue

            story_key = story_res.json()["key"]
            print(f"  Story created: {story_key} → {story['summary']}")

            # ── Step 3: Tasks under each story ───────────────────
            for task in story.get("subtasks", []):
                subtask_payload = {
                    "fields": {
                        "project":   {"key": project_key},
                        "summary":   task["summary"],
                        "issuetype": {"name": subtask_type},
                        "parent":    {"key": story_key}, # story is task's parent
                        "assignee":  task["assignee"],
                        "description": task["description"],   # ← add this line
                    }
                }
                
                
                sub_res = requests.post(url, json=subtask_payload, headers=headers, auth=auth)
                if sub_res.status_code == 201:
                    print(f"    Task created: {sub_res.json()['key']} → {task['summary']}")
                else:
                    print(f"    Task failed: {sub_res.text}")


def parse_json(text):
        text = re.sub(r"```.*?```", lambda m: m.group(0).strip("`"), text, flags=re.DOTALL)
        
        print("parse_json")
        start = text.find("{")
        end = text.rfind("}") + 1
        text = text[start:end]

        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*]", "]", text)
        

        return json.loads(text)

def run(data, url, email, api_token, project_key):
    jira_url = f"{url}/rest/api/3/issue"
    print(url)
    print("you are in createjira")

    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # ── Check if project exists, if not create it ──
    proj_resp = requests.get(
        f"{url}/rest/api/3/project/{project_key}",
        auth=auth,
        headers=headers
    )

    if proj_resp.status_code == 404:
        print(f"⚠️ Project '{project_key}' not found. Creating it...")

        # First get the current user's accountId to set as project lead
        myself_resp = requests.get(
            f"{url}/rest/api/3/myself",
            auth=auth,
            headers=headers
        )

        if myself_resp.status_code != 200:
            print(f"❌ Failed to fetch current user: {myself_resp.text}")
            return

        account_id = myself_resp.json()["accountId"]

        # create_proj_payload = {
        #     "key": project_key,
        #     "name": project_key,
        #     "projectTypeKey": "software",
        #     "leadAccountId": account_id,
        # }
        create_proj_payload = {
    "key": project_key,
    "name": project_key,
    "projectTypeKey": "software",
    "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-simplified-scrum-classic",
    "leadAccountId": account_id,
}

        create_proj_resp = requests.post(
            f"{url}/rest/api/3/project",
            json=create_proj_payload,
            auth=auth,
            headers=headers
        )

        if create_proj_resp.status_code not in (200, 201):
            print(
                f"❌ Failed to create project: "
                f"{create_proj_resp.status_code} - {create_proj_resp.text}"
            )
            return

        project_id = create_proj_resp.json()["id"]
        print(f"✅ Project '{project_key}' created with ID: {project_id}")

    elif proj_resp.status_code == 200:
        proj_data = proj_resp.json()

        if "id" not in proj_data:
            print(f"❌ 'id' not found in project response: {proj_data}")
            return

        project_id = proj_data["id"]
        print(f"✅ Project '{project_key}' already exists with ID: {project_id}")

    else:
        print(
            f"❌ Unexpected error fetching project: "
            f"{proj_resp.status_code} - {proj_resp.text}"
        )
        return

   
    top_type     = "Epic"
    story_type   = "Story"
    subtask_type = "Sub-task"
    parent_map   = {"Epic": None, "Story": "Epic", "Sub-task": "Story"}
    print(top_type, story_type, subtask_type)

    # ── Fetch users ──────────────────────────────────────────────
    search_url = f"{url}/rest/api/3/users/search"
    response = requests.get(search_url, auth=auth, headers=headers)
    user_map = {user["displayName"]: user["accountId"] for user in response.json()}
    
    data={
  
}
   
    try:
        top_summary, story_items, subtask_items = parse_form_data(data, story_type, user_map)
    except Exception as e:
        print(f"❌ Error in parse_form_data: {e}")
        return

    print("create issue ke uper hu")
    
    
    # Step 3: Create all issues
    create_issues(
        top_type=top_type,
        story_type=story_type,
        subtask_type=subtask_type,
        parent_map=parent_map,
        
        project_key=project_key,
        top_summary=top_summary,
        story_items=story_items,
        subtask_items=subtask_items,
        
        url=jira_url,
        headers={"Content-Type": "application/json"},
        auth=HTTPBasicAuth(email, api_token)
    )
    print("automating the jira level 3 and 2")

if __name__ == "__main__":
    run(
        data=None,          # data is overwritten inside run() anyway
        url="https://aryansaxena991204.atlassian.net",
        email="aryansaxena120@gmail.com",
        api_token="",
        project_key="SCRUM"
    )