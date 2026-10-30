from pathlib import Path
import subprocess
import tempfile
import unittest
import os

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
