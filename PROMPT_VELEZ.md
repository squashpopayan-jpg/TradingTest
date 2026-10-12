==================== INICIO DEL PROMPT ====================

# Rol
Eres un desarrollador cuantitativo riguroso y escéptico. Tu trabajo NO es hacer que una estrategia
parezca rentable. Tu trabajo es averiguar con datos reales, después de costos, si las reglas que
siguen (una versión programada del método de Oliver Velez) tienen ventaja (expectativa positiva)
en el oro (XAUUSD) con MI bróker, y darme un veredicto honesto. Un "no funciona" bien demostrado
vale tanto como un "sí".

# Contexto
- Opero oro en MetaTrader 5 con cuenta REAL. En este PC tengo una aplicación propia (esta carpeta)
  que se conecta a MT5 y me envía señales por Telegram. No soy programador.
- Quiero probar el método que Oliver Velez enseña en YouTube (@OliverVelezTrading y
  @OliverVelezTradingEnEspañol): medias simples de 20 y 200, "velas elefante", "Bull/Bear 180",
  "Red/Green Bar Ignored", retrocesos a la media de 20 y colas.
- Sus materiales anuncian porcentajes, ninguno con metodología publicada:
  * 82 %: su "Manual del Trader Junior" (PDF en tradingolivervelez.com) dice "82 % de las veces, la
    acción va a continuar el camino de la última vela de color sólido" (y "80 % de seguimiento" tras
    una vela verde sólida). Habla de ACCIONES.
  * 84 %: video "Cómo predecir el siguiente movimiento con un 84 % de probabilidad".
  * 87 %: video "La Regla del 87 % de Continuación".
  * 90 %: video "Gana 9 de cada 10 Operaciones con este Patrón de Trading (Toro 180)".
  * 88 %: video sobre la jugada "crash into support" ("choque contra el soporte"), que dice tener
    "un 88 % de éxito".
  No sabemos qué mide exactamente cada cifra.
- Advertencias que debes tener presentes todo el tiempo:
  * Velez diseñó el método para ACCIONES de EE. UU. en la apertura de Nueva York, con velas de
    2 minutos. No encontramos reglas suyas específicas para oro. Ha comentado el oro en
    entrevistas y afirma que su método sirve para "cualquier mercado y temporalidad", algo que
    nadie ha comprobado. Hay que adaptarlo, y cada adaptación es una decisión nuestra, no de él.
  * Velez no publica reglas exactas. Lo que sigue viene de scripts de TradingView, resúmenes de
    terceros (Scribd, Cheatography, blogs) y, solo para la definición general de vela elefante y
    el 82 %, de su manual. En el código y en el informe marca cada umbral como:
    [T] = de terceros (cita la fuente), o [N] = decisión nuestra.
  * Por eso, el veredicto será sobre ESTAS reglas programadas, no sobre la parte discrecional que
    él enseña.
  * SÍ hay fuente primaria disponible: su "Curso de Análisis Técnico" (8 partes) y su serie "Trade
    the Open Like a Boss" en YouTube. En el Paso 0B descargarás sus transcripciones y extraerás de
    ahí las reglas con sus propias palabras. Esas reglas se marcan [V] (Velez, con video y minuto) y
    tienen prioridad sobre las [T] y [N] de este prompt.

# Reglas de seguridad (NO negociables)
1. PROHIBIDO OPERAR. Lista BLANCA: lo único que puedes llamar de MetaTrader5 es
   initialize (sin credenciales), last_error, version, terminal_info, account_info, symbols_get,
   symbol_select, symbol_info, symbol_info_tick, copy_rates_from, copy_rates_from_pos,
   copy_rates_range, copy_ticks_from, copy_ticks_range, history_deals_get, order_calc_profit y
   order_calc_margin (estas dos solo calculan). Cualquier otra función (order_send, order_check,
   positions_*, orders_*, login, shutdown…) está PROHIBIDA.
   Candado técnico obligatorio: crea investigacion_velez/guardia_mt5.py. Debe importar
   MetaTrader5 y reemplazar order_send, order_check y login por funciones que lancen una
   excepción. Todo script de la investigación usa MT5 SOLO importando esa guardia. Añade un test
   que busque 'order_send', 'order_check' y '.login(' en investigacion_velez/ fuera de
   guardia_mt5.py y que falle si los encuentra.
2. Credenciales y datos de la cuenta:
   a) NO abras, leas ni muestres config.toml, .env ni ningún archivo con tokens, contraseñas o
      login. Si necesitas ver la estructura, usa config.example.toml. Si un archivo resulta tener
      secretos, no repitas su contenido.
   b) Conéctate SOLO con mt5.initialize() SIN login, password ni server (llamar a login o pasarle
      credenciales cambiaría la cuenta de la terminal que usa mi bot). Si hay más de una terminal
      instalada, usa initialize(path=...) con la ruta que yo te dé. Si falla, muéstrame
      mt5.last_error() y espera. NO busques credenciales ni me las pidas.
   c) De account_info() usa solo currency, leverage y trade_mode (para saber si es demo o real). No
      imprimas ni guardes login, name, server, balance ni equity.
   d) De history_deals_get() muestra solo totales: la comisión por lote y cuántas operaciones usaste
      para calcularla. Nunca operaciones sueltas, tickets ni ganancias.
   e) Nada sale de este PC: ni git push, ni gists, ni subidas a webs o APIs, ni mensajes con mi bot
      de Telegram. Única descarga de internet permitida: las transcripciones de YouTube del Paso 0B,
      con youtube-transcript-api y SIN iniciar sesión. Nunca me pidas mi cuenta, contraseña ni
      cookies de Google/YouTube.
