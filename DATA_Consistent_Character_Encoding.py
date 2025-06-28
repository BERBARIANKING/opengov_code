import requests

def check_endpoint_encoding(endpoint_url):
    """
    Check declared encoding from an API endpoint.
    """
    try:
        r = requests.get(endpoint_url, timeout=10)
        content_type = r.headers.get("Content-Type", "").lower()
        
        if "charset=utf-8" in content_type:
            print(f" {endpoint_url}: Declares UTF-8 encoding correctly.")
        else:
            print(f" {endpoint_url}: Missing or different charset in Content-Type -> {content_type}")
        
        # Optionally, also test parsing to confirm no local errors
        r.encoding = 'utf-8'
        _ = r.text.encode('utf-8')
        
    except Exception as e:
        print(f" {endpoint_url}: Error — {e}")

# Example: Check Greece (data.gov.gr)
check_endpoint_encoding("https://data.gov.gr/api/3/action/package_list")

# Example: Check Germany (govdata.de)
check_endpoint_encoding("https://www.govdata.de/ckan/api/3/action/package_list")

# Example: Belgium (data.gov.be)
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")
check_endpoint_encoding("")

