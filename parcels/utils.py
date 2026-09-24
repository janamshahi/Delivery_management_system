# ============================================================
# SHATHIMART DELIVERY CHARGE UTILITIES
# File: parcels/utils.py
# ============================================================

from decimal import Decimal, InvalidOperation

from .models import DeliveryChargeRate


# ============================================================
# GET DELIVERY CHARGE RATES
# ============================================================

def get_delivery_charge_rates():
    """
    Get the current SHATHIMART delivery charge configuration.

    The system is designed to use one delivery charge
    configuration record.

    If no configuration exists yet, this function automatically
    creates one using the default SHATHIMART rates.

    Default rates:

        Up to 1 kg       = Rs. 100
        Above 1 - 3 kg   = Rs. 150
        Above 3 - 5 kg   = Rs. 200
        Above 5 kg       = Rs. 300
    """

    # Try to find the existing delivery charge configuration.
    rates = DeliveryChargeRate.objects.first()

    # --------------------------------------------------------
    # Create default rates if no record exists.
    # --------------------------------------------------------

    if not rates:

        rates = DeliveryChargeRate.objects.create(
            up_to_1kg=Decimal("100.00"),
            up_to_3kg=Decimal("150.00"),
            up_to_5kg=Decimal("200.00"),
            above_5kg=Decimal("300.00"),
        )

    return rates


# ============================================================
# CALCULATE DELIVERY CHARGE
# ============================================================

def calculate_delivery_charge(weight):
    """
    Calculate the delivery charge according to parcel weight.

    The rates are taken directly from the database.

    This means that if the administrator changes the rates
    from:

        Admin Dashboard
            ↓
        Delivery Charges
            ↓
        Save Delivery Rates

    the new rates will automatically be used here.

    Weight rules:

        0 - 1 kg       → up_to_1kg

        > 1 - 3 kg     → up_to_3kg

        > 3 - 5 kg     → up_to_5kg

        > 5 kg         → above_5kg

    Example:

        Weight = 0.50 kg
        Charge = up_to_1kg

        Weight = 1.00 kg
        Charge = up_to_1kg

        Weight = 2.00 kg
        Charge = up_to_3kg

        Weight = 3.00 kg
        Charge = up_to_3kg

        Weight = 4.00 kg
        Charge = up_to_5kg

        Weight = 5.00 kg
        Charge = up_to_5kg

        Weight = 6.00 kg
        Charge = above_5kg
    """

    # --------------------------------------------------------
    # Convert the supplied weight to Decimal.
    #
    # Decimal is used instead of float because this is a
    # financial calculation.
    # --------------------------------------------------------

    try:

        weight = Decimal(str(weight))

    except (
        InvalidOperation,
        TypeError,
        ValueError
    ):

        raise ValueError(
            "Invalid parcel weight."
        )

    # --------------------------------------------------------
    # Weight must be greater than zero.
    # --------------------------------------------------------

    if weight <= Decimal("0"):

        raise ValueError(
            "Parcel weight must be greater than zero."
        )

    # --------------------------------------------------------
    # Get the rates configured by the administrator.
    # --------------------------------------------------------

    rates = get_delivery_charge_rates()

    # --------------------------------------------------------
    # UP TO 1 KG
    # --------------------------------------------------------

    if weight <= Decimal("1"):

        return rates.up_to_1kg

    # --------------------------------------------------------
    # ABOVE 1 KG TO 3 KG
    # --------------------------------------------------------

    elif weight <= Decimal("3"):

        return rates.up_to_3kg

    # --------------------------------------------------------
    # ABOVE 3 KG TO 5 KG
    # --------------------------------------------------------

    elif weight <= Decimal("5"):

        return rates.up_to_5kg

    # --------------------------------------------------------
    # ABOVE 5 KG
    # --------------------------------------------------------

    else:

        return rates.above_5kg