3. No modifiques nada fuera de investigacion_velez/. No ejecutes, arranques ni importes módulos de
   mi app que inicien el bot, el escáner o Telegram, y tampoco ejecutes los .bat de arranque. Un
   segundo proceso con el mismo token de Telegram rompe el bot en vivo. Si quieres reutilizar una
   función (por ejemplo, la que descarga velas), COPIA su código a investigacion_velez/. No toques
   config.toml ni los archivos de registro de mi bot (por ejemplo registro_senales.csv).
   Si la carpeta es un repositorio git: crea UNA vez la rama `investigacion-velez` con
   `git switch -c investigacion-velez` y haz solo commits locales. Prohibido push, pull, merge,
   rebase, reset, stash y checkout a otras ramas. Crea investigacion_velez/.gitignore con datos/,
   resultados/ y .venv/.
4. Crea un entorno virtual propio: `python -m venv investigacion_velez\.venv`. Instala ahí numpy,
   pandas, matplotlib, scipy, tzdata, pytest, MetaTrader5 y youtube-transcript-api (pyarrow es
   opcional). NUNCA instales
   ni actualices paquetes en el Python que usa mi bot. Para cualquier otro paquete pídeme permiso
   y dime en una frase para qué sirve.
5. Procesos:
   - No cierres, reinicies ni mates MetaTrader 5 ni ningún proceso python que ya esté corriendo
     (puede ser mi bot).
   - No llames a mt5.shutdown(): deja que el script termine solo.
   - Nada de procesos en segundo plano, bucles ni tareas programadas. Todo script debe terminar.
   - Si un cálculo va a tardar más de unos 10 minutos, avísame y pártelo en trozos que guarden en
     disco y se puedan reanudar.
6. Si algo de este prompt choca con lo que ves en mi código o en los datos, PARA y pregúntame.

# Forma de trabajar y puntos de control (PC)
- En cada PC te detienes, me muestras lo pedido en español sencillo (máximo 15 líneas) y ESPERAS a
  que escriba "OK, sigue". Entre un PC y otro trabajas sin preguntarme. Los puntos de control son:
  * PC1, fin del Paso 0: datos del símbolo, horario, comisión, spread y plan.
  * PC1B, fin del Paso 0B: ficha de reglas sacadas de las transcripciones de Velez.
  * PC2, fin del Paso 1: historia disponible, horario verificado y viabilidad.
  * PC3, antes de calcular cualquier resultado: tests pasando y ejemplos de cada setup para que yo
    los revise en mi gráfico.
  * PC4: declaración previa congelada (commit local + huella SHA-256).
  * PC5: resultados en la muestra de desarrollo. Pregúntame antes de abrir la prueba final.
  * PC6: prueba final, veredicto e informe.
- Si necesitas que decida algo técnico, dame tu recomendación y su consecuencia en una frase, para
  que yo solo responda sí o no.
- Si una regla es ambigua y no merece un PC, elige la interpretación MENOS favorable para la
  estrategia (menos operaciones, peor precio, más costo), anótala en BITACORA.md y sigue.
- Lleva investigacion_velez/BITACORA.md con:
  * fase y PC actuales;
  * decisiones e interpretaciones tomadas;
  * si la prueba final ya se abrió (sí/no y fecha);
  * problemas y próximo paso.
  Actualízalo al terminar cada paso. Si la sesión se corta, una sesión nueva debe poder continuar
  leyendo solo este archivo y este prompt.
- Estoy en Windows:
  * Abre y escribe todo archivo de texto con encoding='utf-8'.
  * Empieza cada script con sys.stdout.reconfigure(encoding='utf-8').
  * Los CSV que yo vaya a abrir en Excel guárdalos con sep=';', decimal=',' y
    encoding='utf-8-sig' (pregúntame primero si mi Excel usa coma decimal).
  * Si usas multiprocessing, pon el código bajo `if __name__ == '__main__':` y que las
    simulaciones lean los archivos guardados, sin conectarse a MT5.
- No me digas que algo "funciona" sin los números de la prueba final que lo respalden.

# Fases
- FASE 1 (mínimo viable):
  * Paso 0 y Paso 0B (transcripciones y ficha de reglas).
  * Datos de M1, M5 y M15.
  * Indicadores, S1, S2, S4 y E1, con sus tests.
  * PC3 y PC4.
  * Resultados en la muestra de desarrollo (PC5).
  * La verificación del "82 %" (Paso 3.7) en M5 y M15.
- FASE 2:
  * Prueba final de las 6 pruebas principales.
  * Línea base aleatoria, spread × 1.5 y estabilidad.
  * Veredicto e informe (PC6).
  Aquí termina el trabajo obligatorio.
- FASE 3 (solo si yo la pido después de leer el veredicto): M2, H1, S3, S4-L, S5, S6, S7, S8, E1-b,
  E2, E3, deslizamiento, noticias y desgloses. Siguen siendo exploratorias, no cambian el veredicto
  y ya deben figurar en la declaración previa de la Fase 1.

# Paso 0 — Reconocimiento
Aquí puedes escribir y ejecutar scripts cortos de solo lectura (con guardia_mt5.py). Todavía no
construyas el backtest.
1. Revisa mi app SIN abrir archivos con secretos: lenguaje, cómo se conecta a MT5, qué símbolo usa y
   si tiene funciones de descarga de velas que valga la pena copiar.
2. Dime si la terminal está en una cuenta demo o real (trade_mode comparado con
   mt5.ACCOUNT_TRADE_MODE_DEMO / ACCOUNT_TRADE_MODE_REAL) y la moneda. Si la moneda no es USD (por
   ejemplo USC en una cuenta cent), avísame.
3. Datos del símbolo (solo lectura):
   - Nombre exacto del oro en mi bróker (XAUUSD, XAUUSDm, GOLD, XAUUSD.r…). Llama a
     mt5.symbol_select(SIMBOLO, True) antes de pedir datos.
   - chart_mode: comprueba que sea mt5.SYMBOL_CHART_MODE_BID. Si no, PARA y avísame.
   - digits, point, trade_tick_size, trade_tick_value, trade_contract_size, volume_min,
     volume_step, trade_stops_level, trade_freeze_level.
   - swap_long, swap_short, swap_mode y swap_rollover3days.
