import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from infrastructure.parsers.minecraft_log_parser import MinecraftLogParser
from pathlib import Path


def test_parser():
    print("🧪 Тестирование парсера логов Minecraft")
    print("=" * 50)

    # 1. Проверка создания демо-логов
    print("\n1. Проверка создания демо-логов...")
    parser = MinecraftLogParser("./test_logs")

    log_file = Path("./test_logs/latest.log")
    if log_file.exists():
        print(f"   ✅ Демо-логи созданы: {log_file}")
        print(f"   Размер файла: {log_file.stat().st_size} байт")
    else:
        print("   ❌ Файл логов не создан")
        return

    # 2. Чтение содержимого
    print("\n2. Содержимое логов (первые 5 строк):")
    with open(log_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f.readlines()[:5]):
            print(f"   {i + 1}. {line.strip()}")

    # 3. Тестирование парсинга игроков
    print("\n3. Тест парсинга игроков онлайн:")
    players = parser.parse_online_players()
    if players:
        print(f"   ✅ Найдено игроков: {len(players)}")
        for player in players:
            print(f"      - {player}")
    else:
        print("   ❌ Игроки не найдены")

    # 4. Тестирование статистики
    print("\n4. Тест парсинга статистики:")
    stats = parser.parse_server_stats()

    required_keys = ['online_players', 'errors_count', 'warnings_count']
    for key in required_keys:
        if key in stats:
            print(f"   ✅ {key}: {stats[key]}")
        else:
            print(f"   ❌ {key} отсутствует")

    # 5. Тестирование поиска
    print("\n5. Тест поиска по логам:")
    test_searches = ['joined', 'ERROR', 'WARN']
    for term in test_searches:
        results = parser.search_logs(term, limit=2)
        if results:
            print(f"   ✅ '{term}': найдено {len(results)} результатов")
        else:
            print(f"   ⚠  '{term}': результатов нет")

    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")

    # Очистка (опционально)
    import shutil
    if Path("./test_logs").exists():
        shutil.rmtree("./test_logs")
        print("📁 Тестовые логи удалены")


if __name__ == "__main__":
    test_parser()