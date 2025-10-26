import argparse
import asyncio
import json
from src.uam.nombres_uam import get_prof_names
from src.mp.scrape_prof import find_and_scrape


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["nombres-uam", "prof"])
    ap.add_argument("--name", help="Nombre exacto del profesor")
    args = ap.parse_args()

    if args.cmd == "nombres-uam":
        res = asyncio.run(get_prof_names())
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "prof":
        if not args.name:
            ap.error("--name es requerido")
        res = asyncio.run(find_and_scrape(args.name))
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

