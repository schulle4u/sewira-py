# -*- coding: utf-8 -*-
# MPV downloader
# A part of SeWiRa - the Selfmade Wifi Radio
# Copyright (c) 2024-2025 Steffen Schultz
import sys
import os
import requests
import zipfile
from tqdm import tqdm


def main():
    # Configuration
    url = 'https://nightly.link/mpv-player/mpv/workflows/build/master/mpv-x86_64-pc-windows-msvc.zip'
    zip_filename = 'mpv-x86_64-pc-windows-msvc.zip'
    mpv_filename = 'mpv.exe'

    # Check if MPV is already present before doing anything
    if os.path.exists(mpv_filename):
        overwrite = input(f"A copy of {mpv_filename} already exists. Do you want to overwrite it? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Exiting....")
            sys.exit(0)

    # Start downloading
    try:
        print("Downloading mpv, this may take a moment.")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        with open(zip_filename, 'wb') as file, tqdm(desc=zip_filename, total=total_size, unit='B', unit_scale=True, unit_divisor=1024,) as bar:
            for data in response.iter_content(chunk_size=1024):
                file.write(data)
                bar.update(len(data))

        print(f"Download finished: {zip_filename}. Extracting...")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

    # Extract mpv.exe from zip
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            zip_ref.extract(mpv_filename, os.getcwd())
        print(f"Successfully extracted {mpv_filename}.")

    except zipfile.BadZipFile:
        print("The zip file is damaged and cannot be extracted.")
        sys.exit(1)
    except KeyError:
        print(f"The file {mpv_filename} cannot be found in this zip file.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error while extracting zip file: {e}")
        sys.exit(1)

    # Clean up
    os.remove(zip_filename)
    print(f"Deleting zip file {zip_filename}.")


if __name__ == "__main__":
    main()
