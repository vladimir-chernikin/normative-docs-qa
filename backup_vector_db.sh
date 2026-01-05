#!/bin/bash
# Скрипт резервного копирования векторной базы данных QA System

# Настройки
BACKUP_DIR="/home/olga/backups/qa-system"
VECTOR_DB_DIR="/home/olga/normativ_docs/Волков/vector-db-test/vectordb/unified_all_docs_e5"
SOURCE_DOCS_DIR="/home/olga/normativ_docs/Волков/fulldocx"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="vector_db_${TIMESTAMP}"

echo "=============================================="
echo "Резервное копирование QA System"
echo "Время: $(date)"
echo "=============================================="

# Создаем директорию для бекапов
echo "1. Создание директории для бекапов..."
mkdir -p "${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}/vector_db"
mkdir -p "${BACKUP_DIR}/source_docs"

# Резервное копирование векторной БД
echo "2. Резервное копирование векторной БД..."
if [ -d "${VECTOR_DB_DIR}" ]; then
    tar -czf "${BACKUP_DIR}/vector_db/${BACKUP_NAME}.tar.gz" -C "${VECTOR_DB_DIR}" .
    if [ $? -eq 0 ]; then
        SIZE=$(du -h "${BACKUP_DIR}/vector_db/${BACKUP_NAME}.tar.gz" | cut -f1)
        echo "   ✓ Векторная БД сохранена: ${BACKUP_NAME}.tar.gz (${SIZE})"
    else
        echo "   ✗ Ошибка при создании архива векторной БД"
        exit 1
    fi
else
    echo "   ✗ Директория векторной БД не найдена: ${VECTOR_DB_DIR}"
    exit 1
fi

# Резервное копирование исходных документов
echo "3. Резервное копирование исходных документов..."
tar -czf "${BACKUP_DIR}/source_docs/source_docs_${TIMESTAMP}.tar.gz" -C "${SOURCE_DOCS_DIR}" .
if [ $? -eq 0 ]; then
    SIZE=$(du -h "${BACKUP_DIR}/source_docs/source_docs_${TIMESTAMP}.tar.gz" | cut -f1)
    echo "   ✓ Исходные документы сохранены: source_docs_${TIMESTAMP}.tar.gz (${SIZE})"
else
    echo "   ✗ Ошибка при создании архива исходных документов"
fi

# Удаляем старые бекапы (оставляем последние 10)
echo "4. Очистка старых бекапов (оставляем последние 10)..."
ls -t "${BACKUP_DIR}/vector_db"/vector_db_*.tar.gz | tail -n +11 | xargs -r rm --
ls -t "${BACKUP_DIR}/source_docs"/source_docs_*.tar.gz | tail -n +11 | xargs -r rm --
echo "   ✓ Старые бекапы удалены"

# Создаем манифест бекапа
echo "5. Создание манифеста бекапа..."
cat > "${BACKUP_DIR}/backup_manifest_${TIMESTAMP}.txt" << EOF
Backup Manifest - QA System
=========================
Date: $(date)
Timestamp: ${TIMESTAMP}
Backup Name: ${BACKUP_NAME}

Files:
- Vector DB: ${BACKUP_NAME}.tar.gz
- Source Docs: source_docs_${TIMESTAMP}.tar.gz

Database Info:
- Path: ${VECTOR_DB_DIR}
- Size: $(du -sh ${VECTOR_DB_DIR} | cut -f1)

Source Docs Info:
- Path: ${SOURCE_DOCS_DIR}
- Size: $(du -sh ${SOURCE_DOCS_DIR} | cut -f1)
- Files: $(find ${SOURCE_DOCS_DIR} -type f | wc -l)

Storage:
- Backup Dir: ${BACKUP_DIR}
- Total Size: $(du -sh ${BACKUP_DIR} | cut -f1)
- Backup Files: $(find ${BACKUP_DIR} -type f | wc -l)
EOF

echo "   ✓ Манифест создан: backup_manifest_${TIMESTAMP}.txt"

echo ""
echo "=============================================="
echo "Резервное копирование завершено успешно!"
echo "=============================================="
echo "Бекап сохранен в: ${BACKUP_DIR}"
echo "Последние бекапы:"
ls -lh "${BACKUP_DIR}/vector_db"/ | tail -5
echo ""
echo "Для восстановления:"
echo "  tar -xzf ${BACKUP_DIR}/vector_db/${BACKUP_NAME}.tar.gz -C ${VECTOR_DB_DIR}"
echo "=============================================="
