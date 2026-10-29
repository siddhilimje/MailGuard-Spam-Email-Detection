import os
import glob
import yaml

def test_yaml_files():
    files = glob.glob(".github/workflows/*.yml") + ["docker-compose.yml", "params.yaml"]
    print(f"Checking {len(files)} YAML configurations...")
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            assert data is not None, f"File {fpath} loaded as empty!"
            print(f"  [OK] {fpath}")

if __name__ == "__main__":
    test_yaml_files()

