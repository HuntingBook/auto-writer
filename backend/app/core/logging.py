import logging
import sys


def setup_logging(app_env: str) -> None:
  level = logging.INFO if app_env != "dev" else logging.DEBUG

  root = logging.getLogger()
  root.setLevel(level)
  handler = logging.StreamHandler(sys.stdout)
  formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
  )
  handler.setFormatter(formatter)
  root.handlers = [handler]
