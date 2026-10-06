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
        self.assertIn("vfs:/$ ", result.stdout)
        self.assertIn("Ошибка: неизвестная команда: unknown", result.stdout)
        self.assertIn("cd: аргументы = ['/docs']", result.stdout)

    def test_config_parameters(self):
        for path in ("demo.csv", "data/archive.csv", "my files/demo.csv"):
            with self.subTest(path=path):
                result = run_cli(
                    "--vfs", path,
                    "--script", "examples/startup.txt",
                )
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn(f"VFS: {Path(path)}", result.stdout)
                self.assertIn(str(Path("examples/startup.txt")), result.stdout)
                self.assertIn(f"{Path(path).stem}:/$ exit", result.stdout)

    def test_script_errors(self):
        for name in ("unknown", "arguments", "exit", "ls", "quotes"):
            with self.subTest(name=name):
                result = run_cli("--script", f"examples/error_{name}.txt")
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn("Ошибка в строке", result.stdout)
                self.assertIn("аргументы = ['/after-error']", result.stdout)

    def test_vfs_parameter_without_script(self):
        result = run_cli("--vfs", "missing.csv", commands="ls\nexit\n")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("VFS: missing.csv", result.stdout)
        self.assertIn("Стартовый скрипт: не задан", result.stdout)
        self.assertIn("missing:/$ ls", result.stdout)
        self.assertIn("ls: аргументы = []", result.stdout)

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
