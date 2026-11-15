import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """
    Результат валидации email-адреса (или его части).

    Attributes:
        is_valid (bool): True, если проверка пройдена, иначе False.
        reason (str | None): причина несоответствия; для корректного адреса — None.
    """
    is_valid: bool
    reason: str | None


class EmailValidator:
    """
    Валидатор email-адресов с поддержкой кастомных регулярных выражений.

    Принимает на вход пользовательский шаблон в виде строки, содержащей символ '@'.
    На его основе автоматически генерирует паттерны для локальной части (до @),
    доменной части (после @) и полного email-адреса.

    При отсутствии пользовательского шаблона используется стандартный паттерн:
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'

    Валидация выполняется в три этапа:
    1. Предварительная проверка (тип, длина, наличие одного '@').
    2. Проверка локальной и доменной частей по ряду критериев (пустота, длина, запрещенные символы, паттерн).
    3. Финальная проверка всего адреса по полному пользовательскому шаблону.

    RFC 5322 соблюдается как базовый уровень: запрещённые символы проверяются независимо.
    """

    # паттерн по умолчанию
    DEFAULT_PATTERN = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'

    # запрещенные символы в локальной и доменной частях по RFC 5322
    _FORBIDDEN_LOCAL_CHAR_PATTERN = r'[^a-zA-Z0-9!#$%&\'*+/=?^_`{|}~.-]'
    _FORBIDDEN_DOMAIN_CHAR_PATTERN = r'[^a-zA-Z0-9.\[\]-]'

    # результат проверки по умолчанию (ОК)
    _DEFAULT_OK = ValidationResult(True, None)

    # ограничения на длины локальной и доменной частей
    _MAX_DOMAIN_LENGTH = 253
    _MAX_LOCAL_LENGTH = 64
    _MAX_FULL_LENGTH = 254

    def __init__(self, pattern: str | None = None):
        self._regex_local = None
        self._regex_domain = None
        self._regex_email = None
        self._regex_forbidden_char_local = None
        self._regex_forbidden_char_domain = None

        if pattern is None:
            pattern = self.DEFAULT_PATTERN

        self.set_pattern(pattern)

    def set_pattern(self, pattern: str) -> None:
        """
        Устанавливает пользовательский шаблон и строит на его основе паттерны валидации.

        Метод разбивает шаблон по символу '@' на локальную и доменную части,
        очищает их от якорей '^' и '$' и компилирует три регулярных выражения:
        для локальной части, доменной части и полного email целиком.
        Компилируются также фиксированные паттерны запрещённых символов
        по RFC 5322 (не зависят от пользовательского шаблона).

        Args:
            pattern (str): регулярное выражение полного email, содержащее символ '@'
                (например, r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$').

        Raises:
            ValueError: если pattern не является строкой, пуст или не содержит '@'.
            re.error: если pattern содержит синтаксически некорректное регулярное выражение.
        """
        if not isinstance(pattern, str):
            raise ValueError("Паттерн регулярного выражения для анализа email должен быть строкой")
        if not pattern.strip():
            raise ValueError("Паттерн регулярного выражения для анализа email не должен быть пустым")
        if "@" not in pattern:
            raise ValueError("Паттерн регулярного выражения для анализа email должен содержать символ '@'")

        local_part, _, domain_part = pattern.partition("@")

        # очищаем от ^ и $, чтобы не дублировать позже
        local_part = local_part.removeprefix('^').removesuffix('$')
        # domain_part = domain_part.lstrip('^').rstrip('$')
        domain_part = domain_part.removeprefix('^').removesuffix('$')
         
        # компилируем с явными границами
        self._regex_local = re.compile(r'^' + local_part + r'$')
        self._regex_domain = re.compile(r'^' + domain_part + r'$')
        self._regex_email = re.compile(pattern)

        # пересоздаём паттерны для запрещённых символов
        self._regex_forbidden_char_local = re.compile(self._FORBIDDEN_LOCAL_CHAR_PATTERN)
        self._regex_forbidden_char_domain = re.compile(self._FORBIDDEN_DOMAIN_CHAR_PATTERN)

    def validate(self, email: str) -> ValidationResult:
        """
        Выполняет полную валидацию email-адреса.

        Проверка проходит последовательно по этапам; при первой же ошибке
        возвращается результат с её причиной, дальнейшие проверки не выполняются:
        1. Предварительная проверка (тип, пустота, длина, наличие ровно одного '@').
        2. Проверка локальной части (пустота, длина, запрещённые символы, паттерн).
        3. Проверка доменной части (пустота, длина, точки, запрещённые символы, паттерн).
        4. Финальная проверка всего адреса по пользовательскому (или дефолтному) паттерну.

        Args:
            email (str): проверяемая строка с email-адресом.

        Returns:
            ValidationResult: объект с is_valid=True и reason=None при успехе;
                при ошибке — is_valid=False и человекочитаемым описанием причины в reason.
        """
        
        preliminary_validate = self._preliminary_validation(email)
        if not preliminary_validate.is_valid:
            return preliminary_validate

        local, _, domain = email.partition("@")

        local_validate = self._local_validate(local)
        if not local_validate.is_valid:
            return local_validate

        domain_validate = self._domain_validate(domain)
        if not domain_validate.is_valid:
            return domain_validate

        return self._full_validate(email)

    def _preliminary_validation(self, email: str) -> ValidationResult:
        """Предварительная проверка (тип, длина, наличие одного '@')"""

        if not isinstance(email, str):
            return ValidationResult(False, "Email должен быть строкой")
        if not email:
            return ValidationResult(False, "Email не может быть пустым")
        if len(email) > self._MAX_FULL_LENGTH:
            return ValidationResult(False, f"Длина email превышает {self._MAX_FULL_LENGTH} символов")
        if '@' not in email:
            return ValidationResult(False, "Email не содержит символ '@'")
        if email.count('@') != 1:
            return ValidationResult(False, "Email содержит несколько символов '@'")
        return self._DEFAULT_OK


    def _local_validate(self, local: str) -> ValidationResult:
        """
        Проверка локальной части по критериям:
        - пустота,
        - максимальная длина,
        - запрещенные символы,
        - соответствие локальной части из пользовательского (или дефолтного) паттерна
        """
        if not local:
            return ValidationResult(False, "Локальная часть email пуста")
        if len(local) > self._MAX_LOCAL_LENGTH:
            return ValidationResult(False, f"Локальная часть email превышает {self._MAX_LOCAL_LENGTH} символов")

        match = self._regex_forbidden_char_local.search(local)
        if match:
            char = match.group(0)
            return ValidationResult(False, f"Локальная часть содержит недопустимый символ '{char}' (по RFC 5322)")

        if not self._regex_local.fullmatch(local):
            return ValidationResult(
                False,
                f"Локальная часть '{local}' не соответствует ожидаемой структуре: {self._regex_local.pattern}"
            )

        return self._DEFAULT_OK

    def _domain_validate(self, domain: str) -> ValidationResult:
        """
        Проверка доменной части по критериям:
        - пустота,
        - максимальная длина,
        - наличие точки,
        - отсутствие точки в начале и конце,
        - отсутствие нескольких точек подряд,
        - запрещённые символы,
        - соответствие доменной части из пользовательского (или дефолтного) паттерна
        """
        if not domain:
            return ValidationResult(False, "Доменная часть email пуста")
        if len(domain) > self._MAX_DOMAIN_LENGTH:
            return ValidationResult(False, f"Доменная часть email превышает {self._MAX_DOMAIN_LENGTH} символов")

        if "." not in domain:
            return ValidationResult(False, "Доменная часть email не содержит точки")
        if domain.startswith("."):
            return ValidationResult(False, "Доменная часть email начинается с точки")
        if domain.endswith("."):
            return ValidationResult(False, "Доменная часть email заканчивается точкой")
        if ".." in domain:
            return ValidationResult(False, "Доменная часть email содержит несколько точек подряд")

        match = self._regex_forbidden_char_domain.search(domain)
        if match:
            char = match.group(0)
            return ValidationResult(False, f"Доменная часть содержит недопустимый символ '{char}' (по RFC 5322)")

        if not self._regex_domain.fullmatch(domain):
            return ValidationResult(
                False,
                f"Доменная часть '{domain}' не соответствует ожидаемой структуре: {self._regex_domain.pattern}"
            )

        return self._DEFAULT_OK

    def _full_validate(self, email: str) -> ValidationResult:
        """
        Финальная проверка email на соответствие пользовательскому (или дефолтному) паттерну
        """
        if not self._regex_email.fullmatch(email):
            return ValidationResult(
                False,
                f"Полный email '{email}' не соответствует шаблону: {self._regex_email.pattern}"
            )
        return self._DEFAULT_OK