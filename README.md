# apply-tags

This is a Python-based CLI application that automates the process of applying tags to Snyk Projects, with the end goal of linking containers and repositories for AppRisk Pro issue detection.

## Preparation

To run this script you need to ensure that `requests` is available in Python, which you can achieve by running `pip install requests`.

**Required:**

`--org-id`: The Snyk Organisation ID where you want to apply tags.

`--snyk-token`: Snyk API Token with the permission to retrieve and tag the projects you specify. Can also by a `SNYK_TOKEN` enviroment variable.

`--origin`: The Origin of the Target(s) that you want to apply tags to. Ensure that you specify the precise integration, rather than a general term (e.g. `github-enterprise` or `bitbucket-connect-app`, not `github` or `bitbucket`).


**Optional (Recommended to use one of these to tag Targets instead of a whole Organisation):**

`--target-id`: The Snyk Target ID where you want to apply tags (all projects within the specified target).

*or*

`--target-name`: The name of the Snyk Target where you want to apply tags. This supports partial matches, so if you specify "java", it would include projects like "java-goof" and "java-woof".


**Additional:**

`--base-url`: The API Base URL of the Snyk tenant where you want to apply tags, e.g. `https://api.eu.snyk.io`.

`--dry-run`: Use this command to simulate the process without actually applying tags to projects. This will print the results to the terminal but won't make any changes.

---

## Running the application

First, determine the scope of projects you want to tag. It's recommended to start with a small sample before applying tags to a larger set of projects.
Using the --dry-run option is also highly recommended for the first run to ensure the correct projects and tags are identified.


**Example commands using --target-name:**

```python
# 1) Basic usage (with target-name):
python apply-tags.py --org-id=YOUR_ORG_ID --target-name="my-project" --snyk-token=YOUR_SNYK_TOKEN --origin=github-enterprise

# 2) Using environment variable for Snyk token:
export SNYK_TOKEN=YOUR_SNYK_TOKEN
python apply-tags.py --org-id=YOUR_ORG_ID --target-name="my-project" --origin=azure-repos

# 3) Dry run mode:
export SNYK_TOKEN=YOUR_SNYK_TOKEN
python apply-tags.py --org-id=YOUR_ORG_ID --target-name="my-project" --origin=gitlab --dry-run
```

To see detailed help information about the available arguments and options, you can use the `--help` flag.

`python apply-tags.py --help` output:

```python
Usage: apply-tags.py [OPTIONS]

Options:
  --org-id TEXT        # Your Snyk Org ID  [required]
  --snyk-token TEXT    # Your Snyk API Token (can be set via SNYK_TOKEN env var)
  --origin TEXT        # SCM type. E.g. github-enterprise, bitbucket-connect-app
  --target-id TEXT     # Snyk Target ID to apply tags to
  --target-name TEXT   # Snyk Target Name to apply tags to
  --base-url TEXT      # Base URL for the Snyk API (optional)
  --dry-run            # Simulate the tagging process without applying changes
  --help               # Show this message and exit.
```

---

## Environment Variables
You can also set environment variables for frequently used options, such as the Snyk token, instead of passing them as arguments.

`SNYK_TOKEN`: Used to provide the Snyk API token.
If both the SNYK_TOKEN environment variable and --snyk-token argument are provided, the script will prioritize the command-line argument and print a message indicating that both were present.

---

## Version History

Sep 17 2024: v1.0 published
