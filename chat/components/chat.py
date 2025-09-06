import logging
import reflex as rx
import reflex_chakra as rc

from chat.state import QA, State
from chat.components import loading_icon


message_style = dict(
    display="inline-block",
    padding="1em",
    border_radius="8px",
    max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
)


def setup_logging(log_filepath):
    """
    Setup the logger.

    Parameters:-
    ------------
    log_filepath -- (str) log file path
    """
    # setup logger
    logger = logging.getLogger("designdash_setup_logger")
    logger.setLevel(logging.DEBUG)
    fatal_logger = logging.getLogger("designdash_setup_fatal_logger")
    fatal_logger.setLevel(logging.DEBUG)

    # create logging handlers
    file_handler = logging.FileHandler(log_filepath, "w")
    file_handler.setLevel(logging.DEBUG)
    fatal_f_handler = logging.FileHandler(log_filepath.replace(".log", ".err"), "w")
    fatal_f_handler.setLevel(logging.DEBUG)

    # set logging formats
    FILE_FORMAT = "%(asctime)s - %(levelname)s: %(message)s"
    file_formatter = logging.Formatter(fmt=FILE_FORMAT)
    file_handler.setFormatter(file_formatter)
    fatal_f_handler.setFormatter(file_formatter)

    # add handlers to the logger
    logger.addHandler(file_handler)
    fatal_logger.addHandler(fatal_f_handler)
    return logger, fatal_logger


def message(qa: QA) -> rx.Component:
    """A single question/answer message. Render only if question or answer is non-empty."""

    return rx.cond(
        (qa.question != "") | (qa.answer != ""),
        rx.box(
            rx.cond(
                qa.question != "",
                rx.box(
                    rx.markdown(
                        qa.question,
                        background_color=rx.color("mauve", 4),
                        color=rx.color("mauve", 12),
                        **message_style,
                    ),
                    text_align="right",
                    margin_top="1em",
                ),
            ),
            rx.cond(
                qa.answer != "",
                rx.box(
                    rx.markdown(
                        qa.answer,
                        background_color=rx.color("accent", 4),
                        color=rx.color("accent", 12),
                        **message_style,
                    ),
                    text_align="left",
                    padding_top="1em",
                ),
            ),
            width="100%",
        ),
    )


def chat() -> rx.Component:
    """List all the messages in a single conversation."""
    return rx.vstack(
        rx.box(rx.foreach(State.chats[State.current_chat], message), width="100%"),
        py="8",
        flex="1",
        width="100%",
        max_width="50em",
        padding_x="4px",
        align_self="center",
        overflow="hidden",
        padding_bottom="5em",
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.center(
        rx.vstack(
            rc.form(
                rc.form_control(
                    rx.hstack(
                        rx.input(
                            rx.input.slot(
                                rx.tooltip(
                                    rx.icon("info", size=18),
                                    content="Enter a question to get a response.",
                                )
                            ),
                            placeholder="Type something...",
                            id="question",
                            width=["15em", "20em", "45em", "50em", "50em", "50em"],
                        ),
                        rx.button(
                            rx.cond(
                                State.processing,
                                loading_icon(height="1em"),
                                rx.text("Send"),
                            ),
                            type="submit",
                        ),
                        align_items="center",
                    ),
                    is_disabled=State.processing,
                ),
                on_submit=State.process_question,
                reset_on_submit=True,
            ),
            rx.text(
                "ReflexGPT may return factually incorrect or misleading responses. Use discretion.",
                text_align="center",
                font_size=".75em",
                color=rx.color("mauve", 10),
            ),
            rx.logo(margin_top="-1em", margin_bottom="-1em"),
            align_items="center",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align_items="stretch",
        width="100%",
    )
