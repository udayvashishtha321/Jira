GITHUB_TOKEN = ""
REPO_OWNER = "udayvashishtha321"        # e.g. "facebook"
REPO_NAME = "Jira"          # e.g. "react"
PR_NUMBER = 21                   # the PR number you want

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
import requests
##FETCH PR DETAILS
def get_pr_details(pr_number):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    response = requests.get(url, headers=HEADERS)
    pr_data = response.json()
    
    head_branch = pr_data["head"]["ref"]   # branch name
    head_sha    = pr_data["head"]["sha"]   # commit SHA
    
    return head_branch, head_sha
##STEP 4 — Fetch List of Changed Files
def get_changed_files(pr_number):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
    response = requests.get(url, headers=HEADERS)
    files = response.json()
    
    file_paths = [f["filename"] for f in files]
    return file_paths

##STEP 5 — Fetch Full Content of Each File
import base64

def get_full_file_content(file_path, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    params = {"ref": sha}
    response = requests.get(url, headers=HEADERS, params=params)
    file_data = response.json()
    
    # GitHub returns content as Base64 — decode it
    encoded_content = file_data["content"]
    full_code = base64.b64decode(encoded_content).decode("utf-8")
    
    return full_code

##STEP 6 — Plug Everything Together
def fetch_full_pr_code(pr_number):
    # Step 1: get branch/SHA
    head_branch, head_sha = get_pr_details(pr_number)
    print(f"PR is on branch: {head_branch}")
    
    # Step 2: get changed file paths
    file_paths = get_changed_files(pr_number)
    print(f"Files changed: {file_paths}")
    
    # Step 3: fetch full content of each file
    all_files_code = {}
    for file_path in file_paths:
        print(f"Fetching: {file_path}")
        code = get_full_file_content(file_path, head_sha)
        all_files_code[file_path] = code
    
    return all_files_code


# --- RUN ---
result = fetch_full_pr_code(PR_NUMBER)

# Print each file's full code
for file_path, code in result.items():
    print(f"\n===== {file_path} =====")
    print(code)