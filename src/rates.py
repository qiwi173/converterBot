from __future__ import annotations

import asyncio
from typing import Dict, Optional, Tuple

import httpx


FIAT_BASES = {"USD", "EUR", "GBP", "JPY", "CHF", "CNY", "AUD", "CAD", "RUB", "UAH", "KZT"}
CRYPTO_BASES = {"BTC", "ETH", "USDT", "BNB", "XRP", "SOL", "TON", "DOGE", "TRX"}


class RatesService:
    def __init__(self, user_agent: str) -> None:
        self._client = httpx.AsyncClient(timeout=10, headers={"User-Agent": user_agent})

    async def close(self) -> None:
        await self._client.aclose()

    async def get_rate(self, base: str, quote: str) -> Optional[float]:
        base_u = base.upper()
        quote_u = quote.upper()

        if base_u == quote_u:
            return 1.0

        if base_u in CRYPTO_BASES or quote_u in CRYPTO_BASES:
            val = await self._fetch_crypto_rate(base_u, quote_u)
            if val is not None:
                return val
        # Fallback / fiat
        return await self._fetch_fiat_rate(base_u, quote_u)

    async def _fetch_fiat_rate(self, base: str, quote: str) -> Optional[float]:
        # Try multiple free APIs (no keys required)
        apis = [
            # exchangerate-api.com (no key) - основной
            f"https://api.exchangerate-api.com/v4/latest/{base}",
            # Alternative: currency-converter5.p.rapidapi.com (no key)
            f"https://currency-converter5.p.rapidapi.com/currency/convert?format=json&from={base}&to={quote}&amount=1",
            # Fallback: simple currency converter
            f"https://api.exchangerate.host/latest?base={base}",
        ]
        
        for i, url in enumerate(apis):
            try:
                r = await self._client.get(url)
                r.raise_for_status()
                data = r.json()
                
                if i == 0:  # exchangerate-api.com - основной
                    rates = data.get("rates", {})
                    if quote in rates:
                        return float(rates[quote])
                        
                elif i == 1:  # currency-converter5 (может быть заблокирован)
                    try:
                        result = data.get("result")
                        if result and "converted_amount" in result:
                            return float(result["converted_amount"])
                    except:
                        pass
                        
                elif i == 2:  # exchangerate.host fallback (требует ключ)
                    try:
                        rates = data.get("rates", {})
                        if rates and quote in rates:
                            return float(rates[quote])
                    except:
                        pass
                        
            except Exception as e:
                print(f"API {i+1} failed: {e}")
                continue
        
        # Final fallback: try to get USD rates and cross-calculate
        if base != "USD" and quote != "USD":
            try:
                base_usd = await self._fetch_fiat_rate(base, "USD")
                quote_usd = await self._fetch_fiat_rate(quote, "USD")
                if base_usd and quote_usd and quote_usd != 0:
                    return base_usd / quote_usd
            except Exception:
                pass
                
        return None

    async def _fetch_crypto_rate(self, base: str, quote: str) -> Optional[float]:
        # coingecko simple price (no key)
        # Needs ids, simple map for majors
        symbol_to_id: Dict[str, str] = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "SOL": "solana",
            "TON": "the-open-network",
            "DOGE": "dogecoin",
            "TRX": "tron",
            "USDT": "tether",
        }

        if base in symbol_to_id and quote in symbol_to_id:
            # crypto-to-crypto via USD pivot: base->USD and quote->USD
            base_usd = await self._coingecko_simple(symbol_to_id[base], ["usd"]) or 0.0
            quote_usd = await self._coingecko_simple(symbol_to_id[quote], ["usd"]) or 0.0
            if base_usd > 0 and quote_usd > 0:
                return base_usd / quote_usd

        if base in symbol_to_id:
            target = quote.lower()
            val = await self._coingecko_simple(symbol_to_id[base], [target])
            if val is not None:
                return val

        if quote in symbol_to_id:
            target = base.lower()
            val = await self._coingecko_simple(symbol_to_id[quote], [target])
            if val is not None and val != 0:
                return 1.0 / val
        return None

    async def _coingecko_simple(self, coin_id: str, vs: list[str]) -> Optional[float]:
        vs_currencies = ",".join(vs)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs_currencies}"
        try:
            r = await self._client.get(url)
            r.raise_for_status()
            data = r.json()
            price_block = data.get(coin_id, {})
            # return the first requested currency value
            for k in vs:
                v = price_block.get(k)
                if isinstance(v, (int, float)):
                    return float(v)
        except Exception:
            return None
        return None


