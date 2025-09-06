"""The main Chat app."""

import reflex as rx

from chat.components import chat, navbar
from chat.views.mobile_ui import mobile_ui, mobile_header


@rx.page(
    "/",
    title="Aryan's ChatBot",
    description="A simple chat app using Reflex.",
)
def index() -> rx.Component:
    """The main app."""
    return rx.flex(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.vstack(
                        mobile_header(),
                        mobile_ui(),
                        spacing="2",
                    ),
                    width="20%",
                    height="10%",
                ),
                rx.box(navbar(), width="80%"),
                spacing="2",
                width="100%",
                height="10%",
                wrap="nowrap",
            ),
            rx.spacer(),
            rx.hstack(
                chat.chat(),
                chat.action_bar(),
                spacing="1",
                justify="center",
                width="100%",
                wrap="wrap",
            ),
            background_color=rx.color("mauve", 1),
            color=rx.color("mauve", 12),
            min_height="100vh",
            align="stretch",
            spacing="4",
            padding_x="4",
        ),
        direction="column",
        align="stretch",
        spacing="0",
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="violet",
    ),
)
app.add_page(index)
