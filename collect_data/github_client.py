import os
import time
import requests

from dotenv import load_dotenv


load_dotenv()


API_BASE = "https://api.github.com"


GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN"
)



HEADERS = {

    "Accept":
        "application/vnd.github+json",

    "X-GitHub-Api-Version":
        "2022-11-28"

}



if GITHUB_TOKEN:

    HEADERS["Authorization"] = (
        f"Bearer {GITHUB_TOKEN}"
    )





class GitHubClient:


    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update(
            HEADERS
        )





    def get(
            self,
            url,
            params=None,
            retry=5
    ):

        """
        Unified GitHub GET request

        Handles:
        - Rate limit
        - Retry
        - Network errors
        """


        for attempt in range(retry):

            try:


                response = self.session.get(

                    url,

                    params=params,

                    timeout=30

                )



                if response.status_code == 200:

                    return response




                # Rate limit

                if response.status_code == 403:


                    remaining = response.headers.get(
                        "X-RateLimit-Remaining"
                    )


                    if remaining == "0":


                        reset = int(

                            response.headers.get(

                                "X-RateLimit-Reset"

                            )

                        )


                        wait = (

                            reset -
                            int(time.time())

                        )


                        print(

                            f"Rate limit reached, "
                            f"wait {wait}s"

                        )


                        time.sleep(
                            max(wait,60)
                        )


                        continue





                print(

                    f"Request failed "
                    f"{response.status_code}: {url}"

                )


                print(

                    response.text[:300]

                )




            except Exception as e:


                print(
                    "Network error:",
                    e
                )




            time.sleep(
                2 ** attempt
            )




        return None





def get_next_url(
        link_header
):

    """
    Parse GitHub Link Header

    Example:

    <url?page=2>; rel="next"

    """


    if not link_header:

        return None



    links = link_header.split(",")



    for link in links:


        if 'rel="next"' in link:


            return (

                link

                .split(";")[0]

                .strip()

                .strip("<>")

            )



    return None