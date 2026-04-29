from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests


TEST_PRODUCT_NAME = "Mexico vs South Africa - World Cup - Match 1 (Group A)"
WORLDCUP_PREFIX = "FIFA World Cup 2026 - Group "


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def is_worldcup_name(name: str) -> bool:
    return (name or "").startswith(WORLDCUP_PREFIX)


def parse_bool(raw: str | None, default: bool = True) -> bool:
    if raw is None:
        return default
    return str(raw).strip().lower() == "true"


def build_products_from_csv(csv_path: Path, image_base_url: str) -> list[dict[str, Any]]:
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    if not rows:
        raise ValueError(f"CSV vacio: {csv_path}")

    matches: OrderedDict[tuple[str, str, str, str, str], dict[str, Any]] = OrderedDict()
    for row in rows:
        key = (
            row["ticket_nombre"],
            row["ticket_fecha"],
            row["ticket_ubicacion"],
            row["ticket_estadio"],
            row["ticket_ubicacion_estadio"],
        )

        if key not in matches:
            grupo = (row.get("grupo") or "").strip()
            home = (row.get("home_team") or "").strip()
            away = (row.get("away_team") or "").strip()
            fecha = (row.get("ticket_fecha") or "").strip()

            slug = f"g{slugify(grupo)}-{slugify(home)}-vs-{slugify(away)}-{fecha[:10]}"
            image_url = f"{image_base_url.rstrip('/')}/{slug}.svg"

            base_desc = (row.get("ticket_descripcion") or "").strip()
            extra_desc = (
                f" Datos adicionales: grupo={grupo}; home_team={home}; away_team={away}; "
                f"logo_local_url={(row.get('logo_local_url') or '').strip()}; "
                f"logo_visitante_url={(row.get('logo_visitante_url') or '').strip()}."
            )

            matches[key] = {
                "nombre": row["ticket_nombre"],
                "fecha": row["ticket_fecha"],
                "ubicacion": row["ticket_ubicacion"],
                "estadio": row["ticket_estadio"] or None,
                "ubicacion_estadio": row["ticket_ubicacion_estadio"] or None,
                "descripcion": f"{base_desc}{extra_desc}",
                "imagen": image_url,
                "is_active": parse_bool(row.get("ticket_is_active"), default=True),
                "categorias": [],
            }

        matches[key]["categorias"].append(
            {
                "nombre": row["categoria_nombre"],
                "descripcion": row["categoria_descripcion"] or None,
                "precio": float(row["categoria_precio"]),
                "moneda": (row["categoria_moneda"] or "USD").upper(),
                "unidades_disponibles": int(row["categoria_unidades_disponibles"]),
                # Se fuerza sin limite por requerimiento de negocio.
                "limite_por_usuario": None,
                "activo": parse_bool(row.get("categoria_activo"), default=True),
                "is_active": parse_bool(row.get("categoria_is_active"), default=True),
            }
        )

    return list(matches.values())


