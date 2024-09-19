from csv import DictReader
from pathlib import Path

with Path("data/secondary-metabolism.csv").open(encoding="utf-8") as f:
    articles = [i["Article Title"] for i in DictReader(f)]


__all__ = ["articles"]
