template = """
{
  "packagingVersion": "4.0",
  "upgradesFrom": ["{{upgrades-from}}"],
  "downgradesTo": ["{{downgrades-to}}"],
  "minDcosReleaseVersion": "1.9",
  "name": "%(package-name)s",
  "version": "{{package-version}}",
  "maintainer": "support@YOURNAMEHERE.COM",
  "description": "YOURNAMEHERE on DC/OS",
  "selected": false,
  "framework": false,
  "tags": ["%(package-name)s"],
  "postInstallNotes": "DC/OS YOURNAMEHERE is being installed!\\n\\n\\tDocumentation: {{documentation-path}}\\n\\tIssues: {{issues-path}}",
  "postUninstallNotes": "DC/OS YOURNAMEHERE is being uninstalled."
}
"""
