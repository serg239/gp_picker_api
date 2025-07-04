# Google Photos Picker API workflow using sessions.
import os
import time
import secrets
import requests
from pathlib import Path
from typing import Dict, List     # ,Optional

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Datetime
from datetime import datetime
import pytz

# Exif info
import piexif

from .exif_helper import update_exif_metadata, COPYRIGHT_TEXT, ARTIST_TEXT


class GooglePhotosPickerAPI:
    """
    Google Photos Picker API client for creating sessions and retrieving selected photos.
    """

    # Required scope for Picker API
    SCOPES = ['https://www.googleapis.com/auth/photospicker.mediaitems.readonly']

    # API endpoints
    PICKER_API_BASE = 'https://photospicker.googleapis.com/v1'

    # Date and time format in UTC-to-Local transformations
    DT_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, credentials_path: str = '.env/client_secret.json',
                 token_path: str = '.env/token.json',
                 download_dir: str = 'downloads'):
        """
        Initialize the Google Photos Picker API client.

        Args:
            credentials_path: Path to OAuth 2.0 client secret JSON file
            token_path: Path to store the access token
            download_dir: Directory to save downloaded images
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)

        self.service = None
        self.credentials = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Photos Picker API using OAuth 2.0."""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for future use
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.credentials = creds
        # self.service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
        self.service = build('photospicker', 'v1', credentials=creds, static_discovery=False)
        print("Successfully authenticated with Google Photos Picker API")

    @staticmethod
    def generate_request_id() -> str:
        """
        Generate a UUID v4 string for request ID in the required format:
        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (8-4-4-4-12)
        Returns:
            str: UUID v4 formatted request ID
        """
        # Generate 32 random hexadecimal characters (16 bytes = 32 hex chars)
        hex_string = secrets.token_hex(16)

        # Format as 8-4-4-4-12 with hyphens (UUID v4 format)
        request_id = f"{hex_string[0:8]}-{hex_string[8:12]}-{hex_string[12:16]}-{hex_string[16:20]}-{hex_string[20:32]}"

        return request_id

    @staticmethod
    def _utc_to_local_dt(self, utc_string: str) -> str:
        # Parse the UTC string
        utc_dt = datetime.fromisoformat(utc_string.replace('Z', '+00:00'))
        # Ensure it's marked as UTC
        utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
        # Convert to local timezone (automatically detects system timezone)
        local_dt = utc_dt.astimezone()
        # Format as requested
        return local_dt.strftime(self.DT_FORMAT)

    @staticmethod
    def _update_metadata(self, file_path: Path, media_item: Dict):
        """
        Update metadata of the downloaded image file
        1. Load EXIF data from image file
        2. Clean EXIF dictionary by removing fields with incompatible types
        3. Clean "Program mame", add copyright (if any), artist name (if any)
        4. Save (dump) EXIF data into image file

        Args:
            file_path: Path to the image file
            media_item: Metadata dictionary from mediaItems object
        """
        try:
            # UTC time (date, time wih milliseconds, TZ) as string
            creation_time = media_item.get('createTime', '')
            if creation_time:
                creation_date = self._utc_to_local_dt(self, creation_time)
            else:
                creation_date = None

            exif_dict = update_exif_metadata(file_path, COPYRIGHT_TEXT, ARTIST_TEXT)

            # Add photo taken time to EXIF dict
            if creation_date:
                # Exif.Photo.DateTimeOriginal at offset 36867
                # exif_dict["Exif"][36867] = creation_date.encode("utf-8")
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = creation_date.encode("utf-8")

                # Exif.Image.DateTime, at offset 306
                # exif_dict["0th"][306] = creation_date.encode("utf-8")

                # Exif.Photo.DateTimeDigitized at offset 36868
                # exif_dict["Exif"][36868] = creation_date.encode("utf-8")
                exif_dict["0th"][piexif.ImageIFD.DateTime] = creation_date.encode("utf-8")

            # TBD: Add description if available
            # if description:
            #     exif_dict["0th"][piexif.ImageIFD.ImageDescription] = description    # .encode("utf-8") ?

            #  Trying to save EXIF data back to image file in any case - test piexif.dump()
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, str(file_path))

            # Set file modification time
            if creation_date:
                creation_timestamp = datetime.strptime(creation_date, self.DT_FORMAT).timestamp()
                # print(datetime.fromtimestamp(creation_timestamp))
                # atime and mtime are the same here
                os.utime(file_path, (creation_timestamp, creation_timestamp))
            return True

        except Exception as e:
            print(f"Warning: Could not add metadata to {file_path}: {e}")
            return False

    def create_picking_session(self) -> Dict:
        """
        Create a new picking session for photo selection.

        Returns:
            Dict: Session information including pickerUri and sessionId
        """
        try:
            # Generate unique request ID
            request_id = self.generate_request_id()

            # Prepare the request
            url = f"{self.PICKER_API_BASE}/sessions"

            headers = {
                'Authorization': f'Bearer {self.credentials.token}',
                'Content-Type': 'application/json'
            }

            # Optional. A client-provided unique identifier for this request.
            # This ID is used to enable the streamlined picking experience
            # for applications using the OAuth 2.0 flow for limited-input devices.
            params = {
                'requestId': request_id
            }

            # Make the API request
            response = requests.post(url,
                                     headers=headers,
                                     params=params)

            # test
            # if response.status_code != 200:
            #     print(f'Response: {response.content}')

            response.raise_for_status()
            session_data = response.json()

            print("Successfully created Picking Session")
            print(f"✅ Session Id: {session_data.get('id', 'unknown')}")
            print(f"🔗 Picker URI: {session_data.get('pickerUri', 'Not available')}")
            print(f"⏰ Expires at: {session_data.get('expireTime', 'Unknown')}")

            return session_data

        except HttpError as e:
            print(f"❌ HTTP Error creating session: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error creating picking session: {e}")
            return {}

    def get_session_status(self, session_id: str) -> Dict:
        """
        Get the current status of a picking session.

        Args:
            session_id: The session ID to check

        Returns:
            Dict: Session status information
        """
        try:
            url = f"{self.PICKER_API_BASE}/sessions/{session_id}"

            headers = {
                'Authorization': f'Bearer {self.credentials.token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            session_data = response.json()
            return session_data

        except Exception as e:
            print(f"❌ Error getting session status: {e}")
            return {}

    def poll_session_until_complete(self, session_id: str,
                                    poll_interval: int = 10,
                                    timeout_minutes: int = 10) -> Dict:
        """
        Poll a session until the user completes photo selection or timeout occurs.

        Args:
            session_id: The session ID to poll
            poll_interval: Seconds between polling requests
            timeout_minutes: Maximum time to wait for completion

        Returns:
            Dict: Final session data or empty dict on timeout/error
        """
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        print(f"🔄 Starting to poll session {session_id}")
        print(f"⏱️  Poll interval: {poll_interval}s, Timeout: {timeout_minutes}min")

        while True:
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                print(f"⏰ Polling timeout after {timeout_minutes} minutes")
                return {}

            # Get session status
            session_data = self.get_session_status(session_id)

            if not session_data:
                print("❌ Failed to get session status")
                return {}

            # Check if user has completed selection
            media_items_set = session_data.get('mediaItemsSet', False)

            print(f"📊 Session status: mediaItemsSet={media_items_set}")

            if media_items_set:
                print("✅ User has completed photo selection!")
                return session_data

            # Wait before next poll
            print(f"⏳ Waiting {poll_interval}s before next poll...")
            time.sleep(poll_interval)

    def get_selected_media_items(self, session_id: str) -> List[Dict]:
        """
        Get the media items selected by the user in a session.

        Args:
            session_id: The session ID

        Returns:
            List[Dict]: List of selected media items
        """
        all_media_items = []
        page_token = None

        try:
            while True:
                # Request #1: {'session_id': sessionId, "pageSize": 100}
                request_params = {'sessionId': session_id,
                                  "pageSize": 100}

                if page_token:
                    # Following requests: {"pageSize": "100", "pageToken": "page_token"}
                    request_params["pageToken"] = page_token

                print(f"Making API request with params: {request_params}")

                # Response contains: {"mediaItems": [...], "nextPageToken": "next-page-token"}
                response = self.service.mediaItems().list(**request_params).execute()
                # response.raise_for_status()

                # Get media items
                media_items = response.get('mediaItems', [])
                # Extract media items from response
                all_media_items.extend(media_items)

                print(f"Retrieved {len(media_items)} media items (total: {len(all_media_items)})")

                # Continue pagination until no more nextPageToken
                page_token = response.get('nextPageToken')
                if not page_token:
                    print("No more pages available")
                    break

            return all_media_items

        except Exception as e:
            print(f"❌ Error getting selected media items: {e}")
            return []

    def download_media_item(self, media_item: Dict) -> bool:
        """
        Download a media item to local storage.

        Args:
            media_item: Media item dictionary from API

        Returns:
            bool: True if download successful
        """

        try:

            base_url = media_item['mediaFile'].get('baseUrl')
            mime_type = media_item['mediaFile'].get('mimeType', 'image/jpeg')
            filename = media_item['mediaFile'].get('filename', 'unknown_file')

            if not base_url:
                print(f"❌ No base URL for {filename}")
                return False

            headers = {
                'Authorization': f'Bearer {self.credentials.token}',
                'Content-Type': mime_type
            }

            # Construct download URL for full resolution
            download_url = f"{base_url}=d"

            # Download the file
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()

            # Save to local file
            file_path = self.download_dir / filename
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"✅ Downloaded: {filename}", end=" ")

            # Recover dateTaken from UTC to Local format
            # Assign this date to the file
            # TBD: Exif metadata cleaning / update
            res = self._update_metadata(self, file_path, media_item)

            if res:
                print(" ...and cleaned")

            return True

        except Exception as e:
            print(f"\n❌ Error downloading {media_item['mediaFile'].get('filename', 'unknown')}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a picking session to free up resources.

        Args:
            session_id: The session ID to delete

        Returns:
            bool: True if deletion successful
        """
        try:
            url = f"{self.PICKER_API_BASE}/sessions/{session_id}"

            headers = {
                'Authorization': f'Bearer {self.credentials.token}',
                'Content-Type': 'application/json'
            }

            response = requests.delete(url, headers=headers)
            response.raise_for_status()

            print(f"🗑️  Successfully deleted session: {session_id}")
            return True

        except Exception as e:
            print(f"❌ Error deleting session: {e}")
            return False

    def run_complete_picking_workflow(self) -> List[Dict]:
        """
        Run the complete photo picking workflow:
        1. Create session
        2. Show picker URL to user
        3. Poll until completion
        4. Retrieve selected items
        5. Download files
        6. Clean up session

        Returns:
            List[Dict]: List of downloaded media items
        """
        print("🚀 Starting complete photo picking workflow")
        print("=" * 50)

        # Step 1: Create session
        session_data = self.create_picking_session()
        if not session_data:
            print("❌ Failed to create session")
            return []

        session_id = session_data.get('id')
        picker_uri = session_data.get('pickerUri')

        # Step 2: Show picker URI to user
        print("=" * 50)
        print("\n📱 USER ACTION REQUIRED:")
        print("=" * 23)
        print(f"Please open this URL in your browser to select photos (<2000):")
        print(f"🔗 {picker_uri}")
        print("\nAfter selecting photos, click 'Done' in the Picker interface.")
        print("\nNote: This script will automatically detect when you're finished.\n")
        print("=" * 50)

        # Step 3: Poll until completion
        final_session_data = self.poll_session_until_complete(session_id)
        if not final_session_data:
            print("❌ Session polling failed or timed out")
            self.delete_session(session_id)
            return []

        # Step 4: Get selected media items
        print("\n📥 Retrieving selected media items...")
        media_items = self.get_selected_media_items(session_id)

        if not media_items:
            print("❌ No media items found or failed to retrieve")
            self.delete_session(session_id)
            return []

        print(f"✅ Found {len(media_items)} selected media items")

        # Step 5: Download files
        print(f"\n💾 Downloading {len(media_items)} files...")
        downloaded_items = []

        for i, item in enumerate(media_items, 1):
            print(f"Downloading {i}/{len(media_items)}: {item['mediaFile'].get('filename', 'unknown')}")
            if self.download_media_item(item):
                downloaded_items.append(item)

        print(f"\n✅ Successfully downloaded {len(downloaded_items)}/{len(media_items)} files")

        # Step 6: Clean up session
        self.delete_session(session_id)

        print("🎉 Photo picking workflow completed!")
        return downloaded_items


# Example usage and testing
def main():
    """Google Photos Picker API."""

    print("\nUsing Google Photos Picker API to download photos selected in browser")
    print("=" * 40)

    # Initialize the API client
    try:
        picker_api = GooglePhotosPickerAPI()
    except Exception as e:
        print(f"❌ Failed to initialize API client: {e}")
        return

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


if __name__ == "__main__":
    main()