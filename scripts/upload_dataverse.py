#!/usr/bin/env python3
"""
Upload datasets to Harvard Dataverse via API.

This script uploads a dataset with files to an existing (demo) Dataverse collection.
Optionally, it can create a new Dataverse collection if you have the required permissions.
"""
import os
import sys
import json
import requests
from pathlib import Path

# Configuration from environment variables
SERVER_URL = os.getenv('DATAVERSE_SERVER', 'https://demo.dataverse.org')
API_TOKEN = os.getenv('DATAVERSE_TOKEN')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL')
DATAVERSE_ALIAS = os.getenv('DATAVERSE_ALIAS', 'demo')

# Optional: Only needed if creating a new Dataverse collection
# PARENT_DATAVERSE = os.getenv('PARENT_DATAVERSE', 'root')

# File paths
REPO_ROOT = Path(__file__).parent.parent
DATASET_JSON = REPO_ROOT / 'metadata' / 'dataverse' / 'dataset.json'
FILES_TO_UPLOAD = ['README.md']

# Optional: Only needed if creating a new Dataverse collection
# DATAVERSE_JSON = REPO_ROOT / 'metadata' / 'dataverse' / 'dataverse-collection.json'


def check_prerequisites():
    """Verify all required configuration is present."""
    if not API_TOKEN:
        print("Error: DATAVERSE_TOKEN environment variable not set")
        sys.exit(1)
    
    if not CONTACT_EMAIL:
        print("Error: CONTACT_EMAIL environment variable not set")
        sys.exit(1)
    
    if not DATASET_JSON.exists():
        print(f"Error: Dataset metadata not found at {DATASET_JSON}")
        sys.exit(1)
    
    print(f"Configuration:")
    print(f"  Server: {SERVER_URL}")
    print(f"  Target Dataverse: {DATAVERSE_ALIAS}")
    print(f"  Contact: {CONTACT_EMAIL}")


def test_connection():
    """Test API connection and verify token validity."""
    response = requests.get(
        f"{SERVER_URL}/api/users/:me",
        headers={'X-Dataverse-key': API_TOKEN}
    )
    
    if response.status_code == 200:
        user_data = response.json()
        username = user_data.get('data', {}).get('displayName', 'Unknown')
        print(f"Connected as: {username}")
        return True
    else:
        print(f"Connection failed: {response.text}")
        return False


def verify_dataverse_exists():
    """Verify the target Dataverse collection exists and is accessible."""
    response = requests.get(
        f"{SERVER_URL}/api/dataverses/{DATAVERSE_ALIAS}",
        headers={'X-Dataverse-key': API_TOKEN}
    )
    
    if response.status_code == 200:
        print(f"Dataverse '{DATAVERSE_ALIAS}' verified")
        return True
    else:
        print(f"Error: Dataverse '{DATAVERSE_ALIAS}' not found or not accessible")
        print(f"Ensure the Dataverse exists and you have deposit permissions")
        return False


# ============================================================================
# OPTIONAL: Dataverse Collection Creation
# ============================================================================
# Uncomment these functions if you need to create a new Dataverse collection.
# Note: This requires admin permissions or explicit permissions to create
# collections in the parent Dataverse.
#
# In production, Dataverse collections are typically created once by
# institutional admins. Researchers then deposit datasets into existing
# collections.
# ============================================================================

# def check_dataverse_exists():
#     """Check if the Dataverse collection already exists."""
#     response = requests.get(
#         f"{SERVER_URL}/api/dataverses/{DATAVERSE_ALIAS}",
#         headers={'X-Dataverse-key': API_TOKEN}
#     )
#     
#     if response.status_code == 200:
#         print(f"Dataverse '{DATAVERSE_ALIAS}' already exists")
#         return True
#     elif response.status_code == 404:
#         print(f"Dataverse '{DATAVERSE_ALIAS}' not found")
#         return False
#     else:
#         print(f"Unexpected response checking Dataverse: {response.status_code}")
#         return False


# def create_dataverse_collection():
#     """
#     Create a new Dataverse collection.
#     
#     Requires:
#     - Admin permissions or explicit create permissions
#     - DATAVERSE_JSON file with collection metadata
#     - PARENT_DATAVERSE environment variable
#     
#     Returns:
#         bool: True if creation successful, False otherwise
#     """
#     if not DATAVERSE_JSON.exists():
#         print(f"Error: Dataverse collection config not found at {DATAVERSE_JSON}")
#         return False
#     
#     with open(DATAVERSE_JSON) as f:
#         dataverse_data = json.load(f)
#     
#     # Replace placeholder email with actual contact email
#     for contact in dataverse_data.get('dataverseContacts', []):
#         if contact['contactEmail'] == 'CONTACT_EMAIL_PLACEHOLDER':
#             contact['contactEmail'] = CONTACT_EMAIL
#     
#     print(f"Creating Dataverse collection '{DATAVERSE_ALIAS}' in '{PARENT_DATAVERSE}'")
#     
#     response = requests.post(
#         f"{SERVER_URL}/api/dataverses/{PARENT_DATAVERSE}",
#         headers={
#             'X-Dataverse-key': API_TOKEN,
#             'Content-Type': 'application/json'
#         },
#         json=dataverse_data
#     )
#     
#     if response.status_code in [200, 201]:
#         data = response.json()
#         print(f"Dataverse collection created successfully")
#         return True
#     else:
#         print(f"Error creating Dataverse collection: {response.status_code}")
#         print(f"Response: {response.text}")
#         return False


