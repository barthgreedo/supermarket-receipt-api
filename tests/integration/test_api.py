"""Tests d'intégration HTTP de POST /checkout : route, validation, moteur et sérialisation."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from supermarket_receipt_api.main import app

client = TestClient(app)


def test_checkout_panier_avec_promotions_renvoie_le_ticket_complet() -> None:
    """Vérifier le ticket complet d'un panier qui déclenche les trois promotions.

    Attendus calculés à la main depuis docs/contrat.md, indépendamment du code :

    - toothbrush x3 : brut 3 x 99 = 297, 3 pour 2 offre 1 pièce = 99, net 198.
    - apples 500 g : brut 199 x 500 / 1000 = 99,5 arrondi demi vers le haut = 100,
      20 % de 100 = 20, net 80.
    - rice x2 : brut 2 x 249 = 498, 10 % de 498 = 49,8 arrondi = 50, net 448.
    - Totaux : brut 297 + 100 + 498 = 895, réduction 99 + 20 + 50 = 169, net 726.

    Les lignes suivent l'ordre du panier.

    Returns:
        None: Le test réussit si le statut est 200 et la réponse égale au ticket attendu.

    Raises:
        AssertionError: Si le statut ou un champ du ticket diffère de l'attendu.
    """
    response = client.post(
        "/checkout",
        json={
            "items": [
                {"product_id": "toothbrush", "quantity": 3},
                {"product_id": "apples", "quantity": 500},
                {"product_id": "rice", "quantity": 2},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "lines": [
            {
                "product_id": "toothbrush",
                "name": "Brosse à dents",
                "quantity": 3,
                "unit": "piece",
                "unit_price_cents": 99,
                "subtotal_cents": 297,
                "discount_cents": 99,
                "total_cents": 198,
            },
            {
                "product_id": "apples",
                "name": "Pommes",
                "quantity": 500,
                "unit": "gram",
                "unit_price_cents": 199,
                "subtotal_cents": 100,
                "discount_cents": 20,
                "total_cents": 80,
            },
            {
                "product_id": "rice",
                "name": "Sac de riz",
                "quantity": 2,
                "unit": "piece",
                "unit_price_cents": 249,
                "subtotal_cents": 498,
                "discount_cents": 50,
                "total_cents": 448,
            },
        ],
        "subtotal_cents": 895,
        "discount_cents": 169,
        "total_cents": 726,
    }


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"items": [{"product_id": "milk"}]}, id="quantity-manquante"),
        pytest.param({}, id="items-manquant"),
        pytest.param(
            {"items": [{"product_id": "milk", "quantity": 1, "price_cents": 1}]},
            id="champ-en-trop",
        ),
        pytest.param(
            {"items": [{"product_id": "milk", "quantity": "2"}]},
            id="quantity-chaine-numerique",
        ),
    ],
)
def test_checkout_requete_invalide_renvoie_422(body: dict[str, Any]) -> None:
    """Vérifier qu'un champ manquant, en trop ou mal typé est refusé explicitement.

    Le contrat impose HTTP 422 avec un champ detail listant les erreurs FastAPI,
    sans conversion de type ni champ ignoré silencieusement.

    Args:
        body (dict[str, Any]): Corps JSON invalide fourni par pytest.

    Returns:
        None: Le test réussit si le statut est 422 et detail une liste non vide.

    Raises:
        AssertionError: Si la requête est acceptée ou si detail est absent ou vide.
    """
    response = client.post("/checkout", json=body)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail
