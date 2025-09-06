import reflex as rx

from .. import styles
from chat.state import State
from chat.backend.options import OptionsState
from ..backend.generation import GeneratorState


def image_prompt_input() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("type", size=17, color=rx.color("green", 9)),
            rx.text("Prompt for Image", size="3"),
            rx.spacer(),
            rx.hstack(
                rx.cond(
                    OptionsState.prompt,
                    rx.icon(
                        "eraser",
                        size=20,
                        color=rx.color("gray", 10),
                        cursor="pointer",
                        _hover={"opacity": "0.8"},
                        on_click=OptionsState.setvar("prompt", ""),
                    ),
                ),
                rx.tooltip(
                    rx.box(  # Without the box the tooltip is not visible
                        rx.icon(
                            "dices",
                            size=20,
                            color=rx.color("gray", 10),
                            cursor="pointer",
                            _hover={"opacity": "0.8"},
                            on_click=OptionsState.randomize_prompt,
                        ),
                    ),
                    content="Randomize prompt",
                ),
                spacing="4",
                align="center",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        rx.text_area(
            placeholder="What do you want to see?",
            width="100%",
            size="3",
            value=OptionsState.prompt,
            on_change=OptionsState.set_prompt,
        ),
        width="100%",
    )


def generate_button() -> rx.Component:
    return rx.box(
        rx.cond(
            ~GeneratorState.is_generating,
            rx.button(
                rx.icon("sparkles", size=18),
                "Generate",
                size="3",
                cursor="pointer",
                width="100%",
                on_click=GeneratorState.generate_image,
            ),
            rx.button(
                rx.spinner(size="3"),
                "Cancel",
                size="3",
                width="100%",
                color_scheme="tomato",
                cursor="pointer",
                on_click=GeneratorState.cancel_generation,
            ),
        ),
        position="sticky",
        bottom="0",
        padding="1em",
        bg=rx.color("gray", 2),
        border_top=styles.border,
        width="100%",
    )


def data_table():
    """Render the data as a table using Reflex-native iteration."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.foreach(State.columns, lambda col: rx.table.column_header_cell(col))
            )
        ),
        rx.table.body(
            rx.foreach(
                State.rows,
                lambda row: rx.table.row(
                    rx.foreach(row, lambda cell: rx.table.cell(cell))
                ),
            )
        ),
        width="100%",
        style={"overflowX": "auto", "maxHeight": "500px", "overflowY": "scroll"},
    )


def data_path() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("table", size=17, color=rx.color("green", 9)),
            rx.text("Data path", size="3"),
            rx.spacer(),
            rx.hstack(
                rx.cond(
                    OptionsState.prompt,
                    rx.icon(
                        "eraser",
                        size=20,
                        color=rx.color("gray", 10),
                        cursor="pointer",
                        _hover={"opacity": "0.8"},
                        on_click=OptionsState.setvar("prompt", ""),
                    ),
                ),
                spacing="4",
                align="center",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        rx.text_area(
            placeholder="Which data you do you want to see?",
            width="100%",
            size="3",
            # value=OptionsState.prompt,
            on_change=State.set_data_path,
        ),
        rx.button("Load Data", on_click=State.load_data),
        # rx.cond(State.error_message != "", rx.text(State.error_message, color="red")),
        # rx.cond(State.columns != [], data_table()),
        width="100%",
    )
