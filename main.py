"""
    Google Photos Picker API.
"""
from gp_picker_api import api_helper

print("Google Photos Picker API Test")
print("=" * 40)

# Initialize the API client
picker_api = None
try:
    download_dir = "output"
    picker_api = api_helper.GooglePhotosPickerAPI(download_dir=download_dir)
except Exception as e:
    print(f"❌ Failed to initialize API client: {e}")
    exit(1)

# Run the complete workflow
downloaded_items = picker_api.run_complete_picking_workflow()

# Display results
if downloaded_items:
    print(f"\n📊 Summary:")
    print(f"Downloaded {len(downloaded_items)} files:")
    for item in downloaded_items:
        print(f"  • {item['mediaFile'].get('filename', 'unknown')}")
else:
    print("\n❌ No files were downloaded")
