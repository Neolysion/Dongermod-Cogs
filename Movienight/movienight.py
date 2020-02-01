import pprint
import discord
import asyncio
import requests
import aiohttp
import ssl
import json
import time
import binascii
import hashlib
import hmac
import os
import re
import urllib

from datetime import datetime

from redbot.core.bot import Red
from redbot.core import commands, checks

pp = pprint.PrettyPrinter(indent=4)

# Force the local timezone to be GMT.
os.environ["TZ"] = "GMT"
time.tzset()


class AkamaiTokenError(Exception):
    def __init__(self, text):
        self._text = text

    def __str__(self):
        return "AkamaiTokenError:%s" % self._text

    def _getText(self):
        return str(self)

    text = property(_getText, None, None, "Formatted error text.")


class AkamaiTokenConfig:
    def __init__(self):
        self.ip = ""
        self.start_time = None
        self.window = 300
        self.acl = ""
        self.session_id = ""
        self.data = ""
        self.url = ""
        self.salt = ""
        self.field_delimiter = "~"
        self.algo = "sha256"
        self.param = None
        self.key = "aabbccddeeff00112233445566778899"
        self.early_url_encoding = False


class AkamaiToken:
    def __init__(
        self,
        token_type=None,
        token_name="hdnts",
        ip=None,
        start_time="now",
        end_time=0,
        window_seconds=None,
        url=None,
        acl=None,
        key=None,
        payload=None,
        algorithm="sha256",
        salt=None,
        session_id=None,
        field_delimiter=None,
        acl_delimiter=None,
        escape_early=False,
        escape_early_upper=False,
        verbose=False,
    ):
        self._token_type = token_type
        self._token_name = token_name
        self._ip = ip
        self._start_time = start_time
        self._end_time = end_time
        self._window_seconds = window_seconds
        self._url = url
        self._acl = acl
        self._key = key
        self._payload = payload
        self._algorithm = algorithm
        if not self._algorithm:
            self._algorithm = "sha256"
        self._salt = salt
        self._session_id = session_id
        self._field_delimiter = field_delimiter
        if not self._field_delimiter:
            self._field_delimiter = "~"
        self._acl_delimiter = acl_delimiter
        if not self._acl_delimiter:
            self._acl_delimiter = "!"
        self._escape_early = escape_early
        self._escape_early_upper = escape_early_upper
        self._verbose = verbose
        self._warnings = []

    def _getWarnings(self):
        return self._warnings

    warnings = property(
        _getWarnings, None, None, "List of warnings from the last generate request"
    )

    def escapeEarly(self, text):
        if self._escape_early or self._escape_early_upper:
            # Only escape the text if we are configured for escape early.
            new_text = urllib.quote_plus(text)
            if self._escape_early_upper:

                def toUpper(match):
                    return match.group(1).upper()

                return re.sub(r"(%..)", toUpper, new_text)
            else:

                def toLower(match):
                    return match.group(1).lower()

                return re.sub(r"(%..)", toLower, new_text)

        # Return the original, unmodified text.
        return text

    def generate_token(self, token_config):
        """
        Backwards compatible interface.

        """
        # Copy the config parameters where they need to be.
        self._token_name = token_config.param
        self._ip = token_config.ip
        self._start_time = token_config.start_time
        self._end_time = 0
        self._window_seconds = token_config.window
        self._url = token_config.url
        self._acl = token_config.acl
        self._key = token_config.key
        self._payload = token_config.data
        self._algorithm = token_config.algo
        if not self._algorithm:
            self._algorithm = "sha256"
        self._salt = token_config.salt
        self._session_id = token_config.session_id
        self._field_delimiter = token_config.field_delimiter
        if not self._field_delimiter:
            self._field_delimiter = "~"
        self._acl_delimiter = "!"
        self._escape_early = bool(
            str(token_config.early_url_encoding).lower() in ("yes", "true")
        )
        return self.generateToken()

    def generateToken(self):
        if not self._algorithm:
            self._algorithm = "sha256"

        if str(self._start_time).lower() == "now":
            # Initialize the start time if we are asked for a starting time of
            # now.
            self._start_time = int(time.mktime(time.gmtime()))
        elif self._start_time is not None:
            try:
                self._start_time = int(self._start_time)
            except:
                raise AkamaiTokenError("start_time must be numeric or now")

        if self._end_time is not None:
            try:
                self._end_time = int(self._end_time)
            except:
                raise AkamaiTokenError("end_time must be numeric.")

        if self._window_seconds is not None:
            try:
                self._window_seconds = int(self._window_seconds)
            except:
                raise AkamaiTokenError("window_seconds must be numeric.")

        if self._end_time <= 0:
            if self._window_seconds > 0:
                if self._start_time is None:
                    # If we have a duration window without a start time,
                    # calculate the end time starting from the current time.
                    self._end_time = (
                        int(time.mktime(time.gmtime())) + self._window_seconds
                    )
                else:
                    self._end_time = self._start_time + self._window_seconds
            else:
                raise AkamaiTokenError(
                    "You must provide an expiration time or " "a duration window."
                )

        if self._end_time < self._start_time:
            self._warnings.append("WARNING:Token will have already expired.")

        if self._key is None or len(self._key) <= 0:
            raise AkamaiTokenError(
                "You must provide a secret in order to " "generate a new token."
            )

        if (
            (self._acl is None and self._url is None)
            or self._acl is not None
            and self._url is not None
            and (len(self._acl) <= 0)
            and (len(self._url) <= 0)
        ):
            raise AkamaiTokenError("You must provide a URL or an ACL.")

        if (
            self._acl is not None
            and self._url is not None
            and (len(self._acl) > 0)
            and (len(self._url) > 0)
        ):
            raise AkamaiTokenError("You must provide a URL OR an ACL, " "not both.")

        if self._verbose:
            print(
                """
Akamai Token Generation Parameters
Token Type      : %s
Token Name      : %s
Start Time      : %s
Window(seconds) : %s
End Time        : %s
IP              : %s
URL             : %s
ACL             : %s
Key/Secret      : %s
Payload         : %s
Algo            : %s
Salt            : %s
Session ID      : %s
Field Delimiter : %s
ACL Delimiter   : %s
Escape Early    : %s
Generating token..."""
                % (
                    "".join([str(x) for x in [self._token_type] if x is not None]),
                    "".join([str(x) for x in [self._token_name] if x is not None]),
                    "".join([str(x) for x in [self._start_time] if x is not None]),
                    "".join([str(x) for x in [self._window_seconds] if x is not None]),
                    "".join([str(x) for x in [self._end_time] if x is not None]),
                    "".join([str(x) for x in [self._ip] if x is not None]),
                    "".join([str(x) for x in [self._url] if x is not None]),
                    "".join([str(x) for x in [self._acl] if x is not None]),
                    "".join([str(x) for x in [self._key] if x is not None]),
                    "".join([str(x) for x in [self._payload] if x is not None]),
                    "".join([str(x) for x in [self._algorithm] if x is not None]),
                    "".join([str(x) for x in [self._salt] if x is not None]),
                    "".join([str(x) for x in [self._session_id] if x is not None]),
                    "".join([str(x) for x in [self._field_delimiter] if x is not None]),
                    "".join([str(x) for x in [self._acl_delimiter] if x is not None]),
                    "".join([str(x) for x in [self._escape_early] if x is not None]),
                )
            )

        hash_source = ""
        new_token = ""

        if self._ip:
            new_token += "ip=%s%c" % (self.escapeEarly(self._ip), self._field_delimiter)

        if self._start_time is not None:
            new_token += "st=%d%c" % (self._start_time, self._field_delimiter)

        new_token += "exp=%d%c" % (self._end_time, self._field_delimiter)

        if self._acl:
            new_token += "acl=%s%c" % (
                self.escapeEarly(self._acl),
                self._field_delimiter,
            )

        if self._session_id:
            new_token += "id=%s%c" % (
                self.escapeEarly(self._session_id),
                self._field_delimiter,
            )

        if self._payload:
            new_token += "data=%s%c" % (
                self.escapeEarly(self._payload),
                self._field_delimiter,
            )

        hash_source += new_token
        if self._url and not self._acl:
            hash_source += "url=%s%c" % (
                self.escapeEarly(self._url),
                self._field_delimiter,
            )

        if self._salt:
            hash_source += "salt=%s%c" % (self._salt, self._field_delimiter)

        if self._algorithm.lower() not in ("sha256", "sha1", "md5"):
            raise AkamaiTokenError("Unknown algorithm")
        token_hmac = hmac.new(
            binascii.a2b_hex(self._key),
            hash_source.rstrip(self._field_delimiter).encode("utf-8"),
            getattr(hashlib, self._algorithm.lower()),
        ).hexdigest()
        new_token += "hmac=%s" % token_hmac

        if self._token_name:
            return "%s=%s" % (self._token_name, new_token)
        return new_token


