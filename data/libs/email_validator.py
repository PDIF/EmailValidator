import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reason: str | None


class EmailValidator:
    """
    Валидатор email-адресов с поддержкой кастомных регулярных выражений.

    Принимает на вход пользовательский шаблон в виде строки, содержащей символ '@'.
    На его основе автоматически генерирует паттерны для локальной части (до @),
    доменной части (после @) и полного email-адреса.

    При отсутствии пользовательского шаблона используется стандартный:
        r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'

    Валидация выполняется в три этапа:
    1. Предварительная проверка (тип, длина, наличие одного '@').
    2. Проверка локальной и доменной частей по сформированным паттернам.
    3. Финальная проверка всего адреса по полному пользовательскому шаблону.
    """

    _DEFAULT_PATTERN = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'
    _DEFAULT_OK = ValidationResult(True, None)

    _MAX_DOMAIN_LENGTH = 253
    _MAX_LOCAL_LENGTH = 64
    _MAX_FULL_LENGTH = 254

    def __init__(self, pattern: str | None = None):
        """
        Инициализирует валидатор.

        Args:
            pattern: Опциональный пользовательский регулярный шаблон для полного email.
                     Должен содержать символ '@'. Если не указан — используется стандартный шаблон.
        """
        # нициализируем свойства значением None
        self._regex_local = None
        self._regex_domain = None
        self._regex_email = None

        # проверяем паттерн email
        if pattern is None:
            pattern = self._DEFAULT_PATTERN

        # формируем паттерны для различных частей email
        self.set_pattern(pattern)


    def set_pattern(self, pattern: str) -> None:
        """
        Устанавливает пользовательский регулярный шаблон для email и генерирует производные паттерны.

        Шаблон должен содержать ровно один символ '@', который разделяет локальную и доменную части.
        На основе шаблона формируются:
        - Паттерн для локальной части: `local_part + '$'`
        - Паттерн для доменной части: `'^' + domain_part`
        - Паттерн для полного email: исходный шаблон

        Args:
            pattern: Регулярное выражение для полного email, содержащее символ '@'.

        Raises:
            ValueError: Если шаблон не является строкой, пуст, или не содержит '@'.
        """

        if not isinstance(pattern, str):
            raise ValueError("Паттерн регулярного выражения для анализа email должен быть строкой")

        if not pattern.strip():
            raise ValueError("Паттерн регулярного выражения для анализа email не должен быть пустым")

        if "@" not in pattern:
            raise ValueError("Паттерн регулярного выражения для анализа email должен содержать символ '@'")

        # выделяем из общего паттерна части для local и domain компилируем для последующего анализа
        local_part, _, domain_part = pattern.partition("@")
        self._regex_local = re.compile(local_part + "$")
        self._regex_domain = re.compile("^" + domain_part)
        self._regex_email = re.compile(pattern)


    def validate(self, email: str) -> ValidationResult:
        """
        Проводит комплексную валидацию email-адреса.

        Выполняет последовательные проверки:
        1. Предварительная проверка (тип, длина, наличие одного '@').
        2. Валидация локальной части по сформированному паттерну.
        3. Валидация доменной части по сформированному паттерну.
        4. Финальная проверка всего адреса по полному пользовательскому шаблону.

        Args:
            email: Проверяемый email-адрес.

        Returns:
            ValidationResult: Объект с флагом is_valid и описанием ошибки (если есть).
        """

        # предварительная проверка email
        preliminary_validate = self._preliminary_validation(email)
        if not preliminary_validate.is_valid:
            return preliminary_validate

        # разделяем email на части
        local, _, domain = email.partition("@")

        # проверяем локальную часть
        local_validate = self._local_validate(local)
        if not local_validate.is_valid:
            return local_validate

        # проверяем доменную часть
        domain_validate = self._domain_validate(domain)
        if not domain_validate.is_valid:
            return domain_validate

        # проверяем весь email целиком
        return self._full_validate(email)


    def _preliminary_validation(self, email: str) -> ValidationResult:
        """
        Выполняет базовую предварительную проверку email.

        Проверяет:
        - Тип данных (должен быть str).
        - Непустота строки.
        - Длину (≤254 символа).
        - Наличие ровно одного символа '@'.

        Args:
            email: Проверяемый email-адрес.

        Returns:
            ValidationResult: Результат проверки.
        """

        if not isinstance(email, str):
            return ValidationResult(False, "Email должен быть строкой")

        if not email:
            return ValidationResult(False, "Email не может быть пустым")

        if len(email) > self._MAX_FULL_LENGTH:
            return ValidationResult(False, f"Email превышает {self._MAX_FULL_LENGTH} символов")

        if '@' not in email:
            return ValidationResult(False, "Email не содержит символ '@'")

        if email.count('@') != 1:
            return ValidationResult(False, "Email содержит несколько символов '@'")

        return self._DEFAULT_OK


    def _local_validate(self, local: str) -> ValidationResult:
        """
        Валидирует локальную часть email (до @).

        Проверяет:
        - Наличие содержимого.
        - Длину (≤64 символа).
        - Соответствие сформированному паттерну (без учета '@').

        Args:
            local: Локальная часть email.

        Returns:
            ValidationResult: Результат валидации.
        """

        if not local:
            return ValidationResult(False, "Локальная часть email пуста")

        if len(local) > self._MAX_LOCAL_LENGTH:
            return ValidationResult(False, f"Локальная часть email превышает {self._MAX_LOCAL_LENGTH} символов")

        if not self._regex_local.fullmatch(local):
            return ValidationResult(False, "Локальная часть email содержит недопустимые символы")

        return self._DEFAULT_OK


    def _domain_validate(self, domain: str) -> ValidationResult:
        """
        Валидирует доменную часть email (после @).

        Проверяет:
        - Наличие содержимого.
        - Длину (≤253 символа).
        - Наличие хотя бы одной точки.
        - Отсутствие точек в начале, конце или подряд.
        - Соответствие сформированному паттерну (без учета '@').

        Args:
            domain: Доменная часть email.

        Returns:
            ValidationResult: Результат валидации.
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

        if not self._regex_domain.fullmatch(domain):
            return ValidationResult(False, "Доменная часть email содержит недопустимые символы")

        return self._DEFAULT_OK


    def _full_validate(self, email: str) -> ValidationResult:
        """
        Выполняет финальную проверку всего email-адреса по пользовательскому регулярному шаблону.

        Эта проверка применяется после всех предыдущих этапов и использует полный шаблон,
        переданный в конструктор или установленный через set_pattern.

        Args:
            email: Полный email-адрес.

        Returns:
            ValidationResult: Результат проверки.
        """


        if not self._regex_email.fullmatch(email):
            return ValidationResult(False, "Email содержит недопустимые символы")

        return self._DEFAULT_OK

