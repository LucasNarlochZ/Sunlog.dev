from pathlib import Path
import subprocess
import tempfile
import unittest
import os
import yaml

ROOT = Path(__file__).resolve().parents[2]


class DeploymentTests(unittest.TestCase):
    def test_failed_build_stops_before_migrations(self):
        script = ROOT / 'scripts/deploy-homelab.sh'
        self.assertTrue(script.exists(), 'Homelab deploy script is missing')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / 'docker'
            docker.write_text('#!/bin/sh\nexit 42\n')
            docker.chmod(0o755)
            result = subprocess.run(['bash', str(script)], env={**os.environ, 'PATH': directory + ':' + os.environ['PATH'], 'DEPLOY_PATH': str(ROOT)})
            self.assertNotEqual(result.returncode, 0)


class ProductionCutoverTests(unittest.TestCase):
    def test_main_push_deploys_to_homelab_only(self):
        workflows = ROOT / '.github/workflows'
        homelab = yaml.load((workflows / 'homelab.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(homelab['on'].get('push', {}).get('branches'), ['main'])
        self.assertIn('workflow_dispatch', homelab['on'])
        self.assertEqual(homelab['jobs']['deploy']['environment'], 'production-homelab')
        self.assertEqual(homelab['concurrency']['cancel-in-progress'], 'false')
        vps = yaml.load((workflows / 'cd.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertNotIn('push', vps['on'])
        self.assertEqual(vps['jobs']['deploy'].get('if'), '${{ false }}')

    def test_worker_is_enabled_by_default_and_recovers_after_reboot(self):
        base = yaml.load((ROOT / 'infra/docker-compose.yml').read_text(), Loader=yaml.BaseLoader)
        overlay = yaml.load((ROOT / 'infra/docker-compose.homelab.yml').read_text(), Loader=yaml.BaseLoader)
        worker = {**base['services']['worker'], **overlay['services'].get('worker', {})}
        self.assertFalse(worker.get('profiles'))
        self.assertEqual(worker['restart'], 'unless-stopped')
