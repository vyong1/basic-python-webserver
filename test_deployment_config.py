import unittest

from docker_entrypoint import (
    parse_instance_count,
    render_supervisor_programs,
    render_upstreams,
)


class DeploymentConfigTest(unittest.TestCase):
    def test_instance_count_configures_matching_backends_and_processes(self):
        count = parse_instance_count("3")

        self.assertEqual(
            render_upstreams(count),
            "server 127.0.0.1:8000;\n"
            "server 127.0.0.1:8001;\n"
            "server 127.0.0.1:8002;\n",
        )
        programs = render_supervisor_programs(count)
        for index, port in enumerate((8000, 8001, 8002)):
            self.assertIn(f"[program:gunicorn{index}]", programs)
            self.assertIn(f"--bind 127.0.0.1:{port}", programs)
            self.assertIn("--no-control-socket", programs)

    def test_instance_count_rejects_invalid_values(self):
        for value in ("0", "-1", "many"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_instance_count(value)


if __name__ == "__main__":
    unittest.main()
