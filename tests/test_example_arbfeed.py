import base64
import json
import time
import unittest
from unittest import mock

from examples.strategies.arbsignal import ArbSignalStrategy
from examples.workers import arbfeed, arbscanner
from examples.workers.arbscanner import (
    BASE_USDC,
    ArbScanner,
    PaymentFailed,
    PaymentRefused,
)

try:
    from eth_account import Account
    from eth_account.messages import encode_typed_data
except ImportError:  # eth-account is only required for live mode
    Account = None

PAY_TO = "0x" + "11" * 20
BODY = {
    "opportunities": [
        {
            "pair": "A <-> B",
            "best_direction": {"net_yield_c": 2.5, "net_yield_pct": 2.7},
            "executable": True,
        }
    ]
}


def _requirement(**kwargs):
    requirement = {
        "scheme": "exact",
        "network": "eip155:8453",
        "amount": "20000",
        "asset": BASE_USDC,
        "payTo": PAY_TO,
        "maxTimeoutSeconds": 60,
        "extra": {"name": "USD Coin", "version": "2"},
    }
    requirement.update(kwargs)
    return requirement


def _response(status_code, body=None, headers=None):
    response = mock.Mock(status_code=status_code, headers=headers or {}, text="")
    response.json.return_value = body
    if status_code >= 400 and status_code != 402:
        response.raise_for_status.side_effect = Exception(status_code)
    return response


def _b64url_decode(value):
    return json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))


def _payment_required(accepts, in_header=True, urlsafe=False):
    required = {
        "x402Version": 2,
        "resource": {"url": arbscanner.DEFAULT_URL},
        "accepts": accepts,
    }
    if in_header:
        raw = json.dumps(required).encode()
        if urlsafe:
            header = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        else:
            header = base64.b64encode(raw).decode()
        return _response(402, None, {"PAYMENT-REQUIRED": header})
    return _response(402, required)


class DemoModeTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.Mock()
        with mock.patch.dict("os.environ", {}, clear=True):
            self.scanner = ArbScanner(session=self.session)

    def test_demo(self):
        self.assertTrue(self.scanner.demo)

    def test_scan_opportunities(self):
        response = self.scanner.scan()
        self.assertTrue(response["sample_data"])
        self.assertEqual(len(response["opportunities"]), 2)
        self.assertTrue(all(o["executable"] for o in response["opportunities"]))
        self.session.get.assert_not_called()

    def test_scan_all_limit_q(self):
        self.assertEqual(
            len(self.scanner.scan(mode="all", limit=25)["opportunities"]), 5
        )
        self.assertEqual(
            len(self.scanner.scan(mode="all", limit=1)["opportunities"]), 1
        )
        response = self.scanner.scan(q="senate dem", mode="all")
        self.assertEqual(len(response["opportunities"]), 1)
        self.session.get.assert_not_called()

    def test_sample_event_shape(self):
        rows = self.scanner.scan(mode="all")["opportunities"]
        self.assertTrue(all(row["event"].startswith("SAMPLE") for row in rows))
        self.assertEqual(rows[0]["kalshi"]["ticker"], "SAMPLE-SENATEXX-26-D")
        strategy = ArbSignalStrategy(
            context={"arb_signals": rows, "arb_signals_updated": time.time()}
        )
        self.assertEqual(len(strategy.active_signals()), 2)

    def test_scan_validation(self):
        with self.assertRaises(ValueError):
            self.scanner.scan(limit=26)
        with self.assertRaises(ValueError):
            self.scanner.scan(mode="foo")


