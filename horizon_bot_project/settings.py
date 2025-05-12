import json
import discord
from pydantic import (
    BaseModel,
    ValidationError,
    model_validator,
)
from pydantic_settings import BaseSettings


class Colors(BaseModel):
    default_color: discord.Color = discord.Color.orange()
    finished_color: discord.Color = discord.Color.green()
    error_color: discord.Color = discord.Color.red()

    @model_validator(mode="before")
    def convert_hex_to_color(cls, values):
        for field in ["default_color", "finished_color", "error_color"]:
            color_value = values.get(field)
            if isinstance(color_value, str):
                if not color_value.startswith("#") or len(color_value) != 7:
                    raise ValueError(
                        f"{field} must be a valid hex string of the format #RRGGBB"
                    )
                try:
                    color_int = int(color_value[1:], 16)
                    values[field] = discord.Color(color_int)
                except ValueError:
                    raise ValueError(
                        f"{field} must be a valid hex string of the format #RRGGBB"
                    )
        return values

    class Config:
        arbitrary_types_allowed = True


class Channels(BaseModel):
    signup_channel_id: int
    subs_channel_id: int


class Settings(BaseSettings):
    discord_token: str
    hypixel_api_key: str

    command_prefix: str = "!"
    allowed_guilds: list[int] = []
    colors: Colors = Colors()
    channels: Channels
    icon_url: str

    class Config:
        env_file = ".env"
        frozen = True


settings = None


def reload_config():
    with open("config.json") as f:
        data = json.load(f)
    try:
        new_settings = Settings(**data)
    except ValidationError as e:
        print("Invalid config update, keeping old settings.")
        print(e)
        return
    global settings
    settings = new_settings
    print("✅ Reloaded config!")


reload_config()
