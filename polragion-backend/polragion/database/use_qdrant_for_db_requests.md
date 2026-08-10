Für eine reine Payload-Abfrage ohne Vektorsuche verwendest du in Qdrant am besten den **Scroll-Endpunkt**.

Ersetze `work_items` jeweils durch den Namen deiner Collection.

## 10 Work Items vom Typ „Product Test Case“

Im Qdrant-Dashboard unter **Console**:

```http
POST /collections/work_items/points/scroll
```

```json
{
  "filter": {
    "must": [
      {
        "key": "work_item_type",
        "match": {
          "value": "Product Test Case"
        }
      }
    ]
  },
  "limit": 10,
  "with_payload": true,
  "with_vector": false
}
```

Qdrant gibt damit bis zu zehn passende Points zurück. Der Scroll-Endpunkt ist für paginiertes Lesen mit optionalem Payload-Filter vorgesehen. ([api.qdrant.tech][1])

In PowerShell:

```powershell
$body = @{
    filter = @{
        must = @(
            @{
                key = "work_item_type"
                match = @{
                    value = "Product Test Case"
                }
            }
        )
    }
    limit = 10
    with_payload = $true
    with_vector = $false
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:6333/collections/work_items/points/scroll" `
    -ContentType "application/json" `
    -Body $body

$result.result.points
```

Oder mit dem Python-Client:

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(url="http://localhost:6333")

points, next_offset = client.scroll(
    collection_name="work_items",
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="work_item_type",
                match=models.MatchValue(
                    value="Product Test Case",
                ),
            ),
        ],
    ),
    limit=10,
    with_payload=True,
    with_vectors=False,
)

for point in points:
    print(point.payload)
```

Die Übereinstimmung ist exakt. Groß-/Kleinschreibung und Leerzeichen müssen daher mit dem gespeicherten Wert übereinstimmen.

## Alle verschiedenen Dokumente erhalten

Mit deinem aktuellen Payload ist das nicht sauber möglich. Du hast kein eigenes Dokumentfeld.

Deine Location enthält zwar das Dokument:

```text
default:/KEMRO/Safe/KeSafe_C5/modules/Product-Test/
SCP500-290716-426-001-ProductIntegrationtestSpecification/
workitems/SC5-23026/workitem.xml
```

Qdrant kann beim Faceting aber nicht automatisch einen einzelnen Pfadabschnitt aus `location` extrahieren. Außerdem ist dieser Wert:

```json
"_polragion_document_id": "KeSafe_C5:SC5-23026"
```

offenbar keine Dokument-ID, sondern eine zusammengesetzte **Work-Item-ID**.

Ich würde das Payload daher so erweitern:

```json
{
  "project_id": "KeSafe_C5",
  "document_id": "SCP500-290716-426-001-ProductIntegrationtestSpecification",
  "work_item_id": "SC5-23026",
  "work_item_type": "Product Test Case",

  "_polragion_work_item_id": "KeSafe_C5:SC5-23026",
  "_polragion_document_id": "KeSafe_C5:SCP500-290716-426-001-ProductIntegrationtestSpecification"
}
```

Danach kannst du Qdrants **Facet-Endpunkt** verwenden:

```http
POST /collections/work_items/facet
```

```json
{
  "key": "document_id",
  "limit": 1000,
  "exact": true
}
```

Das Ergebnis sieht ungefähr so aus:

```json
{
  "result": {
    "hits": [
      {
        "value": "SCP500-290716-426-001-ProductIntegrationtestSpecification",
        "count": 342
      },
      {
        "value": "SC5-265525-110-001-SystemSRS",
        "count": 156
      }
    ]
  }
}
```

Der Facet-Endpunkt liefert die unterschiedlichen Werte eines Payload-Feldes zusammen mit der Anzahl zugehöriger Points. `exact: true` fordert eine exakte Zählung an. ([api.qdrant.tech][2])

Nur für ein bestimmtes Projekt:

```json
{
  "key": "document_id",
  "limit": 1000,
  "exact": true,
  "filter": {
    "must": [
      {
        "key": "project_id",
        "match": {
          "value": "KeSafe_C5"
        }
      }
    ]
  }
}
```

## Payload-Indizes anlegen

Da du regelmäßig nach `work_item_type`, `project_id` und `document_id` filtern beziehungsweise gruppieren möchtest, solltest du Keyword-Indizes anlegen:

```http
PUT /collections/work_items/index
```

```json
{
  "field_name": "work_item_type",
  "field_schema": "keyword"
}
```

Dasselbe für die anderen Felder:

```json
{
  "field_name": "project_id",
  "field_schema": "keyword"
}
```

```json
{
  "field_name": "document_id",
  "field_schema": "keyword"
}
```

Qdrant empfiehlt Payload-Indizes für Felder, die regelmäßig in Filtern verwendet werden. Sie sind nicht zwingend für die Korrektheit, verbessern bei größeren Collections aber die Abfrageleistung. ([Qdrant][3])

Für dein Schema wäre daher diese Trennung eindeutig:

```text
_polragion_work_item_id = KeSafe_C5:SC5-23026
document_id             = SCP500-290716-426-001-ProductIntegrationtestSpecification
_polragion_document_id  = KeSafe_C5:SCP500-290716-426-001-ProductIntegrationtestSpecification
```

[1]: https://api.qdrant.tech/api-reference/points/scroll-points "Scroll points | Qdrant | API Reference"
[2]: https://api.qdrant.tech/api-reference/points/facet "Payload field facets | Qdrant | API Reference"
[3]: https://qdrant.tech/documentation/manage-data/indexing/ "Indexing - Qdrant"
