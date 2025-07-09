from dataclasses import dataclass
from typing import List


@dataclass
class QA:
    question: str
    answer: str


def zero_shot_prompt(prompt: str) -> str:
    """
    Zero-shot prompt technique that simply returns the provided prompt.

    Args:
        prompt (str): The input prompt to be used.

    Returns:
        str: The same prompt as input.
    """
    return prompt


def few_shot_prompt(prompt: str, examples: List[QA]) -> str:
    """
    Few-shot prompt technique that appends examples to the prompt.

    Args:
        prompt (str): The input prompt to be used.
        examples (List[QA]): A list of question-answer pairs to provide context.

    Returns:
        str: The prompt with appended examples.
    """
    example_str = "\n\n".join(
        f"<example>Pergunta: {qa.question}\nResposta esperada: {qa.answer}</example>"
        for qa in examples
    )
    return f"<examples>\n{example_str}\n</examples>\n\nBaseado nos exemplos acima, resolva o seguinte problema: {prompt}"


def cot_prompt(prompt: str, include_reasoning_instruction: bool = True) -> str:
    """
    Chain of Thoughts (CoT) prompt technique that encourages step-by-step reasoning.

    Args:
        prompt (str): The input prompt to be used.
        include_reasoning_instruction (bool): Whether to include explicit reasoning instructions.

    Returns:
        str: The prompt with chain of thoughts reasoning instructions.
    """
    if include_reasoning_instruction:
        reasoning_instruction = (
            "Pense passo a passo e explique seu processo de raciocínio. "
            "Divida o problema em partes menores e trabalhe cada etapa metodicamente."
        )
        return f"{reasoning_instruction}\n\n{prompt}\n\nVamos trabalhar isso passo a passo:"
    else:
        return f"{prompt}\n\nVamos pensar passo a passo:"


def cot_few_shot_prompt(prompt: str, examples: List[QA]) -> str:
    """
    Combines Chain of Thoughts with few-shot prompting by providing examples
    that demonstrate step-by-step reasoning.

    Args:
        prompt (str): The input prompt to be used.
        examples (List[QA]): A list of question-answer pairs showing reasoning steps.

    Returns:
        str: The prompt with CoT examples and reasoning instructions.
    """
    example_str = "\n\n".join(
        f"<example>\nPergunta: {qa.question}\nRaciocínio passo a passo e resposta: {qa.answer}\n</example>"
        for qa in examples
    )

    return (
        f"<examples>\n{example_str}\n</examples>\n\n"
        f"Seguindo o padrão de raciocínio passo a passo mostrado nos exemplos acima, "
        f"resolva o seguinte problema:\n\n{prompt}\n\n"
        f"Vamos trabalhar isso passo a passo:"
    )
