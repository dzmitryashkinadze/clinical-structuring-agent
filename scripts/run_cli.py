import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("run_cli")


def run_cli_end_to_end():
    """Runs the CLI process command end-to-end on a sample file."""

    # 1. Ensure the output directory exists
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Define input and output paths
    input_file = Path("data/notes/sample1.txt")
    output_file = output_dir / "sample1.fhir.json"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    logger.info("Running CLI end-to-end test...")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")

    # 3. Build and execute the CLI command
    command = [
        "uv",
        "run",
        "python",
        "src/main.py",
        "process",
        "--file",
        str(input_file),
        "--out",
        str(output_file),
    ]

    logger.info(f"Executing: {' '.join(command)}")

    try:
        # Run the command and capture output
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            env={"PYTHONPATH": "."} | dict(os.environ) if "os" in sys.modules else None,
        )

        # Print stdout and stderr from the CLI
        if result.stdout:
            logger.info("CLI Output:\n" + result.stdout)
        if result.stderr:
            logger.warning("CLI Errors/Warnings:\n" + result.stderr)

        # 4. Verify output file was created
        if output_file.exists():
            logger.info(f"SUCCESS: Output file created at {output_file}")
            with open(output_file, "r") as f:
                content = f.read()
                logger.info(f"Generated FHIR JSON:\n{content}")
        else:
            logger.error("FAILED: Output file was not created.")

    except subprocess.CalledProcessError as e:
        logger.error(f"CLI command failed with exit code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import os

    run_cli_end_to_end()
