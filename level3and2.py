import re
import json
import requests
from createjiradynamic import extract_hierarchy
from requests.auth import HTTPBasicAuth
def parse_form_data(data, story_type, user_map):  
    print("Extract top_summary, story_items, subtask_items from your JSON")

    top_summary = data["epic"]["summary"]

    def build_task(task):
        item = {
            "summary":     task["summary"],
            "description": task.get("description", ""),
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

def run(data, url,email, api_token, project_key):
    # Step 1: Extract hierarchy types
    jira_url = f"{url}/rest/api/3/issue"
    print(url)
    print("you are in createjira")
    
    proj_resp = requests.get(
        f"{url}/rest/api/3/project/{project_key}",
        auth=HTTPBasicAuth(email, api_token),
        headers={"Accept": "application/json"}
    )

    project_id = proj_resp.json()["id"]

    ################# GET HIERARCHY #################
    hierarchy_resp = requests.get(
        f"{url}/rest/api/3/project/{project_id}/hierarchy",
        auth=HTTPBasicAuth(email, api_token)
    )
    
     
    hierarchy = hierarchy_resp.json()["hierarchy"]
        
    top_type, story_type, subtask_type, parent_map = extract_hierarchy(hierarchy)
    
    print(top_type, story_type, subtask_type)
    search_url = f"{url}/rest/api/3/users/search"
    response = requests.get(search_url, auth=HTTPBasicAuth(email, api_token))
    user_map = {user["displayName"]: user["accountId"] for user in response.json()}
    
  
   
    top_summary, story_items, subtask_items = parse_form_data(data, story_type, user_map)
    auth=HTTPBasicAuth(email, api_token),
    headers={"Content-Type": "application/json"},
    
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


################# JIRA ADF FORMAT #################
"""def jira_adf(text):
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}]
                }
            ]
        }"""
    
"""
def create_jira_from_json(response, email, api_token, base_url, project_key):

    ################# PARSE JSON #################
    jira_url = f"{base_url}/rest/api/3/issue"
    
    print("you are in createjira")
    def parse_json(text):
        text = re.sub(r"```.*?```", lambda m: m.group(0).strip("`"), text, flags=re.DOTALL)

        start = text.find("{")
        end = text.rfind("}") + 1
        text = text[start:end]

        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*]", "]", text)

        return json.loads(text)

    # ✅ FIX HERE
    if isinstance(response, dict):
        data = response
    else:
        data = parse_json(response)

    
    

    ################# GET PROJECT ID #################
    proj_resp = requests.get(
        f"{base_url}/rest/api/3/project/{project_key}",
        auth=HTTPBasicAuth(email, api_token),
        headers={"Accept": "application/json"}
    )

    project_id = proj_resp.json()["id"]

    ################# GET HIERARCHY #################
    hierarchy_resp = requests.get(
        f"{base_url}/rest/api/3/project/{project_id}/hierarchy",
        auth=HTTPBasicAuth(email, api_token)
    )
     
    hierarchy = hierarchy_resp.json()["hierarchy"]
    
    top_type, story_type, subtask_type, parent_map = extract_hierarchy(hierarchy)

    print(top_type)    # Epic
    print(story_type)  # Story or None
    print(subtask_type) # Task or None
    print(parent_map)  
    sorted_levels = sorted(hierarchy, key=lambda x: x["level"])

    levels = {}
    for lvl in sorted_levels:
        level_number = lvl["level"]
        issue_names = [i["name"] for i in lvl["issueTypes"]]
        if issue_names:
            levels[level_number] = issue_names

    sorted_keys = sorted(levels.keys(), reverse=True)

    # Detect types
    top_type = levels[sorted_keys[0]][0]

    story_type = None
    for k in sorted_keys[1:]:
        if k < sorted_keys[0] and k != -1:
            story_type = levels[k][0]
            break

    subtask_type = levels.get(-1, [None])[0]

    if story_type is None and subtask_type:
        story_type = top_type

    print("Hierarchy:", levels)
    print("Top:", top_type, "| Story:", story_type, "| Subtask:", subtask_type)

    ################# CREATE TOP ISSUE #################
    epic_data = data.get("epic", data)

    epic_payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": epic_data["summary"],
            "description": jira_adf(epic_data["description"]),
            "issuetype": {"name": top_type}
        }
    }

    epic_resp = requests.post(
    jira_url,
    auth=HTTPBasicAuth(email, api_token),
    headers={"Accept": "application/json","Content-Type": "application/json"},
    json=epic_payload
    )

    if epic_resp.status_code != 201:
        print("Top issue failed:", epic_resp.text)
        return

    epic_key = epic_resp.json()["key"]
    print("Top created:", epic_key)

    ################# FETCH USERS #################
    users_resp = requests.get(
        f"{base_url}/rest/api/3/users/search",
        auth=HTTPBasicAuth(email, api_token)
    )

    users = users_resp.json()
    user_map = {u["displayName"]: u["accountId"] for u in users}

    ################# CREATE STORIES + SUBTASKS #################
    for story in data.get("stories", []):

        story_payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": story["summary"],
                "description": jira_adf(story["description"]),
                "issuetype": {"name": story_type},
                "parent": {"key": epic_key}
            }
        }

        story_resp = requests.post(
            jira_url,
            auth=HTTPBasicAuth(email, api_token),
            headers={"Content-Type": "application/json"},
            json=story_payload
        )

        if story_resp.status_code != 201:
            print("Story failed:", story_resp.text)
            continue

        story_key = story_resp.json()["key"]
        print("Story created:", story_key)

        # -------- SUBTASKS --------
        for task in story.get("tasks", []):

            account_id = user_map.get(task["assignee"])

            task_payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": task["summary"],
                    "description": jira_adf(task["description"]),
                    "issuetype": {"name": subtask_type},
                    "parent": {"key": story_key},
                    "assignee": {"accountId": account_id}
                }
            }

            task_resp = requests.post(
                jira_url,
                auth=HTTPBasicAuth(email, api_token),
                headers={"Content-Type": "application/json"},
                json=task_payload
            )

            if task_resp.status_code != 201:
                print("Subtask failed:", task_resp.text)
                continue

            print("Subtask created:", task_resp.json()["key"])
    print("automating the jira is complete")
"""
    
