#!/usr/bin/python

import argparse
import json
import subprocess

class Delete:
    def __init__(self):
        self.list_of_vm = []
        self.list_of_id = []

    def loadjson(self, file):
        with open(file, 'r') as f:
            out = json.loads(f.read())
            self.list_of_vm = out

    def create_list(self):
        for dict in self.list_of_vm:
            temp_id = dict['id']
            self.list_of_id.append(temp_id)

    def delete_list(self):
        for id in self.list_of_id:
            cmd = "symp -k -u admin -d cloud_admin -p 'admin' --url http://10.201.32.10" \
                   " vm remove " + id
            subprocess.call(cmd, shell=True)

def _get_args():
    parser = argparse.ArgumentParser(description='***Delete VMs in JSON***')
    parser.add_argument('-i', action='store', help='JSON file')
    return parser.parse_args()


if __name__ == "__main__":
    my_args = _get_args()
    delete = Delete()
    delete.loadjson(my_args.i)
    # delete.loadjson('vmlist1')
    delete.create_list()
    delete.delete_list()
