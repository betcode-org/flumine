"""
Minimal client for an external Kalshi <-> PredictIt cross-venue
arbitrage feed, a paid HTTP API using x402 v2 ("exact" scheme,
USDC on Base). Used by examples/workers/arbfeed.py.

Demo mode (default): with no wallet key the client makes no network
calls and returns the bundled SAMPLE fixture
(examples/resources/kalshi_predictit_arb_sample.json), which is
fictional data, not real market data.

Live mode: only when a key is passed or X402_WALLET_KEY is set. Each
call signs an EIP-3009 USDC authorization of at most max_usd_per_call
(requires `pip install eth-account`).
"""

import base64
import json
import logging
import os
import secrets
import time
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)

DEFAULT_URL = (
    "https://x402.bankr.bot/0x69fb671637ed68881f66b9ebf305ec3ef5574f65"
    "/kalshi-predictit-arb"
)
BASE_NETWORKS = ("eip155:8453", "base")
BASE_CHAIN_ID = 8453
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDC_DECIMALS = 6
MODES = ("opportunities", "all")
SAMPLE_FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "resources",
    "kalshi_predictit_arb_sample.json",
)

TRANSFER_WITH_AUTHORIZATION_TYPES = {
    "TransferWithAuthorization": [
        {"name": "from", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "validAfter", "type": "uint256"},
        {"name": "validBefore", "type": "uint256"},
        {"name": "nonce", "type": "bytes32"},
    ]
}


class ArbScannerError(Exception):
    pass


class PaymentRefused(ArbScannerError):
    """No acceptable payment requirement (network/asset/amount/cap)."""


class PaymentFailed(ArbScannerError):
    """Payment was sent but the server still answered 402."""


class ArbScanner:
    def __init__(
        self,
        private_key: str = None,
        max_usd_per_call: float = 0.02,
        timeout: float = 15,
        url: str = DEFAULT_URL,
        fixture_path: str = SAMPLE_FIXTURE,
        session: requests.Session = None,
    ):
        private_key = private_key or os.environ.get("X402_WALLET_KEY")
        self._account = None
        if private_key:
            from eth_account import Account  # live mode only

            self._account = Account.from_key(private_key)
        self.max_atomic = int(Decimal(str(max_usd_per_call)) * 10**USDC_DECIMALS)
        self.timeout = timeout
        self.url = url
        self.fixture_path = fixture_path
        self.session = session or requests.Session()
        self.last_payment_response = None

    @property
    def demo(self) -> bool:
        return self._account is None

    def scan(self, q: str = None, limit: int = 10, mode: str = "opportunities"):
        if not 1 <= int(limit) <= 25:
            raise ValueError("limit must be between 1 and 25")
        if mode not in MODES:
            raise ValueError("mode must be one of %s" % (MODES,))
        if self.demo:
            return self._scan_fixture(q, int(limit), mode)

        params = {"limit": int(limit), "mode": mode}
        if q:
            params["q"] = q
        response = self.session.get(self.url, params=params, timeout=self.timeout)
        if response.status_code == 402:
            required = parse_payment_required(response)
            requirement = select_requirement(required.get("accepts"), self.max_atomic)
            header = build_payment_header(
                self._account,
                requirement,
                required.get("resource") or {"url": self.url},
            )
            response = self.session.get(
                self.url,
                params=params,
                headers={"PAYMENT-SIGNATURE": header, "X-PAYMENT": header},
                timeout=self.timeout,
            )
            if response.status_code == 402:
                raise PaymentFailed("Payment not accepted: %s" % response.text[:200])
            self.last_payment_response = _b64_json(
                response.headers.get("PAYMENT-RESPONSE")
            )
        response.raise_for_status()
        return normalise_response(response.json())

    def _scan_fixture(self, q, limit, mode) -> dict:
        with open(self.fixture_path) as f:
            data = normalise_response(json.load(f))
        opportunities = data["opportunities"]
        if mode == "opportunities":
            opportunities = [o for o in opportunities if is_executable(o)]
        if q:
            words = q.lower().split()
            opportunities = [
                o
                for o in opportunities
                if all(w in json.dumps(o).lower() for w in words)
            ]
        data["opportunities"] = opportunities[:limit]
        data["sample_data"] = True
        return data


def normalise_response(data) -> dict:
    """Tolerate missing/unknown fields: always return
    a dict with a list of dict opportunities.
    """
    if not isinstance(data, dict):
        data = {}
    opportunities = data.get("opportunities")
    if not isinstance(opportunities, list):
        opportunities = []
    data["opportunities"] = [o for o in opportunities if isinstance(o, dict)]
    return data


