import asyncio
import datetime
import os
import traceback
from enum import Enum

import reflex as rx
import replicate
import requests

from .options import OptionsState

DEFAULT_IMAGE = "/default.webp"
API_TOKEN_ENV_VAR = os.getenv("OPENAI_API_KEY")


CopyLocalState = rx._x.client_state(default=False, var_name="copying")


class ResponseStatus(Enum):
    STARTING = "starting"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class GeneratorState(rx.State):
    is_generating: bool = False
    is_upscaling: bool = False
    _request_id: str = None
    output_image: str = DEFAULT_IMAGE
    output_list: list[str] = []
    upscaled_image: str = ""
    is_downloading: bool = False

    @rx.event(background=True)
    async def generate_image(self):
        try:
            import google.generativeai as genai

            # Check if the env variable is set
            api_key = ""
            if not api_key:
                yield rx.toast.warning("No Google Gemini API key found")
                return
            if self.is_upscaling:
                yield rx.toast.warning("Wait for the image to upscale first")
                return
            async with self:
                Options = await self.get_state(OptionsState)
            # If prompt is empty
            if Options.prompt == "":
                yield rx.toast.warning("Please enter a prompt")
                return

            # Configure Gemini API
            genai.configure(api_key=api_key)
            # Use the updated model name as per deprecation notice

            model = genai.GenerativeModel("gemini-1.5-flash")

            # yield rx.toast.warning(f"line 61. model = {model}")
            # Compose the prompt
            prompt = Options.prompt + Options.selected_style_prompt

            # Gemini API expects a single prompt string
            response = await asyncio.to_thread(
                lambda: model.generate_content(prompt, stream=False)
            )

            # Extract image from response
            if (
                not response
                or not hasattr(response, "candidates")
                or not response.candidates
            ):
                async with self:
                    self._reset_state()
                yield rx.toast.error("Error generating image")
                return

            # Find the first image in the response
            image_url = None
            for candidate in response.candidates:
                if hasattr(candidate, "content") and hasattr(
                    candidate.content, "parts"
                ):
                    for part in candidate.content.parts:
                        if hasattr(part, "inline_data") and hasattr(
                            part.inline_data, "data"
                        ):
                            # Gemini returns base64 image data
                            if isinstance(part.inline_data.data, bytes):
                                image_url = (
                                    "data:image/png;base64,"
                                    + part.inline_data.data.decode("utf-8")
                                )
                            else:
                                image_url = (
                                    "data:image/png;base64," + part.inline_data.data
                                )
                            break
                if image_url:
                    break

            if not image_url:
                async with self:
                    self._reset_state()
                yield rx.toast.error("No image returned by Gemini API")
                return

            async with self:
                self.upscaled_image = ""
                self.output_image = image_url
                self.output_list = []
                self._reset_state()

        except Exception as e:
            async with self:
                self._reset_state()
            yield rx.toast.error(f"Error, please try again: {traceback.format_exc()}")

    @rx.event(background=True)
    async def upscale_image(self):
        try:
            # Check if the env variable is set
            if not self._check_api_token():
                return
            if self.is_generating:
                yield rx.toast.warning("Wait for the image to generate first")
                return
            if self.output_image == DEFAULT_IMAGE:
                yield rx.toast.warning("Please generate an image first")
                return
            if self.upscaled_image != "":
                yield rx.toast.warning("Image already upscaled")
                return
            async with self:
                Options = await self.get_state(OptionsState)
            input = {
                "prompt": "masterpiece, best quality, highres, <lora:more_details:0.5> <lora:SDXLrender_v2.0:1>",
                "negative_prompt": "(worst quality, low quality, normal quality:2) JuggernautNegative-neg",
                "num_inference_steps": 18,
                "scheduler": "DPM++ 3M SDE Karras",
                "image": self.output_image,
                "dynamic": 6,
                "handfix": "disabled",
                "sharpen": 0,
                "sd_model": "juggernaut_reborn.safetensors [338b85bc4f]",
                "creativity": 0.35,
                "lora_links": "",
                "downscaling": False,
                "resemblance": 0.6,
                "scale_factor": 2,
                "tiling_width": 112,
                "output_format": "png",
                "tiling_height": 144,
                "custom_sd_model": "",
                "downscaling_resolution": 768,
            }
            # Add "seed" to the input if it is not 0
            if Options.seed != 0:
                input["seed"] = Options.seed

            # Await the output from the replicate API
            response = await replicate.predictions.async_create(
                "029d48aa21712d6769d7a46729c1edf0e4d41919c70b270785f10abb82989ba5",
                input=input,
            )

            if response.status != ResponseStatus.STARTING.value or not response:
                async with self:
                    self._request_id, self.is_upscaling = None, False
                yield rx.toast.error("Error starting upscaling")
                return

            async with self:
                self.is_upscaling = True
                self._request_id = response.id
                yield

            while True:
                response = await replicate.predictions.async_get(response.id)
                async with self:
                    if response.status in (
                        ResponseStatus.CANCELED.value,
                        ResponseStatus.FAILED.value,
                    ):
                        self._reset_state()
                        if response.status == ResponseStatus.FAILED.value:
                            yield rx.toast.warning(
                                f"Error upscaling image: {response.error}"
                            )
                        return
                    elif response.status == ResponseStatus.SUCCEEDED.value:
                        break
                await asyncio.sleep(0.15)
            async with self:
                self.upscaled_image = response.output[0]
                self.output_list = []
                self._request_id, self.is_upscaling = None, False

        except Exception as e:
            async with self:
                self._reset_state()
            yield rx.toast.error(f"Error, please try again: {e}")

    def cancel_generation(self):
        if self._request_id is None:
            return
        try:
            response = replicate.predictions.cancel(self._request_id)
            if response.status != ResponseStatus.CANCELED.value:
                raise Exception("Error cancelling generation")
        except Exception as e:
            yield rx.toast.error(f"Error cancelling generation: {e}")
        finally:
            self._reset_state()

    def _reset_state(self):
        self._request_id = None
        self.is_generating = False
        self.is_upscaling = False

    def _check_api_token(self):
        if os.getenv(API_TOKEN_ENV_VAR) is None:
            yield rx.toast.warning("No API key found")
            return False
        return True

    def download_image(self):
        self.is_downloading = True
        yield
        image_url = self.upscaled_image if self.upscaled_image else self.output_image
        filename = (
            f"reflex_ai_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        )

        try:
            if image_url.startswith("http"):
                response = requests.get(image_url)
                response.raise_for_status()
                image_data = response.content
                return rx.download(data=image_data, filename=filename)
            else:
                return rx.download(url=image_url, filename=filename)
        except Exception as e:
            yield rx.toast.error(f"Error downloading image: {e}")
        finally:
            self.is_downloading = False

    async def copy_image(self):
        try:
            image_url = (
                self.upscaled_image if self.upscaled_image else self.output_image
            )
            if image_url == DEFAULT_IMAGE:
                image_url = (
                    self.router.page.full_raw_path + DEFAULT_IMAGE[1:]
                )  # Remove the /
            yield rx.set_clipboard(image_url)
        except Exception as e:
            yield rx.toast.error(f"Error copying image URL: {e}")


def copy_script():
    return rx.call_script(
        """
        refs['_client_state_setCopying'](true);
        setTimeout(() => {
            refs['_client_state_setCopying'](false);
        }, 1750);
        """
    )