# def publish_dataverse_collection():
#     """
#     Publish the Dataverse collection to make it publicly accessible.
#     
#     Note: Datasets cannot be published in an unpublished Dataverse collection.
#     """
#     response = requests.post(
#         f"{SERVER_URL}/api/dataverses/{DATAVERSE_ALIAS}/actions/:publish",
#         headers={'X-Dataverse-key': API_TOKEN}
#     )
#     
#     if response.status_code == 200:
#         print(f"Dataverse collection '{DATAVERSE_ALIAS}' published")
#         return True
#     else:
#         print(f"Could not publish Dataverse collection: {response.status_code}")
#         print(f"Response: {response.text}")
#         return False

# ============================================================================


def create_dataset():
    """Create a new dataset in the target Dataverse collection."""
    with open(DATASET_JSON) as f:
        dataset_data = json.load(f)
    
    # Replace placeholder email with actual contact email
    citation_fields = dataset_data['datasetVersion']['metadataBlocks']['citation']['fields']
    for field in citation_fields:
        if field['typeName'] == 'datasetContact':
            for contact in field['value']:
                if contact['datasetContactEmail']['value'] == 'CONTACT_EMAIL_PLACEHOLDER':
                    contact['datasetContactEmail']['value'] = CONTACT_EMAIL
    
    # Extract title for logging
    title = next((f['value'] for f in citation_fields if f['typeName'] == 'title'), 'Unknown')
    print(f"Creating dataset: {title}")
    
    response = requests.post(
        f"{SERVER_URL}/api/dataverses/{DATAVERSE_ALIAS}/datasets",
        headers={
            'X-Dataverse-key': API_TOKEN,
            'Content-Type': 'application/json'
        },
        json=dataset_data
    )
    
    if response.status_code == 201:
        data = response.json()
        dataset_pid = data['data']['persistentId']
        print(f"Dataset created: {dataset_pid}")
        return dataset_pid
    else:
        print(f"Error creating dataset: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception("Failed to create dataset")


def upload_file(dataset_pid, filepath):
    """Upload a file to the dataset."""
    file_path = REPO_ROOT / filepath
    
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}")
        return False
    
    print(f"Uploading file: {filepath}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (filepath, f)}
        response = requests.post(
            f"{SERVER_URL}/api/datasets/:persistentId/add",
            params={'persistentId': dataset_pid},
            headers={'X-Dataverse-key': API_TOKEN},
            files=files
        )
    
    if response.status_code == 200:
        print(f"File uploaded: {filepath}")
        return True
    else:
        print(f"Error uploading {filepath}: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def publish_dataset(dataset_pid):
    """Publish the dataset to make it publicly accessible and assign a DOI."""
    print(f"Publishing dataset: {dataset_pid}")
    
    response = requests.post(
        f"{SERVER_URL}/api/datasets/:persistentId/actions/:publish",
        params={
            'persistentId': dataset_pid,
            'type': 'major'
        },
        headers={'X-Dataverse-key': API_TOKEN}
    )
    
    if response.status_code == 200:
        print(f"Dataset published successfully")
        return True
    else:
        print(f"Warning: Could not publish dataset: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def main():
    """Main workflow for uploading a dataset to Dataverse."""
    print("Dataverse Upload Process")
    print("=" * 50)
    
    # Check prerequisites
    check_prerequisites()
    print()
    
    # Test connection
    print("Testing connection...")
    if not test_connection():
        sys.exit(1)
    print()
    
    # Verify target Dataverse exists
    print("Verifying Dataverse collection...")
    if not verify_dataverse_exists():
        sys.exit(1)
    print()
    
    # ========================================================================
    # OPTIONAL: Create Dataverse collection if it doesn't exist
    # ========================================================================
    # Uncomment this section if you need to create a new Dataverse collection.
    # Ensure you have the required permissions and have set PARENT_DATAVERSE.
    #
    # print("Checking if Dataverse collection exists...")
    # if not check_dataverse_exists():
    #     print("Creating Dataverse collection...")
    #     if not create_dataverse_collection():
    #         print("Failed to create Dataverse collection")
    #         sys.exit(1)
    #     
    #     print("Publishing Dataverse collection...")
    #     if not publish_dataverse_collection():
    #         print("Warning: Dataverse collection created but not published")
    # print()
    # ========================================================================
    
    # Create dataset
    print("Creating dataset...")
    dataset_pid = create_dataset()
    print()
    
    # Upload files
    print("Uploading files...")
    for filepath in FILES_TO_UPLOAD:
        upload_file(dataset_pid, filepath)
    print()
    
    # Publish dataset
    print("Publishing dataset...")
    if publish_dataset(dataset_pid):
        print()
        print("SUCCESS: Dataset published")
    else:
        print()
        print("WARNING: Dataset created but not published")
        print("The dataset may require manual review before publishing")
    
    # Display final URL
    print()
    print("=" * 50)
    print(f"Dataset URL: {SERVER_URL}/dataset.xhtml?persistentId={dataset_pid}")
    print("=" * 50)


if __name__ == '__main__':
    main()