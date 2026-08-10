from enum import StrEnum


class EvidenceType(StrEnum):
    FACT = "FACT"
    CALCULATION = "CALCULATION"
    ASSUMPTION = "ASSUMPTION"
    INTERPRETATION = "INTERPRETATION"
    OPINION = "OPINION"


class Recommendation(StrEnum):
    BUY = "BUY"
    WATCH = "WATCH"
    AVOID = "AVOID"