def fetch_all_products(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    response = session.get(
        f"{base_url}/productos/",
        params={"skip": 0, "limit": 5000, "only_active": "false"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def archive_product(session: requests.Session, base_url: str, token: str, product: dict[str, Any]) -> None:
    product_id = int(product["id"])
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    product_resp = session.put(
        f"{base_url}/productos/{product_id}",
        headers=headers,
        json={"is_active": False},
        timeout=60,
    )
    if product_resp.status_code not in (200, 404):
        raise RuntimeError(
            f"No se pudo archivar producto {product_id}: {product_resp.status_code} {product_resp.text[:300]}"
        )

    for category in product.get("categorias") or []:
        category_id = category.get("id")
        if category_id is None:
            continue

        category_resp = session.put(
            f"{base_url}/categorias/{category_id}",
            headers=headers,
            json={
                "activo": False,
                "is_active": False,
                "unidades_disponibles": 0,
                "limite_por_usuario": None,
            },
            timeout=60,
        )
        if category_resp.status_code not in (200, 404):
            raise RuntimeError(
                f"No se pudo archivar categoria {category_id}: {category_resp.status_code} {category_resp.text[:300]}"
            )


def run_import(
    *,
    csv_path: Path,
    base_url: str,
    token: str,
    image_base_url: str,
    dry_run: bool,
) -> int:
    if not csv_path.exists():
        print(f"ERROR: CSV no encontrado: {csv_path}")
        return 1

    products = build_products_from_csv(csv_path, image_base_url=image_base_url)
    expected_products = len(products)
    expected_categories = sum(len(p["categorias"]) for p in products)
    print(f"EXPECTED products={expected_products} categories={expected_categories}")

    desired_names = {p["nombre"] for p in products}

    session = requests.Session()
    existing = fetch_all_products(session, base_url)
    backup_path = csv_path.parent / f"prod_productos_backup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
    backup_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"BACKUP saved={backup_path} count={len(existing)}")

    cleanup_candidates: list[dict[str, Any]] = []
    for product in existing:
        name = (product.get("nombre") or "").strip()
        lower = name.lower()
        if (
            name == TEST_PRODUCT_NAME
            or "prueba" in lower
            or is_worldcup_name(name)
            or name in desired_names
        ):
            cleanup_candidates.append(product)

    print(f"CLEANUP candidates={len(cleanup_candidates)}")
    if dry_run:
        return 0

    auth_headers = {"Authorization": f"Bearer {token}"}
    json_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    deleted = 0
    archived = 0
    for product in cleanup_candidates:
        product_id = int(product["id"])
        name = product.get("nombre") or ""

        delete_resp = session.delete(
            f"{base_url}/productos/{product_id}",
            headers=auth_headers,
            timeout=60,
        )
        if delete_resp.status_code in (204, 404):
            deleted += 1
            print(f"DELETED id={product_id} name={name}")
            continue

        if name == TEST_PRODUCT_NAME or "prueba" in name.lower():
            archive_product(session, base_url, token, product)
            archived += 1
            print(f"ARCHIVED id={product_id} name={name}")
            continue

        raise RuntimeError(
            f"No se pudo eliminar producto de mundial id={product_id}, status={delete_resp.status_code}, body={delete_resp.text[:400]}"
        )

    print(f"CLEANUP_RESULT deleted={deleted} archived={archived}")

    created = 0
    create_errors: list[dict[str, Any]] = []
    for payload in products:
        create_resp = session.post(
            f"{base_url}/productos/",
            headers=json_headers,
            json=payload,
            timeout=90,
        )
        if create_resp.status_code != 201:
            create_errors.append(
                {
                    "nombre": payload["nombre"],
                    "status": create_resp.status_code,
                    "body": create_resp.text[:500],
                }
            )
            continue

        created += 1
        body = create_resp.json()
        print(f"CREATED id={body.get('id')} name={body.get('nombre')} categorias={len(body.get('categorias') or [])}")

    print(f"CREATED total={created} errors={len(create_errors)}")
    if create_errors:
        print("CREATE_ERROR_SAMPLE", json.dumps(create_errors[:5], ensure_ascii=False))
        return 1

    final_items = fetch_all_products(session, base_url)
    worldcup_items = [item for item in final_items if is_worldcup_name(item.get("nombre") or "")]
    final_categories = sum(len(item.get("categorias") or []) for item in worldcup_items)
    non_null_limits = sum(
        1
        for item in worldcup_items
        for category in (item.get("categorias") or [])
        if category.get("limite_por_usuario") is not None
    )

    print(
        "VERIFY "
        f"worldcup_products={len(worldcup_items)} "
        f"worldcup_categories={final_categories} "
        f"non_null_limits={non_null_limits}"
    )

    if len(worldcup_items) != expected_products or final_categories != expected_categories or non_null_limits != 0:
        print("ERROR: Verificacion final no coincide")
        return 1

    print("IMPORT_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa tickets mundial desde CSV via API admin")
    parser.add_argument(
        "--csv",
        default="./mundial_2026_tickets_categorias.csv",
        help="Ruta del CSV",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000/api",
        help="Base URL de la API",
    )
    parser.add_argument(
        "--image-base-url",
        default="http://localhost:8000/assets/mundial-2026",
        help="URL base donde se publican las imagenes SVG de partidos",
    )
    parser.add_argument("--token", default=os.getenv("TICKETS_ADMIN_TOKEN", ""), help="JWT admin")
    parser.add_argument("--dry-run", action="store_true", help="Solo valida y no muta datos")
    args = parser.parse_args()

    if not args.token and not args.dry_run:
        print("ERROR: Debes pasar --token o exportar TICKETS_ADMIN_TOKEN")
        return 1

    return run_import(
        csv_path=Path(args.csv),
        base_url=args.base_url.rstrip("/"),
        token=args.token,
        image_base_url=args.image_base_url,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
