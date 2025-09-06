import pandas as pd
import reflex as rx
import google.generativeai as genai


genai.configure(api_key="")


class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str | pd.DataFrame


DEFAULT_CHATS = {
    "Intros": [],
}


class State(rx.State):
    """The app state."""

    data_path: str = ""
    columns: list[str] = []
    rows: list[list[str]] = []
    error_message: str = ""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS

    # The current chat name.
    current_chat = "Intros"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    main_df: pd.DataFrame = None

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name

    @rx.var(cache=True)
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())

    async def process_question(self, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        model = self.gemini_process_question

        async for value in model(question):
            yield value

    async def gemini_process_question(self, question: str):
        """Get the response from the Gemini API."""

        if self.main_df is not None and question == "Load Data":
            question += str(self.main_df)

        # Add the question to the list of questions.
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)

        # Clear the input and start the processing.
        self.processing = True
        yield

        # Build the messages.
        messages = [
            {"role": "system", "content": "You are a friendly chatbot named Reflex."}
        ]
        for qa in self.chats[self.current_chat]:
            messages.append({"role": "user", "content": qa.question})
            messages.append({"role": "assistant", "content": qa.answer})

        # Remove the last mock answer.
        messages = messages[:-1]

        # Configure Gemini API
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Get the response from Gemini
        response = model.generate_content(
            contents="\n".join([message["content"] for message in messages])
        )
        answer_text = response.text

        # Update the chat with the answer
        self.chats[self.current_chat][-1].answer += answer_text
        self.chats = self.chats  # Trigger reactivity
        yield

        # Toggle the processing flag.
        self.processing = False

    def load_data(self):
        path = self.data_path.strip()
        if not path:
            qa = QA(question="Load Data", answer="❌ Please enter a valid file path.")
            self.chats[self.current_chat].append(qa)
            return

        try:
            if path.endswith(".csv"):
                df = pd.read_csv(path)
            elif path.endswith(".xlsx"):
                df = pd.read_excel(path)
            elif path.endswith(".ldb"):
                df = pd.read_parquet(path, engine="pyarrow")
            else:
                qa = QA(
                    question="Load Data",
                    answer="❌ Unsupported file type. Use CSV, XLSX, or LDB.",
                )
                self.chats[self.current_chat].append(qa)
                return

            # Store the main DataFrame in a state variable for LLM access
            self.main_df = df

            # Generate a markdown preview table with borders using GitHub table format
            preview_table = df.head(5).to_markdown(index=False)
            summary = (
                "✅ Data loaded successfully! Here are the top 5 rows of the data:\n"
                f"```\n{preview_table}\n```"
            )

            # Create QA object and trigger reactivity
            qa = QA(question="Load Data", answer=summary)
            self.chats[self.current_chat].append(qa)

            # Force state update to trigger UI refresh
            self.chats = dict(self.chats)

        except Exception as e:
            qa = QA(question="Load Data", answer=f"❌ Failed to load data: {str(e)}")
            self.chats[self.current_chat].append(qa)
            # Force state update for error case too
            self.chats = dict(self.chats)
