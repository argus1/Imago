import pytest

from imago.storage.policy import DataClassification, FormatFamily, profile_for_format


@pytest.mark.unit
def test_profile_for_clinical_dicom() -> None:
    profile = profile_for_format("study/series/image.dcm")

    assert profile.family == FormatFamily.DICOM
    assert profile.classification == DataClassification.RESTRICTED_CLINICAL
    assert profile.clinical_source_of_truth is True
    assert profile.is_diagnostic is True


@pytest.mark.unit
def test_profile_for_research_formats() -> None:
    extensions = [".nii", ".nii.gz", ".nrrd", ".nhdr", ".mnc", ".hdr", ".img"]

    for ext in extensions:
        profile = profile_for_format(ext)
        assert profile.family == FormatFamily.NEURO_RESEARCH
        assert profile.classification == DataClassification.CONFIDENTIAL_RESEARCH
        assert profile.clinical_source_of_truth is False


@pytest.mark.unit
def test_profile_for_standard_derived_formats() -> None:
    for ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
        profile = profile_for_format(ext)
        assert profile.family == FormatFamily.STANDARD_DERIVED
        assert profile.classification == DataClassification.INTERNAL_DERIVED
        assert profile.is_diagnostic is False


@pytest.mark.unit
def test_profile_for_unknown_extension() -> None:
    profile = profile_for_format("scan.custom")

    assert profile.family == FormatFamily.UNKNOWN
    assert profile.classification == DataClassification.UNCLASSIFIED
