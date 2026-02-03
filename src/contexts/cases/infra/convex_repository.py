"""
Cases Context: Convex Repository Implementation

Implements the case repository using the Convex cloud database.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.shared.common.types import CaseId, SourceId

if TYPE_CHECKING:
    from src.shared.infra.convex import ConvexClientWrapper


class ConvexCaseRepository:
    """
    Convex implementation of CaseRepository.

    Maps between domain Case entities and Convex cas_case documents.
    """

    def __init__(self, client: ConvexClientWrapper) -> None:
        self._client = client

    def get_all(self) -> list[Case]:
        """Get all cases."""
        docs = self._client.get_all_cases()
        cases = []
        for doc in docs:
            case = self._doc_to_case(doc)
            # Load attributes for each case
            attrs = self._load_attributes(case.id)
            case = Case(
                id=case.id,
                name=case.name,
                description=case.description,
                memo=case.memo,
                attributes=tuple(attrs),
                source_ids=case.source_ids,
                created_at=case.created_at,
                updated_at=case.updated_at,
            )
            cases.append(case)
        return cases

    def get_by_id(self, case_id: CaseId) -> Case | None:
        """Get a case by ID."""
        doc = self._client.get_case_by_id(case_id.value)
        if not doc:
            return None
        case = self._doc_to_case(doc)
        attrs = self._load_attributes(case_id)
        return Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=tuple(attrs),
            source_ids=case.source_ids,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def get_by_name(self, name: str) -> Case | None:
        """Get a case by name."""
        doc = self._client.query("cases:getByName", name=name)
        if not doc:
            return None
        case = self._doc_to_case(doc)
        attrs = self._load_attributes(case.id)
        return Case(
            id=case.id,
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=tuple(attrs),
            source_ids=case.source_ids,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def save(self, case: Case) -> None:
        """Save a case (insert or update)."""
        exists = self.get_by_id(case.id) is not None

        if exists:
            self._client.update_case(
                case.id.value,
                name=case.name,
                description=case.description,
                memo=case.memo,
                updated_at=case.updated_at.isoformat(),
            )
        else:
            self._client.mutation(
                "cases:create",
                name=case.name,
                description=case.description,
                memo=case.memo,
                created_at=case.created_at.isoformat(),
                updated_at=case.updated_at.isoformat(),
            )

        # Save attributes
        for attr in case.attributes:
            self.save_attribute(case.id, attr)

    def delete(self, case_id: CaseId) -> None:
        """Delete a case by ID."""
        self._client.delete_case(case_id.value)

    def get_cases_for_source(self, source_id: SourceId) -> list[Case]:
        """Get all cases linked to a source."""
        docs = self._client.query("cases:getCasesForSource", sourceId=source_id.value)
        cases = []
        for doc in docs:
            case = self._doc_to_case(doc)
            attrs = self._load_attributes(case.id)
            case = Case(
                id=case.id,
                name=case.name,
                description=case.description,
                memo=case.memo,
                attributes=tuple(attrs),
                source_ids=case.source_ids,
                created_at=case.created_at,
                updated_at=case.updated_at,
            )
            cases.append(case)
        return cases

    def link_source(
        self, case_id: CaseId, source_id: SourceId, source_name: str, owner: str
    ) -> None:
        """Link a source to a case."""
        self._client.mutation(
            "cases:linkSource",
            caseId=case_id.value,
            sourceId=source_id.value,
            sourceName=source_name,
            owner=owner,
            date=datetime.now(UTC).isoformat(),
        )

    def unlink_source(self, case_id: CaseId, source_id: SourceId) -> None:
        """Unlink a source from a case."""
        self._client.mutation(
            "cases:unlinkSource",
            caseId=case_id.value,
            sourceId=source_id.value,
        )

    def save_attribute(self, case_id: CaseId, attribute: CaseAttribute) -> None:
        """Save a case attribute."""
        value_text = None
        value_number = None
        value_date = None

        if attribute.attr_type == AttributeType.TEXT:
            value_text = str(attribute.value) if attribute.value else None
        elif attribute.attr_type == AttributeType.NUMBER:
            value_number = float(attribute.value) if attribute.value else None
        elif attribute.attr_type == AttributeType.DATE:
            value_date = attribute.value.isoformat() if attribute.value else None
        elif attribute.attr_type == AttributeType.BOOLEAN:
            value_text = str(attribute.value).lower() if attribute.value is not None else None

        self._client.mutation(
            "cases:saveAttribute",
            caseId=case_id.value,
            name=attribute.name,
            attrType=attribute.attr_type.value,
            valueText=value_text,
            valueNumber=value_number,
            valueDate=value_date,
        )

    def get_attributes(self, case_id: CaseId) -> list[CaseAttribute]:
        """Get all attributes for a case."""
        return self._load_attributes(case_id)

    def delete_attribute(self, case_id: CaseId, attribute_name: str) -> None:
        """Delete an attribute from a case."""
        self._client.mutation(
            "cases:deleteAttribute",
            caseId=case_id.value,
            attributeName=attribute_name,
        )

    def _load_attributes(self, case_id: CaseId) -> list[CaseAttribute]:
        """Load all attributes for a case from Convex."""
        docs = self._client.query("cases:getAttributes", caseId=case_id.value)
        return [self._doc_to_attribute(doc) for doc in docs]

    def _doc_to_case(self, doc: dict[str, Any]) -> Case:
        """Map Convex document to domain Case entity."""
        return Case(
            id=CaseId(value=doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            memo=doc.get("memo"),
            attributes=(),  # Loaded separately
            source_ids=(),  # Loaded separately if needed
            created_at=datetime.fromisoformat(doc["created_at"])
            if doc.get("created_at")
            else datetime.now(UTC),
            updated_at=datetime.fromisoformat(doc["updated_at"])
            if doc.get("updated_at")
            else datetime.now(UTC),
        )

    def _doc_to_attribute(self, doc: dict[str, Any]) -> CaseAttribute:
        """Map Convex document to domain CaseAttribute entity."""
        attr_type = AttributeType(doc["attr_type"])

        # Parse value based on type
        value: Any = None
        if attr_type == AttributeType.TEXT:
            value = doc.get("value_text")
        elif attr_type == AttributeType.NUMBER:
            value = doc.get("value_number")
        elif attr_type == AttributeType.DATE:
            value = (
                datetime.fromisoformat(doc["value_date"])
                if doc.get("value_date")
                else None
            )
        elif attr_type == AttributeType.BOOLEAN:
            text_val = doc.get("value_text")
            value = text_val.lower() == "true" if text_val else None

        return CaseAttribute(
            name=doc["name"],
            attr_type=attr_type,
            value=value,
        )
