from uuid import UUID
from polragion.utils.general import StrictModel
from pydantic import AliasPath, BaseModel, ConfigDict, Field, computed_field, BeforeValidator


class CopilotSendMessage(StrictModel):
    user_id: UUID
    text: str
    display_text: str | None = None

class CopilotResponseMessage(StrictModel):
    text: str
    message_id: str | None = None
    is_final: bool = True

class CopilotMessageEvent(StrictModel):
    user_id: UUID
    message: CopilotResponseMessage

class CopilotModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        from_attributes=True,
        populate_by_name=True,
    )

    # Identification
    id: str
    name: str

    # Model picker metadata
    category: str | None = Field(default=None, validation_alias="model_picker_category")

    price_category: str | None = Field(default=None, validation_alias="model_picker_price_category")

    # Context limits
    max_context_tokens: int | None = Field(
        default=None,
        validation_alias=AliasPath(
            "capabilities",
            "limits",
            "max_context_window_tokens",
        ),
    )

    max_prompt_tokens: int | None = Field(
        default=None,
        validation_alias=AliasPath(
            "capabilities",
            "limits",
            "max_prompt_tokens",
        ),
    )

    max_output_tokens: int | None = Field(
        default=None,
        validation_alias=AliasPath(
            "capabilities",
            "limits",
            "max_output_tokens",
        ),
    )

    # Capabilities
    supports_vision: bool | None = Field(
        default=None,
        validation_alias=AliasPath(
            "capabilities",
            "supports",
            "vision",
        ),
    )

    supports_reasoning_effort: bool | None = Field(
        default=None,
        validation_alias=AliasPath(
            "capabilities",
            "supports",
            "reasoning_effort",
        ),
    )

    adaptive_thinking: str | None = Field(
        default=None,
        validation_alias=AliasPath(
            "capabilities",
            "supports",
            "adaptive_thinking",
        ),
    )

    # Reasoning
    default_reasoning_effort: str | None = None

    supported_reasoning_efforts: list[str] | None = None

    # GitHub / organization policy
    policy_state: str | None = Field(
        default=None,
        validation_alias=AliasPath(
            "policy",
            "state",
        ),
    )

    @computed_field
    @property
    def is_auto(self) -> bool:
        return self.id == "auto"
