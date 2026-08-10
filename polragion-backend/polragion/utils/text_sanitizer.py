import html
import re

from bs4 import BeautifulSoup, Comment, Tag, NavigableString
from markdownify import markdownify

from polragion.utils.general import StrictModel


class ParsedDocument(StrictModel):
    markdown: str
    embedding_text: str

ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\u2060\uFEFF]")

REMOVE_TAGS = {
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "canvas",
    "template",
    "object",
    "embed",
}

# These are usually navigation / surrounding page content rather than
# the actual document content.
BOILERPLATE_TAGS = {
    "nav",
    "footer",
    "aside",
}

BOILERPLATE_ROLES = {
    "navigation",
    "banner",
    "contentinfo",
    "complementary",
    "search",
}

HEADING_TAGS = {
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
}

CONTAINER_TAGS = {
    "html",
    "body",
    "main",
    "article",
    "section",
    "div",
    "header",
    "figure",
    "figcaption",
}

INLINE_FORMATTING_TAGS = {
    "a",
    "span",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "small",
    "mark",
    "sub",
    "sup",
    "code",
}

def _clean_text(value: str) -> str:
    """
    Normalize a small piece of plain text.

    Used for individual paragraphs, table cells, list items, etc.
    """
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = ZERO_WIDTH_RE.sub("", value)

    # Within a semantic text block, all whitespace is equivalent.
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _normalize_markdown(value: str) -> str:
    """
    Conservative Markdown normalization.

    Important:
    We intentionally do NOT globally collapse multiple spaces, because that
    could destroy indentation, code blocks, tables, etc.
    """
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = ZERO_WIDTH_RE.sub("", value)

    value = value.replace("\r\n", "\n")
    value = value.replace("\r", "\n")

    # Remove trailing whitespace.
    value = re.sub(r"[ \t]+\n", "\n", value)

    # Empty lines containing spaces/tabs.
    value = re.sub(r"\n[ \t]+\n", "\n\n", value)

    # At most one empty line between blocks.
    value = re.sub(r"\n{3,}", "\n\n", value)

    return value.strip()


def _normalize_embedding_text(value: str) -> str:
    """
    More aggressive normalization for embedding input.

    Unlike Markdown, formatting whitespace has no real semantic purpose here.
    """
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = ZERO_WIDTH_RE.sub("", value)

    value = value.replace("\r\n", "\n")
    value = value.replace("\r", "\n")

    lines: list[str] = []
    previous_was_blank = False

    for raw_line in value.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()

        if not line:
            if lines and not previous_was_blank:
                lines.append("")

            previous_was_blank = True
            continue

        lines.append(line)
        previous_was_blank = False

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# HTML sanitizing
# ---------------------------------------------------------------------------
def _is_hidden(tag: Tag) -> bool:
    """
    Detect common ways of hiding HTML elements.
    """
    if tag.has_attr("hidden"):
        return True

    if tag.has_attr("inert"):
        return True

    aria_hidden = tag.get("aria-hidden")

    if (
        isinstance(aria_hidden, str)
        and aria_hidden.strip().lower() == "true"
    ):
        return True

    style = tag.get("style")

    if isinstance(style, str):
        # Normalize CSS enough to catch:
        #
        # display: none
        # display:none
        # display: none !important
        #
        normalized_style = re.sub(r"\s+", "", style.lower())

        if re.search(r"(?:^|;)display:none(?:!important)?(?:;|$)", normalized_style):
            return True

        if re.search(r"(?:^|;)visibility:hidden(?:!important)?(?:;|$)", normalized_style):
            return True

    return False


def clean_html(value: str, *, remove_boilerplate: bool = True) -> BeautifulSoup:
    """
    Parse and clean HTML while preserving useful semantic structure.

    This cleaned DOM is then used independently for:
    - Markdown rendering
    - Embedding text generation
    """
    soup = BeautifulSoup(value, "html.parser")

    # Completely irrelevant / potentially dangerous elements
    for tag in soup.find_all(REMOVE_TAGS):
        tag.decompose()

    # HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Hidden elements
    # list(...) is intentional because we're modifying the DOM while
    # iterating over it.
    for tag in list(soup.find_all(True)):
        if _is_hidden(tag):
            tag.decompose()

    # Typical webpage boilerplate
    if remove_boilerplate:
        for tag in soup.find_all(BOILERPLATE_TAGS):
            tag.decompose()

        for tag in list(soup.find_all(attrs={"role": True})):
            role = tag.get("role")

            if not isinstance(role, str):
                continue

            roles = {
                item.strip().lower()
                for item in role.split()
            }

            if roles & BOILERPLATE_ROLES:
                tag.decompose()

    return soup


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def _soup_to_markdown(soup: BeautifulSoup) -> str:
    """
    Convert the cleaned DOM to mostly structure-preserving Markdown.
    """
    result = markdownify(
        str(soup),
        heading_style="ATX",
        bullets="-",
        strip=["span"],
    )

    return _normalize_markdown(result)