def ignore_aiohttp_ssl_eror(loop, aiohttpversion="3.5.4"):
    """Ignore aiohttp #3535 issue with SSL data after close

    There appears to be an issue on Python 3.7 and aiohttp SSL that throws a
    ssl.SSLError fatal error (ssl.SSLError: [SSL: KRB5_S_INIT] application data
    after close notify (_ssl.c:2609)) after we are already done with the
    connection. See GitHub issue aio-libs/aiohttp#3535

    Given a loop, this sets up a exception handler that ignores this specific
    exception, but passes everything else on to the previous exception handler
    this one replaces.

    If the current aiohttp version is not exactly equal to aiohttpversion
    nothing is done, assuming that the next version will have this bug fixed.
    This can be disabled by setting this parameter to None

    """
    if aiohttpversion is not None and aiohttp.__version__ != aiohttpversion:
        return

    orig_handler = loop.get_exception_handler()

    def ignore_ssl_error(loop, context):
        if context.get("message") == "SSL error in data received":
            # validate we have the right exception, transport and protocol
            exception = context.get("exception")
            protocol = context.get("protocol")
            if (
                isinstance(exception, ssl.SSLError)
                and exception.reason == "KRB5_S_INIT"
                and isinstance(protocol, asyncio.sslproto.SSLProtocol)
                and isinstance(
                    protocol._app_protocol, aiohttp.client_proto.ResponseHandler
                )
            ):
                if loop.get_debug():
                    asyncio.log.logger.debug("Ignoring aiohttp SSL KRB5_S_INIT error")
                return
        if orig_handler is not None:
            orig_handler(loop, context)
        else:
            loop.default_exception_handler(context)

    loop.set_exception_handler(ignore_ssl_error)


