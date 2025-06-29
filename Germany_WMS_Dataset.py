import requests

def search_ckan_germany():
    url = "https://www.govdata.de/ckan/api/3/action/package_search"
    params = {
        "q": "res_format:WMS OR res_format:WFS",  # search for WMS or WFS in resource formats
        "rows": 50  # number of results to fetch
    }

    print("🔎 Searching GovData CKAN API for WMS/WFS datasets...")
    try:
        response = requests.get(url, params=params)
        data = response.json()

        results = data.get("result", {}).get("results", [])

        if not results:
            print(" No datasets found.")
        else:
            for ds in results:
                title = ds.get("title", "Untitled")
                name = ds.get("name", "")
                url_show = f"https://www.govdata.de/web/guest/daten/-/details/{name}"
                print(f" [{title}] - {url_show}")

    except Exception as e:
        print(f" Error: {e}")

search_ckan_germany()