def net_yield_c(opportunity: dict):
    best = opportunity.get("best_direction")
    if not isinstance(best, dict):
        return None
    try:
        return float(best["net_yield_c"])
    except (KeyError, TypeError, ValueError):
        return None


def is_executable(opportunity: dict) -> bool:
    return opportunity.get("executable") is True


def parse_payment_required(response) -> dict:
    # x402 v2 sends PaymentRequired base64 encoded in the
    # PAYMENT-REQUIRED header, fall back to the JSON body
    required = _b64_json(response.headers.get("PAYMENT-REQUIRED"))
    if required is None:
        try:
            required = response.json()
        except ValueError:
            required = None
    if not isinstance(required, dict):
        raise PaymentRefused("402 response without payment requirements")
    return required


def select_requirement(accepts, max_atomic: int) -> dict:
    if not accepts or not isinstance(accepts, list):
        raise PaymentRefused("402 response offered no payment requirements")
    reasons = []
    for requirement in accepts:
        reason = _refusal_reason(requirement, max_atomic)
        if reason is None:
            return requirement
        reasons.append(reason)
    raise PaymentRefused("; ".join(reasons))


def _refusal_reason(requirement, max_atomic: int):
    if not isinstance(requirement, dict):
        return "malformed requirement"
    if requirement.get("network") not in BASE_NETWORKS:
        return "network %r is not Base" % requirement.get("network")
    if requirement.get("scheme") != "exact":
        return "scheme %r is not exact" % requirement.get("scheme")
    if str(requirement.get("asset", "")).lower() != BASE_USDC.lower():
        return "asset %r is not Base USDC" % requirement.get("asset")
    # v2 uses 'amount', v1 used 'maxAmountRequired'
    amount = requirement.get("amount", requirement.get("maxAmountRequired"))
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return "invalid amount %r" % amount
    if amount <= 0:
        return "amount %s must be positive" % amount
    if amount > max_atomic:
        return "amount %s exceeds cap %s" % (amount, max_atomic)
    pay_to = requirement.get("payTo")
    if not (isinstance(pay_to, str) and pay_to.startswith("0x") and len(pay_to) == 42):
        return "invalid payTo %r" % pay_to
    return None


def build_typed_data(requirement: dict, authorization: dict) -> dict:
    extra = requirement.get("extra") or {}
    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            **TRANSFER_WITH_AUTHORIZATION_TYPES,
        },
        "primaryType": "TransferWithAuthorization",
        "domain": {
            "name": extra.get("name") or "USD Coin",
            "version": extra.get("version") or "2",
            "chainId": BASE_CHAIN_ID,
            "verifyingContract": requirement["asset"],
        },
        "message": authorization,
    }


def build_payment_header(account, requirement: dict, resource, now: int = None) -> str:
    from eth_account.messages import encode_typed_data

    now = int(time.time()) if now is None else now
    amount = int(requirement.get("amount", requirement.get("maxAmountRequired")))
    authorization = {
        "from": account.address,
        "to": requirement["payTo"],
        "value": amount,
        "validAfter": now - 600,
        "validBefore": now + int(requirement.get("maxTimeoutSeconds") or 60),
        "nonce": secrets.token_bytes(32),
    }
    signable = encode_typed_data(
        full_message=build_typed_data(requirement, authorization)
    )
    signed = account.sign_message(signable)
    payload = {
        "x402Version": 2,
        "resource": resource,
        "accepted": requirement,
        "payload": {
            # hexbytes>=1.0 .hex() drops the 0x prefix
            "signature": "0x" + bytes(signed.signature).hex(),
            "authorization": {
                "from": authorization["from"],
                "to": authorization["to"],
                "value": str(authorization["value"]),
                "validAfter": str(authorization["validAfter"]),
                "validBefore": str(authorization["validBefore"]),
                "nonce": "0x" + authorization["nonce"].hex(),
            },
        },
    }
    # base64url without padding, as used by the live-tested client
    return (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )


def _b64_json(value):
    # tolerant decode: accepts standard or urlsafe base64, padded or not
    if not value:
        return None
    try:
        value = value.strip().replace("-", "+").replace("_", "/")
        return json.loads(
            base64.b64decode(value + "=" * (-len(value) % 4), validate=True)
        )
    except (ValueError, TypeError):
        return None
