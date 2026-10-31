
import json
import time
from pathlib import Path
from datetime import datetime
from data.libs.email_validator import ValidationResult, EmailValidator


class DataGather:

    _BASE_DIR = Path(__file__).parent.resolve()
    _DEFAULT_LOG_NAME = "history.json"
    _MAX_LOG_LINES = 100
    _MAX_RETRIES = 3
    _RETRY_DELAY = 0.1


    def __init__(self, log_name: str = None):

        self.email_validator = EmailValidator()
        self._log_name = log_name if log_name else self._DEFAULT_LOG_NAME
        self._fast_history_json = self._set_fast_history_json_path()
        self._slow_history_json = self._set_slow_history_json_path()


    def _set_fast_history_json_path(self):
        """Устанавливаем путь к быстрому логу"""


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


    def check_email(self, email: str) -> dict[str, str]:

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


    def _write_to_file(self, data, file_path: Path, method):

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


    def write_fast_log(self, record: dict) -> None:

        values = list(record.values())
        line = json.dumps(values, ensure_ascii=False) + "\n"

        self._write_to_file(line, self._fast_history_json, "a")


    def write_slow_log(self):
        """Перезапись slow-лога последними записями из fast-лога"""

        # читаем все строки из fast-лога (как текст, без парсинга)
        try:
            with open(self._fast_history_json, "r", encoding="utf-8") as f:
                all_lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return  # Если fast-лога нет — ничего не делаем

        # берём последние _MAX_LOG_LINES строк
        last_lines = all_lines[-self._MAX_LOG_LINES:] if all_lines else []

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


    def single_checking(self, email):
        """Проверяет одиночный введенный пользователем email"""
        result = self.check_email(email)
        self.write_fast_log(result)
        self.write_slow_log()


    def multiple_checking(self, path_file: str):
        """Проверяет файл с содержащимся списком email"""
        try:
            with open(path_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    email = line.strip()
                    result = self.check_email(email)
                    self.write_fast_log(result)

        except FileNotFoundError:
            raise FileNotFoundError(f"Файл с email-адресами не найден: {path_file}")
        except OSError as e:
            raise OSError(f"Ошибка при чтении файла {path_file}: {e}")

        # Перезаписываем медленный лог после обработки всех email
        self.write_slow_log()

    
    def _set_slow_history_json_path(self):
        """Устанавливаем путь к медленному логу"""

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