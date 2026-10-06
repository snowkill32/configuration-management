import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, commands=""):
    # Запускаем программу отдельно и сохраняем ее вывод для проверки.
    return subprocess.run(
        [sys.executable, str(ROOT / "src/main.py"), *args],
        input=commands, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        cwd=ROOT, timeout=10,
    )


class CLITests(unittest.TestCase):
    def test_interactive(self):
        result = run_cli(commands="ls\nunknown\ncd /docs\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("minimal:/$ ", result.stdout)
        self.assertIn("Ошибка: неизвестная команда: unknown", result.stdout)
        self.assertIn("cd: аргументы = ['/docs']", result.stdout)

    def test_vfs_examples(self):
        for name in ("minimal", "files", "deep"):
            with self.subTest(name=name):
                result = run_cli(
                    "--vfs", f"examples/{name}.xml",
                    "--script", "examples/startup.txt",
                )
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn(f"Загружена VFS: {name}", result.stdout)
                self.assertIn(f"{name}:/$ exit", result.stdout)

    def test_script_errors(self):
        for name in ("unknown", "arguments", "exit", "ls"):
            with self.subTest(name=name):
                result = run_cli("--script", f"examples/error_{name}.txt")
                self.assertEqual(result.returncode, 1)
                self.assertIn("Ошибка в строке", result.stdout)
                self.assertNotIn("this-must-not-run", result.stdout)

    def test_loading_errors(self):
        for name in ("missing", "invalid"):
            with self.subTest(name=name):
                result = run_cli(
                    "--vfs", f"examples/{name}.xml",
                    "--script", "examples/startup.txt",
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("Ошибка загрузки VFS:", result.stdout)
                self.assertNotIn("аргументы =", result.stdout)

    def test_missing_script(self):
        result = run_cli("--script", "examples/missing.txt")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Ошибка чтения скрипта:", result.stdout)

    def test_invalid_cli_arguments(self):
        for args in (("--unknown",), ("--vfs",), ("--script",)):
            with self.subTest(args=args):
                self.assertEqual(run_cli(*args).returncode, 2)


if __name__ == "__main__":
    unittest.main()
