import os
import json
import time

from datetime import datetime, timezone

from tqdm import tqdm

from github_client import (
    API_BASE,
    get_next_url
)



# =====================================================
# Existing JSONL issue_id
# =====================================================


def load_existing_ids(
        filename
):

    """
    Read existing issue_id from JSONL

    Used for duplicate filtering
    """

    ids = set()


    if not os.path.exists(filename):

        return ids



    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as f:


        for line in f:


            try:

                data = json.loads(
                    line
                )

                ids.add(
                    data["issue_id"]
                )


            except Exception:

                continue



    return ids





# =====================================================
# Metadata
# =====================================================


def load_last_time(
        metadata_file
):


    """
    Load last crawl time

    Used as GitHub API since parameter
    """


    if not os.path.exists(
        metadata_file
    ):

        return None



    with open(
        metadata_file,
        "r",
        encoding="utf-8"
    ) as f:


        data = json.load(f)



    return data.get(
        "last_crawl_time"
    )





def save_metadata(
        metadata_file,
        repo
):


    """
    Save crawl timestamp

    Only call after successful crawling
    """



    directory = os.path.dirname(
        metadata_file
    )


    if directory:


        os.makedirs(

            directory,

            exist_ok=True

        )




    data = {


        "repo":
            repo,


        "last_crawl_time":
            datetime.now(
                timezone.utc
            ).isoformat()

    }



    with open(
        metadata_file,
        "w",
        encoding="utf-8"
    ) as f:


        json.dump(

            data,

            f,

            indent=4

        )





# =====================================================
# Get All Issues
# =====================================================


def get_all_issues(
        client,
        repo,
        since=None
):


    """
    Get all issues

    Features:
    - state=all
    - Link Header pagination
    - since incremental update
    - remove PR
    """



    issues = []



    url = (

        f"{API_BASE}/repos/"
        f"{repo}/issues"

    )



    params = {


        "state":

            "all",


        "per_page":

            100,


        "sort":

            "updated",


        "direction":

            "asc"

    }



    if since:


        params["since"] = since





    while url:


        response = client.get(

            url,

            params

        )


        if response is None:

            break



        data = response.json()



        for item in data:



            # GitHub Issues API
            # contains PRs

            if "pull_request" in item:

                continue



            issues.append(
                item
            )



        url = get_next_url(

            response.headers.get(
                "Link"
            )

        )



        params = None



        print(

            f"Fetched issues: "
            f"{len(issues)}"

        )



    return issues





# =====================================================
# Comments
# =====================================================


def get_comments(
        client,
        repo,
        issue_number
):


    comments = []



    url = (

        f"{API_BASE}/repos/"
        f"{repo}/issues/"
        f"{issue_number}/comments"

    )



    params = {


        "per_page":

            100

    }



    while url:


        response = client.get(

            url,

            params

        )


        if response is None:

            break



        data=response.json()



        for comment in data:


            comments.append(

                {


                    "author":

                        (
                            comment["user"]["login"]

                            if comment.get("user")

                            else None

                        ),


                    "created_at":

                        comment.get(
                            "created_at"
                        ),


                    "body":

                        comment.get(
                            "body"
                        )

                }

            )



        url = get_next_url(

            response.headers.get(
                "Link"
            )

        )


        params=None



    return comments





# =====================================================
# Reactions
# =====================================================


def get_reactions(
        client,
        repo,
        issue_number
):


    reactions = {


        "+1":0,

        "-1":0,

        "laugh":0,

        "hooray":0,

        "confused":0,

        "heart":0,

        "rocket":0,

        "eyes":0

    }



    url = (

        f"{API_BASE}/repos/"
        f"{repo}/issues/"
        f"{issue_number}/reactions"

    )



    params = {


        "per_page":

            100

    }




    while url:


        response = client.get(

            url,

            params

        )


        if response is None:

            break



        data=response.json()



        for item in data:


            key=item.get(
                "content"
            )


            if key in reactions:


                reactions[key]+=1




        url=get_next_url(

            response.headers.get(
                "Link"
            )

        )


        params=None



    return reactions





# =====================================================
# Build Issue Object
# =====================================================


def build_issue_data(
        client,
        repo,
        issue
):


    issue_number = issue["number"]



    return {


        "repo":

            repo,


        "issue_id":

            issue["id"],


        "issue_number":

            issue_number,


        "title":

            issue.get(
                "title"
            ),


        "body":

            issue.get(
                "body"
            ),


        "state":

            issue.get(
                "state"
            ),


        "author":

            (
                issue["user"]["login"]

                if issue.get("user")

                else None

            ),



        "created_at":

            issue.get(
                "created_at"
            ),


        "updated_at":

            issue.get(
                "updated_at"
            ),


        "closed_at":

            issue.get(
                "closed_at"
            ),



        "labels":

            [

                label["name"]

                for label in issue.get(
                    "labels",
                    []
                )

            ],



        "reactions":

            get_reactions(

                client,

                repo,

                issue_number

            ),



        "comments":

            get_comments(

                client,

                repo,

                issue_number

            )

    }





# =====================================================
# JSONL append
# =====================================================


def append_jsonl(
        filename,
        data
):


    with open(

        filename,

        "a",

        encoding="utf-8"

    ) as f:


        f.write(

            json.dumps(

                data,

                ensure_ascii=False

            )

            + "\n"

        )


        f.flush()





# =====================================================
# Main Crawl Function
# =====================================================


def crawl_repository(
        client,
        repo,
        output_file,
        metadata_file
):


    print(
        "\n=============================="
    )

    print(
        f"Crawling {repo}"
    )



    # last update time

    last_time = load_last_time(

        metadata_file

    )



    print(

        "Since:",

        last_time

    )



    existing_ids = load_existing_ids(

        output_file

    )



    print(

        "Existing issues:",

        len(existing_ids)

    )



    issues = get_all_issues(

        client,

        repo,

        last_time

    )



    print(

        "Fetched:",

        len(issues)

    )



    new_issues = [

        issue

        for issue in issues

        if issue["id"] not in existing_ids

    ]



    print(

        "New issues:",

        len(new_issues)

    )



    success = True



    try:


        for issue in tqdm(

            new_issues,

            desc="Processing"

        ):


            data = build_issue_data(

                client,

                repo,

                issue

            )


            append_jsonl(

                output_file,

                data

            )


            time.sleep(
                0.2
            )



    except Exception as e:


        success=False


        print(

            "Crawler error:",

            e

        )



    # only update metadata after success

    if success:


        save_metadata(

            metadata_file,

            repo

        )


        print(
            "Metadata updated."
        )