template = """
{
  "id": "{{service.name}}",
  "cpus": 1.0,
  "mem": 1024,
  "instances": 1,
  "user": "{{service.user}}",
  "cmd": "export LD_LIBRARY_PATH=$MESOS_SANDBOX/libmesos-bundle/lib:$LD_LIBRARY_PATH; export MESOS_NATIVE_JAVA_LIBRARY=$(ls $MESOS_SANDBOX/libmesos-bundle/lib/libmesos-*.so); export JAVA_HOME=$(ls -d $MESOS_SANDBOX/jdk*/jre/); export JAVA_HOME=${JAVA_HOME%%/}; export PATH=$(ls -d $JAVA_HOME/bin):$PATH && export JAVA_OPTS=\\"-Xms256M -Xmx512M -XX:-HeapDumpOnOutOfMemoryError\\" && ./bootstrap -resolve=false -template=false && ./operator-scheduler/bin/operator svc.yml",
  "labels": {
    "DCOS_COMMONS_API_VERSION": "v1",
    "DCOS_COMMONS_UNINSTALL": "true",
    "DCOS_PACKAGE_FRAMEWORK_NAME": "{{service.name}}",
    "MARATHON_SINGLE_INSTANCE_APP": "true",
    "DCOS_SERVICE_NAME": "{{service.name}}",
    "DCOS_SERVICE_PORT_INDEX": "0",
    "DCOS_SERVICE_SCHEME": "http"
  },
  {{#service.service_account_secret}}
  "secrets": {
    "serviceCredential": {
      "source": "{{service.service_account_secret}}"
    }
  },
  {{/service.service_account_secret}}
  "env": {
    "PACKAGE_NAME": "{{package-name}}",
    "PACKAGE_VERSION": "{{package-version}}",
    "PACKAGE_BUILD_TIME_EPOCH_MS": "%(time_epoch_ms)s",
    "PACKAGE_BUILD_TIME_STR": "%(time_str)s",
    "FRAMEWORK_NAME": "{{service.name}}",
    "SLEEP_DURATION": "{{service.sleep}}",
    "FRAMEWORK_USER": "{{service.user}}",
    "FRAMEWORK_PRINCIPAL": "{{service.service_account}}",
    "FRAMEWORK_LOG_LEVEL": "{{service.log_level}}",
    "MESOS_API_VERSION": "V1",

    "NODE_COUNT": "{{node.count}}",
    "NODE_PLACEMENT": "{{{node.placement_constraint}}}",
    {{#service.virtual_network_enabled}}
    "ENABLE_VIRTUAL_NETWORK": "yes",
    "VIRTUAL_NETWORK_NAME": "{{service.virtual_network_name}}",
    "VIRTUAL_NETWORK_PLUGIN_LABELS": "{{service.virtual_network_plugin_labels}}",
    {{/service.virtual_network_enabled}}
    "NODE_CPUS": "{{node.cpus}}",
    "NODE_MEM": "{{node.mem}}",
    "NODE_DISK": "{{node.disk}}",
    "NODE_DISK_TYPE": "{{node.disk_type}}",

    "PAUSE_OVERRIDE_CMD": "echo This task is PAUSED, sleeping ... && /mnt/mesos/sandbox/bootstrap --resolve=false && while true; do sleep 3600; done",

    "JAVA_URI": "{{resource.assets.uris.jre-tar-gz}}",
    "EXECUTOR_URI": "{{resource.assets.uris.executor-zip}}",
    "BOOTSTRAP_URI": "{{resource.assets.uris.bootstrap-zip}}",
    {{#service.service_account_secret}}
    "DCOS_SERVICE_ACCOUNT_CREDENTIAL": { "secret": "serviceCredential" },
    "MESOS_MODULES": "{\\"libraries\\":[{\\"file\\":\\"libmesos-bundle\\/lib\/mesos\\/libdcos_security.so\\",\\"modules\\":[{\\"name\\": \\"com_mesosphere_dcos_ClassicRPCAuthenticatee\\"},{\\"name\\":\\"com_mesosphere_dcos_http_Authenticatee\\",\\"parameters\\":[{\\"key\\":\\"jwt_exp_timeout\\",\\"value\\":\\"5mins\\"},{\\"key\\":\\"preemptive_refresh_duration\\",\\"value\\":\\"30mins\\"}]}]}]}",
    "MESOS_AUTHENTICATEE": "com_mesosphere_dcos_ClassicRPCAuthenticatee",
    "MESOS_HTTP_AUTHENTICATEE": "com_mesosphere_dcos_http_Authenticatee",
    {{/service.service_account_secret}}
    "LIBMESOS_URI": "{{resource.assets.uris.libmesos-bundle-tar-gz}}"
  },
  "uris": [
    "{{resource.assets.uris.bootstrap-zip}}",
    "{{resource.assets.uris.jre-tar-gz}}",
    "{{resource.assets.uris.scheduler-zip}}",
    "{{resource.assets.uris.libmesos-bundle-tar-gz}}",
    "{{resource.assets.uris.svc}}"
  ],
  "upgradeStrategy":{
    "minimumHealthCapacity": 0,
    "maximumOverCapacity": 0
  },
  "healthChecks": [
    {
      "protocol": "MESOS_HTTP",
      "path": "/v1/health",
      "gracePeriodSeconds": 900,
      "intervalSeconds": 30,
      "portIndex": 0,
      "timeoutSeconds": 30,
      "maxConsecutiveFailures": 0
    }
  ],
  "portDefinitions": [
    {
      "port": 0,
      "protocol": "tcp",
      "name": "api",
      "labels": { "VIP_0": "/api.{{service.name}}:80" }
    }
  ]
}
"""
