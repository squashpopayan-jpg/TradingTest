# Prompt: probar el método de Oliver Velez en el oro (XAUUSD) con MetaTrader 5

## Cómo usar este prompt

1. Abre **Claude Code** (u otra IA que pueda leer tu código y ejecutar Python) **en la carpeta de tu aplicación**, en el PC donde tienes MetaTrader 5.
2. Deja MetaTrader 5 abierto e iniciado. Si puedes, usa una **cuenta demo del mismo bróker**: los precios y spreads son casi iguales y no arriesgas nada.
3. Copia **todo** el bloque de abajo (desde "INICIO DEL PROMPT" hasta "FIN DEL PROMPT") y pégalo como primer mensaje.
4. Antes de que empiece, ten a mano la **comisión por lote** que te cobra tu bróker en el oro (si no la sabes, el prompt le pide a la IA que la calcule de tu historial).

Si la IA que uses no puede ejecutar código, pídele que te entregue los archivos y córrelos tú. Te pedirá pegarle los resultados.

---

```text
==================== INICIO DEL PROMPT ====================

# Rol
Eres un desarrollador cuantitativo riguroso y escéptico. Tu trabajo NO es hacer que una estrategia
parezca rentable: es averiguar con datos reales, después de costos, si el método de trading de
Oliver Velez tiene ventaja (expectativa positiva) en el oro (XAUUSD) con MI bróker, y darme un
veredicto honesto. Un "no funciona" bien demostrado es un resultado igual de valioso que un "sí".

# Contexto
- Opero oro en MetaTrader 5 con cuenta real. Tengo en este PC una aplicación propia (esta carpeta)
  que se conecta a MT5 y me envía señales por Telegram.
- Quiero probar el método que Oliver Velez enseña en YouTube (@OliverVelezTrading y
  @OliverVelezTradingEnEspañol): medias simples de 20 y 200, "velas elefante", "Bull/Bear 180",
  "Red/Green Bar Ignored", retrocesos a la media de 20 y colas.
- Sus videos prometen cifras como "82 %", "84 %" o "87 %" de acierto, sin metodología publicada.
  Quiero comprobarlas también.
- Advertencias que debes tener presentes:
  * Velez diseñó el método para ACCIONES de EE. UU. en la apertura de Nueva York, con velas de
    2 minutos. No hay material suyo específico para oro: hay que adaptar, y cada adaptación es
    una decisión nuestra, no de él.
  * Las reglas exactas no están publicadas por él: lo que sigue son interpretaciones públicas
    (indicadores de TradingView, resúmenes, sus manuales). Por eso los umbrales ambiguos se
    prueban como VARIANTES declaradas de antemano, no se ajustan mirando resultados.

# Reglas de seguridad (NO negociables)
1. PROHIBIDO enviar, modificar o cerrar órdenes. No llames a mt5.order_send, order_check con
   intención de operar, ni a ninguna función de mi app que opere. Solo lectura: copy_rates_*,
   copy_ticks_*, symbol_info*, account_info, history_deals_get.
2. No imprimas, guardes ni subas a ningún lado contraseñas, tokens de Telegram ni números de cuenta.
   Usa la sesión de MT5 que ya está abierta: mt5.initialize() sin login si funciona.
3. No modifiques el comportamiento actual de mi bot. Trabaja en una carpeta nueva
   (por ejemplo `investigacion_velez/`) y, si es un repositorio git, en una rama nueva.
4. Pídeme permiso antes de instalar dependencias que no sean numpy, pandas, matplotlib, pyarrow
   y MetaTrader5.
5. Si algo de este prompt choca con lo que ves en mi código o en los datos, PARA y pregúntame.

# Paso 0 — Reconocimiento (repórtame antes de programar nada)
1. Revisa mi aplicación: lenguaje, cómo se conecta a MT5, qué símbolo usa, si ya tiene funciones
   para descargar velas que puedas reutilizar.
2. Con MT5 (solo lectura) averigua y anota:
   - Nombre exacto del símbolo del oro en mi bróker (XAUUSD, XAUUSDm, GOLD, XAUUSD.r…).
   - digits, point, trade_tick_size, trade_tick_value, trade_contract_size, volume_min/step.
   - swap_long, swap_short, swap_mode y el día de swap triple (swap_rollover3days).
   - Desfase horario del servidor respecto a UTC (compara el time del último tick con la hora UTC
     real) y si el bróker cambia de horario con el de Nueva York (muchos usan GMT+2/GMT+3 para que
     las 17:00 de Nueva York sean las 00:00 del servidor). Verifícalo mirando a qué hora del
     servidor ocurre la pausa diaria del oro en distintas épocas del año.
   - Comisión real por lote: deriva el valor de mi historial con mt5.history_deals_get (campo
     commission de mis operaciones de oro) y confírmamelo. Si no hay historial, pregúntame.
   - Spread típico por hora del día (mediana y percentil 90), usando ticks de al menos 2 semanas.
3. Muéstrame un plan corto con lo que vas a construir y espera mi "OK".

# Paso 1 — Datos
1. Descarga velas de XAUUSD con mt5.copy_rates_range en trozos mensuales (para no chocar con el
   límite de barras), en estas temporalidades:
   - M2 y M5: todo lo disponible, mínimo 6 meses (MT5 tiene TIMEFRAME_M2: es la temporalidad
     original de Velez).
   - M15 y H1: mínimo 2 años, idealmente 3 o más.
   Si MT5 entrega menos historia, dime cuánta hay; la solución suele ser subir
   Herramientas > Opciones > Gráficos > "Máx. barras en el gráfico" y desplazar el gráfico para que
   el terminal descargue historia.
2. Guarda cada serie en Parquet o CSV con: time (hora del servidor), open, high, low, close,
   tick_volume, spread (en puntos y convertido a precio).
3. Control de calidad y repórtalo: barras duplicadas, huecos fuera del fin de semana y la pausa
   diaria, barras con spread 0 o absurdo, picos de spread en el rollover diario.
4. Crea columnas de tiempo en UTC y en hora de Nueva York (America/New_York, con cambio de horario
   de verano). Todas las sesiones se definen en hora de Nueva York.
5. El campo spread de las barras de MT5 no siempre representa el spread medio de la barra.
   Compara, para 5 días de muestra, el spread de las barras con el de los ticks y decide qué
   usar. Si el de las barras subestima, usa el spread mediano de ticks por hora del día.

# Paso 2 — El método, en reglas exactas

## Indicadores (calculados SOLO con velas cerradas)
- SMA20 y SMA200 del cierre (medias SIMPLES, no exponenciales). SMA8 para el trailing.
- ATR(14) de Wilder: NO es parte del método de Velez. Lo usamos solo para trasladar a oro las
  distancias que él da en "centavos por acción".
- rango(t) = high − low; cuerpo(t) = |close − open|; rango_medio(t) = media del rango de las
  N velas anteriores a t (sin incluir t), N = 10.
- buffer = max(spread_actual, 0.05 × ATR). Es la traducción de su "un centavo más allá".

## Filtro de contexto: el "estado" 20/200 (no genera entradas)
- Largos solo si: close > SMA20 > SMA200 y la SMA20 sube (SMA20(t) > SMA20(t−5)).
- Cortos solo si: close < SMA20 < SMA200 y la SMA20 baja.
- Si el precio está entre la SMA20 y la SMA200: no se opera.
- "Narrow state" (medias juntas): |SMA20 − SMA200| < 0.5 × ATR.

## Setups (detectores con la vela t ya cerrada; la orden se pone para la vela t+1)
S1 — Vela elefante ("igniting bar") a favor del estado
  - rango(t) ≥ k × rango_medio(t), con k ∈ {1.5, 2.0} (variantes declaradas).
  - cuerpo(t) ≥ 0.6 × rango(t), y del color del estado (verde para largos).
  - Ubicación: la vela nace cerca de una media: su low (largos) está a ≤ 0.5 × ATR de la SMA20 o de
    la SMA200.
  - Entrada: orden stop en high(t) + buffer (largos) / low(t) − buffer (cortos), válida solo en la
    vela t+1. Si no se activa, se cancela.
  - Stop inicial: low(t) − buffer (largos) / high(t) + buffer (cortos).

S2 — Bull 180 / Bear 180 (dos velas)
  - Vela de control t−1: bajista (para Bull 180), cuerpo ≥ 0.5 × rango, rango ≥ rango_medio.
  - Vela t: alcista, cuerpo ≥ 0.5 × rango y cierra por encima del open de t−1 (envuelve su cuerpo).
  - Ubicación: alguna de las dos velas toca o está a ≤ 0.5 × ATR de la SMA20 o la SMA200.
  - Variante A: exige el estado 20/200 a favor (continuación tras retroceso).
    Variante B: sin filtro de estado (reversión pura).
  - Entrada: stop en high(t) + buffer. Stop inicial: min(low(t−1), low(t)) − buffer.
  - Bear 180: espejo exacto.

S3 — Red Bar Ignored (RBI) / Green Bar Ignored (GBI)
  - Estado largo. Vela de control c = t−1: alcista, rango ≥ rango_medio, cuerpo ≥ 0.6 × rango.
  - Vela ignorada t: bajista, rango ≤ 0.5 × rango(c), y su cuerpo completo en el tercio superior de c
    (min(open,close) de t ≥ low(c) + 2/3 × rango(c)).
  - Entrada: stop en high(t) + buffer. Stop inicial: low(t) − buffer.
  - GBI: espejo para cortos.

S4 — Retroceso a la SMA20 ("beso de la 20")
  - Estado largo con la SMA20 subiendo.
  - Retroceso: entre 3 y 5 velas seguidas con máximos descendentes justo antes de t.
  - La vela t toca la media (low(t) ≤ SMA20 + 0.1 × ATR) pero cierra por encima (close(t) > SMA20).
  - Entrada: stop en high(t) + buffer. Stop inicial: mínimo del retroceso − buffer.
  - Variante: exigir además que t sea vela de giro (cola inferior ≥ 2/3 del rango, o un Bull 180).

S5 — Cola de giro (bottoming / topping tail)
  - Cola inferior (largos) ≥ 2/3 del rango de la vela.
  - Variante A (agotamiento): la vela está a ≥ 2 × ATR por debajo de la SMA20. Objetivo fijo: SMA20.
  - Variante B (continuación): aparece al final de un retroceso a la SMA20 en estado largo (como S4).
  - Entrada: stop en high(t) + buffer. Stop inicial: low(t) − buffer.

S6 — Salida del narrow state (exploratoria)
  - Hubo narrow state en alguna de las 20 velas previas, y ahora aparece S1 o S2 a favor del nuevo
    orden de las medias. Entrada y stop como en S1/S2.

S7 — Adaptación de la "trampa de apertura" / Fabulous 4 (exploratoria, es una invención nuestra)
  - Ancla = 9:30 de Nueva York (apertura del mercado de acciones).
  - Caja = [mínimo, máximo] de: SMA20, SMA200, cierre de las 17:00 NY del día anterior, y máximo y
    mínimo de los últimos 45 minutos antes de las 17:00 NY del día anterior.
  - Si el precio a las 9:30 está dentro de la caja: no se opera ese día (trampa).
    Si está por encima: solo largos con S1, S2 o S4 entre 9:30 y 11:00 NY. Si está por debajo, solo cortos.

## Gestión de la operación (modelos de salida declarados)
- E1 "estilo Velez":
  * Riesgo máximo de una vela: si el stop inicial está a más de 3 × ATR, la operación se descarta.
  * Cuando cierran 2 velas a favor por encima del precio de entrada, el stop pasa a seguir vela a
    vela (debajo del low de la vela anterior − buffer).
  * Toma 50 % en +1R; el resto sigue con el trailing.
- E2 "fijo": take profit en 1.5R (variante 2R), sin trailing.
- E3 "media": salida al primer cierre por debajo de la SMA20 (largos) o por encima (cortos).
- Para todas: en M2/M5 cierre obligatorio a las 16:00 NY (Velez no deja operaciones de un día para
  otro). En M15/H1: máximo 48 velas abiertas, y se cobra swap si cruza el rollover (triple el día
  que indique el bróker).

## Modelo de ejecución (aquí se esconden casi todos los errores: hazlo con cuidado)
- Las velas de MT5 son precio BID. Compra: entra al ASK (bid + spread) y su SL/TP se evalúa sobre
  el BID. Venta: entra al BID y sale al ASK (el SL/TP se evalúa sobre bid + spread).
- Órdenes stop: se llenan en el nivel de activación + deslizamiento (0 en el escenario base). Si la
  vela abre más allá del nivel (hueco), se llenan al open.
- Si en una misma vela se tocan el stop y el objetivo, asume que se tocó PRIMERO EL STOP. Para las
  pruebas principales, resuelve esos casos con velas M1 o ticks si están disponibles.
- Una sola operación abierta a la vez por setup. Sin piramidar.
- Cobra la comisión real por lote en cada operación, convertida a precio.
- Sin mirar al futuro: cualquier cálculo de la vela t usa solo datos hasta t. Escribe un test que lo
  demuestre: modifica velas posteriores a t y comprueba que la señal en t no cambia.

# Paso 3 — Protocolo para no engañarnos
1. Declaración previa: antes de ver ningún resultado, guarda en un archivo la lista exacta de
   pruebas y parámetros. Hay dos grupos:
   - PRINCIPALES (son las que deciden el veredicto): S1, S2-A y S4, con salida E1, en dos escenarios:
     * M5 de 9:30 a 11:30 NY (lo más parecido al "trade the open" de Velez).
     * M15 entre 3:00 y 16:00 NY (Londres + Nueva York).
     Son 6 pruebas.
   - EXPLORATORIAS: todo lo demás (M2, H1, S3, S5, S6, S7, E2, E3, variantes). Se reportan,
     pero NO pueden convertir el veredicto en positivo.
2. División de datos: primer 60 % de la historia = muestra de desarrollo; último 40 % = prueba
   final, que no se mira hasta el final y se usa una sola vez. Además, haz un walk-forward
   (ventanas de 6 meses de desarrollo y 2 de prueba) para las 6 pruebas principales.
3. Prohibido ajustar parámetros mirando la prueba final. Si cambias algo después de verla, dilo
   explícitamente y considera ese resultado contaminado.
4. Control por pruebas múltiples: reporta cuántas variantes probaste en total. Para las 6
   principales usa corrección de Bonferroni (o Holm) sobre el p-valor de la expectativa > 0.
5. Línea base aleatoria: para cada prueba principal genera 1.000 simulaciones con entradas al azar
   (misma dirección permitida por el estado 20/200, misma cantidad de operaciones, mismas horas,
   misma gestión y mismos costos). Si el setup no supera al azar (p < 0.05), el patrón de velas no
   aporta nada.
6. Pruebas de estrés: spread × 1.5; deslizamiento de 0.1 × ATR por operación; resultados por año, por
   sesión (Asia, Londres, Nueva York), por dirección (largos/cortos) y con y sin días de noticias de
   alto impacto (NFP, IPC, FOMC) si consigues un calendario.
7. Verificación de las cifras de marketing de Velez, con intervalo de confianza del 95 %:
   - "82 % de las veces el precio sigue la dirección de la última vela de color sólido": define vela
     sólida como cuerpo ≥ 70 % del rango y mide, en M2, M5 y M15 del oro:
     (a) P(la vela siguiente es del mismo color), y
     (b) P(la vela siguiente supera el extremo de la vela sólida en esa dirección).
   - Mide también el acierto real de S1 y S2 (P de tocar +1R antes que −1R), para compararlo con
     el "84 %" y el "87 %" que anuncia.

# Paso 4 — Métricas (para cada prueba, en desarrollo y en prueba final)
Número de operaciones, % de acierto, ganancia y pérdida media en R, EXPECTATIVA en R con intervalo de
confianza del 95 % (bootstrap), profit factor, caída máxima en R, peor racha de pérdidas,
operaciones por semana, % de meses positivos, costo (spread + comisión + swap) expresado en R,
MAE/MFE medios, curva de capital, y resultado en USD por cada 0.01 lote para que lo entienda.

# Paso 5 — Criterios del veredicto (fijados ANTES de ver resultados)
- 🟢 VERDE (pasar a demo en vivo 3 meses): alguna de las 6 pruebas principales, en la prueba final,
  tiene expectativa ≥ +0.10R después de costos, con límite inferior del intervalo del 95 % > 0;
  profit factor ≥ 1.2; al menos 100 operaciones en la prueba final; supera la línea base aleatoria;
  sigue positiva con spread × 1.5; y el walk-forward es positivo en al menos el 60 % de las ventanas.
- 🟡 AMARILLO: expectativa positiva en la prueba final pero sin cumplir todo lo anterior.
  Solo justifica una prueba en demo, nunca en real.
- 🔴 ROJO: expectativa ≤ 0 en la prueba final, o no supera al azar. Conclusión: no usar.

# Paso 6 — Entregables
1. Código en `investigacion_velez/`, separado de mi bot:
   - Un módulo por setup, con tests unitarios sobre velas inventadas a mano (un caso que debe
     activar y uno que no, por setup).
   - El test anti-futuro del Paso 2.
2. `resultados/operaciones_*.csv` con TODAS las operaciones simuladas (hora del servidor y de NY,
   setup, dirección, entrada, stop, salida, R, costos), para que pueda revisar ejemplos en el
   gráfico de MT5.
3. `resultados/informe.md` (o HTML) con tablas y gráficos, y al principio un RESUMEN EN ESPAÑOL
   SENCILLO (no soy programador):
   - el color del veredicto;
   - cuánto se gana o pierde por operación y al mes con 1 % de riesgo;
   - qué tan mala puede ser una racha;
   - si las cifras del 82/84/87 % se cumplen en el oro;
   - qué recomiendas para mi cuenta real.
4. Si el veredicto es VERDE o AMARILLO: propón (sin implementarlo todavía) cómo añadir el setup a
   mi bot SOLO como alerta por Telegram (nunca ejecución automática), registrando TODAS las señales
   para comparar después lo real contra lo simulado.

# Forma de trabajar
- Avanza por pasos y muéstrame el resultado de cada paso antes de seguir al siguiente.
- Si una regla es ambigua, elige la interpretación más conservadora, anótala en el informe y sigue.
- No me digas que algo "funciona" sin los números de la prueba final que lo respalden.

==================== FIN DEL PROMPT ====================
```

---

## Notas para ti (no hace falta pegarlas)

- **Qué esperar:** lo más probable, por la evidencia disponible, es un veredicto 🔴 o 🟡. Si sale 🟢, igual
  se prueba 3 meses en demo antes de usarlo con dinero real.
- **Por qué tanto protocolo:** con suficientes variantes, *cualquier* método parece ganador en el pasado.
  La prueba final intocable, la línea base aleatoria y el límite de pruebas principales evitan ese
  autoengaño.
- **Si usas el proyecto `semaforo`** (este repositorio): cuando tengas un setup ganador, se puede escribir en
  `semaforo/strategy.py` con la firma `signals(f) -> (compras, ventas)`. Así `/senales` y `/ranking` lo
  vigilan en vivo.
