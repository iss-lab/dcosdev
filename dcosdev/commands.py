from collections import OrderedDict
import json
import os
import click
import base64
import docker, requests
import boto3
from . import oper
from . import basic
from . import helper

sdk_versions = ['0.42.1', '0.53.0', '0.55.2']


@click.group()
def maingroup():
    pass


@maingroup.group()
def operator():
    pass


@operator.command("new")
@click.argument("name")
@click.argument("sdk-version")
def operator_new(name, sdk_version):
    if sdk_version not in sdk_versions:
        click.echo('>>> Error: unsupported sdk version! Supported sdk versions are '+str(sdk_versions)+' .', err=True)
        return

    with open('svc.yml', 'w') as file:
            file.write(oper.svc.template%{'package-name': name})

    minio_host = os.environ.get("MINIO_HOST", "minio.marathon.l4lb.thisdcos.directory:9000")

    with open('config.yml', 'w') as file:
            file.write(oper.local_config.template%{'package-name': name,'version': sdk_version, 'minio-host': minio_host})

    os.makedirs('universe')
    with open('universe/package.json', 'w') as file:
            file.write(oper.package.template%{'package-name': name,'version': sdk_version})
    with open('universe/marathon.json.mustache', 'w') as file:
            file.write(oper.mjm.template)
    with open('universe/config.json', 'w') as file:
            file.write(oper.config.template%{'package-name': name})
    with open('universe/resource.json', 'w') as file:
            d = helper.sha_values()
            file.write(oper.resource.template%{'package-name': name, 'version': sdk_version, 'cli-darwin': d['dcos-service-cli-darwin'], 'cli-linux': d['dcos-service-cli-linux'], 'cli-win': d['dcos-service-cli.exe']})


@operator.group("add")
def operator_add():
    pass


@operator_add.command("java-scheduler")
def operator_add_java_scheduler():
    os.makedirs('java/scheduler/src/main/java/com/mesosphere/sdk/operator/scheduler')
    with open('java/scheduler/build.gradle', 'w') as file:
            file.write(oper.build_gradle.template % {'version': helper.cfg_get('sdk-version')})
    with open('java/scheduler/settings.gradle', 'w') as file:
            file.write(oper.settings_gradle.template)
    with open('java/scheduler/src/main/java/com/mesosphere/sdk/operator/scheduler/Main.java', 'w') as file:
            file.write(oper.main_java.template)


@operator_add.command("tests")
def operator_add_tests():
    os.makedirs('tests')
    package_name = helper.cfg_get('package-name')
    with open('tests/__init__.py', 'w') as file:
            file.write(oper.tests.init_py.template)
    with open('tests/config.py', 'w') as file:
            file.write(oper.tests.config.template%{'package-name': package_name})
    with open('tests/conftest.py', 'w') as file:
            file.write(oper.tests.conftest.template)
    with open('tests/test_overlay.py', 'w') as file:
            file.write(oper.tests.test_overlay.template%{'package-name': package_name})
    with open('tests/test_sanity.py', 'w') as file:
            file.write(oper.tests.test_sanity.template)


@operator.command("upgrade")
@click.argument("new-sdk-version")
def operator_upgrade(new_sdk_version):
    if new_sdk_version not in sdk_versions:
        print('>>> Error: unsupported sdk version! Supported sdk versions are '+str(sdk_versions)+' .')
        return

    old_sdk_version = helper.cfg_get('sdk-version')
    print('>>> INFO: upgrade from '+old_sdk_version+' to '+new_sdk_version)

    with open('universe/package.json', 'r') as f:
            package = f.read().replace(old_sdk_version, new_sdk_version)
    with open('universe/package.json', 'w') as f:
            f.write(package)

    with open('universe/resource.json', 'r') as f:
            resource = f.read().replace(old_sdk_version, new_sdk_version)
    with open('universe/resource.json', 'w') as f:
            f.write(resource)

    if os.path.exists('java/scheduler/build.gradle'):
        with open('java/scheduler/build.gradle', 'r') as f:
                build_gradle = f.read().replace(old_sdk_version, new_sdk_version)
        with open('java/scheduler/build.gradle', 'w') as f:
                f.write(build_gradle)


@maingroup.group("basic")
def basic_group():
    pass


@basic_group.command("new")
@click.argument("name")
def basic_new(name):
    with open('cmd.sh', 'w') as file:
        file.write(basic.cmd.template%{'package-name': name})

    minio_host = os.environ.get("MINIO_HOST", "minio.marathon.l4lb.thisdcos.directory:9000")

    with open('config.yml', 'w') as file:
            file.write(basic.local_config.template%{'package-name': name, 'minio-host': minio_host})

    os.makedirs('universe')
    with open('universe/package.json', 'w') as file:
        file.write(basic.package.template%{'package-name': name})
    with open('universe/marathon.json.mustache', 'w') as file:
        file.write(basic.mjm.template)
    with open('universe/config.json', 'w') as file:
        file.write(basic.config.template%{'package-name': name})
    with open('universe/resource.json', 'w') as file:
        file.write(basic.resource.template%{'package-name': name})


