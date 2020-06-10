template = """
{
  "packagingVersion": "4.0",
  "upgradesFrom": ["{{upgrades-from}}"],
  "downgradesTo": ["{{downgrades-to}}"],
  "minDcosReleaseVersion": "1.9",
  "name": "%(package-name)s",
  "version": "{{package-version}}",
  "maintainer": "{{maintainer}}",
  "description": "YOURNAMEHERE on DC/OS",
  "selected": false,
  "framework": true,
  "tags": ["%(version)s", "%(package-name)s"],
  "postInstallNotes": "DC/OS %(package-name)s is being installed!\\n\\n\\tDocumentation: {{documentation-path}}\\n\\tIssues: {{issues-path}}",
  "postUninstallNotes": "DC/OS %(package-name)s is being uninstalled."
}
"""
