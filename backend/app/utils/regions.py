from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Region:
    id: int
    name: str
    short_name: str
    type: str

    def as_dict(self) -> dict:
        return asdict(self)


REGIONS: dict[int, Region] = {
    1: Region(1, "North Scotland", "North Scotland", "dno"),
    2: Region(2, "South Scotland", "South Scotland", "dno"),
    3: Region(3, "North West England", "North West England", "dno"),
    4: Region(4, "North East England", "North East England", "dno"),
    5: Region(5, "Yorkshire", "Yorkshire", "dno"),
    6: Region(6, "North Wales & Merseyside", "North Wales & Merseyside", "dno"),
    7: Region(7, "South Wales", "South Wales", "dno"),
    8: Region(8, "West Midlands", "West Midlands", "dno"),
    9: Region(9, "East Midlands", "East Midlands", "dno"),
    10: Region(10, "East England", "East England", "dno"),
    11: Region(11, "South West England", "South West England", "dno"),
    12: Region(12, "South England", "South England", "dno"),
    13: Region(13, "London", "London", "dno"),
    14: Region(14, "South East England", "South East England", "dno"),
    15: Region(15, "England", "England", "country"),
    16: Region(16, "Scotland", "Scotland", "country"),
    17: Region(17, "Wales", "Wales", "country"),
    18: Region(18, "Great Britain", "GB", "national"),
}


def get_region(provider_id: int) -> Region:
    return REGIONS.get(
        provider_id,
        Region(provider_id, f"Unknown region {provider_id}", f"Region {provider_id}", "unknown"),
    )
