# Version 1.1, 19 Sep 2024
import requests, sys, urllib.parse, os
from argparse import ArgumentParser

# Setting up command-line argument parser to accept necessary inputs
parser = ArgumentParser()
parser.add_argument("--org-id", dest="org_id", help="your Snyk Org ID", required=True)
parser.add_argument("--target-id", dest="target_id", help="your Snyk Target ID", required=False)
parser.add_argument("--target-name", dest="target_name", help="your Snyk Target Name", required=False)
parser.add_argument("--snyk-token", dest="snyk_token", help="your Snyk Token", required=False)
parser.add_argument("--origin", dest="origin", help="SCM type. Possible values: github, github-enterprise, github-cloud-app, azure-repos, bitbucket-cloud, bitbucket-connect-app, bitbucket-server, gitlab", required=True)
parser.add_argument("--base-url", dest="base_url", help="your Base URL, e.g. https://api.eu.snyk.io", required=False)
parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Simulate tagging without making changes", required=False)

# Parsing arguments from the command line
args = parser.parse_args()
ORG_ID = args.org_id
TARGET_ID = args.target_id
TARGET_NAME = args.target_name
ORIGIN = args.origin
PROVIDED_URL = args.base_url
DRY_RUN = args.dry_run

# Check if SNYK_TOKEN is provided as an argument or from the environment
env_snyk_token = os.getenv("SNYK_TOKEN")  # Get token from environment variable
if args.snyk_token:
    SNYK_TOKEN = args.snyk_token
    if env_snyk_token:
        print("Both environment variable and --snyk-token are present. Using the provided --snyk-token.")
else:
    if env_snyk_token:
        SNYK_TOKEN = env_snyk_token
        print("Using environment variable for Snyk token.")
    else:
        print("Error: No Snyk token provided. Please provide it either via --snyk-token or the SNYK_TOKEN environment variable.")
        sys.exit(1)

# Ensure user provides either target ID or target name, but not both
if TARGET_ID and TARGET_NAME:
    print("Error: You must provide either a target ID or a target name, not both.")
    sys.exit(1)

def startup():

    if DRY_RUN:
        # Confirm to the user if dry-run mode is active or not
        print("Dry Run mode is active -- projects and tags will be identified but no tags will be applied.")
        print("-" * 25)

    # Mapping SCM types (origin) to a tag format for later use
    ORIGIN_TAG_MAP = {
        "azure-repos": "azure",
        "bitbucket-cloud": "bitbucket",
        "bitbucket-connect-app": "bitbucket",
        "bitbucket-server": "bitbucket",
        "cli": "cli",
        "github": "github",
        "github-enterprise": "github",
        "github-cloud-app": "github",
        "gitlab": "gitlab"
    }

    # Global variable to store the tag corresponding to the SCM type
    global ORIGIN_TAG
    ORIGIN_TAG = ORIGIN_TAG_MAP.get(ORIGIN, "")

    # Check if the origin is valid, exit if it's not
    if not ORIGIN_TAG:
        print(f"Error: Invalid origin: {ORIGIN}")

    # Handling the base URL; if no base URL is provided, use the default
    global BASE_URL
    if not PROVIDED_URL:
        BASE_URL = "https://api.snyk.io"  # Set default if 'base_url' is empty
    else:
        # Check if the provided URL is in the correct format, exit if it's not
        if not PROVIDED_URL.startswith("https://api"):
            print("Error: Provided URL must be in the format 'https://api.xx.snyk.io' e.g. https://api.eu.snyk.io")
            sys.exit()
        else: 
            BASE_URL = PROVIDED_URL

    # Display the base URL being used
    print("Using BASE_URL:", BASE_URL)

    try:
        # Setting the headers for the API request, including the token for authorization
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'token {SNYK_TOKEN}'
        }

        # Making a GET request to verify the connection
        response = requests.get(f"{BASE_URL}/v1/user/me", headers=headers)

        # Check if the response status code is not 200 (OK), raise an exception if not
        if response.status_code != 200:
            raise requests.exceptions.RequestException(
                f"Failed to verify credentials: {response.status_code} {response.reason}"
            )

        # Successful connection
        print("Connection successful!")

    except requests.exceptions.ConnectionError as e:
        # Handle connection errors (e.g., network issues or invalid URL)
        print("ERROR: Unable to resolve the server address. Please check the URL or your network connection.")
        exit(1)

    except requests.exceptions.RequestException as e:
        # Handle any other request exceptions
        print("ERROR:", e)
        exit(1)

    # Print a separator line for clarity
    print("-" * 25)


