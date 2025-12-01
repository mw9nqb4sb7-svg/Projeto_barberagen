# Scripts Obsoletos

Esta pasta contém scripts antigos que foram **substituídos** pelo script unificado `inicializar_barbearias.py`.

## Scripts Movidos:

- `criar_barbearia_man.py` → Substituído por `inicializar_barbearias.py --completo`
- `criar_segunda_barbearia.py` → Substituído por `inicializar_barbearias.py --completo`
- `criar_usuarios.py` → Substituído por `inicializar_barbearias.py --completo`
- `criar_usuarios_lote.py` → Substituído por `inicializar_barbearias.py --completo`
- `setup.py` → Substituído por `inicializar_barbearias.py --completo`

## Uso do Novo Sistema:

```bash
# Apenas criar barbearias básicas
python inicializar_barbearias.py

# Criar barbearias + super admin + usuários exemplo
python inicializar_barbearias.py --completo

# Verificar estado do banco
python inicializar_barbearias.py --verificar
```

Estes arquivos foram mantidos apenas para referência histórica e podem ser deletados se desejar.
