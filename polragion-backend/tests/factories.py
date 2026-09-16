from polragion.models.work_item import PolarionWorkItem


def make_work_item(
    *,
    project_id: str = "DEMO",
    workitem_id: str = "REQ-123",
) -> PolarionWorkItem:
    return PolarionWorkItem(
        project_id=project_id,
        work_item_id=workitem_id,
        work_item_type="requirement",
        title="The system shall authenticate users",
        description="Users must authenticate before accessing protected resources.",
        revision=1,
        status="open",
        additional_fields={
            "work_item_type": "requirement",
            "priority": "high",
            "tags": ["secruity"]
        }
    )
