import http.client
import json
import os
import subprocess

MARKETING_WEBSITE_URL = 'marketing'
RELEASE_NOTES_FILENAME = 'release_notes.txt'
DEFAULT_BRANCH_NAME = 'main'


def get_latest_tag():
    subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', '%teamcity.build.checkoutDir%'],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    result = subprocess.run(["git", "describe", "--tags", "--abbrev=0", DEFAULT_BRANCH_NAME, 'HEAD'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

    nearest_tag = result.stdout.strip()

    if not nearest_tag:
        raise Exception("Tag not found!")

    latest_tag = nearest_tag.split('\n')[-1]

    return latest_tag


def get_release_notes(version):
    try:
        conn = http.client.HTTPConnection(MARKETING_WEBSITE_URL, port=80)
        conn.request("GET", "/releasenotes")
        response = conn.getresponse()

        if response.status == 200:
            response_data = response.read()
            json_data = json.loads(response_data.decode("utf-8"))

            return json_data[version]
        else:
            print(f"HTTP GET request failed with status code {response.status}")
            return None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def write_notes(notes):
    with open(RELEASE_NOTES_FILENAME, 'w+') as f:
        f.write(notes)


if __name__ == "__main__":
    latest_tag = get_latest_tag()
    release_notes = get_release_notes(latest_tag)
    if release_notes:
        write_notes(release_notes)