@maingroup.command()
def up():
    package_name = helper.cfg_get('package-name')
    artifacts_url = helper.cfg_get('artifacts-url')
    helper.build_repo()
    artifacts = helper.collect_artifacts()
    print(">>> INFO: uploading "+str(artifacts))
    helper.upload_minio(artifacts)
    os.remove('dist/'+package_name+'-repo.json')
    print('\nafter 1st up: dcos package repo add '+package_name+'-repo --index=0 '+artifacts_url+'/'+package_name+'-repo.json')
    print('\ndcos package install '+package_name+' --yes')
    print('\ndcos package uninstall '+package_name)
    print('\ndcos package repo remove '+package_name+'-repo'+'\n')


@maingroup.group()
def build():
    pass


@build.command("java")
def build_java():
    project_path = os.environ['PROJECT_PATH'] if 'PROJECT_PATH' in os.environ else os.getcwd()
    java_projects = [f for f in os.listdir(os.getcwd()+'/java') if os.path.isdir(os.getcwd()+'/java/'+f)]
    dockerClient = docker.from_env()
    for jp in java_projects:
        print('\n>>> INFO: gradle build starting for ' + jp)
        c = dockerClient.containers.run('gradle:4.8.0-jdk8', 'gradle check distZip', detach=True, auto_remove=True,
                                    volumes={project_path+'/java/'+jp : {'bind': '/home/gradle/project'}}, working_dir='/home/gradle/project')
        g = c.logs(stream=True)
        for l in g:
            print(l[:-1])


@maingroup.command()
@click.argument("dcos-url")
@click.option("--strict", is_flag=True, help="Test cluster is running in strict mode")
@click.option("--dcos-username", help="dc/os username", default="bootstrapuser")
@click.option("--dcos-password", help="dc/os password", default="deleteme")
def test(dcos_url, strict, dcos_username, dcos_password):
    package_name = helper.cfg_get('package-name')
    print(">>> tests starting ...")
    project_path =  os.environ['PROJECT_PATH'] if 'PROJECT_PATH' in os.environ else os.getcwd()
    dockerClient = docker.from_env()
    c = dockerClient.containers.run('realmbgl/dcos-commons:'+helper.cfg_get('sdk-version'), 'bash /build-tools/test_runner.sh /dcos-commons-dist', detach=True, auto_remove=True, working_dir='/build',
                                volumes={project_path : {'bind': '/build'},
                                            project_path+'/tests' : {'bind': '/dcos-commons-dist/tests'},
                                            project_path+'.gradle_cache' : {'bind': '/root/.gradle'}
                                },
                                environment={'DCOS_ENTERPRISE': 'true',
                                                'SECURITY': 'strict' if strict else '',
                                                'DCOS_LOGIN_USERNAME': dcos_username,
                                                'DCOS_LOGIN_PASSWORD': dcos_password,
                                                'CLUSTER_URL': dcos_url,
                                                'STUB_UNIVERSE_URL': 'http://'+os.environ['MINIO_HOST']+':9000/artifacts/'+package_name+'/'+package_name+'-repo.json',
                                                'FRAMEWORK': package_name,
                                                'PYTEST_ARGS': '-m \"sanity and not azure\"'
                                })
    g = c.logs(stream=True)
    for l in g:
        print(l[:-1])


@maingroup.group()
def release():
    pass


@release.command("aws")
@click.argument("s3-bucket")
@click.option("--universe", help="Path to a clone of https://github.com/mesosphere/universe (or universe fork)")
@click.option("--force", is_flag=True, help="Overwrite artifacts and universe files if already exist")
@click.option("--keep", is_flag=True, help="Keep repo file")
def release_aws(s3_bucket, universe, force, keep):
    cfg = helper.cfg_get_all()
    if universe:
        cfg['universe-path'] = universe
    package_name = cfg['package-name']
    package_version = cfg['package-version']
    cfg['artifacts-url'] = 'https://'+s3_bucket+'.s3.amazonaws.com/packages/'+package_name+'/'+package_version
    helper.build_repo(cfg)
    artifacts = helper.collect_artifacts(cfg)
    print(">>> INFO: releasing "+str(artifacts))
    helper.upload_aws(artifacts, s3_bucket, cfg)
    if 'universe-path' in cfg:
        os.makedirs(cfg['universe-path'])
        helper.write_universe_files(force, cfg)
    if not keep:
        os.remove('dist/'+package_name+'-repo.json')

@release.command("file")
@click.option("--universe", help="Path to a clone of https://github.com/mesosphere/universe (or universe fork)")
@click.option("--is-complete-path", is_flag=True, help="Do not generate universe path releaseVersion integer, etc")
@click.option("--force", is_flag=True, help="Overwrite artifacts and universe files if already exist")
@click.option("--keep", is_flag=True, help="Keep repo file")
def release_aws(universe, is_complete_path, force, keep):
    cfg = helper.cfg_get_all()
    if universe:
        cfg['universe-path'] = universe
    cfg['is-complete-path'] = is_complete_path
    package_name = cfg['package-name']
    helper.build_repo(cfg)
    artifacts = helper.collect_artifacts(cfg)
    print(">>> INFO: releasing "+str(artifacts))
    if 'universe-path' in cfg:
        os.makedirs(cfg['universe-path'])
        helper.write_universe_files(force, cfg)
    if not keep:
        os.remove('dist/'+package_name+'-repo.json')