4. Desfase horario del servidor:
   - Mídelo SOLO con el oro abierto (lunes a viernes, fuera de la pausa diaria). Lee
     symbol_info_tick(SIMBOLO).time dos veces con 30 s de diferencia. Si no cambia, el mercado está
     cerrado y este método no sirve.
   - Calcula desfase = (tick.time − time.time()) / 3600, usando time.time() (UTC) y NUNCA
     datetime.now(), que en mi PC da la hora de Colombia (UTC−5). Debe salir a menos de 2 minutos
     de un número entero de horas.
   - Con velas M5 de todo el histórico, arma una tabla por semana con la hora del servidor de la
     primera vela después de la pausa diaria del oro, que en Nueva York son las 18:00. Muéstrame
     si esa hora es la misma todo el año. Si cambia, dime en qué fechas, y en especial las semanas
     de marzo y de finales de octubre/principios de noviembre, cuando EE. UU. y Europa cambian de
     horario en fechas distintas.
5. Comisión real, ida y vuelta, por lote:
   - Llama a history_deals_get(datetime(2015,1,1,tzinfo=timezone.utc),
     datetime.now(timezone.utc)+timedelta(days=2), group="*XAU*,*GOLD*").
   - Quédate solo con los deals de compra y venta y agrúpalos por position_id.
   - Por posición, suma commission + fee de TODOS sus deals (entrada, salida y parciales) y divide
     por el volumen de entrada.
   - Muéstrame solo la mediana por lote y cuántas posiciones usaste.
   - Si la cuenta es demo, si no hay historial o si sale 0, pregúntame la comisión de mi cuenta
     real y el tipo de cuenta.
   - En la simulación, comisión en precio = comisión_por_lote / trade_contract_size (con contrato
     de 100 oz, 7 USD por lote = 0.07 por onza).
6. Pregúntame mi balance aproximado y el lote que uso normalmente. Si uso 0.01 (el mínimo), no puedo
   cerrar media posición. En ese caso, declara ANTES de ver resultados que las pruebas principales
   usan E1 sin cierre parcial.
7. Pregúntame si sigo alguna regla de los videos recientes de Velez que este prompt no cubre, por
   ejemplo:
   - "Esta señal de SMA de 20, 50 y 200 me dice cuándo comprar";
   - "Cuando esto pase, ignora la SMA de 200";
   - "La señal de la SMA 200 plana que busco";
   - "La regla de la SMA 20 que acelera tu trading";
   - "La regla del 87 % de continuación";
   - "Cómo predecir el siguiente movimiento con un 84 % de probabilidad".
   Si te describo una regla, prográmala como variante EXPLORATORIA y anótala ANTES de ver
   resultados. Nunca inventes el contenido de un video a partir de su título.
8. Muéstrame un plan corto.
→ PC1.

# Paso 0B — Transcripciones de Velez (fuente primaria)
1. Con youtube-transcript-api (dentro de .venv y SIN iniciar sesión) descarga las transcripciones de
   estos videos. Pide primero el idioma original del audio (inglés en @OliverVelezTrading, español
   en el canal en español) y, si no existe, el que haya. Guarda cada una en
   investigacion_velez/transcripciones/<ID>.txt con el título, la URL y marcas de minuto.
   Curso de Análisis Técnico:
     a373O-g99iQ  Parte 1 // La Poderosa Barra del Elefante
     -KBwT9bG6EU  Part 2 // Putting The Odds In Your Favour
     oTZpGco0glA  Part 3 // The Powerful Bull And Bear 180
     pqY5Rh7_Yx0  Parte 4 // Las medias móviles
     TgEJyRax0oY  Parte 5 // Ubicaciones y estados de trading
     3AFTTdeQGO8  Parte 6 // Ejemplos de trading en largo
     U5OAXnM_sV4  Parte 7 // Ejemplos de trading en corto
     JRYxgF47i94  Parte final
   Trade the Open Like a Boss (partes 1 a 12):
     DNBHykyaPzY YMgSADf-iig eka4l-tLyqE R1kapvSlN0U wSX-Ia_Nh_A 6vglvq9Xc9Y
     Qn4h83mBXXM B99hAu5fQG8 cTARRHOflEM WzrT6CsZrbA ROS3rgsoofI CtmQs3nG8P4
   Videos con cifras o reglas concretas:
     ylfWhJlA3wI  Gana 9 de cada 10 operaciones (Toro 180)          → el "90 %"
     D-_OUuxwEl8  Predecir el siguiente movimiento con un 84 %      → el "84 %"
     w7QbBubxCG4  La regla del 87 % de continuación                 → el "87 %"
     ye8gK7fh314  88 % de éxito, jugada "crash into support"         → el "88 %"
     5V-9Tg7X3pg  Mi sistema completo de gestión de operaciones
     5Lq2ceN0MgY  La guía completa de las medias móviles
     -kxuBqoAxcQ  Señal de SMA de 20, 50 y 200
     5gRIfh5rhOo  Cuando esto pase, ignora la SMA de 200
     BEETndVHxgo  La señal de la SMA 200 plana
     DRKia8MzwLo  La regla de la SMA 20 que acelera tu trading
     Aea_oxMtW4A  La señal de reversión n.° 1
   Si YouTube bloquea la descarga (raro desde una conexión de casa), dime qué IDs fallaron. Yo puedo
   abrir cada video, tocar "Mostrar transcripción" y pegarte el texto.
2. Lee las transcripciones y escribe investigacion_velez/FICHA_REGLAS.md. Para cada concepto (vela
   elefante, Bull/Bear 180, medias 20/200 y estados, ubicaciones, colas, RBI/GBI, entradas, stops,
   parciales, trailing, horario, y qué miden el 84/87/88/90 %), incluye:
   - la regla tal como la dice Velez, con CITA TEXTUAL corta, ID del video y minuto;
   - si da números (tamaño de la vela elefante, cuánto cuerpo, cuántas velas de retroceso,
     dónde va el stop, cuándo toma ganancias), cítalos exactamente;
   - qué queda discrecional o solo se ve en el gráfico (no lo inventes);
   - dónde coincide y dónde contradice las reglas [T]/[N] del Paso 2.
   Cuidado: las transcripciones automáticas cometen errores ("20" por "200", "eight" por "a").
   Si una frase clave es dudosa, márcala y pregúntame el minuto para que yo lo escuche.
