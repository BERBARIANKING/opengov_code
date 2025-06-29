import requests


portals = {
    #"Greece": "https://repository.data.gov.gr/api/3/action/package_search",
    "Germany": "https://www.govdata.de/ckan/api/3/action/package_search",
    "Italy": "https://www.dati.gov.it/opendata/api/3/action/package_list",
    "Spain": "https://datos.gob.es/apidata/catalog/dataset",
    "Netherlands": "https://ckan.dataplatform.nl/api/3/action/package_search",
    "France": "https://www.data.gouv.fr/api/1/datasets/"  
}

def check_pids(portal_name, endpoint):
    print(f"\n Checking {portal_name} for dataset PIDs...")
    try:
        params = {"rows": 10}
        resp = requests.get(endpoint, params=params)
        data = resp.json()

        results = data.get("result", {}).get("results", [])
        if not results:
            print(" No datasets found or endpoint error.")
            return

        for ds in results:
            title = ds.get("title", "Untitled")
            ds_id = ds.get("id", "No ID")
            ds_name = ds.get("name", "No Name")
            print(f" [{title}] - UUID: {ds_id} - Slug: {ds_name}")

    except Exception as e:
        print(f" Error: {e}")

for name, url in portals.items():
    check_pids(name, url)
