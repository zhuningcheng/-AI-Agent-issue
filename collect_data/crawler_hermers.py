from github_client import GitHubClient
from utils import crawl_repository



# ======================================
# OpenClaw Configuration
# ======================================


REPO = "NousResearch/hermes-agent"

OUTPUT_FILE = "hermes.jsonl"

METADATA_FILE = "metadata/hermes_metadata.json"




def main():


    print(
        "================================"
    )

    print(
        "Start crawling hermes-agent"
    )

    print(
        f"Repository: {REPO}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        "================================"
    )



    client = GitHubClient()



    crawl_repository(

        client,

        REPO,

        OUTPUT_FILE,

        METADATA_FILE

    )



    print(

        "hermes-agent crawling finished."

    )





if __name__ == "__main__":

    main()