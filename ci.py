import argparse
import http.client
import json
import logging
import re
import subprocess
from difflib import ndiff

MARKETING_WEBSITE_URL = 'marketing'
RELEASE_NOTES_FILENAME = 'release_notes.txt'
DEFAULT_BRANCH_NAME = 'main'
RELEASE_NOTES_FILE_NAME = 'RELEASENOTES.md'


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
    conn = http.client.HTTPConnection(MARKETING_WEBSITE_URL, port=80)
    conn.request("GET", "/releasenotes")
    response = conn.getresponse()

    if response.status == 200:
        response_data = response.read()
        json_data = json.loads(response_data.decode("utf-8"))

        return json_data[version]


def get_local_release_notes(tag):
    with open(RELEASE_NOTES_FILE_NAME, 'r') as f:
        full_text = f.read()
        for version, text in re.findall(r'# (v\d\.\d\.\d)\n([\s\S]+?)\n\n# v[\d.]+', full_text):
            if version == tag:
                return text


def compare_text(local, remote):
    diff = list(ndiff(local.splitlines(keepends=True),
                      remote.splitlines(keepends=True)))

    not_common = [s for s in diff if s[0:2] != '  ']
    if not_common:
        text_diff = "".join(diff)
        logging.exception("\n" + text_diff)
        raise Exception("Marketing site gave different release notes, please see diff above.")


def write_notes(notes):
    with open(RELEASE_NOTES_FILENAME, 'w+') as f:
        f.write(notes)


def main():
    parser = argparse.ArgumentParser(description="Release Notes Utility")

    parser.add_argument(
        "--compare-release-notes",
        action="store_true",
        help="Compare release notes from the marketing site with local release notes and throw an error if they don't "
             "match"
    )

    parser.add_argument(
        "--get-release-notes",
        action="store_true",
        help="Get the latest release notes"
    )

    args = parser.parse_args()

    latest_tag = get_latest_tag()
    local_release_notes = get_local_release_notes(latest_tag)
    if args.compare_release_notes:
        release_notes = get_release_notes(latest_tag)
        compare_text(local_release_notes, release_notes)
    elif args.get_release_notes:
        write_notes(local_release_notes)
    else:
        print("Please provide one of the following options: --compare-release-notes or --get-release-notes")


if __name__ == "__main__":
    main()
