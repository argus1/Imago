from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class DataClassification(StrEnum):
    RESTRICTED_CLINICAL = "restricted_clinical"
    CONFIDENTIAL_RESEARCH = "confidential_research"
    INTERNAL_DERIVED = "internal_derived"
    UNCLASSIFIED = "unclassified"


class FormatFamily(StrEnum):
    DICOM = "dicom"
    NEURO_RESEARCH = "neuro_research"
    STANDARD_DERIVED = "standard_derived"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FormatProfile:
    extension: str
    family: FormatFamily
    classification: DataClassification
    is_diagnostic: bool
    clinical_source_of_truth: bool


_FORMAT_PROFILES: dict[str, FormatProfile] = {
    "": FormatProfile(
        extension="",
        family=FormatFamily.DICOM,
        classification=DataClassification.RESTRICTED_CLINICAL,
        is_diagnostic=True,
        clinical_source_of_truth=True,
    ),
    ".dcm": FormatProfile(
        extension=".dcm",
        family=FormatFamily.DICOM,
        classification=DataClassification.RESTRICTED_CLINICAL,
        is_diagnostic=True,
        clinical_source_of_truth=True,
    ),
    ".nii": FormatProfile(
        extension=".nii",
        family=FormatFamily.NEURO_RESEARCH,
        classification=DataClassification.CONFIDENTIAL_RESEARCH,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".nii.gz": FormatProfile(
        extension=".nii.gz",
        family=FormatFamily.NEURO_RESEARCH,
        classification=DataClassification.CONFIDENTIAL_RESEARCH,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".nrrd": FormatProfile(
        extension=".nrrd",
        family=FormatFamily.NEURO_RESEARCH,
        classification=DataClassification.CONFIDENTIAL_RESEARCH,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".nhdr": FormatProfile(
        extension=".nhdr",
        family=FormatFamily.NEURO_RESEARCH,
        classification=DataClassification.CONFIDENTIAL_RESEARCH,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".mnc": FormatProfile(
        extension=".mnc",
        family=FormatFamily.NEURO_RESEARCH,
        classification=DataClassification.CONFIDENTIAL_RESEARCH,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".hdr": FormatProfile(
        extension=".hdr",
        family=FormatFamily.NEURO_RESEARCH,
        classification=DataClassification.CONFIDENTIAL_RESEARCH,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".img": FormatProfile(
        extension=".img",
        family=FormatFamily.NEURO_RESEARCH,
        classification=DataClassification.CONFIDENTIAL_RESEARCH,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".jpg": FormatProfile(
        extension=".jpg",
        family=FormatFamily.STANDARD_DERIVED,
        classification=DataClassification.INTERNAL_DERIVED,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".jpeg": FormatProfile(
        extension=".jpeg",
        family=FormatFamily.STANDARD_DERIVED,
        classification=DataClassification.INTERNAL_DERIVED,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".png": FormatProfile(
        extension=".png",
        family=FormatFamily.STANDARD_DERIVED,
        classification=DataClassification.INTERNAL_DERIVED,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".tif": FormatProfile(
        extension=".tif",
        family=FormatFamily.STANDARD_DERIVED,
        classification=DataClassification.INTERNAL_DERIVED,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
    ".tiff": FormatProfile(
        extension=".tiff",
        family=FormatFamily.STANDARD_DERIVED,
        classification=DataClassification.INTERNAL_DERIVED,
        is_diagnostic=False,
        clinical_source_of_truth=False,
    ),
}


def _normalize_extension(name_or_extension: str) -> str:
    value = name_or_extension.strip().lower()
    if value.endswith(".nii.gz"):
        return ".nii.gz"
    if value.startswith("."):
        return value

    ext = Path(value).suffix.lower()
    if ext == ".gz" and value.endswith(".nii.gz"):
        return ".nii.gz"
    return ext


def profile_for_format(name_or_extension: str) -> FormatProfile:
    extension = _normalize_extension(name_or_extension)
    return _FORMAT_PROFILES.get(
        extension,
        FormatProfile(
            extension=extension,
            family=FormatFamily.UNKNOWN,
            classification=DataClassification.UNCLASSIFIED,
            is_diagnostic=False,
            clinical_source_of_truth=False,
        ),
    )