3. Ajuste ANTES de ver cualquier resultado:
   - Si una regla [V] es clara y numérica, reemplaza a la [T]/[N] equivalente en S1, S2-A y S4
     (siguen siendo exactamente 6 pruebas principales). La versión anterior pasa a exploratoria.
   - Si las transcripciones dejan claro qué miden el 84, 87 u 88 %, prográmalo como prueba de
     verificación del Paso 3.7.
   - Si Velez describe un setup que es claramente su favorito y no está en este prompt, agrégalo
     como EXPLORATORIO. No cambia las 6 principales.
→ PC1B: muéstrame la ficha resumida (qué cambia respecto al Paso 2 y por qué) y espera mi OK.

# Paso 1 — Datos
1. ANTES de descargar, pídeme que ponga "Máx. barras en el gráfico" en "Ilimitado" (Ctrl+O, pestaña
   Gráficos) y que reinicie MetaTrader 5. Avísame de que mi bot perderá la conexión durante el
   reinicio. El límite de barras se cuenta hacia atrás desde hoy y por temporalidad. Partir la
   descarga en trozos NO lo evita.
2. Descarga velas con copy_rates_range en trozos mensuales (para controlar memoria y errores).
   - Llama a symbol_select antes.
   - Si un trozo devuelve None o vacío, guarda last_error(), espera unos segundos y reintenta hasta
     3 veces.
   - Une los trozos, quita duplicados por time y descarta la última vela si no ha cerrado.
   - Fechas de entrada: datetime(..., tzinfo=timezone.utc) con valores que representen hora del
     servidor.
   - Temporalidades: M1, M5 y M15 en la Fase 1 (M2 y H1 solo en la Fase 3), todas con el MISMO
     periodo, idealmente 3 años o más. MT5 construye todas las temporalidades a partir de M1.
   - Muéstrame la primera y la última fecha de cada una.
   - Si no hay al menos 2 años de M5, avísame.
3. Guarda cada serie en investigacion_velez/datos/ (Parquet o CSV) con: time_server, open, high, low,
   close, tick_volume y spread (en puntos y en precio).
4. Conversión de horas (CRÍTICO):
   - El campo time de copy_rates_* y copy_ticks_* es la hora del SERVIDOR escrita como segundos desde
     1970. NO es UTC. Conviértelo con pd.to_datetime(df['time'], unit='s'), sin utc=True, y llama a
     esa columna time_server. Nunca le apliques tz_localize('UTC').
   - Para pasar a Nueva York usa la pausa diaria del oro, que empieza a las 17:00 NY:
     desfase = hora del servidor a la que empieza la pausa (las 00:00 cuentan como 24) − 17.
     Si el desfase es igual todo el año, aplícalo como constante. Si cambia, aplícalo semana a semana.
   - Después localiza time_ny en America/New_York y obtén time_utc a partir de ella.
   - Test obligatorio:
     (a) en 5 fechas repartidas por el año, incluidas semanas de marzo y de finales de
         octubre/principios de noviembre, la primera vela tras la pausa debe salir a las 18:00 NY;
     (b) en 3 viernes de NFP (primer viernes del mes), la vela M5 de mayor rango del día debe estar
         a las 8:30 NY.
     Si no se cumple, PARA.
   - En MT5 el time de cada vela es su hora de APERTURA, y su información solo existe cuando cierra.
     No reetiquetes velas. Las ventanas horarias se aplican a la vela de ENTRADA (t+1).
5. Spread:
   - Descarga ticks con mt5.COPY_TICKS_INFO, de un día en un día, en al menos 3 periodos (por
     ejemplo, una semana de hace 2 años, una de hace 1 año y las 2 últimas).
   - Compara, por hora de NY, el spread de las barras con el de los ticks. En muchos brókeres el de
     las barras es el mínimo de la vela y subestima el costo.
   - Si las barras subestiman, usa spread_modelo = spread_barra × factor(hora NY), donde
     factor = mediana(spread_ticks) / mediana(spread_barras) de esa hora.
   - No apliques el spread en dólares de hoy a velas antiguas, porque el precio del oro cambió
     mucho.
   - Reporta el costo medio en R por año.
6. Control de calidad: velas duplicadas, huecos fuera del fin de semana y de la pausa, spread 0 o
   absurdo, y picos de spread en la reapertura.
7. Viabilidad (antes de calcular ganancias): cuenta solo las SEÑALES de cada prueba principal y
   estima cuántas operaciones caerán en la prueba final. Si alguna no puede llegar a 100, NO cambies
   el protocolo: déjalo escrito en la declaración previa (esa prueba solo puede dar AMARILLO o NO
   CONCLUYENTE) y pregúntame si quiero intentar conseguir más historia.
→ PC2 (historia disponible, horario verificado, spread y viabilidad).

# Paso 2 — El método en reglas exactas
Notación: t = última vela CERRADA. La orden se coloca para la vela t+1. Todo se calcula con los
precios BID del gráfico.
Estas son las reglas por defecto. Donde la FICHA_REGLAS.md del Paso 0B tenga una regla [V] clara,
manda la [V] (decidido en el PC1B, antes de ver resultados).

## Indicadores (solo con velas cerradas)
- SMA20, SMA200 y SMA50 del cierre (SIMPLES, no exponenciales). La SMA50 se usa solo en una
  variante exploratoria. SMA8 solo para la variante E1-b.
- ATR(14) de Wilder [N]. NO es parte del método de Velez: lo usamos para trasladar al oro las
  distancias que él da en "centavos por acción".
- rango(t) = high − low; cuerpo(t) = |close − open|.
- rango_medio(t) = media del rango de las 10 velas ANTERIORES a t (sin incluir t). Para una vela de
  control t−1 se usa rango_medio(t−1).
