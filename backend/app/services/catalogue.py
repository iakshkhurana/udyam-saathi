from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from ..config import get_settings


@dataclass(frozen=True)
class CatalogueProduct:
    product_id: str
    category: str
    name: str
    description: str
    unit: str
    price_min: int
    price_max: int
    setup: int
    min_contract_months: int
    city_tiers: tuple[int, ...]
    min_employees: int
    min_sites: int
    requires_gstin: bool
    requires_one_of: tuple[str, ...]
    install_days: int
    segments: tuple[str, ...]

    def as_dict(self) -> dict:
        return {**self.__dict__, "city_tiers": list(self.city_tiers),
                "requires_one_of": list(self.requires_one_of), "segments": list(self.segments)}


def _split(value, sep: str) -> tuple[str, ...]:
    return tuple(v.strip() for v in str(value).split(sep) if v.strip()) if pd.notna(value) else ()


@lru_cache
def get_catalogue() -> dict[str, CatalogueProduct]:
    df = pd.read_csv(get_settings().data_path / "product_catalogue.csv")
    return {r.product_id: CatalogueProduct(
        product_id=r.product_id, category=r.category, name=r.product_name, description=r.description,
        unit=r.unit.replace("per ", "").strip(), price_min=int(r.price_min_inr_per_month),
        price_max=int(r.price_max_inr_per_month), setup=int(r.one_time_setup_inr),
        min_contract_months=int(r.min_contract_months),
        city_tiers=tuple(int(t) for t in _split(r.available_city_tiers, ";")),
        min_employees=int(r.min_employees), min_sites=int(r.min_sites), requires_gstin=r.requires_gstin == "Y",
        requires_one_of=_split(r.requires_one_of, "|"), install_days=int(r.typical_install_days),
        segments=_split(r.target_segments, ";"),
    ) for r in df.itertuples()}
