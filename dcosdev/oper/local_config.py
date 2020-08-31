template = """
values:
  package-name: %(package-name)s
  package-version: snapshot
  artifacts-url: http://%(minio-host)s/artifacts/%(package-name)s
  minio-host: %(minio-host)s
  minio-access-key: %(minio-access-key)s
  minio-secret-key: %(minio-secret-key)s
  sdk-version: %(version)s
  upgrades-from: ""
  downgrades-to: ""
  documentation-path: https://github.com/YOURNAMEHERE/dcos-%(package-name)s
  issues-path: https://github.com/YOURNAMEHERE/dcos-%(package-name)s/issues
  maintainer: https://github.com/YOURNAMEHERE/dcos-%(package-name)s
  release-version: 0
  universe-path: "dist/universe"
  is-complete-path: true
"""
