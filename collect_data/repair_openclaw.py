import json
import os
from utils import (
    get_all_issues,
    build_issue_data
)

from github_client import GitHubClient


REPO = "openclaw/openclaw"

JSONL_FILE = "data/openclaw.jsonl"



def load_existing_ids(file):

    ids=set()

    if not os.path.exists(file):
        return ids


    with open(
        file,
        encoding="utf-8"
    ) as f:

        for line in f:

            try:

                data=json.loads(line)

                ids.add(
                    data["issue_id"]
                )

            except:

                continue


    return ids



def append_issue(
        file,
        issue
):

    with open(
        file,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            json.dumps(
                issue,
                ensure_ascii=False
            )
        )

        f.write("\n")





def main():


    client=GitHubClient()


    print(
        "Loading existing ids..."
    )


    existing_ids = load_existing_ids(
        JSONL_FILE
    )


    print(
        "Existing:",
        len(existing_ids)
    )



    print(
        "Fetching github issues..."
    )


    issues=get_all_issues(
        client,
        REPO
    )



    print(
        "Github total:",
        len(issues)
    )



    missing=[]


    for issue in issues:


        if issue["id"] not in existing_ids:

            missing.append(issue)



    print(
        "Missing:",
        len(missing)
    )



    if len(missing)==0:

        print(
            "No missing issues"
        )

        return



    for i,issue in enumerate(missing):


        print(
            f"{i+1}/{len(missing)}",
            issue["number"]
        )


        data=build_issue_data(
            client,
            REPO,
            issue
        )


        append_issue(
            JSONL_FILE,
            data
        )



    print(
        "Repair finished"
    )



if __name__=="__main__":

    main()