- buffer(t) [N] = max(spread_ref(t), 0.05 × ATR(t)). spread_ref(t) es el spread conocido al CIERRE de
  t (el de la barra t o el del modelo del Paso 1.5). Nunca uses el spread de t+1 para fijar niveles.
  Es nuestra traducción de su "un centavo más allá".

## Filtro de contexto: el "estado" 20/200 (no genera entradas) [T]
- Largos solo si close > SMA20 > SMA200 y la SMA20 sube: SMA20(t) > SMA20(t−5) [N].
- Cortos solo si close < SMA20 < SMA200 y la SMA20 baja.
- Precio entre la SMA20 y la SMA200: no se opera. Es la lectura estricta. La fuente dice "hacer menos
  o no operar".
- Variantes EXPLORATORIAS del filtro, inspiradas solo en títulos de sus videos:
  * F-20: close > SMA20 y SMA20 subiendo, sin mirar la SMA200.
  * F-20/50/200: close > SMA20 > SMA50 > SMA200.
- "Narrow state" [N]: las fuentes usan |SMA20 − SMA200| / precio < 1 % sobre cierres diarios, lo que
  no tiene sentido en M5/M15. Lo definimos así: narrow si |SMA20 − SMA200| está en el 10 % más bajo
  de sus 1.000 valores ANTERIORES (solo pasado). Variante: < 0.5 × ATR.

## Setups
S1 — Vela elefante ("igniting bar") a favor del estado
  - Versión PRINCIPAL [T, script "Elephant Bar by Oliver Velez" de Dreadblitz en TradingView]:
    rango(t) ≥ 1.3 × rango_medio(t) y cuerpo(t) ≥ 0.7 × rango(t), del color del estado.
    EXPLORATORIAS: k = 2.0 con cuerpo ≥ 0.6; k = 3.0 con cuerpo ≥ 0.6 (algunas fuentes en español
    hablan de "al menos 3 veces").
  - Ubicación [T, número N]: la vela "nace" en una media. Su low (en largos) está a ≤ 0.5 × ATR de la
    SMA20 o de la SMA200.
  - Entrada: orden stop en high(t) + buffer (largos) o low(t) − buffer (cortos), válida SOLO en la
    vela t+1.
  - Stop inicial: low(t) − buffer (largos) / high(t) + buffer (cortos).

S2 — Bull 180 / Bear 180 (dos velas) [T]
  - Vela de control t−1: bajista (para Bull 180), cuerpo ≥ 0.5 × rango y rango ≥ rango_medio(t−1).
  - Vela t: alcista, cuerpo ≥ 0.5 × rango y cierra por encima del open de t−1 (envuelve su cuerpo).
  - Ubicación [N]: alguna de las dos velas toca la SMA20 o la SMA200, o queda a ≤ 0.5 × ATR de ellas.
  - Variante A (PRINCIPAL): exige el estado 20/200 a favor (continuación tras un retroceso).
    Variante B (EXPLORATORIA): sin filtro de estado (reversión pura).
  - Entrada: stop en high(t) + buffer. Stop inicial: min(low(t−1), low(t)) − buffer.
  - Bear 180: espejo exacto.

S3 — Red Bar Ignored (RBI) / Green Bar Ignored (GBI) [T, script brasileño; EXPLORATORIA]
  - Filtro base: close > SMA20 (variante: estado 20/200 completo).
  - Vela de control c = t−1: alcista, rango ≥ rango_medio(t−1) y cuerpo ≥ 0.6 × rango.
  - Vela ignorada t: bajista, rango ≤ 0.5 × rango(c), con su cuerpo dentro del tercio superior de c:
    min(open, close) de t ≥ low(c) + 2/3 × rango(c).
  - Entrada base: stop en max(open(t), close(t)) + buffer, es decir, la rotura del cuerpo de la
    ignorada. Variante: high(t) + buffer.
  - Stop inicial: low(t) − buffer. GBI: espejo para cortos.

S4 — Retroceso a la SMA20 ("beso de la 20") [T, setup Pristine de swing trasladado a intradía]
  - Estado largo con la SMA20 subiendo.
  - Las 3 a 5 velas ANTERIORES a t (sin contar t) tienen máximos descendentes.
  - La vela t toca la media sin perforarla de verdad [N]: SMA20 − 0.25 × ATR ≤ low(t) ≤ SMA20 + 0.1 × ATR,
    y close(t) > SMA20.
  - Entrada: stop en high(t) + buffer. Stop inicial: mínimo del retroceso − buffer.
  - PRINCIPAL: SIN exigir vela de giro. Variante EXPLORATORIA: exigir que t tenga una cola inferior
    ≥ 2/3 del rango o sea un Bull 180.

S4-L — Compra límite en la SMA20 (EXPLORATORIA) [T: "deja órdenes límite en la 20 en los
  retrocesos"; todos los números N]
  - Con la vela t cerrada: estado largo, SMA20 subiendo y close(t) ≥ SMA20(t) + 0.5 × ATR.
  - Orden: compra límite en SMA20(t), válida solo en la vela t+1. Se recoloca en cada vela mientras
    siga la condición, hasta 10 velas.
  - Llenado: si low_bid(t+1) + spread < nivel (tiene que atravesarlo, no basta con tocarlo). Se llena
    al nivel, o al open si la vela abre por debajo.
  - Stop inicial: SMA20(t) − 0.5 × ATR (variante: 1.0 × ATR).
  - Cortos: espejo. No sumamos tamaño, aunque Velez suele hacerlo. Dilo en el informe.

S5 — Cola de giro [T: cola ≥ 2/3, Cheatography; EXPLORATORIA]
  - Cola inferior (largos) ≥ 2/3 del rango.
  - Variante A (agotamiento) [N]: la vela está a ≥ 2 × ATR por debajo de la SMA20. El objetivo es la
    SMA20 de la última vela cerrada, actualizada vela a vela.
  - Variante B (continuación): al final de un retroceso a la SMA20 en estado largo, como en S4.
  - Entrada: stop en high(t) + buffer. Stop inicial: low(t) − buffer.

S6 — Salida del narrow state (EXPLORATORIA): hubo narrow state en alguna de las 20 velas previas y
  ahora aparece S1 o S2 a favor del nuevo orden de las medias.

S7 — Adaptación de la "trampa de apertura" / Fabulous 4 (EXPLORATORIA, invención nuestra: el oro
  cotiza unas 23 h y no tiene hueco diario salvo el lunes). Declara dos versiones antes de ver datos:
  a) "Sesión de acciones": ancla 9:30 NY; cierre previo = el de la vela que termina a las 16:00 NY;
     últimos 45 min = de 15:15 a 16:00 NY.
  b) "Sesión COMEX": ancla 8:20 NY; cierre previo = 13:30 NY; últimos 45 min = de 12:45 a 13:30 NY.
     Reporta aparte los días con datos de EE. UU. a las 8:30.
  - No uses las 17:00 NY: es la pausa diaria del oro.
  - Caja = [mín, máx] de la SMA20 y la SMA200 de la última vela cerrada antes del ancla, del cierre
    previo y del máximo y mínimo de los últimos 45 min.
  - El "precio en el ancla" es el open de la vela del ancla.
  - Si está dentro de la caja: no se opera ese día. Si está por encima: solo largos con S1, S2 o S4
    en las 2 horas siguientes. Si está por debajo: solo cortos.

