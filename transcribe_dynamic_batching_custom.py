import subprocess
import argparse
#import json

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return None

def get_gcloud_access_token():
    gcloud_command = "gcloud auth application-default print-access-token"
    return run_command(gcloud_command)

def main():
    parser = argparse.ArgumentParser(description="Run gcloud storage ls command followed by dynamic_batching curl commands.")
    parser.add_argument("-path", help="Gcloud storage URI path storing the mp3 files that you want to transcribe.")
    parser.add_argument("-project", help="Gcloud project-id.")
    parser.add_argument("-output", help="Gcloud storage URI path that you want to save the transcribed json files to.")
    args = parser.parse_args()

    # Run gcloud storage ls command
    gcloud_command = f'gcloud storage ls --recursive "{args.path}/*.mp3"'
    gcloud_output = run_command(gcloud_command)

    if not gcloud_output:
        print("gcloud storage ls command failed.")
        return

    print("gcloud storage ls command executed successfully. Output:")
    print(gcloud_output)

    # Extract URIs from the output
    uris = [line.strip() for line in gcloud_output.split('\n') if line.strip()]

    if not uris:
        print("No URIs found in the gcloud storage path specified.")
        return

    # Run curl command for each URI
    access_token = get_gcloud_access_token().strip()

    if not access_token:
        print("Failed to retrieve access token for Curl command.")
        return

    for uri in uris:
        curl_command = f'curl -X POST -H "Content-Type: application/json; charset=utf-8" \
            -H "Authorization: Bearer {access_token}" \
            https://asia-southeast1-speech.googleapis.com/v2/projects/{args.project}/locations/asia-southeast1/recognizers/_:batchRecognize \
            --data \'{{"files": [{{"uri": "{uri}"}}], "config": {{"features": {{"enableWordTimeOffsets": true, "enableAutomaticPunctuation": true}}, "autoDecodingConfig": {{}}, "model": "chirp", "languageCodes": ["gu-IN"]}}, "recognitionOutputConfig": {{"gcsOutputConfig": {{"uri": "{args.output}"}}}}, "processingStrategy": "DYNAMIC_BATCHING"}}\''

        curl_output = run_command(curl_command)

        if curl_output:
            print(f"\nCurl command for URI '{uri}' executed successfully.")
            #print("Output:\n"+curl_output)
        else:
            print(f"\nCurl command for URI '{uri}' failed.")

if __name__ == "__main__":
    main()