#!/usr/bin/python3

import os
import sys
import errno
import time
import json
import subprocess
import docker
import requests
import logging

def amcleanURL():
    return os.environ.get('AMCLEAN_URL', 'https://111.229.167.6:8080/v1/container/virus')

def getHostMount():
    return '/host'

def getMounts(cid):
    host = getHostMount()
    if cid == 'host':
        return [(host, '')]
    client = docker.APIClient()
    info = client.inspect_container(cid)
    if info['State']['Running']:
        return [(host + info['GraphDriver']['Data']['MergedDir'], '')]

    ret = []
    return ret
    for path in info['GraphDriver']['Data']['LowerDir'].split(':'):
        ret.append((host + path, ''))
    ret.append((host + info['GraphDriver']['Data']['UpperDir'], ''))
    for mount in info['Mounts']:
        if mount['Type'] == 'volume' and mount['Driver'] == 'local' or\
           mount['Type'] == 'bind':
            ret.append((host + mount['Source'], mount['Destination']))
    return ret

def scan(target):
    result = {'task': 'virus_scan', 'host_id': host_id, 'container_id': target, 'records': []}
    if subprocess.call(['amclean_update.py']) == 0:
        subprocess.call(['clamdscan', '--reload'])
    for source,dest in getMounts(target):
        cmd = 'clamdscan --multiscan --infected --no-summary --fdpass ' + source
        #cmd += '/test'
        scan = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        while True:
            line = scan.stdout.readline().decode('utf-8')
            #expmple: /test/clam-mew.exe: Clamav.Test.File-6 FOUND\n
            #expmple: /host/proc/3278/environ: Access denied. ERROR\n
            if line == '' and scan.poll() is not None:
                break
            if not line.endswith(' FOUND\n'):
                continue
            name = line[:-1].split(':')
            virus = name[1].split()
            p = subprocess.run(['md5sum', name[0]], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if p.returncode == 0:
                md5 = p.stdout.decode('utf-8').split()[0]
            else:
                log.debug(f'md5 err {p.returncode}: {p.stderr}')
                md5 = ''
            try:
                size = os.stat(name[0]).st_size
            except OSError as e:
                size = 0
                log.warning(f'stat {name[0]}: {str(e)}')
            file_name = dest + name[0][len(source):]
            result['records'].append({ 'file_name': file_name,
                    'virus': virus[0],
                    'file_hash': md5,
                    'file_size': size,
                    })
    log.info(result)
    r = requests.post(amcleanURL(), json = result, verify=False)
    log.debug(f'code {r.status_code}, resp: {r.text}')

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
    log = logging.getLogger(__file__)
    #log.setLevel(logging.DEBUG)

    if len(sys.argv) != 2:
        log.error('Invalid argument: ' + str(sys.argv))
        sys.exit(errno.EINVAL)

    with open('/sys/class/dmi/id/product_uuid', 'r') as f:
        host_id = f.readline().strip()
    scan(sys.argv[1])
