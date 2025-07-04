# Google Takeout Photos [Google Photos Picker API]  
This implementation provides a complete solution for integrating<br>
Google Photos Picker functionality into your application.

## Motivation
I have been using the Photos Library API extensively to work with my selected photos since 2007.<br>
The restrictions on user albums and media introduced on March 31st of this year<br>
led me to create a program to access my photos using the Google Photos Picker API.<br>
I also wanted to have correct dates and some metadata of the image files I uploaded.

## Program modules:
### 1. api_helper.py
### 2. exif_helper.py

## 1. api_helper.py module:

### 1.1. Session Management

```shell
_authenticate()
```
Authenticate with Google Photos Picker API using OAuth 2.0.

```sh
create_picking_session()
```
Creates a new session with optional configuration
```sh
get_session_status() 
```
Checks the current status of a session
```sh
delete_session() 
```
Cleans up sessions to avoid resource limits

### 1.2. Polling Mechanism
```sh
poll_session_until_complete()
```
* Automatically polls the session until user completes selection
* Uses configurable polling intervals and timeouts
* Monitors the mediaItemsSet property to detect completion

### 1.3. Media Retrieval
```sh
get_selected_media_items()
```
* Retrieves the photos and videos selected by users after they finish their selection in browser 
* Handles pagination for large selections
```sh
download_media_item() 
```
Downloads media files at full resolution

### 1.4. Update Metadata
```shell
_update_metadata()
```
Update metadata of the downloaded image file:
1. Load EXIF data from image file
2. Clean EXIF dictionary by removing fields with incompatible types
3. Clean "Program mame", add copyright (if any), artist name (if any)
4. Save (dump) EXIF data into image file
5. import from exif_helper module

## 2. exif_helper.py module:

Fixing Issues:
* The library sometimes loads data in one format but expects it in another when saving.
* Update EXIF metadata with custom fields

### 2.1. Fix problematic EXIF fields
```shell
fix_exif_types()
```
Remove or fix problematic EXIF fields that cause type errors

### 2.2. Update EXIF metadata 
```shell
update_exif_metadata()
```
1. Load EXIF data from image file
2. Fix EXIF types 
3. Update EXIF metadata: remove "Software", add copyright, add artist (you can extend the list)
4. Return updated EXIF metadata

### 2.3. Examples:
* 3 solutions of fixing EXIF data and batch process

## 3. Workflow (main.py)

```shell
run_complete_picking_workflow()
```
Run the complete photo picking workflow:
1. Create session
2. Show picker URL to user
3. Poll until completion
4. Retrieve selected item(s)
5. Download file(s)
6. Clean up session

## 4. Installation

### 4.1. Packages
Install the required packages in virtual environment. For that do the following:
```sh
>python -m venv .venv
>mkdir .env downloads
>.venv\Scripts\activate
(.venv)> pip install -r requirements.txt
```

### 4.2. Google Cloud 
Start from Project configuration<br>
#### Google Auth Platform:<br>
* Branding -> App name, user support email, developer contact info  
* Audience -> Testing mode, External user type, test user email
* Clients -> Client name, ClientId -> client_secret.json
* Data Access -> .../auth/photospicker.mediaitems.readonly scope
 
### 4.3. OAuth Scope:
* Enable "Google Photos Picker API"<br>
<i>See: APIs & Services | Enabled APIs & services</i>
* Enable "Google Photos Picker API" Library<br>
<i>See: APIs & Services | API Library</i>
* Requires the https://www.googleapis.com/auth/photospicker.mediaitems.readonly OAuth scope<br>
<i>See: Google Auth Platform | Data Access | Add or remove scopes</i>

### 4.4. Client Secret
Upload client_secret.json generated on https://console.cloud.google.com/ for your project/client to ./env directory.<br>
<i>See: Google Auth Platform | Clients | ClientId for Desktop</i>
The token.json files will be generated and updated in this directory automatically in case of successful connection to Google Cloud.

## 5. Running the program
```sh
(.venv)> python main.py 
```
Follow the instructions on the screen

## 6. Complete Workflow
The run_complete_picking_workflow() method demonstrates the full process:
#### 6.1. Create Session
Generates a new session during which the user can pick photos<br>
and videos for third-party access<br> 
<i>See: Create and manage sessions | Google Photos APIs | Google for Developers</i>
### 6.2. Present Picker URI
Shows the user a URL to open Google Photos picker
### 6.3. Poll Session
Periodically polls the session to check the status, <br>
looking for the <b>mediaItemsSet</b> property to return true<br> 
<i>See Method: mediaItems.list | Google Photos APIs | Google for Developers</i>
### 6.4. Retrieve Items
Gets the selected media items
### 6.5. Download Files
Downloads selected photos/videos
### 6.6. Cleanup
Deletes the session

## 7. Notes
### 7.1. requestID format
Must contain 32 hexadecimal characters divided into five groups separated by hyphens,<br>
in the format: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" (or 8-4-4-4-12)<br>
See: https://developers.google.com/photos/picker/reference/rest/v1/sessions/create

### 7.2. Session Lifecycle
Clients are recommended to call sessions.delete after each session,<br>
to proactively stay within resource limits<br>
<i>See: "Create and manage sessions" in "Google Photos APIs" | "Google for Developers"</i>

## 8. License
This software is released under the MIT license, see LICENSE.txt.
