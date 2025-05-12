import aiohttp


async def is_valid_minecraft_ign(ign: str) -> bool:
    url = f"https://api.mojang.com/users/profiles/minecraft/{ign}"
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as resp:
                return resp.status == 200
        except:
            return False


async def fetch_mojang_profile(ign: str) -> tuple[str, str]:
    uuid = None
    canonical_ign = ign
    mojang_url = f"https://api.mojang.com/users/profiles/minecraft/{ign}"

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(mojang_url) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        uuid = data.get("id")
                        canonical_ign = data.get("name", ign)
                    except aiohttp.ContentTypeError:
                        print(f"Mojang returned non-JSON response for IGN: {ign}")
                else:
                    print(
                        f"(minecraft/mojang) Failed to fetch profile for {ign}, status code: {response.status}"
                    )
    except Exception as e:
        print(f"Error fetching Mojang data for {ign}: {e}")

    return uuid, canonical_ign
