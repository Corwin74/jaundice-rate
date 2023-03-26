# Фильтр желтушных новостей
Данный проект это бекенд к плагину браузера. Задача плагина — просканировать страницу новостного сайта и найти все ссылки на статьи. Дальше в дело вступает веб-сервис: он скачивает текст статьи, проводит анализ и выносит свой вердикт — присваивает рейтинг желтушности. Информация передается обратно в плагин и тот отображает рейтинг прямо на странице новостного сайта.

Пока поддерживается только один новостной сайт - [ИНОСМИ.РУ](https://inosmi.ru/). Для него разработан специальный адаптер, умеющий выделять текст статьи на фоне остальной HTML разметки. Для других новостных сайтов потребуются новые адаптеры, все они будут находиться в каталоге `adapters`. Туда же помещен код для сайта ИНОСМИ.РУ: `adapters/inosmi_ru.py`.

В перспективе можно создать универсальный адаптер, подходящий для всех сайтов, но его разработка будет сложной и потребует дополнительных времени и сил.

# Как установить

Вам понадобится Python версии 3.7 или старше. Для установки пакетов рекомендуется создать виртуальное окружение.

Первым шагом установите пакеты:

```python3
pip install -r requirements.txt
```
Фильтр загружает список "заряженных" слов из файла `negative_words.txt`, расположенного в подкаталоге `charged_dict`. Формат файла:  
```txt
авария
авиакатастрофа
ад
аннуляция
аутсайдер
банкротство
бегство
бедность
бес
```  
# Как запустить

```python3
python server.py
```  
Запустится сервер по адресу: `http://127.0.0.1:8080`. Сервер принимает переменную `urls` через адресную строку, в качестве значения перечисленны ссылки на статьи, которые необходимо проверить, перечисленные через запятую:  
`http://127.0.0.1:8080/?urls=https://inosmi.ru/20230322/kitay-261582482.html,https://inosmi.ru/20230323/ukraina-261622481.html`  
Количество ссылок в одном запросе ограничено 10.  
После анализа сервер ответит в формате JSON:
```json
[  
{"status": "FETCH_ERROR", "url": "https://inosmi.ru/20230323/ukraina-261622481.ht", "score": null, "word_count": null},  
{"status": "OK", "url": "https://inosmi.ru/20230322/kitay-261582482.html", "score": 0.32, "word_count": 621}  
]
```  
Чем выше значение `score`, тем выше "желтушность" статьи.
# Как запустить тесты

Для тестирования используется [pytest](https://docs.pytest.org/en/latest/), тестами покрыты фрагменты кода сложные в отладке: функция process_article, text_tools.py и адаптеры. Команды для запуска тестов:

```
python -m pytest adapters/inosmi_ru.py
```

```
python -m pytest text_tools.py
```
```
python -m pytest server.py
```
# Цели проекта

Код написан в учебных целях. Это урок из курса по веб-разработке — [Девман](https://dvmn.org).