@unittest.skipIf(Account is None, "eth-account not installed")
class PaymentTest(unittest.TestCase):
    def setUp(self):
        self.account = Account.create()  # throwaway, never funded
        self.session = mock.Mock()
        self.scanner = ArbScanner(private_key=self.account.key, session=self.session)

    def test_live(self):
        self.assertFalse(self.scanner.demo)

    def test_env_key(self):
        with mock.patch.dict("os.environ", {"X402_WALLET_KEY": self.account.key.hex()}):
            self.assertFalse(ArbScanner(session=self.session).demo)

    def test_no_payment_required(self):
        self.session.get.return_value = _response(200, BODY)
        self.assertEqual(self.scanner.scan(q="x"), BODY)
        self.assertEqual(self.session.get.call_count, 1)

    def _pay(self, in_header=True, urlsafe=False):
        requirement = _requirement()
        self.session.get.side_effect = [
            _payment_required([requirement], in_header, urlsafe),
            _response(200, BODY),
        ]
        now = int(time.time())
        self.assertEqual(self.scanner.scan(q="senate", limit=5), BODY)
        self.assertEqual(self.session.get.call_count, 2)
        headers = self.session.get.call_args_list[1][1]["headers"]
        self.assertEqual(headers["PAYMENT-SIGNATURE"], headers["X-PAYMENT"])
        # outgoing header is base64url without padding
        self.assertNotRegex(headers["PAYMENT-SIGNATURE"], r"[+/=]")
        payload = _b64url_decode(headers["PAYMENT-SIGNATURE"])
        self.assertEqual(payload["x402Version"], 2)
        self.assertEqual(payload["accepted"], requirement)
        self.assertEqual(payload["resource"], {"url": arbscanner.DEFAULT_URL})
        auth = payload["payload"]["authorization"]
        self.assertEqual(auth["from"], self.account.address)
        self.assertEqual(auth["to"], PAY_TO)
        self.assertEqual(auth["value"], "20000")
        self.assertTrue(all(isinstance(v, str) for v in auth.values()))
        self.assertAlmostEqual(int(auth["validAfter"]), now - 600, delta=5)
        self.assertAlmostEqual(int(auth["validBefore"]), now + 60, delta=5)
        self.assertEqual(len(bytes.fromhex(auth["nonce"][2:])), 32)
        # signature recovers to the payer
        message = dict(auth)
        for k in ("value", "validAfter", "validBefore"):
            message[k] = int(message[k])
        message["nonce"] = bytes.fromhex(message["nonce"][2:])
        signable = encode_typed_data(
            full_message=arbscanner.build_typed_data(requirement, message)
        )
        recovered = Account.recover_message(
            signable, signature=payload["payload"]["signature"]
        )
        self.assertEqual(recovered, self.account.address)

    def test_pay_header(self):
        self._pay(in_header=True)

    def test_pay_body_fallback(self):
        self._pay(in_header=False)

    def test_pay_urlsafe_incoming_header(self):
        self._pay(in_header=True, urlsafe=True)

    def test_default_cap(self):
        self.assertEqual(ArbScanner(private_key=self.account.key).max_atomic, 20000)

    def test_payment_failed(self):
        self.session.get.side_effect = [
            _payment_required([_requirement()]),
            _response(402, {}),
        ]
        with self.assertRaises(PaymentFailed):
            self.scanner.scan()

    def test_typed_data_matches_manual_hash(self):
        from eth_abi import encode
        from eth_utils import keccak

        requirement = _requirement()
        auth = {
            "from": self.account.address,
            "to": PAY_TO,
            "value": 20000,
            "validAfter": 1,
            "validBefore": 2,
            "nonce": b"\x07" * 32,
        }
        domain_type = keccak(
            text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
        )
        domain = keccak(
            encode(
                ["bytes32", "bytes32", "bytes32", "uint256", "address"],
                [
                    domain_type,
                    keccak(text="USD Coin"),
                    keccak(text="2"),
                    8453,
                    BASE_USDC,
                ],
            )
        )
        auth_type = keccak(
            text="TransferWithAuthorization(address from,address to,uint256 value,"
            "uint256 validAfter,uint256 validBefore,bytes32 nonce)"
        )
        struct = keccak(
            encode(
                ["bytes32", "address", "address", "uint256", "uint256", "uint256"]
                + ["bytes32"],
                [auth_type, auth["from"], PAY_TO, 20000, 1, 2, auth["nonce"]],
            )
        )
        digest = keccak(b"\x19\x01" + domain + struct)
        manual = Account.unsafe_sign_hash(digest, self.account.key)
        typed = self.account.sign_message(
            encode_typed_data(
                full_message=arbscanner.build_typed_data(requirement, auth)
            )
        )
        self.assertEqual(manual.signature, typed.signature)


@unittest.skipIf(Account is None, "eth-account not installed")
class RefusalTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.Mock()
        self.scanner = ArbScanner(
            private_key=Account.create().key, session=self.session
        )

    def _refused(self, accepts):
        self.session.get.side_effect = [_payment_required(accepts)]
        with self.assertRaises(PaymentRefused):
            self.scanner.scan()
        self.assertEqual(self.session.get.call_count, 1)

    def test_wrong_network(self):
        self._refused([_requirement(network="eip155:1")])

    def test_wrong_asset(self):
        self._refused([_requirement(asset="0x" + "22" * 20)])

    def test_over_cap(self):
        self._refused([_requirement(amount="20001")])

    def test_zero_amount(self):
        self._refused([_requirement(amount="0")])

    def test_wrong_scheme(self):
        self._refused([_requirement(scheme="upto")])

    def test_empty_accepts(self):
        self._refused([])

    def test_missing_requirements(self):
        self.session.get.side_effect = [_response(402, None)]
        with self.assertRaises(PaymentRefused):
            self.scanner.scan()

    def test_selects_acceptable(self):
        good = _requirement()
        self.assertEqual(
            arbscanner.select_requirement(
                [_requirement(network="solana:x"), good], 20000
            ),
            good,
        )


