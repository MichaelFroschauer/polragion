# Synthetisches Polarion-Workitem-Testset

Enthaltene Workitems: **2000**

## Felder

- `title`
- `text` — HTML-Rich-Text mit Überschriften, Listen, Tabellen, Blockquotes und Code-Blöcken
- `revision`
- `status`
- `workitem_id`
- `linked_workitems` — Liste aus `id` und `role`
- `custom_fields` — realistische zusätzliche Felder wie Typ, Priorität, Komponente,
  Release, Autor, Assignee, Safety Class, Verifikationsmethode und Tags

## Formate

- `polarion_workitems_testset_2000.jsonl`: ein Workitem pro Zeile; für Streaming und Batch-Import
- `polarion_workitems_testset_2000.json`: vollständiges JSON-Array
- `load_polarion_testset.py`: einfaches Python-Ladebeispiel

Alle Daten sind vollständig synthetisch.
