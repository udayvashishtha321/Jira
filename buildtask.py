def build_task(task):
    ac_list = task.get("acceptance_criteria", [])
    ac_text = "\n".join(f"- {ac}" for ac in ac_list)
    description_text = f"{task.get('description', '')}\n\nAcceptance Criteria:\n{ac_text}"

    item = {
        "summary":     task["summary"],
        "description": description_text,
        "status":      task.get("status", "TODO"),
    }

    assignee_name = task.get("assignee")
    if assignee_name:
        account_id = user_map.get(assignee_name)
        if account_id:
            item["assignee"] = {"accountId": account_id}
        else:
            print(f"⚠️ Assignee '{assignee_name}' not found in user_map")

    return item
