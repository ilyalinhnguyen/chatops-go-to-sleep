from aiogram.fsm.context import FSMContext

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("ru", "en")
LANGUAGE_KEY = "language"
PENDING_FIRST_LANGUAGE_KEY = "pending_first_language"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        "language_ru": "Русский",
        "language_en": "English",
        "choose_language": "Выбери язык интерфейса.",
        "language_changed": "Язык изменен.",
        "welcome_fun_line": "🚀✨🛠️⚙️🐳☸️💫",
        "menu_welcome": (
            "Привет! 👋\n\n"
            "Добро пожаловать! Это бот команды motorscrewdriver.\n"
            "Он позволяет управлять Kubernetes-кластером прямо из Telegram.\n\n"
            "Выбери действие ниже — и поехали! 🎯"
        ),
        "menu_deployments": "Деплойменты",
        "menu_pods": "Поды",
        "menu_restart": "Рестарт",
        "menu_rollback": "Откат",
        "menu_scale": "Скейл",
        "menu_status": "Статус",
        "menu_language": "Язык",
        "menu_history": "История действий",
        "actions_password_prompt": "Введите пароль для этой операции:",
        "actions_password_wrong": "Неверный пароль. Попробуйте ещё раз.",
        "history_title": "Последние действия",
        "history_hint": "Меньший номер записи — новее. Внутри блока: сначала команда, затем ответ.",
        "history_label_command": "Команда",
        "history_label_result": "Ответ",
        "history_record_heading": "Запись {n}",
        "history_empty": "Пока нет записей в истории.",
        "history_close": "Закрыть",
        "back_home_button": "Вернуться на главную",
        "back_home_prompt": "Готово. Нажми кнопку, чтобы вернуться в главное меню.",
        "internal_error": "Внутренняя ошибка.",
        "operation_cancelled": "Операция отменена.",
        "invalid_selection": "Некорректный выбор.",
        "could_not_load_deployments": "Не удалось загрузить деплойменты.",
        "deployments_prompt": "Отправь имя деплоймента или нажми кнопку ниже, чтобы получить список всех.",
        "deployments_choose_deployment": "Выбери деплоймент или нажми «Показать все».",
        "return_all": "Показать все",
        "cancel": "Отмена",
        "yes": "Да",
        "no": "Нет",
        "pods_invalid_usage": "`/pods [NAMESPACE]`",
        "nodes_loading_failed": "Не удалось получить узлы.",
        "namespaces_loading_failed": "Не удалось получить namespace'ы.",
        "deployments_invalid_usage": "`/deployments <NAME>`",
        "restart_choose_deployment": "Выбери деплоймент для рестарта:",
        "restart_requested": "🔁 Запрошен рестарт {namespace}:{name}.",
        "restart_invalid_usage": "`/restart <NAMESPACE>:<NAME>`",
        "rollback_choose_deployment": "Выбери деплоймент для отката:",
        "rollback_confirm": "Точно откатить `{name}` в `{namespace}`?",
        "rollback_in_progress": "Откатываю, подожди...",
        "rollback_missing_data": "Не хватает данных для отката.",
        "rollback_no_revision": "Для деплоймента не найдена ревизия.",
        "rollback_requested": "⏪ Запрошен откат {namespace}:{name}.",
        "rollback_invalid_usage": "`/rollback <NAMESPACE>:<NAME>`",
        "scale_choose_deployment": "Выбери деплоймент для масштабирования:",
        "scale_now_replicas": "Сейчас: задано реплик: {replicas}, готовых подов: {ready}.",
        "scale_selected_send_replicas": (
            "Выбран `{namespace}:{name}`. Отправь количество реплик (например, `2`)."
        ),
        "scale_send_non_negative_int": "Отправь неотрицательное целое количество реплик.",
        "validation_number_digits_only": (
            "Нужно одно целое число цифрами (например, 2). Без букв, слов и дробей."
        ),
        "validation_k8s_name": (
            "Некорректное имя: только строчные латинские буквы, цифры и дефис, до 63 символов."
        ),
        "scale_missing_selection": "Не выбран деплоймент.",
        "scale_done": "⚖️ Масштабировал {namespace}:{name} до {replicas} реплик.",
        "scale_invalid_usage": "`/scale <NAMESPACE>:<NAME> <REPLICAS>`",
        "status_choose_deployment": "Выбери деплоймент для проверки статуса:",
        "status_invalid_usage": "`/status <NAMESPACE>:<NAME>`",
    },
    "en": {
        "language_ru": "Русский",
        "language_en": "English",
        "choose_language": "Choose interface language.",
        "language_changed": "Language updated.",
        "welcome_fun_line": "🚀✨🛠️⚙️🐳☸️💫",
        "menu_welcome": (
            "Hey there! 👋\n\n"
            "Welcome! This is a bot by the motorscrewdriver team.\n"
            "It lets you manage a Kubernetes cluster right from Telegram.\n\n"
            "Pick an action below — let's ship it! 🎯"
        ),
        "menu_deployments": "Deployments",
        "menu_pods": "Pods",
        "menu_restart": "Restart",
        "menu_rollback": "Rollback",
        "menu_scale": "Scale",
        "menu_status": "Status",
        "menu_language": "Language",
        "menu_history": "Action history",
        "actions_password_prompt": "Enter the password for this operation:",
        "actions_password_wrong": "Wrong password. Try again.",
        "history_title": "Recent actions",
        "history_hint": "Lower record number = newer. Inside: command first, then answer.",
        "history_label_command": "Command",
        "history_label_result": "Answer",
        "history_record_heading": "Record {n}",
        "history_empty": "No history yet.",
        "history_close": "Close",
        "back_home_button": "Back to main menu",
        "back_home_prompt": "Done. Press the button to return to the main menu.",
        "internal_error": "Internal error.",
        "operation_cancelled": "Operation cancelled.",
        "invalid_selection": "Invalid selection.",
        "could_not_load_deployments": "Could not load deployments.",
        "deployments_prompt": "Send deployment name or press button below to return all deployments.",
        "deployments_choose_deployment": "Pick a deployment or press «Return all».",
        "return_all": "Return all",
        "cancel": "Cancel",
        "yes": "Yes",
        "no": "No",
        "pods_invalid_usage": "`/pods [NAMESPACE]`",
        "nodes_loading_failed": "Could not fetch nodes.",
        "namespaces_loading_failed": "Could not fetch namespaces.",
        "deployments_invalid_usage": "`/deployments <NAME>`",
        "restart_choose_deployment": "Choose deployment to restart:",
        "restart_requested": "🔁 Restart requested for {namespace}:{name}.",
        "restart_invalid_usage": "`/restart <NAMESPACE>:<NAME>`",
        "rollback_choose_deployment": "Choose deployment to rollback:",
        "rollback_confirm": "Are you sure you want to roll back `{name}` in `{namespace}`?",
        "rollback_in_progress": "Rolling back, please wait...",
        "rollback_missing_data": "Missing rollback data.",
        "rollback_no_revision": "No revision found for deployment.",
        "rollback_requested": "⏪ Rollback requested for {namespace}:{name}.",
        "rollback_invalid_usage": "`/rollback <NAMESPACE>:<NAME>`",
        "scale_choose_deployment": "Choose deployment to scale:",
        "scale_now_replicas": "Right now: desired replicas: {replicas}, ready pods: {ready}.",
        "scale_selected_send_replicas": (
            "Selected `{namespace}:{name}`. Send replicas count (e.g. `2`)."
        ),
        "scale_send_non_negative_int": "Send a non-negative integer replicas count.",
        "validation_number_digits_only": (
            "Send one non-negative integer as digits only (e.g. 2). No words or decimals."
        ),
        "validation_k8s_name": (
            "Invalid name: lowercase Latin letters, digits, hyphens only, up to 63 characters."
        ),
        "validation_number_digits_only": (
            "Send one non-negative integer as digits only (e.g. 2). No words or decimals."
        ),
        "validation_k8s_name": (
            "Invalid name: lowercase Latin letters, digits, hyphens only, up to 63 characters."
        ),
        "scale_missing_selection": "Missing deployment selection.",
        "scale_done": "⚖️ Scaled {namespace}:{name} to {replicas} replicas.",
        "scale_invalid_usage": "`/scale <NAMESPACE>:<NAME> <REPLICAS>`",
        "status_choose_deployment": "Choose deployment to check status:",
        "status_invalid_usage": "`/status <NAMESPACE>:<NAME>`",
    },
}


async def get_language(state: FSMContext) -> str | None:
    data = await state.get_data()
    if LANGUAGE_KEY not in data:
        return None
    language = data[LANGUAGE_KEY]
    if language not in SUPPORTED_LANGUAGES:
        return None
    return language


async def get_effective_language(state: FSMContext) -> str:
    language = await get_language(state)
    return language if language is not None else DEFAULT_LANGUAGE


async def set_language(state: FSMContext, language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    await state.update_data(**{LANGUAGE_KEY: language})


def tr_by_lang(language: str, key: str, **kwargs: object) -> str:
    lang_map = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE])
    template = lang_map.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    return template.format(**kwargs)


async def tr(state: FSMContext, key: str, **kwargs: object) -> str:
    language = await get_effective_language(state)
    return tr_by_lang(language, key, **kwargs)
