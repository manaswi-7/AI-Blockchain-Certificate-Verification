"""Compatibility entry point for the canonical certificate generator.

Do not maintain a second certificate renderer here. The canonical generator
creates the genuine/tampered pair from one fixed template.
"""
import argparse

from generate_500_certificate_dataset import generate


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=500)
    args = parser.parse_args()
    generate(args.count)
