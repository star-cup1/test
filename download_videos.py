#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download videos from blobstore by photo_id.

Example:
    python download_videos.py 118074311217 123456789
    python download_videos.py --file photo_ids.txt --output-dir videos
"""

import argparse
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="Boto3 will no longer support Python 3.9.*")


def read_photo_ids(path):
    photo_ids = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            photo_ids.append(value)
    return photo_ids


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download videos as {photo_id}.mp4 from video_def_{photo_id}.mp4."
    )
    parser.add_argument(
        "photo_ids",
        nargs="*",
        help="Photo ids to download. Example: 118074311217",
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Text file containing one photo_id per line.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="videos",
        help="Directory to save downloaded videos. Default: videos",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite local files that already exist.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    photo_ids = list(args.photo_ids)

    if args.file:
        photo_ids.extend(read_photo_ids(args.file))

    photo_ids = [str(photo_id).strip() for photo_id in photo_ids if str(photo_id).strip()]
    photo_ids = list(dict.fromkeys(photo_ids))

    if not photo_ids:
        raise SystemExit("Please provide at least one photo_id, or use --file photo_ids.txt")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from blobstore import download
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Cannot import blobstore dependency '{}'. Please run this script in the "
            "same Python environment that can run blobstore.py.".format(exc.name)
        )

    success_count = 0
    failed = []

    for photo_id in photo_ids:
        resource_id = "video_def_{}.mp4".format(photo_id)
        output_path = output_dir / "{}.mp4".format(photo_id)

        if output_path.exists() and not args.overwrite:
            print("[skip] {} already exists".format(output_path))
            continue

        print("[download] {} -> {}".format(resource_id, output_path))
        try:
            ok = download(resource_id, str(output_path))
        except Exception as exc:
            failed.append((photo_id, str(exc)))
            print("[failed] {}: {}".format(photo_id, exc))
            continue

        if ok and output_path.exists() and os.path.getsize(output_path) > 0:
            success_count += 1
            print("[ok] {}".format(output_path))
        else:
            failed.append((photo_id, "output file was not created or is empty"))
            print("[failed] {}: output file was not created or is empty".format(photo_id))

    print("Done. success={}, failed={}".format(success_count, len(failed)))
    if failed:
        print("Failed photo_ids:")
        for photo_id, reason in failed:
            print("  {}  {}".format(photo_id, reason))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
