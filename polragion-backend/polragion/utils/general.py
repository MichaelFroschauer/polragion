from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict

import html
import re

from bs4 import BeautifulSoup, Comment
from markdownify import markdownify

def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

def html_to_markdown(value: str | None) -> str | None:
    if not value:
        return None

    soup = BeautifulSoup(value, "html.parser")

    # Remove everything that should never be in a vector-db or an ai-prompt
    for tag in soup.find_all(
        ["script", "style", "noscript", "iframe", "svg", "canvas"]
    ):
        tag.decompose()

    # Remove HTML-comments
    for comment in soup.find_all(
        string=lambda text: isinstance(text, Comment)
    ):
        comment.extract()

    # Remove invisible text
    for tag in soup.find_all(style=True):
        style = tag.get("style", "").lower().replace(" ", "")

        if "display:none" in style or "visibility:hidden" in style:
            tag.decompose()

    # Convert HTML into markdown
    result = markdownify(
        str(soup),
        heading_style="ATX",
        bullets="-",
        strip=["span"],
    )

    # Decode HTML-entities
    result = html.unescape(result)
    result = result.replace("\xa0", " ")

    # Normalize whitespace
    result = re.sub(r"[ \t]+\n", "\n", result)
    result = re.sub(r"\n[ \t]+\n", "\n\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r"[ \t]{2,}", " ", result)

    return result.strip()
