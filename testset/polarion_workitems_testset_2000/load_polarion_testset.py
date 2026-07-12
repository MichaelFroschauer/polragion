import json
import uuid
from pathlib import Path

from qdrant_client import QdrantClient, models


DATA_FILE = Path("polarion_workitems_testset_2000.jsonl")
COLLECTION_NAME = "polarion_workitems"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
BATCH_SIZE = 128

# Stabiler Namespace: dieselbe Polarion-ID erzeugt bei jedem Import dieselbe UUID.
POINT_ID_NAMESPACE = uuid.UUID("8604873a-0779-49ef-81c4-840c4567d718")


def iter_workitems(path: Path):
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Ungültiges JSON in Zeile {line_number}"
                ) from exc


def chunks(iterable, size):
    batch = []

    for item in iterable:
        batch.append(item)

        if len(batch) >= size:
            yield batch
            batch = []

    if batch:
        yield batch


def qdrant_point_id(workitem_id: str) -> str:
    """Erzeugt eine deterministische UUID aus der Polarion-Workitem-ID."""
    return str(uuid.uuid5(POINT_ID_NAMESPACE, workitem_id))


def main() -> None:
    client = QdrantClient(url="http://localhost:6333")

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=client.get_embedding_size(MODEL_NAME),
                distance=models.Distance.COSINE,
            ),
        )

    imported = 0

    for batch in chunks(iter_workitems(DATA_FILE), BATCH_SIZE):
        client.upload_collection(
            collection_name=COLLECTION_NAME,
            ids=[
                qdrant_point_id(item["workitem_id"])
                for item in batch
            ],
            vectors=[
                models.Document(
                    text=f'{item["title"]}\n\n{item["text"]}',
                    model=MODEL_NAME,
                )
                for item in batch
            ],
            payload=batch,
        )

        imported += len(batch)
        print(f"{imported} Workitems importiert")

    print("Import abgeschlossen.")


if __name__ == "__main__":
    main()
