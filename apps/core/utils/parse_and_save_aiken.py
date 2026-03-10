import re


def parse_and_save_aiken(file_path, quiz):
    from apps.quiz.models import Question, Option
    """
    Parses an Aiken format file and saves questions, options,
    and correct answers to the database.

    Args:
        file_path (str): Path to the Aiken file.
        quiz (Quiz): The Quiz object to associate the questions with.

    Raises:
        ValueError: If the file format is invalid.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    question = None
    options = []
    correct_answer = None

    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        if line.startswith('ANSWER:'):
            if not question or not options:
                raise ValueError("Invalid Aiken file format. Missing question or options.")
            correct_answer = line.split(':', 1)[1].strip()

            # Save question and options
            db_question = Question.objects.create(quiz=quiz, text=question)
            for option in options:
                Option.objects.create(
                    question=db_question,
                    text=option['text'],
                    is_correct=(option['key'] == correct_answer)
                )

            # Reset for the next question
            question = None
            options = []
            correct_answer = None
        elif re.match(r'^[A-Z]\.', line):  # Option line (e.g., "A. Option Text")
            key, text = line.split('.', 1)
            options.append({'key': key.strip(), 'text': text.strip()})
        else:
            # A new question
            if question is not None:
                raise ValueError("Invalid Aiken file format. Missing ANSWER for previous question.")
            question = line

    if question or options:
        raise ValueError("Invalid Aiken file format. Unfinished question detected.")
