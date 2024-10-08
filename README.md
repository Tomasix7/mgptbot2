
### Подключение нового пользователя

1. Получить `chat_id` нового пользователя: через команду `/restart` в боте или в меню Настройках Андроид `"Пользователи и аккаунты"/"Номер Телеграм"`
2. В файле config.py добавить новый `chat_id` в `AUTHORIZED_CHAT_IDS`.
3. В файле characters.py добавить новый вложенный объект в объект `CHARACTER_MAP`.
4. Создать новую переменную окружения со значением `chat_id` нового пользователя.
5. Создать новый файл `<newuser_script.py>` в папке `users_scriprs`. Прописать вызов chat_id нового пользователя в виде:  `chat_id = str(os.getenv("CHATID")) # CHARACTER to NEW_USER`.
7. Выполнить деплой новых и измененных файлов на хостинг. 
8. Задать расписание вызова нового файла `<newuser_script.py>`.
9. Проверить вызов файла по расписанию по логам.

### mgptbot - это чат-бот с моделью нейросети через API Telegram 

1. Данный файл-инструкция применим к приложениям: 
	- mgptbot
	- mgptbot2
	- mgptbot_test

2. Если в какое-то из перечисленных приложений внесены изменения, которые нужно применить к остальным приложениям группы, то можно просто скопировать все файлы приложения-лидера в папку приложения-получателя.

> [!warning] 
> Не нужно удалять папки prompts2 в mgptbot2 и файлы .env


3. Файлы .env не влияют на работу приложения на сервере, но в них могут быть отличия по значениям переменных окружения, которые влияют на работу при пробных локальных запусках.

4. При нормальном положении дел локальный запуск и тесты лучше делать в приложении mgptbot_test.

5. Отличия в приложениях:
	- Ключ ТГ бота
	- Название базы данных
	- Название коллекции базы данных
	- В тестовом приложении за чат номером администратора закреплен другой характер. 
		
6. Все переменные, необходимые для различий в работе приложений получаются из ключей на серверах. Названия ключей везде одинаковые, поэтому после деплоя, они получают свои значения так, как они определены в настройках сервера.

7. Список файлов, использующих переменные окружения:
	- users_scripts (все скрипты в папке)
	- app.py
	- config.py
	- dialogue_storage.py
	- unsplash_functions.py


| Key         | @mygpt721_bot                                                                                                                        | @runimara_bot                                                                                                                          | @yofriend_bot                                                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| SERVER      | Heroku                                                                                                                               | Render                                                                                                                                 | Local                                                                                                                              |
| TELKEY      | `7169178697:AAHU4qpbWioOmqqaeFmG2gg0uHtua6WvvcA`                                                                                     | `6758936853:AAHRu5q5Jg5ddxmwfzOYzSsRuWD0LtS2xco`                                                                                       | `7099589470:AAG3tfCwbwBhi4d9eVXswaruDcGkrS2-f8w`                                                                                   |
| MONGO_URI   | `mongodb+srv://luminiaruni:Sn9Pg5G6sQ6cPvKI@cluster0.0zku6.mongodb.net/heroku_dialogue?retryWrites=true&w=majority&appName=Cluster0` | `mongodb+srv://luminiaruni:Sn9Pg5G6sQ6cPvKI@cluster0.0zku6.mongodb.net/dialogue_database?retryWrites=true&w=majority&appName=Cluster0` | `mongodb+srv://luminiaruni:Sn9Pg5G6sQ6cPvKI@cluster0.0zku6.mongodb.net/test_database?retryWrites=true&w=majority&appName=Cluster0` |
| DBASE       | heroku_dialogue                                                                                                                      | dialogue_database                                                                                                                      | test_database                                                                                                                      |
| DCOLLECTION | ula                                                                                                                                  | dialogs                                                                                                                                | margo                                                                                                                              |
| WEBHOOK_URL | `https://mgptbot-app-faae879a9e48.herokuapp.com/`                                                                                    | `https://mgptbot2.onrender.com/`                                                                                                       | no                                                                                                                                 |


| Key    | Value                                                    | Note     | Model           |
| :----- | :------------------------------------------------------- | :------- | :-------------- |
| UNSKEY | QSber4N0pqeXdCOJJRD7C-dKd-lssL1MT6LpvrGDp1c              | Unsplash |                 |
| CLIKEY | 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 | Groq     | lLama3-70b-8192 |


| Номер чата. Key    | Chat ID    | Note       |
| ------------------ | ---------- | ---------- |
| CHATID             | 514396790  | Own        |
| CHAT_ID_GREEN_OCEA | 5378562535 | Green Ocen |
| ALIYA_ID           | 1309731434 | Aliya      |
