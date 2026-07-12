# Synthetic Polarion Workitem Test Dataset

Included workitems: **2000**

## Fields

- `title`
- `text` — HTML rich text with headings, lists, tables, blockquotes, links, and code blocks
- `revision`
- `status`
- `workitem_id`
- `linked_workitems` — list containing `id` and `role`
- `custom_fields` — realistic additional fields such as type, priority, component,
  release, author, assignee, safety class, verification method, and tags

## Files

- `polarion_workitems_testset_2000_en.jsonl`: one workitem per line; recommended for streaming and batch imports
- `polarion_workitems_testset_2000_en.json`: complete JSON array
- `load_polarion_testset_en.py`: example Qdrant import script

The dataset preserves the same IDs and link graph as the German version.
All data is fully synthetic.