# ---------------------------------------------------------------------------
# Embedding tables
# ---------------------------------------------------------------------------

def _table_to_embedding_text(
    table: Tag,
) -> str:
    """
    Convert an HTML table into embedding-friendly plain text.

    Example:

        | Name | Role  | Age |
        |------|-------|-----|
        | Anna | Admin | 31  |
        | Max  | User  | 27  |

    becomes:

        Name: Anna
        Role: Admin
        Age: 31

        Name: Max
        Role: User
        Age: 27

    This makes individual rows much more self-contained for chunking
    and embedding.
    """

    html_rows = table.find_all("tr")

    if not html_rows:
        return ""

    parsed_rows: list[list[str]] = []

    for row in html_rows:
        cells = [
            _clean_text(cell.get_text(" ", strip=True))
            for cell in row.find_all(["th", "td"], recursive=False)
        ]

        if cells:
            parsed_rows.append(cells)

    if not parsed_rows:
        return ""

    # Treat the first row as a header only when it actually contains <th>.
    first_html_row = html_rows[0]

    has_header = bool(
        first_html_row.find_all(
            "th",
            recursive=False,
        )
    )

    if has_header:
        headers = parsed_rows[0]
        records: list[str] = []

        for cells in parsed_rows[1:]:
            fields: list[str] = []

            for index, value in enumerate(cells):
                if not value:
                    continue

                if (index < len(headers) and headers[index]):
                    header = headers[index]
                else:
                    header = f"Column {index + 1}"

                fields.append(f"{header}: {value}")

            if fields:
                records.append("\n".join(fields))

        if records:
            return "\n\n".join(records)

    # ------------------------------------------------------------------
    # Fallback
    #
    # Some HTML uses tables purely for layout or doesn't have real
    # headers. We don't want to invent semantics in that case.
    # ------------------------------------------------------------------

    result_rows: list[str] = []

    for index, cells in enumerate(parsed_rows, start=1):
        values = [cell for cell in cells if cell]

        if not values:
            continue

        result_rows.append(f"Row {index}: " + " | ".join(values))

    return "\n".join(result_rows)


# ---------------------------------------------------------------------------
# Embedding lists
# ---------------------------------------------------------------------------

def _text_without_nested_lists(li: Tag) -> str:
    """
    Extract the text belonging directly to a list item without accidentally
    including the complete text of nested lists.
    """
    clone = BeautifulSoup(
        str(li),
        "html.parser",
    )

    root = clone.find(li.name)

    if root is None:
        return _clean_text(li.get_text(" ", strip=True))

    for nested in root.find_all(["ul", "ol"]):
        nested.decompose()

    return _clean_text(root.get_text(" ", strip=True))


def _render_list(tag: Tag, blocks: list[str]) -> None:
    ordered = tag.name == "ol"
    index = 1

    for child in tag.children:
        if (
            not isinstance(child, Tag)
            or child.name != "li"
        ):
            continue

        text = _text_without_nested_lists(
            child
        )

        if text:
            if ordered:
                prefix = f"{index}. "
                index += 1
            else:
                prefix = "- "

            blocks.append(
                prefix + text
            )

        # Render directly nested lists afterwards.
        for nested_list in child.find_all(
            ["ul", "ol"],
            recursive=False,
        ):
            _render_list(
                nested_list,
                blocks,
            )


# ---------------------------------------------------------------------------
# Embedding DOM renderer
# ---------------------------------------------------------------------------

