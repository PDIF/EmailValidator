
import json
import time
from pathlib import Path
from datetime import datetime
from data.libs.email_validator import EmailValidator


class DataGather:
    """
    Сборщик и хранитель истории проверок email-адресов.

    Класс отвечает за валидацию email-адресов (одиночных и пакетных) и ведение
    двухуровневой истории проверок:

    - быстрый лог (fast-лог) — файл в формате NDJSON (по одной JSON-строке на запись),
    дописывается при каждой проверке; обеспечивает быструю запись;
    - медленный лог (slow-лог) — файл в виде отформатированного JSON-массива,
    перезаписывается актуальными записями из fast-лога и используется для чтения истории
    методом get_history.

    Оба лога ограничены количеством записей MAX_LOG_LINES: при каждом обновлении
    slow-лога fast-лог усекается до последних MAX_LOG_LINES строк, поэтому в истории
    хранятся только самые свежие проверки.

    Записи в файлах выполняются с повторными попытками (до _MAX_RETRIES раз с паузой
    _RETRY_DELAY) — на случай временной блокировки файла другим процессом.

    Пути к лог-файлам определяются автоматически по расположению модуля:
    - при ожидаемой структуре проекта (project_root/data/libs) fast-лог пишется
        в директорию data/, slow-лог — в корень проекта;
    - при иной структуре оба файла создаются в директории модуля.

    Имена файлов формируются на основе _DEFAULT_LOG_NAME либо пользовательского
    log_name, переданного в конструктор.

    Пример использования:
        dg = DataGather()
        result = dg.single_checking("user@example.com")
        history = dg.get_history()

    Attributes:
        MAX_LOG_LINES (int): максимальное количество записей в каждом лог-файле.
        email_validator (EmailValidator): валидатор email-адресов.
    """
    
    # Максимальное количество записей в лог-файле (истории проверок)
    MAX_LOG_LINES = 1000

    # Технические данные
    _BASE_DIR = Path(__file__).parent.resolve()  # путь к папке, где лежит модуль с классом
    _DEFAULT_LOG_NAME = "history.json"  # название лог-файла (история проверок)
    _MAX_RETRIES = 3  # максимальное количество попыток записи в файл
    _RETRY_DELAY = 0.1  # пауза перед попытками записи в файл (на случай если он занят)


    def __init__(self, log_name: str | None = None):

        self.email_validator = EmailValidator()
        self._log_name = log_name if log_name else self._DEFAULT_LOG_NAME  
        self._fast_history_json = self._set_fast_history_json_path()
        self._slow_history_json = self._set_slow_history_json_path()


    def check_email(self, email: str) -> dict[str, str]:
        """
        Проверяет email и возвращает результат проверки без записи в лог.

        Валидация выполняется через self.email_validator.validate(email).

        Формирует и возвращает словарь вида:
        {
            "timestamp": дата/время проверки в формате ГГГГ.ММ.ДД ЧЧ:ММ:СС,
            "email": проверенный email,
            "status": результат проверки ("Корректен" / "Некорректен"),
            "reason": причина некорректности; для корректного email — пустая строка
        }

        Args:
            email (str): строка с email-адресом для проверки.

        Returns:
            dict[str, str]: словарь с ключами "timestamp", "email", "status", "reason".
        """

        # предварительный результат проверки
        email_validation_result = self.email_validator.validate(email)

        # статус
        status = "Корректен" if email_validation_result.is_valid else "Некорректен"

        # причина
        reason = "" if email_validation_result.is_valid else str(email_validation_result.reason)

        # текущая дата / время в формате ГГГГ.ММ.ДД ЧЧ:ММ:СС
        current_time = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

        # результат
        return {
            "timestamp": current_time,
            "email": email,
            "status": status,
            "reason": reason
        }


    def single_checking(self, email) -> dict[str, str]:
        """
        Проверяет одиночный email и сохраняет результат в быстрый и медленный логи.

        Метод выполняет валидацию переданного адреса через check_email, затем:
        - добавляет запись в быстрый лог (в формате NDJSON, по одной строке на запись);
        - обновляет медленный лог, перезаписывая его актуальными записями из быстрого лога
        с учётом ограничения MAX_LOG_LINES.

        Args:
            email: строка с email-адресом для проверки.

        Returns:
            dict[str, str]: словарь результата проверки с ключами:
                - "timestamp": время проверки в формате ГГГГ.ММ.ДД ЧЧ:ММ:СС;
                - "email": проверенный email;
                - "status": "Корректен" или "Некорректен";
                - "reason": причина некорректности либо пустая строка.

        Raises:
            RuntimeError: если не удалось записать данные в лог-файл после _MAX_RETRIES попыток.
        """

        result = self.check_email(email)
        self._write_fast_log(result)
        self._write_slow_log()
        return result


    def multiple_checking(self, path_file: str) -> list[dict[str, str]]:
        """
        Проверяет список email-адресов из текстового файла и сохраняет результаты в логи.

        Метод читает файл построчно, для каждой непустой строки выполняет проверку через check_email,
        добавляет результат в быстрый лог и накапливает записи для возврата. После обработки всех строк
        обновляет медленный лог, перезаписывая его актуальными записями из быстрого лога с учётом
        ограничения MAX_LOG_LINES.

        Возвращаемый список — это срез последних MAX_LOG_LINES записей из локального буфера результатов,
        а не из файла лога. Самые новые записи находятся в конце списка.
        Каждая запись — словарь с ключами: "timestamp", "email", "status", "reason".

        Args:
            path_file (str): путь к текстовому файлу, содержащему список email-адресов (по одному в строке).

        Returns:
            list[dict[str, str]]: список результатов проверок (не более MAX_LOG_LINES записей),
                где каждый элемент — словарь вида:
                {
                    "timestamp": время проверки в формате ГГГГ.ММ.ДД ЧЧ:ММ:СС,
                    "email": проверенный email,
                    "status": "Корректен" или "Некорректен",
                    "reason": причина некорректности либо пустая строка
                }

        Raises:
            FileNotFoundError: если файл с email-адресами не найден.
            OSError: если произошла ошибка при чтении файла.
            RuntimeError: если не удалось записать данные в лог-файл после _MAX_RETRIES попыток.
        """

        multiple_result = list()
        try:
            with open(path_file, "r", encoding="utf-8") as f:
                for line in f:
                    email = line.strip()
                    result = self.check_email(email)
                    self._write_fast_log(result)
                    multiple_result.append(result)

        except FileNotFoundError:
            raise FileNotFoundError(f"Файл с email-адресами не найден: {path_file}")

        except OSError as e:
            raise OSError(f"Ошибка при чтении файла {path_file}: {e}")

        # Перезаписываем медленный лог после обработки всех email
        self._write_slow_log()

        return multiple_result[-self.MAX_LOG_LINES:]


    def get_history(self):
        """
        Возвращает историю проверок email из медленного лог-файла (slow-лога).

        Метод читает файл, указанный в _slow_history_json, и пытается распарсить его как JSON-массив.
        Формат записей зависит от текущего содержимого файла: обычно это списки вида
        [timestamp, email, status, reason], но метод не гарантирует этот формат и возвращает
        данные «как есть».

        Если файл не найден или содержит некорректный JSON, возвращается пустой список.
        Если содержимое файла не является списком — также возвращается пустой список.

        Returns:
            list: содержимое JSON-файла (обычно список списков). Если история пуста или файл
                недоступен — возвращается [].
        """
        try:
            with open(self._slow_history_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return []
        except (FileNotFoundError, json.JSONDecodeError):
            return []


    def _write_fast_log(self, record: dict) -> None:
        """
        Добавляет результат проверки email в быстрый лог (fast-лог) в формате NDJSON.

        Метод извлекает значения из переданного словаря record (в порядке ключей),
        преобразует их в JSON-строку и дописывает в файл _fast_history_json как отдельную строку.
        Каждая строка файла представляет собой JSON-массив значений:
        [timestamp, email, status, reason].

        Запись выполняется с повторными попытками при ошибках доступа к файлу (до _MAX_RETRIES раз).

        Args:
            record (dict): словарь результата проверки (как возвращает check_email) с ключами:
                - "timestamp": время проверки;
                - "email": проверенный email;
                - "status": статус ("Корректен" / "Некорректен");
                - "reason": причина или пустая строка.

        Returns:
            None

        Raises:
            RuntimeError: если не удалось записать данные в лог-файл после _MAX_RETRIES попыток.
        """

        values = list(record.values())
        line = json.dumps(values, ensure_ascii=False) + "\n"

        self._write_to_file(line, self._fast_history_json, "a")


    def _write_slow_log(self):
        """
        Обновляет медленный лог (slow-лог), перезаписывая его актуальными записями из быстрого лога.

        Метод выполняет следующие шаги:
        1. Читает все строки из fast-лога (_fast_history_json) как текст (без парсинга).
        2. Оставляет только последние MAX_LOG_LINES строк (самые новые записи).
        3. Парсит каждую строку как JSON-массив и формирует из них JSON-список для slow-лога.
           Некорректные (битые) строки пропускаются, чтобы не нарушить целостность файла.
        4. Записывает итоговый список в _slow_history_json в виде отформатированного JSON-массива.
        5. Затем перезаписывает fast-лог, оставляя в нём только те же последние MAX_LOG_LINES строк,
           чтобы контролировать размер файла и поддерживать согласованность между логами.

        Запись в оба файла выполняется с повторными попытками при ошибках доступа (до _MAX_RETRIES раз).
        Если fast-лог отсутствует, метод ничего не делает.

        Returns:
            None

        Raises:
            RuntimeError: если не удалось записать данные в лог-файл после _MAX_RETRIES попыток.
        """

        # читаем все строки из fast-лога (как текст, без парсинга)
        try:
            with open(self._fast_history_json, "r", encoding="utf-8") as f:
                all_lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return  # Если fast-лога нет — ничего не делаем

        # берём последние _MAX_LOG_LINES строк
        last_lines = all_lines[-self.MAX_LOG_LINES:] if all_lines else []

        # Обрезаем fast-лог: оставляем только последние _MAX_LOG_LINES строк
        if last_lines:
            records_slow = list()
            for line in last_lines:
                try:
                    record_slow = json.loads(line)
                    records_slow.append(record_slow)

                except json.JSONDecodeError:
                    # Пропускаем битые записи — лучше пропустить, чем сломать весь файл
                    continue

            # формируем JSON-массив для записи в slow-лог
            data_slow = json.dumps(records_slow, ensure_ascii=False, indent=2) + "\n"
            self._write_to_file(data_slow, self._slow_history_json, "w")

            # перезаписываем fast-лог в виде NDJSON, оставив в нем только ограниченное число самых актуальных записей
            data_fast = "\n".join(last_lines) + "\n"
            self._write_to_file(data_fast, self._fast_history_json, "w")


    def _write_to_file(self, data, file_path: Path, method):
        """
        Записывает данные в указанный файл с поддержкой повторных попыток при ошибках.

        Метод пытается выполнить запись в файл file_path с режимом доступа method.
        Если операция завершается ошибкой (OSError, PermissionError), выполняется до _MAX_RETRIES
        попыток с паузой _RETRY_DELAY между ними. При исчерпании лимита попыток выбрасывается RuntimeError.

        Args:
            data: данные для записи в файл (обычно строка).
            file_path (Path): путь к целевому файлу.
            method (str): режим открытия файла (например, 'w' для перезаписи, 'a' для дописывания).

        Returns:
            None

        Raises:
            RuntimeError: если не удалось записать данные после _MAX_RETRIES попыток.
        """
        for attempt in range(self._MAX_RETRIES):
            try:
                with open(file_path, method, encoding="utf-8") as f:
                    f.write(data)

                return  # Успешно — выходим

            except (OSError, PermissionError) as e:
                if attempt == self._MAX_RETRIES - 1:

                    raise RuntimeError(
                        f"Не удалось записать данные в '{file_path.name}' после {self._MAX_RETRIES} попыток: {e}"
                    )
                time.sleep(self._RETRY_DELAY)


    def _set_fast_history_json_path(self):
        """
        Определяет путь к файлу быстрого лога (fast-лога).

        Метод анализирует структуру проекта относительно расположения текущего модуля,
        чтобы корректно задать путь к файлу fast-лога:
        - Если проект имеет ожидаемую структуру (папка data, внутри неё libs, где лежит модуль),
            путь устанавливается в родительскую директорию от data (то есть в data/).
        - Если структура не соответствует ожиданиям, путь задаётся в текущей директории модуля.

        Имя файла формируется на основе _log_name с добавлением суффикса «l»
        (например, history.json → history.jsonl).

        При использовании ожидаемой структуры метод проверяет существование целевой директории
        и выбрасывает FileNotFoundError, если она отсутствует.

        Returns:
            Path: абсолютный путь к файлу быстрого лога (_fast_history_json).

        Raises:
            FileNotFoundError: если при ожидаемой структуре проекта целевая директория не найдена.
        """

        # имя файла
        fast_history_json_filename = f"{self._log_name}l"

        # если структура проекта не нарушена, то устанавливаем путь к файлу в папку data, если нарушена, то в текущую
        parts = self._BASE_DIR.parts
        if len(parts) >= 2 and parts[-2].lower() == "data" and parts[-1].lower() == "libs":
            # структура соблюдена: пишем в (data/)
            data_dir = self._BASE_DIR.parent
            if not data_dir.exists():
                raise FileNotFoundError(f"Ожидаемая директория для быстрого лога '{data_dir}' не существует")
            return data_dir / fast_history_json_filename

        # структура проекта нарушена: пишем в текущую директорию
        return self._BASE_DIR / fast_history_json_filename


    def _set_slow_history_json_path(self):
        """
        Определяет путь к файлу медленного лога (slow-лога).

        Метод анализирует структуру проекта относительно расположения текущего модуля,
        чтобы корректно задать путь к файлу slow-лога:
        - Если проект имеет ожидаемую структуру (project_root/data/libs), путь устанавливается
            в корневую директорию проекта (project_root), где будет лежать файл с именем _log_name.
        - Если структура не соответствует ожиданиям, путь задаётся в текущей директории модуля.

        При использовании ожидаемой структуры метод проверяет существование целевой директории
        и выбрасывает FileNotFoundError, если она отсутствует.

        Returns:
            Path: абсолютный путь к файлу медленного лога (_slow_history_json).

        Raises:
            FileNotFoundError: если при ожидаемой структуре проекта целевая директория не найдена.
        """

        # имя файла
        slow_history_json_filename = self._log_name

        # если структура проекта не нарушена, то устанавливаем путь к файлу в родительскую папку от data
        parts = self._BASE_DIR.parts
        if len(parts) >= 3 and parts[-2].lower() == "data" and parts[-1].lower() == "libs":
            # структура нормальная (project_root/data/libs) - пишем в project_root
            project_root = self._BASE_DIR.parent.parent
            if not project_root.exists():
                raise FileNotFoundError(f"Ожидаемая директория для медленного лога '{project_root}' не существует")
            return project_root / slow_history_json_filename

        # структура проекта нарушена: пишем в текущую директорию
        return self._BASE_DIR / slow_history_json_filename

