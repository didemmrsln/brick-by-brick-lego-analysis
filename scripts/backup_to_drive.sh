#!/bin/zsh
# Projeyi Google Drive for Desktop klasörüne yedekler (Drive'da: brick_by_brick/proje_yedek).
# launchd günlük çekimden sonra çağırır; elle de çalıştırılabilir:
#   zsh scripts/backup_to_drive.sh
#
# - venv, .git (GitHub'da zaten var), .env (API anahtarları) ve ayrı projeler kopyalanmaz.
# - --delete kullanılmaz: yerelde silinen bir dosya Drive'da kalır (yedek amaçlı).

PROJECT_ROOT="${0:A:h:h}"
LOG="$PROJECT_ROOT/logs/drive_backup.log"
mkdir -p "$PROJECT_ROOT/logs"

# Arayüz diline göre klasör adı "My Drive" ya da "Drive'ım" olur; (N) = eşleşme yoksa boş liste
drives=( "$HOME"/Library/CloudStorage/GoogleDrive-*/("My Drive"|"Drive'ım")(N/) )
DRIVE_ROOT="${drives[1]}"
if [[ -z "$DRIVE_ROOT" ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') Google Drive for Desktop bulunamadı — yedek atlandı." >> "$LOG"
    exit 0
fi

DEST="$DRIVE_ROOT/brick_by_brick/proje_yedek"
mkdir -p "$DEST"

if rsync -a \
    --exclude 'venv/' --exclude '.git/' --exclude '.env' \
    --exclude 'data-seaborn-regression/' \
    --exclude '__pycache__/' --exclude '.ipynb_checkpoints/' --exclude '.DS_Store' \
    "$PROJECT_ROOT/" "$DEST/" 2>> "$LOG"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') Yedek tamam → $DEST ($(du -sh "$DEST" | cut -f1))" >> "$LOG"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') HATA: rsync başarısız (ayrıntı yukarıda)." >> "$LOG"
    exit 1
fi
