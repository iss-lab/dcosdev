template = """
{
  "packagingVersion": "4.0",
  "upgradesFrom": ["%%(upgrades-from)s"],
  "downgradesTo": ["%%(downgrades-to)s"],
  "minDcosReleaseVersion": "1.9",
  "name": "%(package-name)s",
  "version": "%%(package-version)s",
  "maintainer": "%%(maintainer)s",
  "description": "%(package-name)s on DC/OS",
  "selected": false,
  "framework": true,
  "tags": ["%(version)s", "%(package-name)s"],
  "postInstallNotes": "DC/OS %(package-name)s is being installed!\\n\\n\\tDocumentation: %%(documentation-path)s\\n\\tIssues: %%(issues-path)s",
  "postUninstallNotes": "DC/OS %(package-name)s is being uninstalled."
}
"""