class B64DecodeTest(unittest.TestCase):
    def test_accepts_standard_and_urlsafe(self):
        data = {"k": "???>>>" * 3, "n": 1}
        raw = json.dumps(data).encode()
        std = base64.b64encode(raw).decode()
        url = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        self.assertTrue(set("+/") & set(std) and set("-_") & set(url))
        self.assertEqual(arbscanner._b64_json(std), data)
        self.assertEqual(arbscanner._b64_json(url), data)
        self.assertIsNone(arbscanner._b64_json("not base64!"))


class ArbFeedWorkerTest(unittest.TestCase):
    def setUp(self):
        self.flumine = mock.Mock()
        self.scanner = mock.Mock()

    def test_poll_arb_feed(self):
        self.scanner.scan.return_value = BODY
        context = {}
        arbfeed.poll_arb_feed(context, self.flumine, self.scanner, q="x", limit=3)
        self.scanner.scan.assert_called_with(q="x", limit=3, mode="opportunities")
        event = self.flumine.handler_queue.put.call_args[0][0]
        self.assertEqual(event.event, BODY)
        self.assertEqual(event.callback, arbfeed.callback)
        self.assertEqual(context["polls"], 1)

    def test_poll_arb_feed_error(self):
        self.scanner.scan.side_effect = PaymentRefused("no")
        with self.assertLogs(arbfeed.logger, "WARNING"):
            arbfeed.poll_arb_feed({}, self.flumine, self.scanner)
        self.flumine.handler_queue.put.assert_not_called()

    def test_callback(self):
        strategy = mock.Mock(context={})
        self.flumine.strategies = [strategy]
        arbfeed.callback(self.flumine, mock.Mock(event=BODY))
        self.assertEqual(strategy.context["arb_signals"], BODY["opportunities"])
        self.assertIn("arb_signals_updated", strategy.context)


class ArbSignalStrategyTest(unittest.TestCase):
    def setUp(self):
        self.strategy = ArbSignalStrategy(context={"min_net_yield_c": 1.0})
        self.market = mock.Mock(market_id="1.1", context={})
        self.market_book = mock.Mock(status="OPEN")

    def _signals(self, signals, age=0):
        self.strategy.context["arb_signals"] = signals
        self.strategy.context["arb_signals_updated"] = time.time() - age

    def test_check_market_book_no_signals(self):
        self.assertFalse(self.strategy.check_market_book(self.market, self.market_book))

    def test_check_market_book(self):
        self._signals(BODY["opportunities"])
        self.assertTrue(self.strategy.check_market_book(self.market, self.market_book))
        self.market_book.status = "SUSPENDED"
        self.assertFalse(self.strategy.check_market_book(self.market, self.market_book))

    def test_check_market_book_stale(self):
        self._signals(BODY["opportunities"], age=1000)
        self.assertFalse(self.strategy.check_market_book(self.market, self.market_book))

    def test_active_signals_tolerant(self):
        self._signals(
            [
                {"pair": "missing fields"},
                {"executable": True, "best_direction": None},
                {"executable": True, "best_direction": {"net_yield_c": 0.5}},
                {"executable": False, "best_direction": {"net_yield_c": 5}},
                BODY["opportunities"][0],
            ]
        )
        self.assertEqual(self.strategy.active_signals(), BODY["opportunities"])

    def test_process_market_book(self):
        self._signals(BODY["opportunities"])
        self.strategy.process_market_book(self.market, self.market_book)
        self.strategy.process_market_book(self.market, self.market_book)
        self.assertEqual(self.market.context["arb_signals_seen"], {"A <-> B"})

    def test_event_first(self):
        signal = {
            "event": "E",
            "pair": "P",
            "best_direction": {"net_yield_c": 2.5},
            "executable": True,
        }
        self._signals([signal])
        self.assertEqual(self.strategy.active_signals(), [signal])
        self.strategy.process_market_book(self.market, self.market_book)
        self.assertEqual(self.market.context["arb_signals_seen"], {"E"})

    def test_pair_fallback(self):
        signal = {
            "pair": "P",
            "best_direction": {"net_yield_c": 2.5},
            "executable": True,
        }
        self._signals([signal])
        self.assertEqual(self.strategy.active_signals(), [signal])
        self.strategy.process_market_book(self.market, self.market_book)
        self.assertEqual(self.market.context["arb_signals_seen"], {"P"})

    def test_missing_event_and_pair_skipped(self):
        self._signals(
            [
                {"best_direction": {"net_yield_c": 2.5}, "executable": True},
                {"event": "", "pair": None, "executable": True},
            ]
        )
        self.assertEqual(self.strategy.active_signals(), [])
        self.strategy.process_market_book(self.market, self.market_book)
        self.assertEqual(self.market.context["arb_signals_seen"], set())