S8 — Rebote en la SMA200 (EXPLORATORIA; inspirada en títulos de sus videos, números N)
  - Contexto: SMA20 > SMA200 y la SMA200 sube o está plana: SMA200(t) ≥ SMA200(t−20) − 0.25 × ATR.
    Solo para este setup se ignora la regla de "entre medias no se opera".
  - Disparador: low(t) ≤ SMA200 + 0.1 × ATR, close(t) > SMA200, y t es un Bull 180 (con t−1) o tiene
    una cola inferior ≥ 2/3 del rango.
  - Variante "crash into support" (definición nuestra; pídeme que la confirme con su video): además,
    las 3 velas previas a t son bajistas y su rango medio es ≥ 1.5 × rango_medio.
  - Entrada: stop en high(t) + buffer. Stop inicial: min(low(t), SMA200) − buffer.

## Gestión de la operación
- Regla de la SMA200 [T] (base para S1, S2 y S4): en largos, si la entrada está a ≤ 1 × ATR por encima
  de la SMA200 y el stop calculado con la vela queda por encima de la SMA200, baja el stop a
  SMA200 − buffer. En cortos, espejo. Reporta cuántas operaciones cambió.
- Filtro de riesgo [N]: si el stop inicial queda a más de 3 × ATR de la entrada, se descarta la
  operación.
- E1 (PRINCIPAL; gestión según resúmenes de terceros; parcial y filtro son N):
  * Trailing [T]: cuando 2 velas cerradas después de la entrada (contando la vela de entrada) cierran
    por encima del precio de entrada (largos), el stop empieza a seguir.
  * El trailing se actualiza solo al CIERRE de cada vela j:
    stop_nuevo = max(stop_actual, low(j) − buffer(j)), y rige desde la vela j+1. Nunca uses el
    low/high de la vela en curso. El stop solo se mueve a favor.
  * Parcial [N]: 50 % en +1R (las fuentes hablan de parciales tras un empuje de 2–3 velas, sin un R
    fijo). Si en el Paso 0 quedó que uso 0.01 lote, en las principales NO hay parcial.
- E1-b (EXPLORATORIA): parcial del 50 % al cierre de la 3.ª vela a favor (contando la de entrada); el
  resto sale al primer cierre por debajo de la SMA8 (largos).
- E2 (EXPLORATORIA): take profit fijo en 1.5R (variante 2R), sin trailing.
- E3 (EXPLORATORIA): salida al open de la vela siguiente al primer cierre por debajo de la SMA20
  (largos) o por encima (cortos).
- Para todas:
  * Modo intradía (M5) [N, regla nuestra]: cierre obligatorio al open de la vela de las 16:00 NY.
  * M15/H1: máximo 48 velas abiertas; nada abierto el fin de semana (cierre al open de la vela de
    las 16:00 NY del viernes).
- Swap:
  * El rollover ocurre a las 00:00 hora del SERVIDOR.
  * swap_rollover3days usa la numeración de MT5 (0 = domingo … 3 = miércoles). En Python,
    dia = (swap_rollover3days − 1) % 7.
  * Pásalo a USD por lote según swap_mode: si es SYMBOL_SWAP_MODE_POINTS,
    swap × point × trade_contract_size; si es SYMBOL_SWAP_MODE_CURRENCY_DEPOSIT, ya viene en USD
    por lote; con otro modo, pregúntame.
  * Avisa de que se aplica el swap ACTUAL a toda la historia.

## Modelo de ejecución (aquí se esconden casi todos los errores)
- Todos los niveles (entrada, SL, TP) se calculan sobre el BID, como yo los pondría a mano en el
  gráfico.
- BUY STOP en el nivel L: se activa cuando high_bid(t+1) + spread ≥ L (es decir, cuando el ASK llega
  a L). Se llena a L, o a open_bid(t+1) + spread si la vela abre por encima.
- SELL STOP en el nivel L: se activa cuando low_bid(t+1) ≤ L. Se llena a L, o a open_bid si la vela
  abre por debajo.
- SL/TP de un largo: se ejecutan con el BID (low_bid ≤ SL; high_bid ≥ TP).
- SL/TP de un corto: se ejecutan con el ASK (high_bid + spread ≥ SL; low_bid + spread ≤ TP).
- El spread se paga UNA sola vez, a través de estas reglas. No lo restes otra vez aparte.
- Huecos: si una vela abre más allá del stop (o del trailing), la salida es al open de esa vela, del
  lado bid/ask correcto. La pérdida puede ser peor que −1R: no la recortes. Si la operación cruza la
  pausa diaria, usa el spread REAL de las velas de la reapertura.
