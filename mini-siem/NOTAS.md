# Notas del Proyecto — Mini-SIEM

## Configuración de correo (notifier.py)

El módulo de notificaciones funciona con cualquier proveedor de correo.
Solo hay que cambiar el servidor SMTP en `notifier.py`:

```python
with smtplib.SMTP("smtp.tudominio.com", 587) as servidor:
```

### Referencia de servidores SMTP comunes

| Proveedor         | Servidor SMTP              | Puerto |
|-------------------|----------------------------|--------|
| Gmail             | `smtp.gmail.com`           | 587    |
| Outlook / Hotmail | `smtp.office365.com`       | 587    |
| Yahoo             | `smtp.mail.yahoo.com`      | 587    |
| Correo corporativo| Preguntar a TI             | Varía  |

### Para correo corporativo

El servidor SMTP interno varía por empresa. Solicitar a TI:
- Dirección del servidor SMTP (ej. `smtp.empresa.com`)
- Puerto (comúnmente 587, 465 o uno personalizado)
- Si requiere conexión VPN para enviar correos desde scripts externos

### Credenciales

Siempre guardar en el archivo `.env` — nunca en el código:

```
EMAIL_REMITENTE=tucorreo@dominio.com
EMAIL_PASSWORD=contraseña_de_aplicacion
EMAIL_DESTINATARIO=destinatario@dominio.com
```

> El archivo `.env` está en `.gitignore` y nunca se sube a GitHub.
