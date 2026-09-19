import logging
from collections.abc import Iterable, Mapping
from itertools import batched
from time import perf_counter
from typing import Any, Final, Collection

from fastembed import SparseEmbedding, SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import CollectionInfo, Filter

from polragion.application.work_item_mapper import work_item_payload_to_reranker_text
from polragion.domain.vector_store import JsonValue, VectorDocument, VectorSearchHit
from polragion.infrastructure.db_filter import DbFilter, FilterType
from polragion.infrastructure.errors import (
    VectorStoreConfigurationError,
    VectorStoreUnavailableError,
)
from polragion.infrastructure.qdrant_utils import (
    _DOCUMENT_ID_PAYLOAD_KEY,
    _RESERVED_PAYLOAD_KEYS,
    qdrant_point_id,
    register_custom_fastembed_models,
)
from polragion.settings import Settings

logger = logging.getLogger(__name__)

_DENSE_VECTOR_NAME: Final = "text-dense"
_SPARSE_VECTOR_NAME: Final = "text-sparse"
# The revision key MUST be set for every ingested document, otherwise it will not be possible to track changes.
_REVISION_PAYLOAD_KEY: Final = "revision"
# These models require a language specification to function correctly.
_BM25_MODEL_NAME: Final = "Qdrant/bm25"
# Documents are sorted by length within a window of this many batches before embedding.
_LENGTH_SORT_WINDOW_BATCHES: Final = 16


def _get_qdrant_filter(db_filters: Collection[DbFilter] | None) -> models.Filter:

    if db_filters is None or len(db_filters) <= 0:
        return models.Filter()

    def _get_condition(db_filter: DbFilter) -> models.FieldCondition:
        match db_filter.filter_type:
            case FilterType.MUST_MATCH:
                if isinstance(db_filter.value, list):
                    raise ValueError(f"Filter '{db_filter.key}' of type {db_filter.filter_type} needs a single value")

                return models.FieldCondition(
                    key=db_filter.key,
                    match=models.MatchValue(value=db_filter.value),
                )

            case FilterType.MUST_MATCH_ANY:
                values = db_filter.value if isinstance(db_filter.value, list) else [db_filter.value]
                if not values:
                    raise ValueError(f"Filter '{db_filter.key}' of type {db_filter.filter_type} needs at least one value")

                return models.FieldCondition(
                    key=db_filter.key,
                    match=models.MatchAny(any=values),
                )

            case _:
                raise ValueError(f"Unsupported filter type: {db_filter.filter_type}")

    return models.Filter(
        must=[
            _get_condition(db_filter)
            for db_filter in db_filters
        ]
    )