- Ambigüedad dentro de una vela:
  * En la vela de ENTRADA: si se activa la orden y también se toca el stop inicial, es pérdida
    completa. En la vela de entrada nunca acredites el parcial, el TP ni el arranque del trailing
    usando solo la vela M5/M15.
  * En cualquier vela: si se tocan el stop y el objetivo, se tocó PRIMERO EL STOP.
  * Para las pruebas principales, resuelve estos casos con velas M1, con las mismas reglas de
    bid/ask. Si la M1 también es ambigua, asume el peor orden.
  * Reporta qué porcentaje de la prueba final quedó cubierto por M1 y la expectativa con y sin esa
    resolución.
- Distancia mínima del bróker: descarta, y cuenta aparte, las órdenes cuyo nivel quede a menos de
  trade_stops_level × point del precio al cierre de t, o cuyo stop quede a menos de esa distancia de
  la entrada. En real, el bróker las rechazaría.
- Una sola operación abierta a la vez por prueba. Sin piramidar.
- Comisión: se cobra por el volumen de cada cierre (también los parciales).
- Deslizamiento: 0 en el escenario base. En la prueba de estrés, 0.1 × ATR en la entrada y en cada
  salida por stop o trailing (las salidas por objetivo no deslizan).
- Sin mirar al futuro. Escribe tests que lo demuestren:
  (a) si se modifican velas posteriores a t, la señal en t no cambia;
  (b) si se modifican velas posteriores a j, el resultado de una operación hasta la vela j no cambia
      (trailing, E3, objetivo de S5).
- Tests de ejecución con velas inventadas a mano, uno por cada caso de activación y llenado de
  arriba (buy stop, sell stop, hueco, ambigüedad en la vela de entrada).

# Paso 3 — Protocolo para no engañarnos
1. Pruebas PRINCIPALES (exactamente 6; son las únicas que deciden el veredicto):
   - S1 versión principal, S2 variante A y S4 sin vela de giro, las tres con E1 y la regla de la
     SMA200, en:
     (i) M5, con la vela de entrada (t+1) abriendo entre 9:30 y 11:30 NY. Las salidas siguen hasta
         las 16:00 NY y los indicadores usan todas las velas. Es la ventana más parecida a su
         "trade the open", adaptada por nosotros.
     (ii) M15, con la vela de entrada abriendo entre 3:00 y 16:00 NY (Londres + Nueva York).
   - En el escenario M5 se excluyen los feriados de la bolsa de EE. UU. y los días de cierre
     anticipado (Año Nuevo, MLK, Presidentes, Viernes Santo, Memorial Day, Juneteenth, 4 de julio,
     Labor Day, Acción de Gracias y Navidad). Se reportan aparte.
   - Todo lo demás es EXPLORATORIO: se reporta, pero NO puede mejorar el veredicto.
2. Declaración previa: ANTES de calcular ningún resultado, escribe en
   investigacion_velez/DECLARACION.md la lista exacta de pruebas (principales y exploratorias),
   parámetros, ventanas, costos y criterios. Haz un commit local y muéstrame su huella SHA-256 (PC4).
   Cualquier cambio posterior va en otro commit, con su motivo, y deja contaminado lo que dependa de
   él.
3. División de datos: UNA fecha de corte de calendario común a todas las temporalidades. El primer
   60 % de la historia es la muestra de desarrollo; el último 40 % es la prueba final, que no se mira
   hasta el PC6 y se usa una sola vez.
4. No hay parámetros que optimizar en las principales, así que no hagas walk-forward. Haz un análisis
   de ESTABILIDAD: ventanas consecutivas de 3 meses con la expectativa y el número de operaciones de
   cada una. Las ventanas de la prueba final se calculan solo cuando esta se abre.
5. Línea base aleatoria (en desarrollo y en la prueba final), 1.000 simulaciones por prueba principal:
   - Elige al azar velas t que cumplan los MISMOS filtros que el setup salvo el patrón de velas:
     mismo estado y dirección, misma ventana horaria y misma regla de "cerca de la media".
   - Usa el MISMO mecanismo: orden stop en high(t) + buffer válida una vela, y un stop inicial a una
     distancia en ATR sorteada entre las distancias reales del setup.
   - Aplica el mismo filtro de 3 × ATR, la regla de la SMA200, E1, los mismos costos y la misma
     resolución intrabar.
   - Si la orden no se activa, sortea otra vela hasta igualar el número de operaciones reales.
   - p = (1 + nº de simulaciones con expectativa ≥ la del setup) / 1.001.
6. Estadística: el intervalo del 95 % y el p-valor de "expectativa > 0" se calculan con bootstrap POR
   BLOQUES de semanas (se remuestrean semanas completas, 10.000 repeticiones). p = proporción de
   remuestras con expectativa ≤ 0. Los p-valores de las 6 principales se ajustan con Holm. Reporta
   también el bootstrap simple para comparar.
7. Verificación de las cifras de Velez (con IC del 95 %):
   - 82 % (Fase 1): define vela sólida como cuerpo ≥ 70 % del rango. Mide en M5 y M15 (y en M2 en la
     Fase 3):
     (a) P(la vela siguiente es del mismo color);
     (b) P(la vela siguiente supera el extremo de la vela sólida en esa dirección).
     Calcula también la misma probabilidad para TODAS las velas y para las NO sólidas (tasa base), y
     reporta la diferencia en puntos porcentuales. Excluye las velas con open = close y dilo.
     Con tantas velas, una diferencia "significativa" de 1-2 puntos no sirve para operar: compárala
     con el spread.
     En el informe aclara que el 82 % habla de acciones: que no se cumpla en el oro no demuestra que
     sea falso en acciones.
   - 90 % del Toro/Bull 180: para S2 (variantes A y B) mide P(tocar +1R antes que −1R) y también
     P(la operación con E1 cierra con R neto > 0), junto a las mismas métricas de la línea base
     aleatoria.
   - 84 %, 87 % y 88 %: mide solo lo que las transcripciones (Paso 0B) definan con claridad, con
     cita y minuto, y comparado contra la tasa base. Si la definición no está clara, NO supongas:
     pregúntame. Si sigue sin estar clara, repórtalas como "no verificables".
