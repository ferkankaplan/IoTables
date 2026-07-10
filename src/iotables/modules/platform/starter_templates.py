from dataclasses import dataclass


@dataclass(frozen=True)
class StarterProduct:
    station_name: str
    category_name: str
    product_name: str
    variant_name: str
    price_minor: int


@dataclass(frozen=True)
class StarterStaff:
    display_name: str
    username: str
    role: str
    station_name: str | None = None
    all_halls: bool = False


@dataclass(frozen=True)
class StarterTemplate:
    sector: str
    template_key: str
    template_version: int
    service_delivery_tracking_enabled: bool
    halls: tuple[str, ...]
    stations: tuple[str, ...]
    products: tuple[StarterProduct, ...]
    staff: tuple[StarterStaff, ...]


CAFE_V1_TEMPLATE = StarterTemplate(
    sector="cafe",
    template_key="cafe_default",
    template_version=1,
    service_delivery_tracking_enabled=True,
    halls=("Salon 1", "Salon 2"),
    stations=("Mutfak", "Kahve"),
    products=(
        StarterProduct("Mutfak", "Yiyecekler", "Sandviç", "Standart", 18000),
        StarterProduct("Mutfak", "Yiyecekler", "Tost", "Standart", 15000),
        StarterProduct("Mutfak", "Tatlılar", "Kurabiye", "Standart", 7500),
        StarterProduct("Mutfak", "Tatlılar", "Kek", "Standart", 9000),
        StarterProduct("Mutfak", "Yiyecekler", "Poğaça", "Standart", 7000),
        StarterProduct("Kahve", "Kahveler", "Kapuçino", "Standart", 12000),
        StarterProduct("Kahve", "Kahveler", "Americano", "Standart", 10000),
        StarterProduct("Kahve", "Kahveler", "Türk Kahvesi", "Standart", 9000),
        StarterProduct("Kahve", "Çaylar", "Çay", "Standart", 4000),
        StarterProduct("Kahve", "Kahveler", "Latte", "Standart", 12500),
        StarterProduct("Kahve", "Kahveler", "Espresso", "Standart", 8500),
    ),
    staff=(
        StarterStaff("Kasiyer", "kasiyer", "cashier"),
        StarterStaff("Aşçı", "asci", "station_staff", station_name="Mutfak"),
        StarterStaff("Barista", "barista", "station_staff", station_name="Kahve"),
        StarterStaff("Garson", "garson", "service_staff", all_halls=True),
        StarterStaff("Komi", "komi", "service_staff", all_halls=True),
    ),
)

STARTER_TEMPLATES = {CAFE_V1_TEMPLATE.sector: CAFE_V1_TEMPLATE}


def get_starter_template(sector: str) -> StarterTemplate | None:
    return STARTER_TEMPLATES.get(sector)
