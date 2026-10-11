# 🚦 Semáforo de señales para MetaTrader 5 + Telegram

Te dice desde el celular, con un semáforo, si una señal vale la pena y qué
probabilidad de ganar tiene, y te muestra todas las señales aprovechables
de todos tus pares.

Ejemplo de aviso (los números son ilustrativos):

```
🟢 VERDE · XAUUSD COMPRA
Vale la pena

🎯 Probabilidad de ganar: 58% (rango 51%–65%)
💰 Valor esperado: +0.45R por operación
⚖️ Necesitas acertar 40% para no perder con R:R 1:1.5

Entrada 2650.30 · SL 2641.10 · TP 2664.10
Lote sugerido: 0.05

Confluencia 78/100 · basado en 112 situaciones parecidas
✅ Tendencia alcista (EMA50 vs EMA200)
✅ ADX 27: tendencia con fuerza a favor
✅ RSI 58: impulso sano
❌ Volatilidad muy baja: el precio puede no llegar al TP
✅ Sesión: Londres+NY
```

| Color | Significado |
|---|---|
| 🟢 **VERDE** | Ganancia esperada positiva **y** con suficiente evidencia en el historial |
| 🟡 **AMARILLO** | Ganancia esperada positiva pero con poca evidencia: entra solo si tu análisis la confirma |
| 🔴 **ROJO** | Pierde en promedio, o hay un bloqueo (spread enorme, cierre de semana) |

---

## ¿Oro u otro par? Cuál es "el mejor"

No hay un par que sea el mejor para todo el mundo: el mejor es **en el que tu
estrategia gana dinero después de pagar el spread de tu bróker**. Eso se mide,
no se adivina. El comando `/ranking` lo calcula con tu historial real
(ejemplo ilustrativo):

```
🏆 Ranking de pares para tu estrategia
1. 🟢 XAUUSD · +0.21R/op · acierto 48%
    410 ops (9.8/semana) · PF 1.4 · caída máx −12.0R
    spread = 4% del stop
2. 🟡 EURUSD · +0.05R/op · acierto 43%
...
```

Para comparar pares fíjate en:

* **R/op (expectativa)**: cuánto ganas en promedio por operación, medido en
  "R" (1R = lo que arriesgas). Es más importante que el % de acierto: un 40 %
  de acierto con R:R 1:2 gana más que un 60 % con R:R 1:0.5.
* **spread = X % del stop**: cuánto te come el costo. Por debajo de 10 % es
  cómodo.
* **caída máx**: la peor racha. Con 1 % de riesgo por operación, −12R son
  −12 % de la cuenta.

Características generales (tu ranking manda sobre esto):

* **Oro (XAUUSD)**: mucho movimiento y tendencias fuertes, bueno para
  intradía. Pero da latigazos violentos con noticias de EE. UU. (NFP, IPC,
  FOMC) y el spread se abre en esos momentos. Si tu sistema ya gana en oro,
  no hay motivo para dejarlo.
* **EURUSD**: el par más líquido y con spread más bajo; movimientos más
  suaves. Bueno para validar una estrategia.
* **GBPUSD / USDJPY**: término medio entre ambos.
* **No operes a la vez pares muy correlacionados** (EURUSD y GBPUSD se
  mueven casi igual): no son dos señales, es la misma apostada dos veces.

Recomendación práctica: deja el oro, agrega 2 o 3 pares en `symbols`, corre
`/ranking` y quédate con los que salgan 🟢.

---

## Cómo se calcula el % de ganar

1. Se mide la "confluencia" de la vela actual (tendencia, fuerza, RSI, MACD,
   volatilidad, sesión) de 0 a 100.
2. Se buscan en el historial de ese mismo par todas las situaciones con una
   confluencia parecida.
3. Desde cada una se simula **tu misma operación** (mismo SL y TP medidos en
   ATR, con el spread actual) y se cuenta cuántas veces tocó el TP antes que
   el SL. Si tocó ambos en la misma vela se cuenta como pérdida.
4. Solo cuentan las situaciones que no se solapan en el tiempo, y con poca
   evidencia el % se acerca al promedio del par.

**Es una estimación sobre el pasado, no una garantía.** Por eso cada señal
queda registrada (también las rojas) y `/resultados` te muestra el acierto real
de las verdes, amarillas y rojas. Si las verdes no ganan más que las amarillas,
el semáforo no te está ayudando con ese par.

> ⚠️ Si tu bot actual solo guarda o muestra las señales que salieron
> ganadoras, su % de acierto está inflado: estás viendo los resultados después
> de conocerlos. Para medir de verdad hay que registrar **todas** las señales
> en el momento en que aparecen, que es lo que hace este programa.

---

## Instalación (en el PC Windows donde tienes MetaTrader 5)

El programa tiene que correr donde está abierta la terminal MT5 (tu PC o un
VPS con Windows). Al celular te llega todo por Telegram. La app MT5 del
celular no puede ejecutar este tipo de programas.

1. Instala Python 3.11 o 3.12 desde <https://www.python.org/downloads/>
   (marca **"Add Python to PATH"**).