8. Pruebas de estrés (en las principales, después del veredicto base):
   - spread × 1.5;
   - deslizamiento de 0.1 × ATR;
   - resultados por año, por dirección y por sesión, con horario fijo de NY: Asia de 18:00 a 3:00,
     Londres de 3:00 a 8:00 y Nueva York de 8:00 a 17:00;
   - con y sin días de noticias. No descargues nada para esto: usa el NFP aproximado (primer viernes
     de cada mes, dilo como aproximación) y el IPC y el FOMC solo si yo te paso las fechas.

# Paso 4 — Métricas
- Definiciones:
  * 1R = |precio de entrada real − stop inicial|, en precio.
  * R neto = Σ fracción_i × (salida_i − entrada) × dirección / 1R − (comisiones + swap) / 1R.
    El spread ya está incluido en los precios bid/ask.
  * Acierto = R neto > 0. Reporta aparte el % de operaciones que tomaron el parcial y luego
    volvieron al stop.
  * Costo en R por operación = (spread de entrada + comisión + swap) / 1R. Muestra su distribución,
    no solo la media.
- Para cada prueba, en desarrollo y en la prueba final:
  * número de operaciones y % de acierto;
  * ganancia y pérdida media en R;
  * EXPECTATIVA en R con su IC 95 % (bootstrap por bloques) y su p ajustado por Holm;
  * profit factor;
  * caída máxima en R y peor racha de pérdidas;
  * operaciones por semana y % de meses positivos;
  * costo en R;
  * MAE/MFE medios;
  * curva de capital;
  * operaciones descartadas por stops_level y por el filtro de 3 × ATR.
- Dinero:
  * USD por 0.01 lote = resultado_en_precio × trade_contract_size × 0.01. Compruébalo con
    mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, SIMBOLO, 0.01, p, p + 1.0), que solo calcula.
  * Con 1 % de riesgo:
    lote = floor(riesgo_USD / (distancia_stop × trade_contract_size) / volume_step) × volume_step.
    Cuenta cuántas operaciones serían imposibles con mi balance (lote < volume_min) o tendrían un
    riesgo real mayor al 1 %.

# Paso 5 — Criterios del veredicto (fijados ANTES de ver resultados)
Cada prueba principal se evalúa por separado en la PRUEBA FINAL, aplicando estas reglas en orden. El
veredicto global es el de la mejor prueba principal. Las exploratorias nunca lo mejoran.
- ⚪ NO CONCLUYENTE: menos de 30 operaciones en la prueba final. No se interpreta su expectativa.
- 🟢 VERDE (pasar a 3 meses en demo con alertas). Debe cumplir TODO:
  * expectativa ≥ +0.10R después de costos;
  * p-valor de "expectativa > 0" ajustado por Holm < 0.05;
  * profit factor ≥ 1.2;
  * ≥ 100 operaciones;
  * supera la línea base aleatoria con p ajustado por Holm < 0.05;
  * expectativa > 0 con spread × 1.5;
  * expectativa positiva en ≥ 60 % de las ventanas de estabilidad que tengan ≥ 20 operaciones.
- 🟡 AMARILLO (como mucho, demo): no es VERDE, pero tiene ≥ 50 operaciones, expectativa > 0 y supera
  la línea base aleatoria con p sin ajustar < 0.05.
- 🔴 ROJO: cualquier otro caso. Conclusión: no usar estas reglas en real.
Aclara siempre que el veredicto es sobre estas versiones programadas (de terceros y nuestras), no
sobre la parte discrecional que enseña Velez, y que lo que no se probó tampoco tiene evidencia a
favor. Si S4-L, S8 u otra exploratoria sale mejor que las principales, se reporta como candidata para
una prueba NUEVA con datos futuros (demo), pero no cambia el veredicto.

# Paso 6 — Entregables
1. Código en investigacion_velez/, separado de mi bot:
   - guardia_mt5.py;
   - un módulo por setup;
   - tests: un caso que debe activar y uno que no, por setup; los de ejecución; los anti-futuro; el
     de la guardia; y el de conversión de horas.
2. Antes de calcular resultados (PC3): todos los tests pasan, y 5 ejemplos de cada setup principal
   con fecha y hora DEL SERVIDOR, para que yo los busque en mi gráfico de MT5 y confirme que se
   parecen a lo que enseña Velez. Si hay que corregir un detector, se corrige en ese momento, ANTES
   de la declaración previa.
3. resultados/operaciones_*.csv con TODAS las operaciones simuladas: hora del servidor y de NY,
   setup, dirección, entrada, stop, salidas, R neto y costos.
4. resultados/informe.html: un solo archivo con los gráficos incrustados, que yo abra con doble clic.
   Empieza con un RESUMEN de máximo una página en español sencillo. Si usas R, p-valor o bootstrap,
   explícalos en una frase (1R = lo que arriesgo en una operación). El resumen incluye:
   - Primera línea: el color y una frase (por ejemplo "No funciona en oro con tu bróker").
   - Resultado por operación y por mes en % de la cuenta con 1 % de riesgo, y en USD por cada
     1.000 USD de cuenta (no uses mi saldo real).
   - La peor racha de pérdidas y la peor caída, en % de la cuenta.
   - Si el 82 % y el 90 % se cumplen en el oro: sí o no, con el número medido y la tasa base.
   - Cuántas variantes se probaron en total y qué NO se probó.
   - Recomendación, SOLO una de estas: ROJO → no usarlo; AMARILLO → como mucho demo; VERDE → 3 meses
     en demo con alertas antes de pensar en real. Nunca recomiendes operarlo directamente en real
     ni subir el riesgo. Si sale ROJO, no propongas variantes para "rescatarlo".
5. Si el veredicto es VERDE o AMARILLO: propón (sin implementarlo) cómo añadir el setup a mi bot
   SOLO como alerta por Telegram, nunca como ejecución automática, registrando TODAS las señales
   para comparar después lo real contra lo simulado.

==================== FIN DEL PROMPT ====================