class Movienight(commands.Cog):
    """Wowza Cloud stream manager"""

    def __init__(self, bot: Red):
        self.bot = bot

        # Wowza API config
        # ---------------------------------------------------
        self.wsc_access_key = "..."
        self.wsc_api_key = "..."
        self.wsc_host = "https://api.cloud.wowza.com/api/"
        self.wsc_version = "v1.4"

        # Wowza CDN stream config
        # ---------------------------------------------------
        self.expiration_time = 10800
        self.live_stream_id = "..."
        self.trusted_shared_secret = "..."

        # Player hosting
        # ---------------------------------------------------
        self.player_domain = "movie.admiralbulldog.live"
        self.player_port = "8000"

        # Discord bot settings
        # ---------------------------------------------------
        self.logo_url = "https://images.all-free-download.com/images/graphiclarge/movie_logo_design_text_reel_filmstrip_icons_decoration_6829232.jpg"
        self.alert_channel_id = 588693719646076929
        self.bd_id = 111601428375601152
        self.bo_id = 95174017710821376
        self.he_id = 147349764281729024

        # Program vars, don't touch
        # ----------------------------------------------------

        self.ull_stream_running = False
        self.cdn_stream_running = False
        self.ull_playback_key = ""
        self.cdn_playback_key = ""

        ignore_aiohttp_ssl_eror(self.bot.loop)

        asyncio.ensure_future(self.stream_check())

    def __unload(self):
        pass

    # -----------------------------------------------------------------------------------------
    # Stream state checker
    # -----------------------------------------------------------------------------------------

    def create_ull_fetch_targets_request(self):
        request = {
            "header": {
                "Content-Type": "application/json",
                "wsc-api-key": self.wsc_api_key,
                "wsc-access-key": self.wsc_access_key,
            },
            "url": "{}{}/stream_targets/ull".format(self.wsc_host, self.wsc_version),
        }
        return request

    def create_ull_fetch_target_request(self, target_id):
        request = {
            "header": {
                "Content-Type": "application/json",
                "wsc-api-key": self.wsc_api_key,
                "wsc-access-key": self.wsc_access_key,
            },
            "url": "{}{}/stream_targets/ull/{}".format(
                self.wsc_host, self.wsc_version, target_id
            ),
        }
        return request

    def create_stream_state_request(self, target_id):
        request = {
            "header": {
                "Content-Type": "application/json",
                "wsc-api-key": self.wsc_api_key,
                "wsc-access-key": self.wsc_access_key,
            },
            "url": "{}{}/live_streams/{}/state".format(
                self.wsc_host, self.wsc_version, target_id
            ),
        }
        return request

    def fetch_latest_ull_target_id(self):
        req = self.create_ull_fetch_targets_request()
        res = requests.get(req["url"], headers=req["header"])
        jres = json.loads(res.content)

        latest_target = None

        for target in jres["stream_targets_ull"]:
            if latest_target is None:
                latest_target = target
            elif datetime.strptime(
                latest_target["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
            ) < datetime.strptime(target["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"):
                latest_target = target
        if latest_target:
            return latest_target["id"]
        else:
            return None

    def fetch_cdn_stream_state(self):
        req = self.create_stream_state_request(self.live_stream_id)
        res = requests.get(req["url"], headers=req["header"])
        jres = json.loads(res.content)
        return jres

    async def stream_check(self):

        while True:
            print("Running stream check")

            # check for ULL stream
            # -----------------------------------------
            target_id = self.fetch_latest_ull_target_id()
            req = self.create_ull_fetch_target_request(target_id)
            res = requests.get(req["url"], headers=req["header"])
            jres = json.loads(res.content)

            print("ULL state: " + jres["stream_target_ull"]["state"])

            if jres["stream_target_ull"]["state"] == "started":
                if not self.ull_stream_running:
                    target = jres["stream_target_ull"]
                    self.ull_playback_key = target["playback_urls"]["ws"][1].split("/")[
                        5
                    ]
                    print(
                        "Detected ull stream (playback key"
                        + self.ull_playback_key
                        + ")"
                    )

                    c = self.bot.get_channel(self.alert_channel_id)
                    embed = discord.Embed(
                        title="Movienight is online!",
                        color=0x0600FF,
                        description="Use the normal player if you are having problems with the low latency one.",
                    )
                    embed.set_thumbnail(url=self.logo_url)
                    embed.add_field(
                        name="Web (low latency):",
                        value="https://movie.admiralbulldog.live/ull_player.html?key={}".format(
                            self.ull_playback_key
                        ),
                        inline=False,
                    )
                    embed.add_field(
                        name="Web:",
                        value="https://movie.admiralbulldog.live/ull_player-hls-forced.html?key={}".format(
                            self.ull_playback_key
                        ),
                        inline=True,
                    )
                    await c.send(embed=embed)

                    self.ull_stream_running = True
            else:
                self.ull_stream_running = False

            # check for CDN stream
            # -----------------------------------------
            jres = self.fetch_cdn_stream_state()

            print("CDN state: " + jres["live_stream"]["state"])

            if jres["live_stream"]["state"] == "started":
                if not self.cdn_stream_running:
                    print("Detected cdn stream")

                    self.cdn_playback_key = self.generate_cdn_token()
                    print(self.cdn_playback_key)

                    c = self.bot.get_channel(self.alert_channel_id)
                    embed = discord.Embed(
                        title="Movienight is about to start!",
                        color=0x0600FF,
                        description="Use the following link to watch: ",
                    )
                    embed.set_thumbnail(url=self.logo_url)
                    embed.add_field(
                        name="Web:",
                        value="https://movie.admiralbulldog.live/cdn_player.html?key={}".format(
                            self.cdn_playback_key
                        ),
                        inline=True,
                    )
                    await c.send(embed=embed)

                    self.cdn_stream_running = True
            else:
                self.cdn_stream_running = False

            await asyncio.sleep(20)

    def generate_cdn_token(self):
        try:
            generator = AkamaiToken(
                window_seconds=self.expiration_time,
                acl="*",
                key=self.trusted_shared_secret,
                verbose=True,
            )
            token = generator.generateToken()
            if generator.warnings:
                print("\n".join(generator.warnings))
            print("%s" % token)

            return token

        except AkamaiTokenError as ex:
            print("%s\n" % ex)
        except Exception as ex:
            print(str(ex))

    # ------------------------------------------------------------------------------------------

    @commands.command(pass_context=True, no_pm=True, help="Shows the movienight links")
    async def movietest(self, ctx):
        pass

    @commands.guild_only()
    @commands.command(pass_context=True, no_pm=True, help="Shows the movienight links")
    async def movienight(self, ctx):
        if (
            not ctx.channel.id == 588693719646076929
            and not ctx.channel.id == 557634996743962625
        ):
            return

        if self.ull_stream_running:
            embed = discord.Embed(
                title="Movienight is online!",
                color=0x0600FF,
                description="Try the normal player if you are having problems with the low latency one.",
            )
            embed.set_thumbnail(url=self.logo_url)
            embed.add_field(
                name="Web (low latency):",
                value="https://movie.admiralbulldog.live/ull_player.html?key={}".format(
                    self.ull_playback_key
                ),
                inline=False,
            )
            embed.add_field(
                name="Web:",
                value="https://movie.admiralbulldog.live/ull_player-hls-forced.html?key={}".format(
                    self.ull_playback_key
                ),
                inline=True,
            )
            await ctx.send(embed=embed)
        elif self.cdn_stream_running:
            embed = discord.Embed(
                title="Movienight is online!",
                color=0x0600FF,
                description="Use the following link to watch: ",
            )
            embed.set_thumbnail(url=self.logo_url)
            embed.add_field(
                name="Web:",
                value="https://movie.admiralbulldog.live/cdn_player.html?key={}".format(
                    self.cdn_playback_key
                ),
                inline=True,
            )
            await ctx.send(embed=embed)

        else:
            await ctx.send("Movienight is offline right now :(")

    # -----------------------------------------------------------------------------------------
    # Server management
    # -----------------------------------------------------------------------------------------

    @checks.admin_or_permissions(manage_roles=True)
    @commands.group(name="moviestart")
    async def _moviestart(self, ctx: commands.Context):
        """Movienight server management"""

    @_moviestart.command(
        pass_context=True,
        help="Creates an ultra-low-latency target (lowest latency, source quality only)",
    )
    async def ull(self, ctx):
        if (
            self.bd_id == ctx.author.id
            or self.bo_id == ctx.author.id
            or self.he_id == ctx.author.id
        ):

            if not ctx.author.dm_channel:
                await ctx.author.create_dm()

            server, stream_key = self.create_ull_target()

            embed = discord.Embed(
                title="A new Wowza ULL target has been created! Use the following OBS settings:",
                color=0x008000,
            )
            embed.set_author(name="Movienight (ULL)")
            embed.add_field(name="Server:", value=server, inline=False)
            embed.add_field(name="Stream Key:", value=stream_key, inline=False)
            embed.add_field(name="Authentication:", value="Disabled", inline=False)

            await ctx.author.dm_channel.send(embed=embed)

    @_moviestart.command(
        pass_context=True,
        help="Starts a normal cdn target with transcoder (higher latency, adaptive bitrate)",
    )
    async def cdn(self, ctx):
        if (
            self.bd_id == ctx.author.id
            or self.bo_id == ctx.author.id
            or self.he_id == ctx.author.id
        ):

            if not ctx.author.dm_channel:
                await ctx.author.create_dm()

            await ctx.author.dm_channel.send(
                "Starting transcoder, this usually takes less than a minute..."
            )

            if self.start_cdn_target():
                embed = discord.Embed(
                    title="Wowza CDN target ready. Here are the OBS settings:",
                    color=0x008000,
                )
                embed.set_author(name="Movienight (CDN)")
                embed.add_field(
                    name="Server:", value="rtmp://entrypoint...", inline=False
                )
                embed.add_field(name="Stream Key:", value="stream_key", inline=False)
                embed.add_field(name="Authentication:", value="Enabled", inline=False)
                embed.add_field(name="Username:", value="username", inline=False)
                embed.add_field(name="Password:", value="pw", inline=False)

                await ctx.author.dm_channel.send("Target ready!", embed=embed)
            else:
                await ctx.author.dm_channel.send(
                    "Was unable to start the transcoder, please check logs"
                )

    def create_ull_target_request(self, name):
        request = {
            "header": {
                "Content-Type": "application/json",
                "wsc-api-key": self.wsc_api_key,
                "wsc-access-key": self.wsc_access_key,
            },
            "payload": {
                "stream_target_ull": {
                    "name": name,
                    "source_delivery_method": "push",
                    "enable_hls": True,
                }
            },
            "url": "{}{}/stream_targets/ull".format(self.wsc_host, self.wsc_version),
        }
        return request

    def create_transcoder_start_request(self, transcoder_id):
        request = {
            "header": {
                "Content-Type": "application/json",
                "wsc-api-key": self.wsc_api_key,
                "wsc-access-key": self.wsc_access_key,
            },
            "url": "{}{}/transcoders/{}/start".format(
                self.wsc_host, self.wsc_version, transcoder_id
            ),
        }
        return request

    def fetch_transcoder_state_request(self, transcoder_id):
        request = {
            "header": {
                "Content-Type": "application/json",
                "wsc-api-key": self.wsc_api_key,
                "wsc-access-key": self.wsc_access_key,
            },
            "url": "{}{}/transcoders/{}/state".format(
                self.wsc_host, self.wsc_version, transcoder_id
            ),
        }
        return request

    def create_ull_target(self):
        stream_name = "Movienight(ULL)-{}".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        req = self.create_ull_target_request(stream_name)
        res = requests.post(
            req["url"], data=json.dumps(req["payload"]), headers=req["header"]
        )
        jres = json.loads(res.content)

        endpoint = jres["stream_target_ull"]["primary_url"]
        server = "/".join(endpoint.split("/")[:4])
        stream_key = endpoint.split("/")[4]

        return server, stream_key

    def start_cdn_target(self):
        transcoder_id = "trans_id"

        req = self.fetch_transcoder_state_request(transcoder_id)
        res = requests.get(req["url"], headers=req["header"])
        jres = json.loads(res.content)

        if not res.status_code == 200:
            print("Unable to fetch transcoder")

        if jres["transcoder"]["state"] == "started":
            print("Transcoder is already running")
            return True

        req = self.create_transcoder_start_request(transcoder_id)
        res = requests.put(req["url"], headers=req["header"])
        jres = json.loads(res.content)

        if not res.status_code == 200:
            print("Transcoder start request failed")
        else:
            for _ in range(30):
                req = self.fetch_transcoder_state_request(transcoder_id)
                res = requests.get(req["url"], headers=req["header"])
                jres = json.loads(res.content)

                if jres["transcoder"]["state"] == "started":
                    return True
                time.sleep(1)
            print("Transcoder startup timed out")

        return False

    # ------------------------------------------------------------------------------------------