2. Descarga este repositorio y abre una terminal en la carpeta.
3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
4. Copia `config.example.toml` como `config.toml` y complétalo:
   * `symbols`: los nombres **exactos** de tu bróker (mira "Observación del
     mercado": puede ser `XAUUSD`, `XAUUSDm`, `GOLD`...).
   * `[telegram] token`: el token de tu bot actual (o crea otro con
     @BotFather).
   * `chat_id`: déjalo vacío, arranca el bot, escríbele cualquier cosa y te
     responderá con tu chat_id. Ponlo en el archivo y vuelve a arrancar.
5. Deja MT5 abierto con tu cuenta iniciada y arranca el bot:
   ```
   python -m semaforo bot
   ```
   (o doble clic en `iniciar_semaforo.bat`).

En MT5 sube el historial disponible: **Herramientas > Opciones > Gráficos >
Máx. barras en el gráfico** a 100000 o más. El cálculo usa 20000 velas (unos
10 meses en M15); con menos, el % se vuelve poco fiable.

### Probar sin MT5 ni Telegram

```
python -m semaforo demo
```

Usa precios simulados (aparece la advertencia en cada mensaje). Sirve solo para
ver cómo funciona.

---

## Comandos desde el celular (Telegram)

| Comando | Qué hace |
|---|---|
| `/senales` | Señales de la estrategia en la última vela cerrada de todos tus pares |
| `/panorama` | Para cada par: la mejor dirección y su color si entraras ahora |
| `/evaluar XAUUSD compra 2650 2640 2670` | Semáforo de tu señal (entrada, SL, TP) |
| `/evaluar XAUUSD venta` | Igual, con el precio actual y el SL/TP por defecto |
| `/ranking` | Qué par le conviene más a la estrategia |
| `/resultados` | Acierto real de las señales registradas, por color |
| `/ayuda` | Lista de comandos |

Además, cada vez que la estrategia del escáner encuentra una señal nueva te
llega un aviso automático (por defecto solo verdes y amarillas; se cambia con
`notify_colors`). El bot solo responde a tu `chat_id`.

Los mismos comandos funcionan en la consola del PC:
`python -m semaforo evaluar XAUUSD compra 2650 2640 2670`.

---

## Conectar las señales de tu bot actual

Si tu bot está en Python, agrega el semáforo a tu mensaje de Telegram:

```python
from semaforo import Semaforo, messages

sem = Semaforo.from_config("config.toml")      # una sola vez al arrancar

# cada vez que tu bot genera una señal:
ev = sem.evaluate("XAUUSD", "compra", entrada, sl, tp)
if ev.color != "ROJO":
    enviar_a_telegram(messages.evaluation(ev))  # o solo ev.color y ev.estimate.p_win
```

Si tu bot es un Expert Advisor en MQL5, la forma más simple es que deje la
señal en un archivo y este programa la lea; sube el código del bot a este
repositorio y se conecta.

El escáner trae una estrategia de ejemplo (retroceso a la EMA20 a favor de la
tendencia) en `semaforo/strategy.py`. Puedes reemplazarla por la lógica de tu
bot para que `/senales` y `/ranking` midan **tu** sistema.

---

## Ajustes importantes (`config.toml`)

| Opción | Por defecto | Para qué |
|---|---|---|
| `timeframe` | `M15` | Temporalidad de las velas |
| `strategy.sl_atr` / `strategy.rr` | 1.5 / 1.5 | SL = 1.5 × ATR, TP = 1.5 × SL |
| `semaforo.ev_green` | 0.20 | Exigencia para VERDE (ganancia esperada en R) |
| `semaforo.min_samples` | 40 | Evidencia mínima para VERDE |
| `semaforo.max_spread_to_sl` | 0.20 | ROJO si el spread se come más del 20 % del stop |
| `risk.risk_pct` | 1.0 | % del balance por operación para el lote sugerido |

---

## Advertencias

* **Esto no abre operaciones**: solo avisa. La decisión es tuya.
* Ningún sistema gana siempre. Arriesga como máximo 0.5–1 % de la cuenta por
  operación: así una mala racha (que llegará) no te saca del mercado.
* El semáforo no lee noticias: revisa el calendario económico antes de entrar,
  sobre todo en oro.
* Antes de confiar en el verde, deja que `/resultados` acumule al menos 30–50
  señales cerradas y compara el acierto real con el estimado.

---

## Para desarrolladores

```
pip install pytest
python -m pytest
```

| Archivo | Contenido |
|---|---|
| `semaforo/engine.py` | Evaluación de señales, colores, escáner y panorama |
| `semaforo/probability.py` | Simulación sobre el historial y cálculo del % |
| `semaforo/features.py` | Indicadores y puntaje de confluencia |
| `semaforo/strategy.py` | Estrategia de ejemplo del escáner |
| `semaforo/backtest.py` | Ranking de pares |
| `semaforo/journal.py` | Registro de señales y resultados reales |
| `semaforo/telegram_bot.py` | Bot y comandos |
| `semaforo/data.py` | Conexión con MT5, CSV y datos demo |
