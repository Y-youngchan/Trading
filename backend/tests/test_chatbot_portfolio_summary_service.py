from backend.services.chatbot.portfolio_summary_service import (
    build_portfolio_totals,
    format_portfolio_reply,
    normalize_account_summary,
)


def test_portfolio_totals_convert_currency_and_separate_real_mock():
    accounts = [
        normalize_account_summary(
            "KIS",
            "REAL",
            {
                "total_evaluation": 1000000,
                "available_cash": 200000,
                "currency": "KRW",
            },
        ),
        normalize_account_summary(
            "BINANCE",
            "REAL",
            {
                "total_evaluation": 100,
                "available_cash": 20,
                "currency": "USDT",
                "exchange_rate": 1500,
            },
        ),
        normalize_account_summary(
            "KIS",
            "MOCK",
            {
                "total_evaluation": 5000000,
                "available_cash": 1000000,
                "currency": "KRW",
            },
        ),
    ]

    totals = build_portfolio_totals(accounts)

    assert totals["REAL"]["total_evaluation_krw"] == 1150000
    assert totals["REAL"]["available_cash_krw"] == 230000
    assert totals["MOCK"]["total_evaluation_krw"] == 5000000


def test_portfolio_reply_is_summary_not_holding_dump():
    reply = format_portfolio_reply(
        {
            "REAL": {
                "total_evaluation_krw": 1150000,
                "available_cash_krw": 230000,
                "account_count": 2,
            },
            "MOCK": {
                "total_evaluation_krw": 5000000,
                "available_cash_krw": 1000000,
                "account_count": 1,
            },
        },
        [],
        [],
    )

    assert "실거래 평가자산 합계: 1,150,000원" in reply
    assert "모의계좌 평가자산 합계: 5,000,000원" in reply
    assert "보유 현황입니다" not in reply


def test_toss_summary_converts_evaluation_and_cash_with_separate_currencies():
    account = normalize_account_summary(
        "TOSS",
        "REAL",
        {
            "total_evaluation": 100,
            "currency": "USD",
            "available_cash": 200000,
            "available_cash_currency": "KRW",
            "exchange_rate": 1500,
        },
    )

    assert account["total_evaluation_krw"] == 150000
    assert account["available_cash_krw"] == 200000
    assert account["available_cash_currency"] == "KRW"
