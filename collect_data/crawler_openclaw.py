from github_client import GitHubClient
from utils import crawl_repository



# ======================================
# OpenClaw Configuration
# ======================================


REPO = "openclaw/openclaw"


OUTPUT_FILE = "openclaw.jsonl"


METADATA_FILE = (
    "metadata/openclaw_metadata.json"
)





def main():


    print(
        "================================"
    )

    print(
        "Start crawling OpenClaw"
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

        "OpenClaw crawling finished."

    )





if __name__ == "__main__":

    main()