"""Literal, non-executing configuration."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    paid_tests_enabled: bool = False


def load_config(*, environ=None, path=None):
    return Config()
