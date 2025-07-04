"""
Problem:
The library sometimes loads data in one format but expects it in another when saving.

Solutions:
1: Remove problematic fields before dumping - we use this solution here !
    exif_dict = fix_exif_types(exif_dict)
2. Fix ColorSpace field (exif_dict["Exif"][41729]) specifically
    exif_dict = fix_colorspace_field(exif_dict)
3. Clean EXIF dictionary by removing fields with incompatible types
    exif_dict = clean_exif_dict(exif_dict)
4. Complete solution:
    * Fix types
    + clean Program Name
    + add copyright
    + add artist
5. Batch processing function

Alternative:
    Use piexif.transplant() for safer copying
    This copies EXIF from one file to another without type issues:
    piexif.transplant(source_file, destination_file)

See also:
https://piexif.readthedocs.io/en/latest/functions.html
"""

from pathlib import Path
import piexif

# EXIF Personification
COPYRIGHT_TEXT = "©2025, Sergiy Zaytsev. All rights reserved."
ARTIST_TEXT = "Sergiy Zaytsev (https://zayarts.com)"

# Solution 1.
def fix_exif_types(exif_dict: dict) -> dict:
    """Remove or fix problematic EXIF fields that cause type errors"""

    # Fields that commonly cause issues
    problematic_fields = [
        41729,  # ColorSpace
        41730,  # WhitePoint
        41985,  # CustomRendered
        41986,  # ExposureMode
        41987,  # WhiteBalance
        41988,  # DigitalZoomRatio
        41989,  # FocalLengthIn35mmFilm
        41990,  # SceneCaptureType
        41991,  # GainControl
        41992,  # Contrast
        41993,  # Saturation
        41994,  # Sharpness
        41995,  # DeviceSettingDescription
        41996,  # SubjectDistanceRange
    ]

    # Remove problematic fields from Exif IFD
    if "Exif" in exif_dict:
        for field in problematic_fields:
            if field in exif_dict["Exif"]:
                del exif_dict["Exif"][field]

    return exif_dict

# Solution 2: Example.
# Fixing just ColorSpace field
# def fix_colorspace_field(exif_dict: dict) -> dict:
#     """Fix ColorSpace field specifically"""
#     if "Exif" in exif_dict and 41729 in exif_dict["Exif"]:
#         # Convert to tuple format that piexif expects
#         value = exif_dict["Exif"][41729]
#         if isinstance(value, int):
#             exif_dict["Exif"][41729] = (value,)  # Convert to tuple
#     return exif_dict


# Solution 3. Example.
# Clean EXIF dictionary by removing fields with incompatible types
# def clean_exif_dict(exif_dict: dict) -> dict:
#     """Clean EXIF dictionary by removing fields with incompatible types"""
#     clean_dict = {}
#
#     for ifd_name in exif_dict:
#         if ifd_name in ["0th", "Exif", "GPS", "1st", "thumbnail"]:
#             clean_dict[ifd_name] = {}
#
#             if isinstance(exif_dict[ifd_name], dict):
#                 for tag, value in exif_dict[ifd_name].items():
#                     try:
#                         # Test if the value can be dumped
#                         test_dict = {"Exif": {tag: value}}
#                         piexif.dump(test_dict)
#                         clean_dict[ifd_name][tag] = value
#                     except:
#                         # Skip problematic fields
#                         print(f"Skipping problematic field {tag}: {value}")
#             else:
#                 clean_dict[ifd_name] = exif_dict[ifd_name]
#
#     return clean_dict


def update_exif_metadata(file_path: Path, copyright_text: str='', artist_text: str='') -> dict:
    """ 1. Load EXIF data
        2. Fix EXIF types
        3. Update EXIF metadata:
        Remove "Software", add copyright, add artist
        4. Return updated EXIF metadata
    """
    # Load EXIF data
    exif_dict = piexif.load(str(file_path))

    # Fix problematic fields
    exif_dict = fix_exif_types(exif_dict)

    # Clean "Program Name" field: "Software" field in 0th IFD (tag 305)
    if "0th" in exif_dict and piexif.ImageIFD.Software in exif_dict["0th"]:
        del exif_dict["0th"][piexif.ImageIFD.Software]

    # Also check for "Software" in Exif IFD (sometimes it's there)
    if "Exif" in exif_dict and piexif.ImageIFD.Software in exif_dict["Exif"]:
        del exif_dict["Exif"][piexif.ImageIFD.Software]

    # Add Copyright information: Copyright field in 0th IFD (tag 33432)
    if "0th" not in exif_dict:
        exif_dict["0th"] = {}

    exif_dict["0th"][piexif.ImageIFD.Copyright] = copyright_text.encode('utf-8')

    # Add Artist field (tag 315)
    exif_dict["0th"][piexif.ImageIFD.Artist] = artist_text.encode('utf-8')

    return exif_dict

# Example:
# Batch processing function
# def batch_update_exif(file_paths: list, copyright_text: str='', artist_text: str='') -> dict:
#     """Update multiple files at once"""
#     for file_path in file_paths:
#         try:
#             exif_dict = update_exif_metadata(file_path, copyright_text, artist_text)
#             exif_bytes = piexif.dump(exif_dict)
#             piexif.insert(exif_bytes, str(file_path))
#             print(f"✅ Updated: {file_path}")
#         except Exception as e:
#             print(f"❌ Failed: {file_path} - {e}")

if __name__ == "__main__":

    # Replace with your data
    file_path = Path("..\downloads\<image_file>.jpg")
    copyright_text = "©2025, <user>. All rights reserved."  # optional
    artist_text = "<user> (<email>"                         # optional

    try:
        # Load EXIF data
        exif_dict = update_exif_metadata(file_path, copyright_text, artist_text)

        # Dump and insert
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, str(file_path))

        print("EXIF metadata updated successfully!")
        print(f"- Removed Program Name from Software field")
        print(f"- Added copyright: {copyright_text}")
        print(f"- Added artist: {artist_text}")

    except Exception as e:
        print(f"❌ Error updating EXIF: {e}")

