import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
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
        for path in ("examples/minimal.csv", "examples/files.csv",
                     "examples/deep.csv"):
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
        result = run_cli("--vfs", "examples/files.csv", commands="ls\nexit\n")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(str(Path("examples/files.csv")), result.stdout)
        self.assertIn("Стартовый скрипт: не задан", result.stdout)
        self.assertIn("files:/$ ", result.stdout)
        self.assertIn("Добро пожаловать в VFS files!", result.stdout)
        self.assertIn("ls: аргументы = []", result.stdout)

    def test_default_in_memory(self):
        result = run_cli(commands="exit\n")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("VFS: по умолчанию (в памяти)", result.stdout)
        self.assertIn("  /: каталог", result.stdout)

    def test_loading_errors_before_script(self):
        for name in ("missing", "invalid"):
            with self.subTest(name=name):
                result = run_cli(
                    "--vfs", f"examples/{name}.csv",
                    "--script", "examples/startup.txt",
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("Ошибка загрузки VFS:", result.stdout)
                self.assertNotIn("ls: аргументы", result.stdout)

    def test_motd_before_commands(self):
        result = run_cli(
            "--vfs", "examples/files.csv",
            "--script", "examples/startup.txt",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertLess(
            result.stdout.index("Добро пожаловать в VFS files!"),
            result.stdout.index("files:/$ ls"),
        )

    def test_paths_with_spaces(self):
        with TemporaryDirectory(prefix="my files ") as folder:
            vfs_path = Path(folder) / "my vfs.csv"
            script_path = Path(folder) / "my startup.txt"
            vfs_path.write_bytes((ROOT / "examples/minimal.csv").read_bytes())
            script_path.write_text("exit\n", encoding="utf-8")
            result = run_cli(
                "--vfs", str(vfs_path), "--script", str(script_path)
            )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("my vfs:/$ exit", result.stdout)

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
