from polragion.domain.work_item import CustomFields, PolarionWorkItem


def make_work_item(
    *,
    project_id: str = "DEMO",
    workitem_id: str = "REQ-123",
) -> PolarionWorkItem:
    return PolarionWorkItem(
        project_id=project_id,
        workitem_id=workitem_id,
        title="The system shall authenticate users",
        text="Users must authenticate before accessing protected resources.",
        revision=1,
        status="open",
        custom_fields=CustomFields(
            workitem_type="requirement",
            priority="high",
            tags=["security"],
        ),
    )
