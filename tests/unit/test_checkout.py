"""Tests unitaires de départ pour les calculs de sous-total et de réduction."""

import pytest

from supermarket_receipt_api.checkout import (
    line_subtotal_cents,
    percentage_discount_cents,
    validate_quantity,
)


@pytest.mark.parametrize(
    "unit_price_cents, quantity, unit, expected",
    [(100, 2, "piece", 200), (199, 1000, "gram", 199), (199, 2000, "gram", 398)],
)
def test_line_subtotal_nominal(
    unit_price_cents: int, quantity: int, unit: str, expected: int
) -> None:
    """Vérifier des calculs de sous-total.

    Aucun effet de bord ni application HTTP.

    Args:
        unit_price_cents (int): Prix unitaire en centimes fourni par pytest.
        quantity (int): Quantité de pièces ou de grammes fournie par pytest.
        unit (str): Unité de vente du cas paramétré.
        expected (int): Montant brut attendu en centimes.

    Returns:
        None: Le test réussit si le montant calculé correspond à l'attendu.

    Raises:
        AssertionError: Si le montant calculé diffère de expected.
    """
    assert line_subtotal_cents(unit_price_cents, quantity, unit) == expected


@pytest.mark.parametrize(
    "subtotal_cents, discount_percent, expected",
    [(1000, 20, 200), (1200, 10, 120), (800, 25, 200)]
    + [(100 * amount_euros, 10, 10 * amount_euros) for amount_euros in range(20, 114)],
)
def test_percentage_discount_nominal(
    subtotal_cents: int, discount_percent: int, expected: int
) -> None:
    """Vérifier des calculs de réduction en pourcentage.

    Aucun effet de bord ni application HTTP.

    Args:
        subtotal_cents (int): Montant brut en centimes fourni par pytest.
        discount_percent (int): Pourcentage de réduction fourni par pytest.
        expected (int): Réduction attendue en centimes.

    Returns:
        None: Le test réussit si la réduction calculée correspond à l'attendu.

    Raises:
        AssertionError: Si la réduction calculée diffère de expected.
    """
    assert percentage_discount_cents(subtotal_cents, discount_percent) == expected


def test_validate_quantity_valeur_normale():

    # Cas nominal : quantité positive
    assert validate_quantity(5) == 5


def test_validate_quantity_valeur_zero():
    # Cas limite : quantité nulle refusée (strictement positive)
    with pytest.raises(ValueError):
        validate_quantity(0)


def test_validate_quantity_valeur_negative():
    # Erreur attendue : quantité négative
    with pytest.raises(ValueError):
        validate_quantity(-3)


def test_validate_quantity_valeur_non_entier():
    # Erreur attendue : quantité non entière
    with pytest.raises(TypeError):
        validate_quantity(2.5)


def test_validate_quantity_valeur_non_nombre():
    # Erreur attendue : quantité non nombre
    with pytest.raises(TypeError):
        validate_quantity("abc")


def test_validate_quantity_valeur_none():
    # Erreur attendue : quantité None
    with pytest.raises(TypeError):
        validate_quantity(None)


def three_for_two_discount(subtotal_cents: float, quantity: float) -> float:
    """Calculer la réduction pour une offre "3 pour 2".
    Args:
        subtotal_cents (int): Montant brut en centimes.
        quantity (int): Quantité de produits achetés.

    Returns:
        int: Montant de la réduction en centimes.
    """
    if quantity < 3:
        return 0
    # Calculer combien de groupes de 3 produits sont présents
    groups_of_three = quantity // 3
    # Chaque groupe de 3 donne droit à un produit gratuit
    discount_per_group = subtotal_cents // quantity  # Prix d'un produit
    total_discount = groups_of_three * discount_per_group
    return total_discount
