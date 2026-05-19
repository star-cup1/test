# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# Author     ：Bo Wang
# File       : blobstore.py
# Time       ：2022/10/26 11:41
"""
# -*- encoding: utf-8 -*-
import glob
import logging
import threading
import traceback

import boto3
import os
from botocore import UNSIGNED
from botocore.config import Config
import boto3
from urllib.parse import urlsplit
from typing import Tuple
import cv2
import os
from get_kconf_params import get_kconf_value

s3_client_config = Config(s3={'addressing_style': 'path'}, signature_version=UNSIGNED)  # 固定配置，不可更改

# s3_endpoint_url = "http://bs3-hb1.internal"  # 线上环境


# endpoint_url = "http://bs3-hb1.staging.kuaishou.com"         # Staging 环境


class BlobStoreClient(object):
    def __init__(self, bucket_name):
        self.s3_bucket = bucket_name
        kconf_params = get_kconf_value("ad.algorithm.nieuwlandGeneration", "json")
        cfg = kconf_params["blobstore_for_outsea"]
        # cfg = ['ad-i18n-dsp']
        if bucket_name in cfg:
            s3_endpoint_url = "http://bs3-sgp.internal"  # 海外环境
        else:
            s3_endpoint_url = "http://bs3-hb1.internal"  # 国内线上环境

        self.s3_client = boto3.client("s3", endpoint_url=s3_endpoint_url, config=s3_client_config)

    def check_key_exists(self, key):
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                return False
            return True
        except:
            return False
        return False 

    # see: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_object
    def upload_binary_to_s3(self, file_path, key):
        try:
            # binfile = open(file_path, 'rb')
            with open(file_path, 'rb') as binfile:
                self.s3_client.put_object(Bucket=self.s3_bucket, Body=binfile, Key=key)
                print('upload_succ:', key)
        except Exception as e:
            logging.error(e)

    def upload_bytes_to_s3(self, string, key):
        try:
            self.s3_client.put_object(Bucket=self.s3_bucket, Body=string, Key=key)
            print(f'upload_succ: {key}')
        except Exception as e:
            print(f'error:{e}')
            return False
        return True

    # see: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_object
    def download_binary_from_s3(self, key, dest_key, bucket=""):
        try:
            real_bucket = bucket if len(bucket) > 0 else self.s3_bucket
            response = self.s3_client.get_object(Bucket=real_bucket, Key=key)
            # print(response)
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                print(response)
                return False
            with open(dest_key, 'wb') as binfile:
                chunk_size = 1024 * 128
                while True:
                    chunk = response["Body"].read(chunk_size)
                    if not chunk:
                        break
                    binfile.write(chunk)
            # print('download and write succ:', key, dest_key)
        except Exception as e:
            logging.error(e)
            return False
        return True

    def download_bytes_from_s3(self, key, bucket=""):
        byte_val = None
        try:
            real_bucket = bucket if len(bucket) > 0 else self.s3_bucket
            response = self.s3_client.get_object(Bucket=real_bucket, Key=key)
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                print(f"error response:{response}")
                return False, byte_val
            byte_val = response['Body'].read()
            print(f'download_succ: {key}')
        except Exception as e:
            print(f'error:{e}')
            return False, byte_val
        return True, byte_val

    def batch_download_binary_from_s3(self, item_map):
        for k, v in item_map.items():
            self.download_binary_from_s3(k, v[0], v[1])

    def concurrency_download(self, item_map, batch_size=1):
        count = 0
        batch_list = []
        thread_list = []
        for k, v in item_map.items():
            if count % batch_size == 0:
                batch_list.append({})
            batch_list[-1].update({k: v})
            count += 1

        for batch in batch_list:
            thread_list.append(threading.Thread(target=self.batch_download_binary_from_s3, args=(batch, )))

        for t in thread_list:
            t.start()

        for t in thread_list:
            t.join()

    def object_exists(self, key):
        try:
            # response = self.s3_client.object_exists(Bucket=self.s3_bucket, Key=key)
            response = self.s3_client.head_object(Bucket=self.s3_bucket, Key=key)
            print(response)
            return True
        except Exception as e:
            logging.error(e)
            return False

    def get_object_bytes(self, key):
        try:
            real_bucket = self.s3_bucket
            response = self.s3_client.get_object(Bucket=real_bucket, Key=key)
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                print(response)
                return None
            return response["Body"].read()
        except Exception as e:
            logging.error(e)
            return None

    def list(self, prefix, delimiter='/'):
        return self.s3_client.list_objects(Bucket=self.s3_bucket, Prefix=prefix, Delimiter=delimiter)

def blobstore_download(bucket_name, key, local_file):
    try:
        client = BlobStoreClient(bucket_name)
        client.download_binary_from_s3(key, local_file)
        return True
    except:
        print(traceback.format_exc())
        return True


# see: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_object
# def get_meta_demo(self):
#    try:
#        response = client.get_object(Bucket=bucket, Key="test-python")
#        print(response["ContentType"])
#    except Exception as e:
#        logging.error(e)


def test_client():
    key = 'fullsds_45009408746.mp4'
    dest_key = 'test_wide_fullsds_45009408746.mp4'
    client = BlobStoreClient('ad-ad-material-union')
    if client.download_binary_from_s3(key, dest_key):
        here_direction = os.path.dirname(__file__)
        file_path = os.path.join(here_direction, dest_key)
        client.upload_binary_to_s3(file_path, dest_key)
        response = client.s3_client.get_object(Bucket=client.s3_bucket, Key=dest_key)
        if os.path.exists(file_path):
            os.remove(file_path)
        print(response)


def upload(filename, key):
    client = BlobStoreClient('ad-nieuwland-material')
    # for filename in filenames:
        # key = os.path.splitext(os.path.basename(filename))[0]
    client.upload_binary_to_s3(filename, key)
    response = client.s3_client.get_object(Bucket=client.s3_bucket, Key=key)
    print(response)


def resource_decode(source, split_flag="_"):
    items = source.split(split_flag)
    db, tabel, key = items[0], items[1], split_flag.join(items[2:])
    return db, tabel, key

def download(resource_id, output):
    # db, tabel, key = resource_decode(resource_id)
    client = BlobStoreClient('ad-nieuwland-material')
    client.download_binary_from_s3(resource_id, output)


if __name__ == '__main__':
    # test_client()
    download("video_def_195252462634.mp4", "195252462634.mp4")
    print("download ok ")
    # upload(["/data/phd/wan720p_output/uno/b64bc59e-6300-44fb-b46b-170a4169529b/output/0_0.png"], "i2t2v/image/20250606_103643_0_0.png")
    # print("upload ok ")