# Function to retrieve target ID(s) by target name
def get_target_id_by_name(target_name):
    url = f"{BASE_URL}/rest/orgs/{ORG_ID}/targets?version=2024-09-04&source_types={ORIGIN}&display_name={target_name}"
    headers = {
        'Accept': 'application/vnd.api+json',
        'Authorization': f'token {SNYK_TOKEN}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        sys.exit(f"Failed to retrieve targets: {response.status_code} {response.reason} (Check your Org ID is valid)")


    targets = response.json()

    # Extracting target IDs from the response
    if 'data' in targets and len(targets['data']) > 0:
        target_ids = [target['id'] for target in targets['data']]
        print("Applying filter based on Target Name. Number of Targets found:", len(target_ids))
        return target_ids
    else:
        print(f"Error: No targets found with the name '{target_name}'.")
        sys.exit(1)

# If a target name is provided, fetch the corresponding target IDs
def get_target_ids():
    global TARGET_FILTER

    if TARGET_NAME:
        # URL encode the TARGET_NAME
        encoded_target_name = urllib.parse.quote(TARGET_NAME, safe='')
        target_ids = get_target_id_by_name(encoded_target_name)
        TARGET_FILTER = f"target_id={'&target_id='.join(target_ids)}&"  # Create filter with all target IDs
    elif TARGET_ID:
        TARGET_FILTER = f"target_id={TARGET_ID}&"
        print("Applying filter based on Target ID")
    else:
        TARGET_FILTER = ""  # No filtering if neither ID nor name is provided



def get_projects_page(next_url):
    # Construct the URL for the next page of projects
    url = BASE_URL + next_url

    # Headers for the API request
    headers = {
        'Accept': 'application/vnd.api+json',
        'Authorization': f'token {SNYK_TOKEN}'
    }

    # Make a GET request to fetch projects data
    return requests.request("GET", url, headers=headers)


def get_all_projects():
    # Construct the initial URL to fetch projects for the given organization
    next_url = f"/rest/orgs/{ORG_ID}/projects?{TARGET_FILTER}version=2024-03-12&limit=100&origins={ORIGIN}"

    all_projects = []  # List to store all projects

    # Loop through pages of projects as long as there is a next URL
    while next_url is not None:
        res = get_projects_page(next_url).json()

        # Check if there is a 'next' link in the response to paginate
        if 'links' in res and 'next' in res['links']:
            next_url = res['links']['next']
        else:
            next_url = None

        # Add projects to the list if the 'data' field is present
        if 'data' in res:
            all_projects.extend(res['data'])

    return all_projects


def tag_project(project_id, key, value):
    # URL for tagging a project
    url = f'{BASE_URL}/v1/org/{ORG_ID}/project/{project_id}/tags'

    # Payload containing the tag key and value
    payload = {
        "key": key,
        "value": value
    }

    # Headers for the API request
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {SNYK_TOKEN}'
    }

    # Send a POST request to add the tag to the project
    return requests.request("POST", url, headers=headers, json=payload)


def main():
    # Start retrieving projects
    print(f"Retrieving Projects...")

    projects = get_all_projects()  # Fetch all projects

    if projects:
        # Start tagging projects if there are any
        print(f"Tagging Projects...")
        print("-" * 5)

        # Loop through each project and apply tags
        for p in projects:        
            project_id = p['id']
            repo = p['attributes']['name'].split(":")[0].split("(")[0]  # Extract repository name
            branch = p['attributes'].get('target_reference')  # Get branch name
            if not branch:
                # If no branch (target reference) is found, print error and skip tagging
                print(f"ERROR: No Target Reference (branch) detected for project '{project_id}' in '{repo}', no tag applied.")
                print("-" * 5)
                continue  # Skip to the next project

            tag_value = f'pkg:{ORIGIN_TAG}:{repo}@{branch}'  # Create tag value

            if DRY_RUN:
                # In dry-run mode, just print what would happen
                print(f"[Dry Run] Project {project_id} would be tagged with value {tag_value}")
            else:
                # Actual tagging when dry-run is not enabled

                # Tag the project
                res = tag_project(project_id, 'component', tag_value)

                if res.status_code == 200:
                    # Successful tagging
                    print(f"Project {project_id} tagged with value {tag_value}")
                    print("-" * 5)
                else:
                    # Handle different error statuses for tagging
                    error_message = {
                        400: "Bad request: Invalid project ID or tag value.",
                        401: "Unauthorized: Authentication failed.",
                        403: "Forbidden: You do not have permission to tag this project.",
                        422: "Is the project already tagged?",
                        # Add more error codes and messages as needed
                    }.get(res.status_code, f"Unknown error: Status code {res.status_code}")
                    print(f"ERROR: Project {project_id} could not be tagged.")
                    print(f"{error_message}")
                    print("-" * 5)
    else:
        print("ERROR: No Projects found.")
    
    print("Process complete!")


# Call startup function to initialize and verify connection
startup()

# Parse Target Name or Target IDs
get_target_ids()

# Call main function to start retrieving and tagging projects
main()
