import reflex as rx

from .. import styles
from ..components.options_ui import (
    image_prompt_input,
    data_path,
    generate_button,
)


def mobile_ui():
    return rx.box(
        rx.vstack(
            image_prompt_input(),
            generate_button(),
            data_path(),
            width="100%",
            height="100%",
            align_items="flex-start",
            padding="1em",
            spacing="6",
        ),
        width="100%",
        spacing="0",
        direction="column",
    )


def mobile_header() -> rx.Component:
    return rx.hstack(
        rx.link(
            rx.color_mode_cond(
                rx.image(src="/reflex_black.svg", height="1.15em", width="auto"),
                rx.image(src="/reflex_white.svg", height="1.15em", width="auto"),
            ),
            href="/",
            is_external=False,
            padding="0",
        ),
        rx.spacer(),
        rx.color_mode.button(
            style={"padding": "0", "height": "1.15em", "width": "1.15em"},
        ),
        align="center",
        width="100%",
        border_bottom=styles.border,
        padding="1em",
    )
