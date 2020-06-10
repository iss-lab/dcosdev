import os, sys, json, base64, time, datetime, shutil
from collections import OrderedDict
sys.dont_write_bytecode=True
from minio import Minio
from minio.error import ResponseError
import requests
import boto3
import yaml

def cfg_get(key, default='', cfg={}):
    if not cfg:
        cfg = cfg_get_all()
    if key in cfg:
        return cfg[key]
    return default

def cfg_get_all():
    with open('universe/package.json', 'r') as f:
         package = json.load(f)

    minio_host = os.environ.get("MINIO_HOST", "minio.marathon.l4lb.thisdcos.directory:9000")

    runtime_values = {
        'time_epoch_ms': str(int(time.time()*1000)),
        'time_str': datetime.datetime.utcnow().isoformat(),
        'package-name': package['name'],
        'package-version': package['version'],
        'sdk-version': package['tags'][0],
        'artifacts-url': 'http://'+minio_host+'/artifacts/'+package['name'],
        'release-version': 0,
        'upgrades-from': '',
        'downgrades-to': '',
        'documentation-path': 'https://github.com/YOURNAMEHERE/dcos-'+package['name'],
        'issues-path': 'https://github.com/YOURNAMEHERE/dcos-'+package['name']+'/issues',
        'maintainer': 'https://github.com/YOURNAMEHERE/dcos-'+package['name']
    }

    config_values = dict()
    if os.path.exists("config.yml"):
        with open("config.yml") as f:
            config_values = yaml.safe_load(f.read()).get("values", dict())
    return {**runtime_values, **config_values}

def sha_values():
    r = requests.get('https://downloads.mesosphere.com/dcos-commons/artifacts/'+cfg_get('sdk-version')+'/SHA256SUMS')
    return {e[1]:e[0] for e in map(lambda e: e.split('  '), str(r.text).split('\n')[:-1])}

def build_repo(cfg={}):
    if not cfg:
        cfg = cfg_get_all()

    repository = {'packages': [] }
    packages = repository['packages']

    package = json.loads(_prerender_file(cfg, 'universe/package.json'), object_pairs_hook=OrderedDict)
    config = json.loads(_read_file('universe/config.json'), object_pairs_hook=OrderedDict)
    resource = json.loads(_prerender_file(cfg, 'universe/resource.json'), object_pairs_hook=OrderedDict)
    marathon = base64.b64encode(_prerender_file(cfg, 'universe/marathon.json.mustache').encode("utf-8")).decode("utf-8")

    if os.path.exists('java/scheduler/build/distributions/operator-scheduler.zip'):
         resource['assets']['uris']['scheduler-zip'] = cfg['artifacts-url']+'/operator-scheduler.zip'

    package['version'] = cfg['package-version']
    package['releaseVersion'] = cfg['release-version']
    package['config'] = config
    package['resource'] = resource
    package['marathon'] = {"v2AppMustacheTemplate": marathon}

    packages.append(package)
    os.makedirs("dist", exist_ok=True)
    with open('dist/'+cfg['package-name']+'-repo.json', 'w') as file:
         file.write(json.dumps(repository, indent=4))


def collect_artifacts(cfg={}):
    artifacts = [str('dist/'+cfg_get('package-name', '', cfg)+'-repo.json')]
    if os.path.exists("files"):
        artifacts.extend([os.path.join("files", f) for f in os.listdir('files')])
    if os.path.exists("svc.yml"):
        artifacts.append("svc.yml")
    if os.path.exists('java'):
       java_projects = ['java/'+f for f in os.listdir('java') if os.path.isdir('java/'+f)]
       dists = {jp+'/build/distributions':os.listdir(jp+'/build/distributions') for jp in java_projects}
       artifacts.extend([d+'/'+f for d in dists for f in dists[d]])
    return artifacts


def upload_minio(artifacts, cfg={}):
    minio_host = os.environ.get("MINIO_HOST", "minio.marathon.l4lb.thisdcos.directory:9000")
    access_key = os.environ.get("MINIO_ACCESS_KEY", "minio")
    secret_key = os.environ.get("MINIO_SECRET_KEY", "minio123")
    minioClient = Minio(minio_host, access_key=access_key, secret_key=secret_key, secure=False)

    for a in artifacts:
        try:
           file_stat = os.stat(a)
           file_data = open(a, 'rb')
           minioClient.put_object('artifacts', cfg_get('package-name','',cfg)+'/'+os.path.basename(a), file_data, file_stat.st_size, content_type='application/vnd.dcos.universe.repo+json;charset=utf-8;version=v4')
        except ResponseError as err:
           print(err)

def upload_aws(artifacts, bucket, cfg={}):
    if not cfg:
        cfg = cfg_get_all()

    s3 = boto3.client('s3')

    for a in artifacts:
        with open(a, "rb") as f:
             s3.upload_fileobj(f, bucket, 'packages/'+cfg['package-name']+'/'+cfg['package-version']+'/'+os.path.basename(a), ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/vnd.dcos.universe.repo+json;charset=utf-8;version=v4'})


def write_universe_files(force, cfg={}):
    if not cfg:
        cfg = cfg_get_all()

    is_complete_path = cfg_get('is-complete-path', False, cfg)
    if is_complete_path:
        path = cfg['universe-path']
    else:
        path = cfg['universe-path']+'/packages/'+cfg['package-name'][0].upper()+'/'+cfg['package-name']
        if not os.path.exists(path):
            print('>>> ERROR: package folder %s does not exist' % path)
            return
        path = path+'/'+str(cfg['release-version'])
    if not force and not is_complete_path and os.path.exists(path):
        print('>>> ERROR: release version folder \''+cfg['release-version']+'\' exists already !')
        return
    
    os.makedirs(path, exist_ok=True)
    package = _prerender_file(cfg, 'universe/package.json')
    config = _read_file('universe/config.json')
    resource = _prerender_file(cfg, 'universe/resource.json')
    marathon = _prerender_file(cfg, 'universe/marathon.json.mustache')

    with open(path+'/config.json', 'w') as f:
        f.write(config)
    with open(path+'/resource.json', 'w') as f:
        f.write(resource)
    with open(path+'/marathon.json.mustache', 'w') as f:
        f.write(marathon)
    with open(path+'/package.json', 'w') as f:
        f.write(package)
        
def _prerender_file(cfg, filename):
    data = _read_file(filename)
    return data % cfg

def _read_file(filename):
    with open(filename) as f:
        return f.read()
