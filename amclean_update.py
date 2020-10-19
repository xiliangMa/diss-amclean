#!/usr/bin/python3

import os
import sys
import json
import logging
import requests
import subprocess

def updateURL():
    return os.environ.get('AMCLEAN_UPDATE_URL', 'http://114.67.110.120:8080/v1/probe/virus/db/file/')

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
    log = logging.getLogger(__file__)
    #log.setLevel(logging.DEBUG)
    r = requests.get(updateURL() + 'info')
    r.raise_for_status()
    log.debug(r.text)
    updated = False
    for f in json.loads(r.text):
        filename = '/var/lib/clamav/' + f['file_name']
        #filename = '/var/lib/clamav/test/' + f['file_name']
        try:
            p = subprocess.check_output(['md5sum', filename], encoding='utf-8')
            md5 = p.split()[0]
        except Exception as e:
            log.warning(str(e))
            md5 = ''
        if md5 == f['file_hash']:
            log.info(f'Skip identical {f["file_name"]}')
            continue
        try:
            with open(filename + '.tmp', "xb") as target:
                log.info(f'Start downloading {f["file_name"]}')
                r = requests.get(updateURL() + 'download?filename=' + f['file_name'], stream=True)
                #r = requests.get(updateURL() + f['file_name'], timeout=10, stream=True)
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=4096):
                    target.write(chunk)
            p = subprocess.check_output(['md5sum', filename + '.tmp'], encoding='utf-8')
            md5 = p.split()[0]
            if md5 != f['file_hash']:
                log.warning(f'{f["file_name"]} md5 mismatch: {md5}/{f["file_hash"]}')
                os.remove(filename + '.tmp')
                continue
            os.rename(filename + '.tmp', filename)
            log.info(f'{f["file_name"]} updated')
            updated = True
        except FileExistsError as e:
            log.error(str(e))
            pass
        except Exception as e:
            log.error(f'Download {f["file_name"]} failed: {str(e)}')
            os.remove(filename + '.tmp')
        except:
            if os.path.exists(filename + '.tmp'):
                os.remove(filename + '.tmp')
            raise
    if not updated:
        sys.exit(1)
