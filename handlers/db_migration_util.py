import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

def copy_collection(source_db, dest_db, collection_name):
    # Копируем все документы из исходной коллекции
    documents = list(source_db[collection_name].find())  # Преобразуем курсор в список
    
     # Вставляем документы в целевую коллекцию
    if len(documents) > 0:
        dest_db[collection_name].insert_many(documents)
        print(f"Скопировано {len(documents)} документов.")
    else:
        print("Исходная коллекция пуста.")

def main():
    client = MongoClient(MONGO_URI)
    # Выбор исходной и целевой баз данных
    source_db = client['test_database']
    dest_db = client['dialogue_database']
    
    # Имя коллекции для копирования
    collection_name = 'users_collection'
    
    try:
        copy_collection(source_db, dest_db, collection_name)
        print(f"Коллекция '{collection_name}' успешно скопирована из source в dest.")
    except Exception as e:
        print(f"Произошла ошибка при копировании коллекции: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()