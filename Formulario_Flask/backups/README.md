# Pasta de Backups

Esta pasta é destinada para armazenar backups do banco de dados.

## 📦 Como fazer backup

### Manual
```bash
copy meubanco.db backups\meubanco_backup_YYYYMMDD.db
```

### Automático (futuro)
Será criado script para backup automático.

## ⚠️ Importante

- Faça backups regulares antes de:
  - Migrações do banco
  - Atualizações importantes
  - Deploy em produção
  
- Mantenha backups recentes
- Teste a restauração periodicamente

## 🔄 Como restaurar

```bash
copy backups\meubanco_backup_YYYYMMDD.db meubanco.db
```

**Atenção:** Isso substituirá o banco atual!
