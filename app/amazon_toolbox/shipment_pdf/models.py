from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class FilenameShipmentInfo:
    factory_name: str = ""
    sku: str = ""
    product_name: str = ""
    country: str = ""
    warehouse: str = ""
    fba_code: str = ""
    box_count: int | None = None
    total_units: int | None = None
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "factory_name": self.factory_name,
            "sku": self.sku,
            "product_name": self.product_name,
            "country": self.country,
            "warehouse": self.warehouse,
            "fba_code": self.fba_code,
            "box_count": self.box_count,
            "total_units": self.total_units,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ShipmentRecord:
    source_path: Path
    original_filename: str
    sku: str
    product_name: str
    destination_country: str
    warehouse: str
    fba_code: str
    box_count: int
    carton_codes: tuple[str, ...]
    is_single_sku: bool
    quantity_per_box: int | None = None
    total_units: int | None = None
    label_title: str = ""
    title_product_name: str = ""
    created_at: str = ""
    filename_info: FilenameShipmentInfo = FilenameShipmentInfo()
    comparison_notes: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.notes and not self.filename_info.notes and not self.comparison_notes

    def with_paths(self, source_path: Path) -> "ShipmentRecord":
        return replace(self, source_path=source_path, original_filename=source_path.name)

    def as_dict(self) -> dict:
        return {
            "source_path": str(self.source_path),
            "original_filename": self.original_filename,
            "sku": self.sku,
            "product_name": self.product_name,
            "destination_country": self.destination_country,
            "warehouse": self.warehouse,
            "fba_code": self.fba_code,
            "box_count": self.box_count,
            "quantity_per_box": self.quantity_per_box,
            "total_units": self.total_units,
            "label_title": self.label_title,
            "title_product_name": self.title_product_name,
            "created_at": self.created_at,
            "filename_info": self.filename_info.as_dict(),
            "comparison_notes": list(self.comparison_notes),
            "carton_codes": list(self.carton_codes),
            "is_single_sku": self.is_single_sku,
            "is_valid": self.is_valid,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class RenamePlan:
    source_path: Path
    target_path: Path
    can_apply: bool
    reason: str

    def as_dict(self) -> dict:
        return {
            "source_path": str(self.source_path),
            "target_path": str(self.target_path),
            "target_filename": self.target_path.name,
            "can_apply": self.can_apply,
            "reason": self.reason,
        }
