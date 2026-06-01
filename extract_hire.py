def extract_hierarchy(hierarchy):
    sorted_levels = sorted(hierarchy, key=lambda x: x["level"])

    levels = {}
    for lvl in sorted_levels:
        level_number = lvl["level"]
        issue_names = [i["name"] for i in lvl["issueTypes"]]
        if issue_names:
            levels[level_number] = issue_names

    sorted_keys = sorted(levels.keys(), reverse=True)
    num_levels = len(sorted_keys)

    # ── Assign top / story / subtask ──────────────────────────────
    if num_levels == 0:
        top_type = story_type = subtask_type = None

    elif num_levels == 1:
        top_type     = levels[sorted_keys[0]][0]
        story_type   = None
        subtask_type = None

    elif num_levels == 2:
        top_type     = levels[sorted_keys[0]][0]
        story_type   = None                          # no middle level
        subtask_type = levels[sorted_keys[1]][0]

    else:  # 3+
        top_type     = levels[sorted_keys[0]][0]
        story_type   = levels[sorted_keys[1]][0]     # first middle
        subtask_type = levels[sorted_keys[-1]][0]    # last / bottom

    print("Top:", top_type, "| Story:", story_type, "| Subtask:", subtask_type)

    # ── Dynamic parent-child wiring ───────────────────────────────
    #  Rule: each non-None type is parent of the next non-None type
    active = [t for t in [top_type, story_type, subtask_type] if t is not None]

    parent_map = {}
    for i, type_name in enumerate(active):
        parent_map[type_name] = active[i - 1] if i > 0 else None   # None = root

    # ── Print relationships ───────────────────────────────────────
    print("\n--- Parent-Child Map ---")
    for child, parent in parent_map.items():
        if parent is None:
            print(f"  {child}  [root]")
        else:
            print(f"  {parent}  →  {child}")

    return top_type, story_type, subtask_type, parent_map
    