def _render_embedding_node(
    node: Tag | NavigableString,
    blocks: list[str],
) -> None:
    """
    Convert an individual DOM node into embedding-friendly semantic blocks.
    """

    # Plain text directly inside a container
    if isinstance(
        node,
        NavigableString,
    ):
        text = _clean_text(str(node))

        if text:
            blocks.append(text)

        return

    if not isinstance(node, Tag):
        return

    name = node.name.lower()

    # Headings
    if name in HEADING_TAGS:
        text = _clean_text(
            node.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            level = int(name[1])

            if level == 1:
                label = "Title"
            else:
                label = "Section"

            blocks.append(
                f"{label}: {text}"
            )

        return

    # Tables
    if name == "table":
        text = _table_to_embedding_text(
            node
        )

        if text:
            blocks.append(text)

        return

    # Lists
    if name in {"ul", "ol"}:
        _render_list(
            node,
            blocks,
        )
        return

    # Paragraphs
    if name == "p":
        text = _clean_text(
            node.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            blocks.append(text)

        return

    # Quotes
    if name == "blockquote":
        text = _clean_text(
            node.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            blocks.append(
                f"Quote: {text}"
            )

        return

    # Code blocks
    if name == "pre":
        code = node.get_text(
            "\n",
            strip=True,
        )

        code = html.unescape(code)
        code = code.replace("\xa0", " ")
        code = ZERO_WIDTH_RE.sub(
            "",
            code,
        )
        code = code.strip()

        if code:
            blocks.append(
                f"Code:\n{code}"
            )

        return

    # Definition lists
    #
    # <dl>
    #   <dt>Name</dt>
    #   <dd>Anna</dd>
    # </dl>
    #
    # -> Name: Anna
    if name == "dl":
        items: list[str] = []
        current_term: str | None = None

        for child in node.children:
            if not isinstance(child, Tag):
                continue

            if child.name == "dt":
                current_term = _clean_text(
                    child.get_text(
                        " ",
                        strip=True,
                    )
                )

            elif child.name == "dd":
                value = _clean_text(
                    child.get_text(
                        " ",
                        strip=True,
                    )
                )

                if not value:
                    continue

                if current_term:
                    items.append(
                        f"{current_term}: {value}"
                    )
                else:
                    items.append(value)

        if items:
            blocks.append(
                "\n".join(items)
            )

        return

    # Images
    # URLs are not interesting for embeddings, but alt text can be.
    if name == "img":
        alt = node.get("alt")

        if isinstance(alt, str):
            alt = _clean_text(alt)

            if alt:
                blocks.append(
                    f"Image: {alt}"
                )

        return

    # <br> is handled by the surrounding block.
    if name == "br":
        return

    # Semantic/container elements
    if name in CONTAINER_TAGS:
        for child in node.children:
            _render_embedding_node(
                child,
                blocks,
            )

        return

    # Unknown tags
    #
    # Don't discard them. Recursively inspect their children so things like
    # <strong>, <a>, <em>, custom elements, etc. keep their textual content.
    children = list(node.children)

    if children:
        for child in children:
            _render_embedding_node(
                child,
                blocks,
            )
    else:
        text = _clean_text(
            node.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            blocks.append(text)


def _soup_to_embedding_text(
    soup: BeautifulSoup,
) -> str:
    """
    Generate embedding-friendly text from the cleaned DOM.

    We intentionally reparse the soup so future embedding-specific DOM
    transformations cannot accidentally affect Markdown generation.
    """
    embedding_soup = BeautifulSoup(str(soup), "html.parser")

    # Remove inline formatting elements but KEEP their textual content.
    for tag in list(embedding_soup.find_all(INLINE_FORMATTING_TAGS)):
        tag.unwrap()

    # After unwrap(), BeautifulSoup may contain multiple adjacent
    embedding_soup.smooth()

    blocks: list[str] = []

    root: Tag | BeautifulSoup

    if embedding_soup.body:
        root = embedding_soup.body
    else:
        root = embedding_soup

    for child in root.children:
        _render_embedding_node(child, blocks)

    text = "\n\n".join(block for block in blocks if block.strip())

    return _normalize_embedding_text(text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def html_to_document(value: str | None, *, remove_boilerplate: bool = True) -> ParsedDocument | None:
    """
    Recommended entry point.

    Generates both:
    - structure-preserving Markdown
    - normalized embedding text

    from the same cleaned HTML document.
    """
    if not value or not value.strip():
        return ParsedDocument(markdown="", embedding_text="")

    soup = clean_html(value, remove_boilerplate=remove_boilerplate)
    markdown = _soup_to_markdown(soup)
    embedding_text = _soup_to_embedding_text(soup)

    if not markdown and not embedding_text:
        return None

    return ParsedDocument(
        markdown=markdown,
        embedding_text=embedding_text,
    )


def html_to_markdown(
    value: str | None,
    *,
    remove_boilerplate: bool = True,
) -> str | None:
    """
    Convenience wrapper if only Markdown is needed.
    """
    document = html_to_document(
        value,
        remove_boilerplate=remove_boilerplate,
    )

    if document is None:
        return None

    return document.markdown


def html_to_embedding_text(
    value: str | None,
    *,
    remove_boilerplate: bool = True,
) -> str | None:
    """
    Convenience wrapper if only embedding text is needed.
    """
    document = html_to_document(
        value,
        remove_boilerplate=remove_boilerplate,
    )

    if document is None:
        return None

    return document.embedding_text