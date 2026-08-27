import requests
import os
from dotenv import load_dotenv

load_dotenv()

NVD_API_KEY = os.getenv("NVD_API_KEY")
BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def test_connection():
    """
    Fetch a single CVE to verify API access and inspect the data shape.
    """
    headers = {"apiKey": NVD_API_KEY}
    params = {
        "resultsPerPage": 1,
        "startIndex": 0
    }

    print("Testing NVD API connection...")
    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Connection successful!")
        print(f"Total CVEs available: {data['totalResults']}")
        print(f"\n--- Sample CVE ---")

        cve = data["vulnerabilities"][0]["cve"]
        print(f"ID: {cve['id']}")
        print(f"Published: {cve['published']}")
        print(f"Description: {cve['descriptions'][0]['value'][:200]}...")

        # Print CVSS score if available
        metrics = cve.get("metrics", {})
        if "cvssMetricV31" in metrics:
            score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
            severity = metrics["cvssMetricV31"][0]["cvssData"]["baseSeverity"]
            print(f"CVSS v3.1 Score: {score} ({severity})")
        else:
            print("CVSS v3.1: Not available for this CVE")

        print(f"\n--- Raw keys available on CVE object ---")
        print(list(cve.keys()))

    else:
        print(f"❌ Connection failed. Status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_connection()