class QdrantHybridVectorStore:
    """
    Dense+sparse retrieval with Qdrant RRF and FastEmbed reranking.
    """

    def __init__(self, settings: Settings) -> None:
        self._initialized = False

        self._settings = settings
        self._collection_name = settings.qdrant_collection_name
        self._dense_model_name = settings.fastembed_dense_model
        self._sparse_model_name = settings.fastembed_sparse_model
        self._reranker_model_name = settings.fastembed_reranker_model
        self._candidate_limit = max(1, int(getattr(settings, "qdrant_hybrid_candidate_limit", 50)))

        self._client = QdrantClient(url=settings.qdrant_url, timeout=settings.qdrant_client_timeout_seconds)
        self._sparse_model: SparseTextEmbedding | None = None
        self._dense_model: TextEmbedding | None = None
        self._reranker: TextCrossEncoder | None = None

    def initialize(self) -> None:
        self._initialized = False

        try:
            if not self._reranker_model_name:
                raise VectorStoreConfigurationError("fastembed_reranker_model must be configured")

            register_custom_fastembed_models()

            logger.info("Loading sparse model '%s'...", self._sparse_model_name)
            start = perf_counter()
            self._sparse_model = SparseTextEmbedding(model_name=self._sparse_model_name, cache_dir=self._settings.fastembed_cache_path, **self._sparse_model_kwargs())
            logger.info("Sparse model loaded in %.1fs", perf_counter() - start)

            logger.info("Loading dense model '%s'...", self._dense_model_name)
            start = perf_counter()
            self._dense_model = TextEmbedding(model_name=self._dense_model_name, cache_dir=self._settings.fastembed_cache_path)
            self._apply_dense_max_tokens()
            logger.info("Dense model loaded in %.1fs",perf_counter() - start)

            logger.info("Loading reranker '%s'...", self._reranker_model_name)
            start = perf_counter()
            self._reranker = TextCrossEncoder(model_name=self._reranker_model_name, cache_dir=self._settings.fastembed_cache_path)
            logger.info("Reranker loaded in %.1fs", perf_counter() - start)

            logger.info("Determining dense embedding size...")
            expected_size = self._client.get_embedding_size(self._dense_model_name)
            logger.info("Dense embedding size: %d", expected_size)

            if not self._client.collection_exists(self._collection_name):
                logger.info(
                    "Creating Qdrant collection '%s' with dense model '%s', "
                    "sparse model '%s', and reranker '%s'",
                    self._collection_name,
                    self._dense_model_name,
                    self._sparse_model_name,
                    self._reranker_model_name,
                )
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config={
                        _DENSE_VECTOR_NAME: models.VectorParams(
                            size=expected_size,
                            distance=models.Distance.COSINE,
                        )
                    },
                    sparse_vectors_config={
                        _SPARSE_VECTOR_NAME: models.SparseVectorParams(
                            index=models.SparseIndexParams(on_disk=True),
                            modifier=self._sparse_modifier(),
                        )
                    },
                    metadata={
                        "schema_version": self._settings.index_schema_version,
                        "embedding_models": {
                            "dense_model": self._dense_model_name,
                            "dense_max_tokens": self._dense_max_tokens(),
                            "sparse_model": self._sparse_model_name,
                            "sparse_language": self._sparse_language(),
                        }
                    },
                )

            collection_info: CollectionInfo = self._client.get_collection(self._collection_name)
            self._validate_collection(collection_info, expected_size)
            self._initialized = True

            logger.info("Using validated Qdrant collection '%s'", self._collection_name)

        except VectorStoreConfigurationError:
            self._initialized = False
            raise
        except Exception as exc:
            self._initialized = False
            raise VectorStoreUnavailableError(f"Could not initialize Qdrant at {self._settings.qdrant_url}") from exc

    def upsert(self, documents: Iterable[VectorDocument]) -> None:
        self._ensure_initialized()

        for document_batch in self._length_sorted_batches(documents):
            document_list = list(document_batch)
            if not document_list:
                continue

            if not self._validate_document_metadata(document_list):
                logger.error("Discard batch, because items contains reserved key ...")
                continue

            document_list = self._drop_unchanged_documents(document_list)
            if not document_list:
                continue

            dense_texts = [document.dense_text for document in document_list]
            sparse_texts = [document.sparse_text for document in document_list]

            try:
                dense_embeddings = self._make_dense_passage_embeddings(dense_texts)
                sparse_embeddings = self._make_sparse_passage_embeddings(sparse_texts)

                if not (len(document_list) == len(dense_embeddings) == len(sparse_embeddings)):
                    raise VectorStoreUnavailableError("FastEmbed returned an unexpected number of embeddings")

                points: list[models.PointStruct] = []
                for document, dense_embedding, sparse_embedding in zip(
                    document_list,
                    dense_embeddings,
                    sparse_embeddings,
                    strict=True,
                ):
                    payload = dict(document.metadata)
                    payload[_DOCUMENT_ID_PAYLOAD_KEY] = document.id

                    points.append(
                        models.PointStruct(
                            id=qdrant_point_id(document.id),
                            vector={
                                _DENSE_VECTOR_NAME: dense_embedding.tolist(),
                                _SPARSE_VECTOR_NAME: models.SparseVector(
                                    indices=sparse_embedding.indices.tolist(),
                                    values=sparse_embedding.values.tolist(),
                                ),
                            },
                            payload=payload,
                        )
                    )

                logger.info(
                    "Uploading %d points to Qdrant, text chars=%d, max text chars=%d",
                    len(points),
                    sum(len(document.sparse_text) for document in document_list),
                    max(len(document.sparse_text) for document in document_list),
                )
                self._client.upsert(
                    collection_name=self._collection_name,
                    points=points,
                    wait=True,
                )
                # self._client.upload_points(
                #     collection_name=self._collection_name,
                #     points=points,
                #     batch_size=self._settings.qdrant_batch_size,
                #     parallel=self._settings.qdrant_upload_parallel,
                #     wait=True,
                # )
            except VectorStoreConfigurationError:
                raise
            except VectorStoreUnavailableError:
                raise
            except Exception as exc:
                raise VectorStoreUnavailableError("Qdrant ingestion failed") from exc

    def ensure_payload_indexes(self, keys: Collection[str]) -> None:
        self._ensure_initialized()

        # The document id backs the exact lookup path and is always indexed.
        for key in dict.fromkeys((_DOCUMENT_ID_PAYLOAD_KEY, *keys)):
            try:
                self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name=key,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                    wait=True,
                )
            except Exception as exc:
                raise VectorStoreUnavailableError(f"Could not create payload index for '{key}'") from exc

        logger.info("Payload indexes ensured for: %s", ", ".join(dict.fromkeys((_DOCUMENT_ID_PAYLOAD_KEY, *keys))))

    def search(
        self,
        query: str,
        *,
        limit: int,
        db_filters: Collection[DbFilter] | None = None,
        exact_search: bool = False,
        score_threshold: float | None = None,
        **kwargs
    ) -> list[VectorSearchHit]:
        if limit <= 0 or not query.strip():
            return []

        self._ensure_initialized()

        db_filter = _get_qdrant_filter(db_filters)
        if exact_search:
            hits = self._exact_search_by_filter(db_filter)
            return hits

        candidate_limit = max(limit, self._candidate_limit)

        try:
            dense_query = self._make_dense_query_embedding(query)
            sparse_query = self._make_sparse_query_embedding(query)

            response = self._client.query_points(
                collection_name=self._collection_name,
                prefetch=[
                    models.Prefetch(
                        query=dense_query,
                        using=_DENSE_VECTOR_NAME,
                        limit=candidate_limit,
                    ),
                    models.Prefetch(
                        query=sparse_query,
                        using=_SPARSE_VECTOR_NAME,
                        limit=candidate_limit,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                query_filter=db_filter,
                limit=candidate_limit,
                score_threshold=score_threshold,
                with_payload=True,
            )

            if not kwargs.get("do_reranking", False):
                hits: list[VectorSearchHit] = []
                for point in response.points:
                    if point.payload is None:
                        continue

                    payload = dict(point.payload)
                    document_id = str(payload.pop(_DOCUMENT_ID_PAYLOAD_KEY, point.id))
                    for key in _RESERVED_PAYLOAD_KEYS:
                        payload.pop(key, None)

                    hits.append(
                        VectorSearchHit(
                            document_id=document_id,
                            point_id=str(point.id),
                            score=float(point.score),
                            reranker_score=None,
                            metadata=self._as_json_mapping(payload),
                        )
                    )
                    if len(hits) >= limit:
                        break

            else:
                candidates: list[tuple[models.ScoredPoint, dict[str, Any], str]] = []

                for point in response.points:
                    if point.payload is None:
                        continue

                    payload = dict(point.payload)
                    # TODO: Maybe make the reranker text generation more generic and the specific function not a dependency here
                    document_reranker_text = work_item_payload_to_reranker_text(payload)
                    candidates.append((point, payload, document_reranker_text))

                if not candidates:
                    return []

                reranker = self._require_reranker()
                rerank_scores = list(
                    reranker.rerank(
                        query,
                        [document_text for _, _, document_text in candidates],
                        batch_size=self._settings.fastembed_reranker_batch_size,
                    )
                )
                if len(rerank_scores) != len(candidates):
                    raise VectorStoreUnavailableError("FastEmbed reranker returned an unexpected number of scores")

                ranked = sorted(
                    zip(candidates, rerank_scores, strict=True),
                    key=lambda item: (float(item[1]), float(item[0][0].score)),
                    reverse=True,
                )

                hits: list[VectorSearchHit] = []
                for (point, payload, _), rerank_score in ranked:

                    document_id = str(payload.pop(_DOCUMENT_ID_PAYLOAD_KEY, point.id))
                    for key in _RESERVED_PAYLOAD_KEYS:
                        payload.pop(key, None)

                    hits.append(
                        VectorSearchHit(
                            document_id=document_id,
                            point_id=str(point.id),
                            score=float(point.score),
                            reranker_score=float(rerank_score),
                            metadata=self._as_json_mapping(payload),
                        )
                    )
                    if len(hits) >= limit:
                        break

            return hits
        except VectorStoreConfigurationError:
            raise
        except VectorStoreUnavailableError:
            raise
        except (UnexpectedResponse, OSError, TimeoutError) as exc:
            raise VectorStoreUnavailableError("Qdrant search failed") from exc
        except Exception as exc:
            raise VectorStoreUnavailableError("Qdrant search failed") from exc

    def get_facet(self, key: str) -> list[str]:

        self._ensure_initialized()

        result = self._client.facet(
            collection_name=self._collection_name,
            key=key,
            limit=1000,
            exact=True,
        )

        return [str(hit.value) for hit in result.hits]

    def _make_sparse_passage_embeddings(
        self, texts: Iterable[str]
    ) -> list[SparseEmbedding]:
        model = self._require_sparse_model()
        return list(
            model.passage_embed(
                texts,
                batch_size=self._settings.qdrant_batch_size,
                parallel=self._settings.fastembed_parallel,
            )
        )

    def _make_dense_passage_embeddings(self, texts: Iterable[str]) -> list[Any]:
        model = self._require_dense_model()
        return list(
            model.passage_embed(
                texts,
                batch_size=self._settings.qdrant_batch_size,
                parallel=self._settings.fastembed_parallel,
            )
        )

    def _make_sparse_query_embedding(self, query: str) -> models.SparseVector:
        model = self._require_sparse_model()
        embedding = next(
            iter(
                model.query_embed(
                    query,
                    batch_size=1,
                    parallel=self._settings.fastembed_parallel,
                )
            )
        )
        return models.SparseVector(
            indices=embedding.indices.tolist(),
            values=embedding.values.tolist(),
        )

    def _make_dense_query_embedding(self, query: str) -> list[float]:
        model = self._require_dense_model()
        embedding = next(
            iter(
                model.query_embed(
                    query,
                    batch_size=1,
                    parallel=self._settings.fastembed_parallel,
                )
            )
        )
        return embedding.tolist()

    def _validate_collection(self, collection_info: CollectionInfo, expected_dense_size: int) -> None:
        collection = self._client.get_collection(self._collection_name)
        vectors = collection.config.params.vectors
        sparse_vectors = collection.config.params.sparse_vectors or {}

        if not isinstance(vectors, dict):
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' uses an unnamed dense "
                "vector and must be recreated or migrated for hybrid search"
            )

        dense_config = vectors.get(_DENSE_VECTOR_NAME)
        if dense_config is None:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' is missing dense vector "
                f"'{_DENSE_VECTOR_NAME}'"
            )
        if dense_config.size != expected_dense_size:
            raise VectorStoreConfigurationError(
                f"Dense vector '{_DENSE_VECTOR_NAME}' has size "
                f"{dense_config.size}, expected {expected_dense_size}"
            )
        if dense_config.distance != models.Distance.COSINE:
            raise VectorStoreConfigurationError(
                f"Dense vector '{_DENSE_VECTOR_NAME}' must use cosine distance"
            )

        sparse_config = sparse_vectors.get(_SPARSE_VECTOR_NAME)
        if sparse_config is None:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' is missing sparse vector "
                f"'{_SPARSE_VECTOR_NAME}'"
            )

        expected_modifier = self._sparse_modifier()
        if sparse_config.modifier != expected_modifier:
            expected = expected_modifier.value if expected_modifier else None
            actual = sparse_config.modifier.value if sparse_config.modifier else None

            raise VectorStoreConfigurationError(
                f"Sparse vector '{_SPARSE_VECTOR_NAME}' has modifier "
                f"'{actual}', expected '{expected}' for model "
                f"'{self._sparse_model_name}'"
            )

        collection_metadata = collection_info.config.metadata
        if not collection_metadata:
            logger.warning(f"Collection '{self._collection_name}' has no metadata to check embedding and reranker models.")
            return

        collection_embedding_info = collection_metadata["embedding_models"]
        if not collection_embedding_info["dense_model"]:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' was created without saving the used dense embedding model as metadata."
            )

        if self._settings.fastembed_dense_model != collection_embedding_info["dense_model"]:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' uses different dense embedding model "
                f"configured in settings: '{self._settings.fastembed_dense_model}' "
                f"embedding model of collection: '{collection_embedding_info["dense_model"]}'."
            )

        if not collection_embedding_info["sparse_model"]:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' was created without saving the used sparse embedding model as metadata."
            )

        if self._settings.fastembed_sparse_model != collection_embedding_info["sparse_model"]:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' uses different sparse embedding model "
                f"configured in settings: '{self._settings.fastembed_sparse_model}' "
                f"embedding model of collection: '{collection_embedding_info["sparse_model"]}'."
            )

        expected_sparse_language = self._sparse_language()
        if expected_sparse_language != collection_embedding_info.get("sparse_language"):
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' uses different sparse tokenizer language "
                f"configured in settings: '{expected_sparse_language}' "
                f"language of collection: '{collection_embedding_info.get("sparse_language")}'."
            )

        expected_dense_max_tokens = self._dense_max_tokens()
        if expected_dense_max_tokens != collection_embedding_info.get("dense_max_tokens"):
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' uses different dense truncation limit "
                f"configured in settings: '{expected_dense_max_tokens}' "
                f"limit of collection: '{collection_embedding_info.get("dense_max_tokens")}'."
            )

        # Validate reranker not needed!
        # Because the ingesting documents does not need the reranker, so the reranker could be changed anytime.


    def _validate_document_metadata(
        self, documents: Iterable[VectorDocument]
    ) -> bool:
        reserved_keys = set(_RESERVED_PAYLOAD_KEYS)
        reserved_keys.update(
            {
                _DOCUMENT_ID_PAYLOAD_KEY,
            }
        )

        contains_reserved_keys = False
        for document in documents:
            collisions = reserved_keys.intersection(document.metadata)
            if collisions:
                keys = ", ".join(sorted(collisions))
                logger.error(f"Document '{document.id}' metadata uses reserved keys: {keys}")
                contains_reserved_keys = True

        return not contains_reserved_keys


    def _length_sorted_batches(
        self, documents: Iterable[VectorDocument]
    ) -> Iterable[tuple[VectorDocument, ...]]:
        """Group similar-length documents, FastEmbed pads every batch to its longest sequence."""

        batch_size = self._settings.qdrant_batch_size
        for window in batched(documents, batch_size * _LENGTH_SORT_WINDOW_BATCHES):
            ordered = sorted(window, key=lambda document: len(document.dense_text))
            yield from batched(ordered, batch_size)


    def _drop_unchanged_documents(self, documents: list[VectorDocument]) -> list[VectorDocument]:
        """Skip documents whose indexed revision still matches, embedding dominates ingest cost."""

        point_ids = [qdrant_point_id(document.id) for document in documents]
        stored_points = self._client.retrieve(
            collection_name=self._collection_name,
            ids=point_ids,
            with_payload=[_REVISION_PAYLOAD_KEY],
            with_vectors=False,
        )
        stored_revisions = {
            str(point.id): (point.payload or {}).get(_REVISION_PAYLOAD_KEY)
            for point in stored_points
        }

        changed_documents = [
            document
            for document, point_id in zip(documents, point_ids, strict=True)
            if document.metadata.get(_REVISION_PAYLOAD_KEY) is None
            or document.metadata[_REVISION_PAYLOAD_KEY] != stored_revisions.get(point_id)
        ]

        skipped = len(documents) - len(changed_documents)
        if skipped:
            logger.info("Skipping %d of %d document(s) with unchanged revision", skipped, len(documents))

        return changed_documents


    def _dense_max_tokens(self) -> int | None:
        return self._settings.fastembed_dense_max_tokens


    def _apply_dense_max_tokens(self) -> None:
        max_tokens = self._dense_max_tokens()
        if max_tokens is None:
            return

        # FastEmbed exposes no public knob, the truncation limit lives on the loaded tokenizer.
        self._require_dense_model().model.tokenizer.enable_truncation(max_length=max_tokens)
        logger.info("Dense tokenizer truncation set to %d tokens", max_tokens)


    def _sparse_language(self) -> str | None:
        # Only the BM25 sparse model is language aware, the ONNX models are not.
        if self._sparse_model_name.lower() != _BM25_MODEL_NAME.lower():
            return None
        return self._settings.fastembed_sparse_language


    def _sparse_model_kwargs(self) -> dict[str, Any]:
        language = self._sparse_language()
        return {} if language is None else {"language": language}


    def _sparse_modifier(self) -> models.Modifier | None:
        model_info = next(
            (
                model
                for model in SparseTextEmbedding.list_supported_models()
                if model["model"] == self._sparse_model_name
            ),
            None,
        )

        if model_info is None:
            raise VectorStoreConfigurationError(f"Unsupported sparse model '{self._sparse_model_name}'")

        if model_info.get("requires_idf"):
            return models.Modifier.IDF

        return None


    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise VectorStoreConfigurationError("QdrantHybridVectorStore.initialize() must complete successfully first")

        self._require_dense_model()
        self._require_sparse_model()
        self._require_reranker()

    def _require_dense_model(self) -> TextEmbedding:
        if self._dense_model is None:
            raise VectorStoreConfigurationError("QdrantHybridVectorStore.initialize() must be called first")
        return self._dense_model

    def _require_sparse_model(self) -> SparseTextEmbedding:
        if self._sparse_model is None:
            raise VectorStoreConfigurationError("QdrantHybridVectorStore.initialize() must be called first")
        return self._sparse_model

    def _require_reranker(self) -> TextCrossEncoder:
        if self._reranker is None:
            raise VectorStoreConfigurationError("QdrantHybridVectorStore.initialize() must be called first")
        return self._reranker

    def _exact_search_by_filter(self, db_filter: Filter) -> list[VectorSearchHit]:
        points, _ = self._client.scroll(
            collection_name=self._collection_name,
            scroll_filter=db_filter,
            with_payload=True,
            with_vectors=False,
        )

        results = []

        for point in points:
            payload = (
                self._as_json_mapping(dict(point.payload))
                if point.payload
                else {}
            )
            document_id = str(payload.pop(_DOCUMENT_ID_PAYLOAD_KEY, point.id))

            for key in _RESERVED_PAYLOAD_KEYS:
                payload.pop(key, None)

            results.append(
                VectorSearchHit(
                    document_id=document_id,
                    point_id=str(point.id),
                    score=1.0,
                    reranker_score=1.0,
                    metadata=payload,
                )
            )

        return results

    @staticmethod
    def _as_json_mapping(payload: Mapping[str, Any]) -> dict[str, JsonValue]:
        return dict(payload)  # type: ignore[return-value]

    def is_ready(self) -> bool:
        if not self._initialized:
            return False

        try:
            return self._client.collection_exists(self._collection_name)
        except Exception:
            logger.exception("Qdrant readiness check failed")
            return False

    def close(self) -> None:
        self._client.close()
